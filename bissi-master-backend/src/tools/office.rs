//! Office document tools (mirrors `functions/office/`).
//!
//! docx / xlsx / pptx / pdf porting targets:
//! - `office_oxide` (docx, xlsx, pptx native Rust) — primary candidate
//! - `lopdf` / `pdf-extract` for PDFs
//! These are stubbed for the scaffold and will be filled in during the port.

use serde_json::{json, Value};

/// Placeholder for not-yet-ported office tools.
pub fn stub(name: &str, _args: &Value) -> Result<Value, String> {
    Ok(json!({ "tool": name, "status": "not_ported" }))
}
