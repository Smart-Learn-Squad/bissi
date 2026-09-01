//! Filesystem tools (mirrors `functions/filesystem/`).

use serde_json::{json, Value};
use std::fs;
use std::path::Path;

fn arg<'a>(args: &'a Value, key: &str) -> &'a str {
    args.get(key).and_then(Value::as_str).unwrap_or("")
}

/// Real implementation: list directory entries.
pub fn list_directory(args: &Value) -> Result<Value, String> {
    let path = arg(args, "path");
    if path.is_empty() {
        return Err("list_directory requires `path`".into());
    }
    let mut entries = Vec::new();
    for entry in fs::read_dir(path).map_err(|e| e.to_string())? {
        let entry = entry.map_err(|e| e.to_string())?;
        let meta = entry.metadata().map_err(|e| e.to_string())?;
        entries.push(json!({
            "name": entry.file_name().to_string_lossy().to_string(),
            "path": entry.path().to_string_lossy().to_string(),
            "is_dir": meta.is_dir(),
            "size": meta.len(),
        }));
    }
    Ok(json!({ "path": path, "entries": entries }))
}

/// Real implementation: read a text file (like the Python backend, reads
/// bytes lossily as UTF-8 — consistent with the file-preview behavior).
pub fn read_text_file(args: &Value) -> Result<Value, String> {
    let path = arg(args, "path");
    if path.is_empty() {
        return Err("read_text_file requires `path`".into());
    }
    let bytes = fs::read(path).map_err(|e| e.to_string())?;
    let text = String::from_utf8_lossy(&bytes).to_string();
    Ok(json!({ "path": path, "content": text, "length": text.chars().count() }))
}

/// Real implementation: write a text file.
pub fn write_text_file(args: &Value) -> Result<Value, String> {
    let path = arg(args, "path");
    let content = arg(args, "content");
    if path.is_empty() {
        return Err("write_text_file requires `path`".into());
    }
    let parent = Path::new(path).parent();
    if let Some(dir) = parent {
        if !dir.as_os_str().is_empty() {
            fs::create_dir_all(dir).map_err(|e| e.to_string())?;
        }
    }
    fs::write(path, content).map_err(|e| e.to_string())?;
    Ok(json!({ "path": path, "ok": true }))
}

/// Placeholder for tools not yet ported. Returns a structured "not ported"
/// marker so the dispatch contract stays stable.
pub fn stub(name: &str, _args: &Value) -> Result<Value, String> {
    Ok(json!({ "tool": name, "status": "not_ported" }))
}
