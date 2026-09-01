//! BISSI backend configuration (mirrors core/config.py).
//!
//! Ports are fixed by the project and MUST NOT change (scripts and the
//! Electron renderer hardcode `:8001` for llama.cpp and `:8765` for this
//! backend). See AGENTS.md.

/// llama.cpp OpenAI-compatible server.
pub const LLAMA_HOST: &str = "http://127.0.0.1:8001";
pub const LLAMA_MODEL: &str = "bissi-gemma4-e2b-Q4_K_M";
pub const LLAMA_TIMEOUT_SECS: u64 = 300;
pub const LLAMA_MAX_RETRIES: u32 = 3;
pub const LLAMA_TEMPERATURE: f32 = 0.5;
pub const LLAMA_N_CTX: u32 = 16384;

/// Agent loop settings.
pub const AGENT_MAX_ITERATIONS: u32 = 5;
pub const AGENT_CONTEXT_TOKEN_LIMIT: usize = 14000;

/// Backend server settings.
pub const SERVER_HOST: &str = "127.0.0.1";
pub const SERVER_PORT: u16 = 8765;

/// Data dir for conversations (mirrors ~/.bissi).
pub fn data_dir() -> std::path::PathBuf {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".into());
    std::path::Path::new(&home).join(".bissi")
}
