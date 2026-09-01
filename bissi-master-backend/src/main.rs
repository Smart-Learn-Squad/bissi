//! BISSI backend (Rust) — axum router bridging Electron UI and llama.cpp.
//!
//! Mirrors `api/server.py` (FastAPI). Fixed ports: llama.cpp `:8001` proxied
//! through the shared engine, this backend on `:8765`. Do NOT change ports.

mod agent;
mod config;
mod conversation;
mod llama;
mod tools;

use std::sync::Arc;

use agent::AgentEvent;
use axum::extract::ws::{Message, WebSocket};
use axum::extract::{Multipart, Path as AxumPath, State, WebSocketUpgrade};
use axum::http::StatusCode;
use axum::response::{sse::Event, IntoResponse, Response};
use axum::routing::{delete, get, patch, post};
use axum::{Json, Router};
use futures_util::StreamExt;
use serde_json::{json, Value};
use tokio::sync::mpsc;
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;

use crate::conversation::ConversationStore;
use crate::llama::LlamaEngine;

/// Shared application state.
#[derive(Clone)]
struct AppState {
    engine: Arc<LlamaEngine>,
    agent: Arc<agent::Agent>,
    conversations: Arc<ConversationStore>,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info,bissi_backend=debug".into()),
        )
        .init();

    let engine = Arc::new(LlamaEngine::new());
    let conversations = Arc::new(ConversationStore::new());
    let agent = Arc::new(agent::Agent::new(engine.clone()));

    let state = AppState { engine, agent, conversations };

    let app = Router::new()
        .route("/chat", post(chat))
        .route("/ws", get(ws_handler))
        .route("/conversations", get(list_conversations))
        .route(
            "/conversations/:id/history",
            get(conversation_history),
        )
        .route("/conversations/:id", delete(delete_conversation))
        .route(
            "/conversations/:id/title",
            patch(update_conversation_title),
        )
        .route(
            "/conversations/:id/archive",
            patch(archive_conversation),
        )
        .route("/health", get(health))
        .route("/tools", get(list_tools))
        .route("/transcribe", post(transcribe))
        .layer(CorsLayer::very_permissive())
        .layer(TraceLayer::new_for_http())
        .with_state(state);

    let addr = format!("{}:{}", config::SERVER_HOST, config::SERVER_PORT);
    tracing::info!("BISSI backend listening on {addr}");
    let listener = tokio::net::TcpListener::bind(&addr).await.expect("bind");
    axum::serve(listener, app).await.expect("serve");
}

/// Convert an `AgentEvent` into the JSON object streamed to the client
/// (`None` for the internal `End` sentinel, which is not sent).
fn to_sse_json(event: &AgentEvent) -> Option<Value> {
    match event {
        AgentEvent::Chunk(c) => Some(json!({"type":"chunk","content":c})),
        AgentEvent::Thinking(c) => Some(json!({"type":"thinking","content":c})),
        AgentEvent::ToolStart { name, args } => Some(json!({"type":"tool_start","name":name,"args":args})),
        AgentEvent::ToolDone { name, result } => Some(json!({"type":"tool_done","name":name,"result":result})),
        AgentEvent::FileCreated { name, file_path, file_name } => {
            Some(json!({"type":"file_created","name":name,"file_path":file_path,"file_name":file_name}))
        }
        AgentEvent::Done { full_response, conversation_id } => {
            Some(json!({"type":"done","full_response":full_response,"conversation_id":conversation_id}))
        }
        AgentEvent::Error(m) => Some(json!({"type":"error","message":m})),
        AgentEvent::End => None,
    }
}

fn to_sse_event(event: &AgentEvent) -> Option<Event> {
    to_sse_json(event).map(|v| Event::default().data(v.to_string()))
}

/// POST /chat — SSE stream. Mirrors the FastAPI `chat` endpoint, including
/// attached-file decoding (UTF-8 char-based truncation à la Python preview).
async fn chat(
    State(state): State<AppState>,
    mut multipart: Multipart,
) -> Response {
    let mut message = String::new();
    let mut thinking = true;
    let mut conversation_id: Option<i64> = None;
    let mut file_contexts: Vec<String> = Vec::new();

    while let Some(field) = match multipart.next_field().await {
        Ok(f) => f,
        Err(_) => None,
    } {
        let name = field.name().unwrap_or("").to_string();
        match name.as_str() {
            "message" => {
                message = field.text().await.unwrap_or_default();
            }
            "thinking" => {
                thinking = field.text().await.map(|t| t != "false").unwrap_or(true);
            }
            "conversation_id" => {
                conversation_id = field.text().await.ok().and_then(|t| t.trim().parse().ok());
            }
            "files" => {
                if let Ok(bytes) = field.bytes().await {
                    let text = String::from_utf8_lossy(&bytes).to_string();
                    let preview: String = text.chars().take(3000).collect();
                    let preview = if text.chars().count() > 3000 {
                        format!("{preview}\n... [tronqué — {} caractères au total]", text.chars().count())
                    } else {
                        preview
                    };
                    if let Some(filename) = field.file_name() {
                        file_contexts.push(format!("[Fichier joint : {filename}]\n{preview}"));
                    }
                }
            }
            _ => {}
        }
    }

    if message.trim().is_empty() {
        return (StatusCode::BAD_REQUEST, Json(json!({"error":"Empty message"}))).into_response();
    }

    if !file_contexts.is_empty() {
        message = format!("{}\n\n{}", file_contexts.join("\n\n"), message);
    }

    let (tx, mut rx) = mpsc::channel::<AgentEvent>(64);
    let agent_clone = state.agent.clone();
    tokio::spawn(async move {
        agent_clone.process_request(&message, conversation_id, tx).await;
    });

    let stream = async_stream::stream! {
        loop {
            match tokio::time::timeout(std::time::Duration::from_secs(15), rx.recv()).await {
                Ok(Some(AgentEvent::End)) => break,
                Ok(Some(event)) => {
                    if let Some(evt) = to_sse_event(&event) {
                        yield Ok::<_, std::convert::Infallible>(evt);
                    }
                }
                Ok(None) => break,
                Err(_) => {
                    let ping = Event::default().data(json!({"type":"ping"}).to_string());
                    yield Ok::<_, std::convert::Infallible>(ping);
                }
            }
        }
    };

    axum::response::sse::Sse::new(stream).into_response()
}

