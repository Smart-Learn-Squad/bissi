//! System / clipboard tools (mirrors `functions/system/clipboard.py`).
//!
//! Porting target: `arboard` crate for clipboard read/write.

use serde_json::{json, Value};

/// Placeholder clipboard read — returns empty until `arboard` is wired.
pub fn get_clipboard(_args: &Value) -> Result<Value, String> {
    Ok(json!({ "content": "" }))
}

/// Placeholder clipboard write.
pub fn set_clipboard(_args: &Value) -> Result<Value, String> {
    Ok(json!({ "ok": true }))
}
