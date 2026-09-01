//! OpenAI-compatible client for llama.cpp (mirrors core/engine.py).
//!
//! Proxies chat completions to the GGUF server on `:8001`, aggregating
//! streamed tool-call deltas into complete OpenAI-style `tool_calls`.

use std::time::Duration;

use serde_json::{json, Value};
use thiserror::Error;

use crate::config;

#[derive(Debug, Error)]
pub enum EngineError {
    #[error("llama.cpp {0} failed: {1}")]
    Llama(&'static str, String),
    #[error("llama.cpp unreachable: {0}")]
    Transport(#[from] reqwest::Error),
    #[error("llama.cpp unavailable: service returned no usable model/health")]
    Unavailable,
}

/// One normalized stream chunk yielded by [`LlamaEngine::chat`].
#[derive(Debug, Clone)]
pub enum ChatChunk {
    /// A text delta.
    Content(String),
    /// A completed set of tool calls (triggered by finish_reason "tool_calls").
    ToolCalls(Vec<ToolCall>),
}

/// Normalized, parsed tool call (mirrors `_finalize_tool_calls`).
#[derive(Debug, Clone)]
pub struct ToolCall {
    pub id: String,
    pub name: String,
    pub arguments: Value,
}

pub struct LlamaEngine {
    model: String,
    temperature: f32,
    client: reqwest::Client,
}

impl LlamaEngine {
    pub fn new() -> Self {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(config::LLAMA_TIMEOUT_SECS))
            .build()
            .expect("reqwest client");
        Self {
            model: config::LLAMA_MODEL.to_string(),
            temperature: config::LLAMA_TEMPERATURE,
            client,
        }
    }

    /// True when llama.cpp `/v1/models` is reachable and non-empty.
    pub async fn health_check(&self) -> Result<bool, EngineError> {
        let response = self.client.get(format!("{}/v1/models", config::LLAMA_HOST)).send().await?;
        let status = response.status();
        if !status.is_success() {
            tracing::warn!(%status, "llama.cpp health: bad status");
            return Ok(false);
        }
        let body: Value = response.json().await?;
        let models = body.get("data").and_then(Value::as_array).cloned().unwrap_or_default();
        if models.is_empty() {
            return Ok(false);
        }
        let has_named = models.iter().any(|m| {
            ["id", "name", "model"].iter().any(|k| {
                m.get(*k).and_then(Value::as_str).map_or(false, |s| !s.is_empty())
            })
        });
        Ok(has_named)
    }

    /// Stream a chat completion with optional function tools.
    ///
    /// Returns a stream of [`ChatChunk`]. Text deltas come through as
    /// `Content`, tool calls are emitted whole when the finish reason marks
    /// them complete.
    pub async fn chat_stream(
        &self,
        messages: Vec<Value>,
        tools: Option<Vec<Value>>,
    ) -> Result<impl futures_util::Stream<Item = Result<ChatChunk, EngineError>>, EngineError> {
        let mut payload = json!({
            "model": self.model,
            "messages": messages,
            "stream": true,
            "temperature": self.temperature,
        });
        if let Some(tools) = tools {
            payload["tools"] = Value::Array(tools);
        }

        let response = self
            .client
            .post(format!("{}/v1/chat/completions", config::LLAMA_HOST))
            .json(&payload)
            .header("Accept", "text/event-stream")
            .send()
            .await?;

        if !response.status().is_success() {
            let status = response.status();
            return Err(EngineError::Llama("chat", format!("HTTP {status}")));
        }

        let byte_stream = response.bytes_stream();
        Ok(async_stream::stream! {
            let mut buf = String::new();
            let mut pending: Vec<(usize, ToolCall)> = Vec::new();
            let mut index: std::collections::HashMap<usize, usize> = std::collections::HashMap::new();

            let mut stream = byte_stream;
            use futures_util::StreamExt;
            while let Some(chunk) = stream.next().await {
                let chunk = match chunk {
                    Ok(c) => c,
                    Err(e) => {
                        yield Err(EngineError::Transport(e));
                        return;
                    }
                };
                buf.push_str(&String::from_utf8_lossy(&chunk));

                // Consume complete SSE "data:" lines.
                while let Some(nl) = buf.find('\n') {
                    let line = buf[..nl].trim().to_string();
                    buf.drain(..=nl);
                    if !line.starts_with("data:") {
                        continue;
                    }
                    let data = line[5..].trim().to_string();
                    if data.is_empty() || data == "[DONE]" {
                        continue;
                    }
                    let event: Value = match serde_json::from_str(&data) {
                        Ok(v) => v,
                        Err(_) => continue,
                    };
                    let Some(choice) = event.get("choices").and_then(Value::as_array)
                        .and_then(|c| c.first()) else { continue };

                    if let Some(content) = choice.get("delta").and_then(|d| d.get("content"))
                        .and_then(Value::as_str) {
                        if !content.is_empty() {
                            yield Ok(ChatChunk::Content(content.to_string()));
                        }
                    }

                    if let Some(deltas) = choice.get("delta").and_then(|d| d.get("tool_calls"))
                        .and_then(Value::as_array) {
                        for delta in deltas {
                            merge_tool_delta(delta, &mut pending, &mut index);
                        }
                    }

                    let finish = choice.get("finish_reason").and_then(Value::as_str);
                    if finish == Some("tool_calls") && !pending.is_empty() {
                        let joins = pending.split_off(0);
                        yield Ok(ChatChunk::ToolCalls(joins.into_iter().map(|(_, t)| t).collect()));
                        index.clear();
                    }
                }
            }
            if !pending.is_empty() {
                yield Ok(ChatChunk::ToolCalls(pending.into_iter().map(|(_, t)| t).collect()));
            }
        })
    }
}

impl Default for LlamaEngine {
    fn default() -> Self {
        Self::new()
    }
}

/// Accumulate streamed tool-call deltas into complete calls (mirrors
/// `_merge_tool_call_delta` + `_finalize_tool_calls`).
fn merge_tool_delta(
    delta: &Value,
    pending: &mut Vec<(usize, ToolCall)>,
    index: &mut std::collections::HashMap<usize, usize>,
) {
    let position = delta.get("index").and_then(Value::as_u64).unwrap_or(0) as usize;
    let merged_index = match index.get(&position) {
        Some(&i) => i,
        None => {
            let i = pending.len();
            index.insert(position, i);
            pending.push((
                position,
                ToolCall {
                    id: delta.get("id").and_then(Value::as_str).unwrap_or("call").to_string(),
                    name: String::new(),
                    arguments: json!({}),
                },
            ));
            i
        }
    };

    let target = &mut pending[merged_index].1;

    if let Some(id) = delta.get("id").and_then(Value::as_str) {
        if !id.is_empty() {
            target.id = id.to_string();
        }
    }

    let Some(function) = delta.get("function").and_then(Value::as_object) else {
        return;
    };

    if let Some(name) = function.get("name").and_then(Value::as_str) {
        if !name.is_empty() {
            target.name = name.to_string();
        }
    }

    if let Some(args) = function.get("arguments").and_then(Value::as_str) {
        if !args.is_empty() {
            // Accumulate raw argument JSON fragments, parse at the end.
            let raw = if target.arguments.is_null() {
                args.to_string()
            } else {
                target.arguments.as_str().map(|s| s.to_string()).unwrap_or_default() + args
            };
            // Attempt incremental parse; fall back to raw string accumulation.
            target.arguments = serde_json::from_str(&raw)
                .unwrap_or_else(|_| Value::String(raw));
        }
    }
}
