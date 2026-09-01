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

/// The full tool registry (schemas mirror `core/agent.py` _build_tool_definitions).
pub fn registry() -> Vec<ToolDef> {
    vec![
        ToolDef { name: "analyze_chart", description: "Analyze chart image.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"}},"required":["file_path"]}) },
        ToolDef { name: "analyze_screenshot", description: "Analyze screenshot content.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"}},"required":["file_path"]}) },
        ToolDef { name: "delete_file", description: "Delete a file from disk.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"}},"required":["file_path"]}) },
        ToolDef { name: "describe_image", description: "Describe an image.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"},"prompt":{"type":"string"},"detail":{"type":"string"}},"required":["file_path"]}) },
        ToolDef { name: "edit_text_file", description: "Replace text in file.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"},"old_text":{"type":"string"},"new_text":{"type":"string"}},"required":["file_path","old_text","new_text"]}) },
        ToolDef { name: "extract_text_from_image", description: "Extract text from image.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"},"language":{"type":"string"}},"required":["file_path"]}) },
        ToolDef { name: "get_clipboard", description: "Read clipboard content.", parameters: json!({"type":"object","properties":{}}) },
        ToolDef { name: "get_directory_tree", description: "Get directory tree.", parameters: json!({"type":"object","properties":{"path":{"type":"string"},"max_depth":{"type":"integer"}},"required":["path"]}) },
        ToolDef { name: "get_file_info", description: "Get file metadata.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"}},"required":["file_path"]}) },
        ToolDef { name: "get_recent_files", description: "Get recent files from directory.", parameters: json!({"type":"object","properties":{"directory":{"type":"string"},"limit":{"type":"integer"}},"required":["directory"]}) },
        ToolDef { name: "list_directory", description: "List directory content.", parameters: json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}) },
        ToolDef { name: "move_file", description: "Move or rename a file.", parameters: json!({"type":"object","properties":{"source":{"type":"string"},"destination":{"type":"string"}},"required":["source","destination"]}) },
        ToolDef { name: "python_runner", description: "Execute Python code for analysis/calculations.", parameters: json!({"type":"object","properties":{"code":{"type":"string"}},"required":["code"]}) },
        ToolDef { name: "read_excel", description: "Read rows from Excel file.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"},"max_rows":{"type":"integer"}},"required":["file_path"]}) },
        ToolDef { name: "read_pdf", description: "Extract text from PDF.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"},"max_chars":{"type":"integer"}},"required":["file_path"]}) },
        ToolDef { name: "read_pptx", description: "Read text from PowerPoint.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"}},"required":["file_path"]}) },
        ToolDef { name: "read_text_file", description: "Read plain text file.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"},"max_lines":{"type":"integer"}},"required":["file_path"]}) },
        ToolDef { name: "read_word", description: "Read paragraphs from a .docx file.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"}},"required":["file_path"]}) },
        ToolDef { name: "safe_operator", description: "Run safe introspection operation.", parameters: json!({"type":"object","properties":{"operation":{"type":"string","enum":["get_python_version","get_current_directory"]}},"required":["operation"]}) },
        ToolDef { name: "search_by_content", description: "Search files by content.", parameters: json!({"type":"object","properties":{"directory":{"type":"string"},"query":{"type":"string"},"extensions":{"type":"array","items":{"type":"string"}}},"required":["directory","query"]}) },
        ToolDef { name: "search_files", description: "Search files by name.", parameters: json!({"type":"object","properties":{"query":{"type":"string"},"root_dir":{"type":"string"}},"required":["query"]}) },
        ToolDef { name: "set_clipboard", description: "Set clipboard content.", parameters: json!({"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}) },
        ToolDef { name: "write_excel", description: "Write tabular data to Excel file.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"},"data":{"type":"array","items":{"type":"object"}},"sheet_name":{"type":"string"}},"required":["file_path","data"]}) },
        ToolDef { name: "write_pptx", description: "Write PowerPoint slides.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"},"title":{"type":"string"},"slides":{"type":"array","items":{"type":"object"}}},"required":["file_path","title","slides"]}) },
        ToolDef { name: "write_text_file", description: "Write plain text file.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"},"content":{"type":"string"},"append":{"type":"boolean"}},"required":["file_path","content"]}) },
        ToolDef { name: "write_word", description: "Write the FULL content to a .docx file in one call (400-500 mots max). Ne pas utiliser append.", parameters: json!({"type":"object","properties":{"file_path":{"type":"string"},"content":{"type":"string"},"append":{"type":"boolean"}},"required":["file_path","content"]}) },
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
    let out = match name {
        // Real filesystem implementations.
        "list_directory" => filesystem::list_directory(&args)?,
        "read_text_file" => filesystem::read_text_file(&args)?,
        "write_text_file" => filesystem::write_text_file(&args)?,
        "edit_text_file" => filesystem::edit_text_file(&args)?,
        "delete_file" => filesystem::delete_file(&args)?,
        "move_file" => filesystem::move_file(&args)?,
        "get_file_info" => filesystem::get_file_info(&args)?,
        "get_directory_tree" => filesystem::get_directory_tree(&args)?,
        "get_recent_files" => filesystem::get_recent_files(&args)?,
        "search_files" => filesystem::search_files(&args)?,
        "search_by_content" => filesystem::search_by_content(&args)?,
        // Clipboard (real stubs in system.rs).
        "get_clipboard" => system::get_clipboard(&args)?,
        "set_clipboard" => system::set_clipboard(&args)?,
        // Introspection tool (mirrors safe_operator).
        "safe_operator" => system::safe_operator(&args)?,
        // Office / vision / code stubs (not yet ported).
        "read_word" | "read_excel" | "read_pptx" | "read_pdf" => office::stub(name, &args)?,
        "write_word" | "write_excel" | "write_pptx" => office::stub(name, &args)?,
        "describe_image" | "analyze_chart" | "analyze_screenshot" | "extract_text_from_image" => {
            vision::stub(name, &args)?
        }
        "python_runner" => code::python_runner(&args)?,
        _ => return Err(format!("unknown tool: {name}")),
    };
    Ok(out.to_string())
}
