//! Tool registry and dispatch (mirrors `functions/` + `core.agent.available_functions`).
//!
//! Each tool is declared with its JSON schema (fed to llama.cpp function
//! calling) and a dispatch function. The 26 tools exposed by the current
//! Python backend are listed here; implementations are stubbed for the
//! scaffold and will be ported module-by-module.

use serde_json::{json, Value};

pub mod filesystem;
pub mod office;
pub mod code;
pub mod vision;
pub mod system;

/// Descriptor for one agent tool.
pub struct ToolDef {
    pub name: &'static str,
    pub description: &'static str,
    pub parameters: Value,
}

/// The full tool registry (order mirrors `available_functions`).
pub fn registry() -> Vec<ToolDef> {
    vec![
        ToolDef { name: "analyze_chart", description: "Analyze a chart/image and return insights", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "analyze_screenshot", description: "Analyze a screenshot image", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "delete_file", description: "Delete a file", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "describe_image", description: "Describe an image", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "edit_text_file", description: "Edit text in a file", parameters: json!({"type":"object","properties":{"path":{"type":"string"},"search":{"type":"string"},"replacement":{"type":"string"}},"required":["path","search","replacement"]}) },
        ToolDef { name: "extract_text_from_image", description: "OCR an image", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "get_clipboard", description: "Read clipboard content", parameters: json!({"type":"object","properties":{}}) },
        ToolDef { name: "get_directory_tree", description: "Return directory tree", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "get_file_info", description: "Return file metadata", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "get_recent_files", description: "Return recent files", parameters: json!({"type":"object","properties":{"limit":{"type":"integer"}}}) },
        ToolDef { name: "list_directory", description: "List directory entries", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "move_file", description: "Move/rename a file", parameters: json!({"type":"object","properties":{"source":{"type":"string"},"destination":{"type":"string"}},"required":["source","destination"]}) },
        ToolDef { name: "python_runner", description: "Run a Python snippet", parameters: json!({"type":"object","properties":{"code":{"type":"string"}},"required":["code"]}) },
        ToolDef { name: "read_excel", description: "Read an Excel workbook", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "read_pdf", description: "Read a PDF document", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "read_pptx", description: "Read a PowerPoint deck", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "read_text_file", description: "Read a text file", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "read_word", description: "Read a Word document", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "safe_operator", description: "Run a safe shell operator", parameters: json!({"type":"object","properties":{"command":{"type":"string"}},"required":["command"]}) },
        ToolDef { name: "search_by_content", description: "Search files by content", parameters: json!({"type":"object","properties":{"query":{"type":"string"},"path":{"type":"string"}},"required":["query"]}) },
        ToolDef { name: "search_files", description: "Search files by name", parameters: json!({"type":"object","properties":{"pattern":{"type":"string"},"path":{"type":"string"}},"required":["pattern"]}) },
        ToolDef { name: "set_clipboard", description: "Write to clipboard", parameters: json!({"type":"object","properties":{"content":{"type":"string"}},"required":["content"]}) },
        ToolDef { name: "write_excel", description: "Write an Excel workbook", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "write_pptx", description: "Write a PowerPoint deck", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "write_text_file", description: "Write a text file", parameters: json!({"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}) },
        ToolDef { name: "write_word", description: "Write a Word document", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
    ]
}

/// Convert the registry into OpenAI function-tool `tools` payloads.
pub fn tools_payload() -> Vec<Value> {
    registry()
        .into_iter()
        .map(|t| {
            json!({"type":"function","function":{"name":t.name,"description":t.description,"parameters":t.parameters}})
        })
        .collect()
}

/// Dispatch a named tool call; returns a JSON string result (mirrors the
/// `tool_done` result contract produced by the Python backend).
pub async fn dispatch(name: &str, args: Value) -> Result<String, String> {
    match name {
        "list_directory" => filesystem::list_directory(&args).map(serde_json::to_string).map_err(|e| e.to_string()),
        "read_text_file" => filesystem::read_text_file(&args).map(serde_json::to_string).map_err(|e| e.to_string()),
        "write_text_file" => filesystem::write_text_file(&args).map(serde_json::to_string).map_err(|e| e.to_string()),
        "get_clipboard" => system::get_clipboard(&args).map(serde_json::to_string).map_err(|e| e.to_string()),
        "set_clipboard" => system::set_clipboard(&args).map(serde_json::to_string).map_err(|e| e.to_string()),
        // Office / vision / code stubs.
        "read_word" | "read_excel" | "read_pptx" | "read_pdf" => {
            office::stub(name, &args).map(serde_json::to_string).map_err(|e| e.to_string())
        }
        "write_word" | "write_excel" | "write_pptx" => {
            office::stub(name, &args).map(serde_json::to_string).map_err(|e| e.to_string())
        }
        "describe_image" | "analyze_chart" | "analyze_screenshot" | "extract_text_from_image" => {
            vision::stub(name, &args).map(serde_json::to_string).map_err(|e| e.to_string())
        }
        "python_runner" => code::python_runner(&args).map(serde_json::to_string).map_err(|e| e.to_string()),
        // Remaining filesystem / sys stubs.
        "delete_file" | "move_file" | "get_file_info" | "get_directory_tree"
        | "get_recent_files" | "search_files" | "search_by_content"
        | "edit_text_file" | "safe_operator" => {
            filesystem::stub(name, &args).map(serde_json::to_string).map_err(|e| e.to_string())
        }
        _ => Err(format!("unknown tool: {name}")),
    }
}
