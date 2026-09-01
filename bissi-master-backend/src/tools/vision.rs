//! Vision / image tools (mirrors `functions/vision/`, `functions/media/image.py`).
//!
//! Porting target: `image` crate for decode, optionally a Rust OCR crate for
//! `extract_text_from_image`. Image description may proxy through
//! llama.cpp's multimodal support if the GGUF supports it. Stubbed for now.

use serde_json::{json, Value};

/// Placeholder for not-yet-ported vision tools.
pub fn stub(name: &str, _args: &Value) -> Result<Value, String> {
    Ok(json!({ "tool": name, "status": "not_ported" }))
}
