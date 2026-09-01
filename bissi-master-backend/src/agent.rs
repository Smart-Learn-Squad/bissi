//! Agent loop (mirrors `core/agent.py` `BissiAgent`).
//!
//! Holds per-request conversation state, calls the llama engine, dispatches
//! tool calls through the registry, and emits the same SSE event stream the
//! Electron renderer expects:
//!   chunk | thinking | tool_start | tool_done | file_created | done | error

use std::sync::Arc;

use futures_util::StreamExt;
use serde_json::{json, Value};
use tokio::sync::mpsc;

use crate::config;
use crate::llama::{ChatChunk, LlamaEngine};
use crate::tools;

/// Payload sent to the SSE / WS stream (mirrors the Python event dicts).
#[derive(Debug, Clone)]
pub enum AgentEvent {
    Chunk(String),
    ToolStart { name: String, args: Value },
    ToolDone { name: String, result: String },
    FileCreated { name: String, file_path: String, file_name: String },
    Done { full_response: String, conversation_id: Option<i64> },
    Error(String),
    End,
}

type EventSender = mpsc::Sender<AgentEvent>;

pub struct Agent {
    engine: Arc<LlamaEngine>,
}

impl Agent {
    pub fn new(engine: Arc<LlamaEngine>) -> Self {
        Self { engine }
    }

    /// Run the agent on one user message, streaming events to `tx`.
    pub async fn process_request(&self, user_input: &str, conversation_id: Option<i64>, tx: EventSender) {
        let mut messages: Vec<Value> = vec![
            json!({"role":"user","content":user_input.to_string()}),
        ];

        for _ in 0..config::AGENT_MAX_ITERATIONS {
            match self
                .engine
                .chat_stream(messages.clone(), Some(tools::tools_payload()))
                .await
            {
                Ok(stream) => {
                    tokio::pin!(stream);
                    let mut assistant_content = String::new();
                    let mut tool_calls: Vec<tools_hack::Named> = Vec::new();

                    while let Some(chunk) = stream.next().await {
                        match chunk {
                            Ok(ChatChunk::Content(c)) => {
                                assistant_content.push_str(&c);
                                let _ = tx.send(AgentEvent::Chunk(c)).await;
                            }
                            Ok(ChatChunk::ToolCalls(calls)) => {
                                for call in calls {
                                    let _ = tx
                                        .send(AgentEvent::ToolStart {
                                            name: call.name.clone(),
                                            args: call.arguments.clone(),
                                        })
                                        .await;
                                    match tools::dispatch(&call.name, call.arguments.clone()).await {
                                        Ok(result_json) => {
                                            let _ = tx.send(AgentEvent::ToolDone {
                                                name: call.name.clone(),
                                                result: result_json.clone(),
                                            })
                                            .await;
                                            emit_file_created(&call.name, &result_json, &tx).await;
                                            tool_calls.push(tools_hack::Named {
                                                id: call.id,
                                                name: call.name,
                                                arguments: call.arguments,
                                                result: result_json,
                                            });
                                        }
                                        Err(e) => {
                                            let _ = tx.send(AgentEvent::Error(e.clone())).await;
                                        }
                                    }
                                }
                            }
                            Err(e) => {
                                let _ = tx.send(AgentEvent::Error(e.to_string())).await;
                            }
                        }
                    }

                    // If the model produced tool calls, feed results back to it.
                    if !tool_calls.is_empty() {
                        messages.push(json!({"role":"assistant","content":assistant_content,
                            "tool_calls": tool_calls.iter().map(|t| json!({
                                "id": t.id, "type":"function",
                                "function":{"name":t.name,"arguments":t.arguments}
                            })).collect::<Vec<_>>()}));
                        for t in &tool_calls {
                            messages.push(json!({"role":"tool","tool_call_id":t.id,"content":t.result}));
                        }
                        continue;
                    }

                    // No tool calls: assistant answered.
                    let _ = tx
                        .send(AgentEvent::Done {
                            full_response: assistant_content,
                            conversation_id,
                        })
                        .await;
                    let _ = tx.send(AgentEvent::End).await;
                    return;
                }
                Err(e) => {
                    let _ = tx.send(AgentEvent::Error(e.to_string())).await;
                    let _ = tx.send(AgentEvent::End).await;
                    return;
                }
            }
        }

        // Iteration cap reached without a final answer.
        let _ = tx
            .send(AgentEvent::Error("max_iterations reached".into()))
            .await;
        let _ = tx.send(AgentEvent::End).await;
    }
}

/// Extract a `file_created` event when a tool result carries a `path`
/// (mirrors the Python `on_tool_done` path sniffing).
async fn emit_file_created(name: &str, result_json: &str, tx: &EventSender) {
    if let Ok(parsed) = serde_json::from_str::<Value>(result_json) {
        if let Some(path) = parsed.get("path").and_then(Value::as_str) {
            let file_name = std::path::Path::new(path)
                .file_name()
                .map(|s| s.to_string_lossy().to_string())
                .unwrap_or_else(|| path.to_string());
            let _ = tx
                .send(AgentEvent::FileCreated {
                    name: name.to_string(),
                    file_path: path.to_string(),
                    file_name,
                })
                .await;
        }
    }
}

/// Lightweight local type to avoid coupling the event loop to serde internals.
mod tools_hack {
    use serde_json::Value;

    #[derive(Debug)]
    pub struct Named {
        pub id: String,
        pub name: String,
        pub arguments: Value,
        pub result: String,
    }
}
