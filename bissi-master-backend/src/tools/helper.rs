//! Bridge to the proven Python tool implementations.
//!
//! The Rust backend calls the repo's `.venv` Python on `rust_shell.py` for the
//! office / vision / python_runner tools (heavy native crates would be gross
//! overkill and risk build breakage). `rust_shell.py` maps the canonical Rust
//! arg names to the Python `_tool_*` implementations and returns the exact
//! `ToolResult` JSON the Python backend would produce.
//!
//! Protocol: one JSON object on stdin (`{"tool", "args"}`), one JSON object
//! (a `ToolResult.to_dict()`) on stdout.
//!
//! Interpreter location: `BISSI_PYTHON` env override, else `./.venv/bin/python`
//! (or the Windows equivalent), else `python`. Script location:
//! `BISSI_RUST_SHELL` env override, else `./bissi-master-backend/rust_shell.py`,
//! else `./rust_shell.py`. Overrides let start scripts pin exact paths.

use serde_json::{json, Value};
use std::env;
use std::io::Write;
use std::path::Path;
use std::process::{Command, Stdio};

fn python_interpreter() -> String {
    if let Ok(p) = env::var("BISSI_PYTHON") {
        if !p.trim().is_empty() {
            return p;
        }
    }
    for cand in ["./.venv/bin/python", "./.venv/Scripts/python.exe"] {
        if Path::new(cand).exists() {
            return cand.to_string();
        }
    }
    // Fall back to PATH-resolved interpreters.
    "python".to_string()
}

fn shell_script() -> String {
    if let Ok(s) = env::var("BISSI_RUST_SHELL") {
        if !s.trim().is_empty() {
            return s;
        }
    }
    for cand in ["./bissi-master-backend/rust_shell.py", "./rust_shell.py"] {
        if Path::new(cand).exists() {
            return cand.to_string();
        }
    }
    // Default assumption: launched from repo root.
    "./bissi-master-backend/rust_shell.py".to_string()
}

/// Run a helper-backed tool. Always returns a `ToolResult`-shaped JSON Value,
/// so a subprocess failure still emits a proper `tool_done` (not a raw error).
pub fn run(tool: &str, args: &Value) -> Value {
    match run_inner(tool, args) {
        Ok(v) => v,
        Err(e) => json!({"success": false, "error": e, "task_done": false}),
    }
}

fn run_inner(tool: &str, args: &Value) -> Result<Value, String> {
    let request = json!({"tool": tool, "args": args});
    let mut child = Command::new(python_interpreter())
        .arg(shell_script())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("impossible de lancer l'aide Python: {e}"))?;

    if let Some(mut stdin) = child.stdin.take() {
        stdin
            .write_all(request.to_string().as_bytes())
            .map_err(|e| format!("échec écriture entrée Python: {e}"))?;
    }

    let output = child
        .wait_with_output()
        .map_err(|e| format!("échec attente Python: {e}"))?;

    if !output.stderr.is_empty() {
        tracing::warn!(
            "rust_shell stderr: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }

    let text = String::from_utf8_lossy(&output.stdout).to_string();
    let trimmed = text.trim();
    if trimmed.is_empty() {
        return Err("réponse vide de l'aide Python".into());
    }
    let value: Value = serde_json::from_str(trimmed)
        .map_err(|e| format!("JSON invalide de l'aide Python ({e}): {:.200}", trimmed))?;
    Ok(value)
}