/// GET /ws — WebSocket mirroring the SSE /chat behaviour (added for future
/// consumers; the current Electron UI still uses POST /chat).
async fn ws_handler(State(state): State<AppState>, ws: WebSocketUpgrade) -> Response {
    ws.on_upgrade(move |socket| ws_run(socket, state))
}

async fn ws_run(mut socket: WebSocket, state: AppState) {
    loop {
        let msg = match socket.next().await {
            Some(Ok(m)) => m,
            _ => return,
        };
        let Message::Text(text) = msg else { continue };
        let Ok(raw) = serde_json::from_str::<Value>(&text) else {
            let _ = socket.send(Message::Text("{\"type\":\"error\",\"message\":\"bad json\"}".into())).await;
            continue;
        };
        let message = raw.get("message").and_then(Value::as_str).unwrap_or("").to_string();
        if message.trim().is_empty() {
            let _ = socket
                .send(Message::Text("{\"type\":\"error\",\"message\":\"Empty message\"}".into()))
                .await;
            continue;
        }
        let conversation_id = raw.get("conversation_id").and_then(Value::as_i64);

        let (tx, mut rx) = mpsc::channel::<AgentEvent>(64);
        let agent_clone = state.agent.clone();
        tokio::spawn(async move {
            agent_clone.process_request(&message, conversation_id, tx).await;
        });

        loop {
            match tokio::time::timeout(std::time::Duration::from_secs(15), rx.recv()).await {
                Ok(Some(AgentEvent::End)) => break,
                Ok(Some(event)) => {
                    if let Some(v) = to_sse_json(&event) {
                        if socket.send(Message::Text(v.to_string().into())).await.is_err() {
                            return;
                        }
                    }
                }
                Ok(None) => break,
                Err(_) => {
                    if socket
                        .send(Message::Text("{\"type\":\"ping\"}".into()))
                        .await
                        .is_err()
                    {
                        return;
                    }
                }
            }
        }
    }
}

/// GET /conversations
async fn list_conversations(State(state): State<AppState>) -> Json<Value> {
    Json(json!(state.conversations.list(50)))
}

/// GET /conversations/:id/history
async fn conversation_history(
    State(state): State<AppState>,
    AxumPath(id): AxumPath<i64>,
) -> Response {
    match state.conversations.history(id) {
        Some(v) => Json(v).into_response(),
        None => (StatusCode::NOT_FOUND, Json(json!({"error":"not found"}))).into_response(),
    }
}

/// DELETE /conversations/:id
async fn delete_conversation(
    State(state): State<AppState>,
    AxumPath(id): AxumPath<i64>,
) -> Json<Value> {
    Json(json!({"success": state.conversations.delete(id)}))
}

/// PATCH /conversations/:id/title
async fn update_conversation_title(
    State(state): State<AppState>,
    AxumPath(id): AxumPath<i64>,
    Json(body): Json<Value>,
) -> Response {
    let title = body.get("title").and_then(Value::as_str).unwrap_or("").trim().to_string();
    if title.is_empty() {
        return (StatusCode::BAD_REQUEST, Json(json!({"error":"Title cannot be empty"}))).into_response();
    }
    let success = state.conversations.rename(id, &title);
    Json(json!({"success": success, "title": title})).into_response()
}

/// PATCH /conversations/:id/archive
async fn archive_conversation(
    State(state): State<AppState>,
    AxumPath(id): AxumPath<i64>,
) -> Json<Value> {
    Json(json!({"success": state.conversations.archive(id)}))
}

/// GET /health — llama.cpp reachability + model availability.
async fn health(State(state): State<AppState>) -> Json<Value> {
    let ok = match state.engine.health_check().await {
        Ok(v) => v,
        Err(e) => {
            tracing::error!("health check failed: {e}");
            false
        }
    };
    Json(json!({
        "llama_cpp": ok,
        "model": config::LLAMA_MODEL,
        "status": if ok { "ok" } else { "error" },
    }))
}

/// GET /tools — available tool names (for function calling).
async fn list_tools() -> Json<Value> {
    let names: Vec<&str> = tools::registry().into_iter().map(|t| t.name).collect();
    Json(json!(names))
}

/// POST /transcribe — offline STT via faster-whisper.
///
/// The Rust backend proxies transcription to a bounded helper subprocess
/// (the repo's `.venv/bin/python` invoking faster-whisper), keeping the
/// model lazy. The scaffold returns 501 until wiring is completed.
async fn transcribe(mut _multipart: Multipart) -> Response {
    tracing::warn!("transcribe: not yet ported (faster-whisper subprocess wiring pending)");
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({"error":"transcribe not yet ported in Rust backend"})),
    )
        .into_response()
}
