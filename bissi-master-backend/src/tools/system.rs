//! System / clipboard tools (mirrors `functions/system/clipboard.py` +
//! `core/agent.py` `_tool_safe_operator`).
//!
//! Porting target: `arboard` crate for clipboard read/write.

use serde_json::{json, Value};

/// Clipboard read — returns empty until `arboard` is wired.
pub fn get_clipboard(_args: &Value) -> Result<Value, String> {
    Ok(json!({ "content": "" }))
}

/// Clipboard write (`text` param, mirroring the Python schema).
pub fn set_clipboard(args: &Value) -> Result<Value, String> {
    let text = args.get("text").and_then(Value::as_str).unwrap_or("");
    // TODO(arboard): write `text` to the system clipboard.
    let _ = text;
    Ok(json!({ "ok": true }))
}

/// Safe introspection operation (mirrors `_tool_safe_operator`).
pub fn safe_operator(args: &Value) -> Result<Value, String> {
    let operation = args.get("operation").and_then(Value::as_str).unwrap_or("");
    match operation {
        "get_python_version" => {
            Ok(json!({"success": true, "output": RUST_RUNTIME_VERSION, "task_done": true}))
        }
        "get_current_directory" => {
            let cwd = std::env::current_dir()
                .map(|p| p.to_string_lossy().to_string())
                .unwrap_or_else(|e| format!("<error: {e}>"));
            Ok(json!({"success": true, "output": cwd, "task_done": true}))
        }
        _ => Ok(
            json!({"success": false, "error": format!("Unknown operation: {operation}"), "task_done": false}),
        ),
    }
}

const RUST_RUNTIME_VERSION: &str = concat!(
    "rustc ",
    env!("CARGO_PKG_VERSION"),
    " (bissi-backend rust runtime)"
);
