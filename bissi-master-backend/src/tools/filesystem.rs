//! Filesystem tools (mirrors `functions/filesystem/explorer.py` + `writer.py`
//! + the agent's `_tool_*` adapters).
//!
//! Results follow the Python `ToolResult.to_dict()` contract:
//! `{"success", "output", "error", "path", "task_done"}`. A top-level `path`
//! lets the agent's `emit_file_created` fire `file_created` for write/move.

use serde_json::{json, Value};
use std::fs;
use std::path::Path;

const MAX_FILE_SIZE: u64 = 50 * 1024 * 1024; // 50 Mo

fn arg<'a>(args: &'a Value, key: &str) -> &'a str {
    args.get(key).and_then(Value::as_str).unwrap_or("")
}

fn ok(output: Value, path: Option<&str>) -> Value {
    let mut v = json!({"success": true, "output": output, "task_done": true});
    if let Some(p) = path {
        v["path"] = json!(p);
    }
    v
}

fn fail(error: &str, path: Option<&str>) -> Value {
    let mut v = json!({"success": false, "error": error, "task_done": false});
    if let Some(p) = path {
        v["path"] = json!(p);
    }
    v
}

fn iso(t: std::time::SystemTime) -> String {
    let secs = t
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs() as i64)
        .unwrap_or(0);
    // Local RFC3339 approximation; mirrors datetime.fromtimestamp().isoformat().
    let days = secs.div_euclid(86_400);
    let rem = secs.rem_euclid(86_400);
    let (y, m, d) = civil_from_days(days);
    let (hh, mm, ss) = (rem / 3600, (rem % 3600) / 60, rem % 60);
    format!("{y:04}-{m:02}-{d:02}T{hh:02}:{mm:02}:{ss:02}")
}

// Howard Hinnant's algorithm: Days from Civil
fn civil_from_days(z: i64) -> (i64, u32, u32) {
    let z = z + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z.rem_euclid(146_097);
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146_096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = (doy - (153 * mp + 2) / 5 + 1) as u32;
    let m = if mp < 10 { mp + 3 } else { mp - 9 } as u32;
    (if m <= 2 { y + 1 } else { y }, m, d)
}

fn format_size(mut size: u64) -> String {
    for unit in ["B", "KB", "MB", "GB", "TB"] {
        if size < 1024 {
            return format!("{size:.1} {unit}");
        }
        size /= 1024;
    }
    format!("{size:.1} PB")
}

fn hidden(name: &str) -> bool {
    name.starts_with('.')
}

/// Real implementation: read a text file (lossy UTF-8, mirroring
/// `errors="ignore"`), with optional line cap.
pub fn read_text_file(args: &Value) -> Result<Value, String> {
    let path = arg(args, "file_path");
    if path.is_empty() {
        return Err("read_text_file requires `file_path`".into());
    }
    let p = Path::new(path);
    if !p.exists() {
        return Ok(fail(&format!("File not found: {path}"), Some(path)));
    }
    if !p.is_file() {
        return Ok(fail(&format!("Not a file: {path}"), Some(path)));
    }
    let meta = match p.metadata() {
        Ok(m) => m,
        Err(e) => return Ok(fail(&e.to_string(), Some(path))),
    };
    if meta.len() > MAX_FILE_SIZE {
        return Ok(fail(
            &format!("Fichier trop volumineux (> 50 Mo) : {path}"),
            Some(path),
        ));
    }
    let bytes = match fs::read(path) {
        Ok(b) => b,
        Err(e) => return Ok(fail(&e.to_string(), Some(path))),
    };
    let text = String::from_utf8_lossy(&bytes).to_string();

    let max_lines = args.get("max_lines").and_then(Value::as_u64).unwrap_or(0);
    let (content, truncated) = if max_lines > 0 {
        let lines: Vec<&str> = text.split('\n').take(max_lines as usize).collect();
        (
            lines.join("\n"),
            text.split('\n').count() > max_lines as usize,
        )
    } else {
        (text, false)
    };
    let absolute = std::fs::canonicalize(path)
        .unwrap_or_else(|_| p.to_path_buf())
        .to_string_lossy()
        .to_string();
    Ok(ok(
        json!({
            "content": content,
            "lines": content.split('\n').count(),
            "size": meta.len(),
            "truncated": truncated,
        }),
        Some(&absolute),
    ))
}

/// Real implementation: list a directory (hidden skipped by default).
pub fn list_directory(args: &Value) -> Result<Value, String> {
    let path = arg(args, "path");
    if path.is_empty() {
        return Err("list_directory requires `path`".into());
    }
    let mut items = Vec::new();
    let dir = match fs::read_dir(path) {
        Ok(d) => d,
        Err(e) => return Ok(fail(&format!("Permission denied/error: {e}"), Some(path))),
    };
    for entry in dir.flatten() {
        let name = entry.file_name().to_string_lossy().to_string();
        if hidden(&name) {
            continue;
        }
        let is_dir = entry.file_type().map(|t| t.is_dir()).unwrap_or(false);
        let size = entry.metadata().map(|m| m.len()).unwrap_or(0);
        items.push(json!({
            "name": name,
            "path": entry.path().to_string_lossy().to_string(),
            "type": if is_dir { "directory" } else { "file" },
            "size": if is_dir { Value::Null } else { json!(size) },
        }));
    }
    items.sort_by(|a, b| {
        let da = a["type"] == "directory";
        let db = b["type"] == "directory";
        da.cmp(&db).reverse().then_with(|| {
            a["name"]
                .as_str()
                .unwrap_or("")
                .to_lowercase()
                .cmp(&b["name"].as_str().unwrap_or("").to_lowercase())
        })
    });
    Ok(ok(json!({"items": items}), None))
}

/// Real implementation: write/append a text file. Emits a `path` for
/// `file_created`.
pub fn write_text_file(args: &Value) -> Result<Value, String> {
    let path = arg(args, "file_path");
    let content = arg(args, "content");
    if path.is_empty() {
        return Err("write_text_file requires `file_path`".into());
    }
    let p = Path::new(path);
    if let Some(dir) = p.parent() {
        if !dir.as_os_str().is_empty() && !dir.exists() {
            if let Err(e) = fs::create_dir_all(dir) {
                return Ok(fail(&e.to_string(), Some(path)));
            }
        }
    }
    let append = args.get("append").and_then(Value::as_bool).unwrap_or(false);
    let result: std::io::Result<()> = if append {
        use std::io::Write;
        match fs::OpenOptions::new().create(true).append(true).open(path) {
            Ok(mut f) => f.write_all(content.as_bytes()),
            Err(e) => Err(e),
        }
    } else {
        fs::write(path, content)
    };
    if let Err(e) = result {
        return Ok(fail(&e.to_string(), Some(path)));
    }
    let size = fs::metadata(path).map(|m| m.len()).unwrap_or(0);
    let absolute = std::fs::canonicalize(path)
        .unwrap_or_else(|_| p.to_path_buf())
        .to_string_lossy()
        .to_string();
    Ok(ok(
        json!({"action": if append { "append" } else { "write" }, "size": size}),
        Some(&absolute),
    ))
}

/// Real implementation: replace text in a file (occurrence 0 = all).
pub fn edit_text_file(args: &Value) -> Result<Value, String> {
    let path = arg(args, "file_path");
    let old_text = arg(args, "old_text");
    let new_text = arg(args, "new_text");
    if path.is_empty() || old_text.is_empty() {
        return Err("edit_text_file requires `file_path` and `old_text`".into());
    }
    let p = Path::new(path);
    if !p.exists() {
        return Ok(fail(&format!("File not found: {path}"), Some(path)));
    }
    let content = match fs::read(path) {
        Ok(b) => String::from_utf8_lossy(&b).to_string(),
        Err(e) => return Ok(fail(&e.to_string(), Some(path))),
    };
    if !content.contains(old_text) {
        return Ok(fail(
            &format!("Text '{old_text}' not found in file."),
            Some(path),
        ));
    }
    let count = content.matches(old_text).count();
    let new_content = content.replace(old_text, new_text);
    if let Err(e) = fs::write(path, new_content) {
        return Ok(fail(&e.to_string(), Some(path)));
    }
    let absolute = std::fs::canonicalize(path)
        .unwrap_or_else(|_| p.to_path_buf())
        .to_string_lossy()
        .to_string();
    Ok(ok(
        json!({"replacements": count, "message": format!("Updated {count} occurrence(s) in {path}")}),
        Some(&absolute),
    ))
}

/// Real implementation: delete a file.
pub fn delete_file(args: &Value) -> Result<Value, String> {
    let path = arg(args, "file_path");
    if path.is_empty() {
        return Err("delete_file requires `file_path`".into());
    }
    let p = Path::new(path);
    if !p.exists() {
        return Ok(fail(&format!("File not found: {path}"), Some(path)));
    }
    if let Err(e) = fs::remove_file(path) {
        return Ok(fail(&format!("Delete failed: {e}"), Some(path)));
    }
    let absolute = std::fs::canonicalize(path)
        .unwrap_or_else(|_| p.to_path_buf())
        .to_string_lossy()
        .to_string();
    Ok(ok(
        json!({"message": format!("Deleted {path}")}),
        Some(&absolute),
    ))
}

/// Real implementation: move / rename a file.
pub fn move_file(args: &Value) -> Result<Value, String> {
    let source = arg(args, "source");
    let destination = arg(args, "destination");
    if source.is_empty() || destination.is_empty() {
        return Err("move_file requires `source` and `destination`".into());
    }
    match fs::rename(source, destination) {
        Ok(()) => Ok(ok(
            json!({"message": format!("Moved {source} -> {destination}")}),
            Some(destination),
        )),
        Err(e) => Ok(fail(&format!("Move failed: {e}"), Some(source))),
    }
}

/// Real implementation: file metadata.
pub fn get_file_info(args: &Value) -> Result<Value, String> {
    let path = arg(args, "file_path");
    if path.is_empty() {
        return Err("get_file_info requires `file_path`".into());
    }
    let p = Path::new(path);
    if !p.exists() {
        return Ok(fail(&format!("File not found: {path}"), Some(path)));
    }
    let meta = match p.metadata() {
        Ok(m) => m,
        Err(e) => return Ok(fail(&e.to_string(), Some(path))),
    };
    let is_file = p.is_file();
    let absolute = std::fs::canonicalize(path)
        .unwrap_or_else(|_| p.to_path_buf())
        .to_string_lossy()
        .to_string();
    let name = p
        .file_name()
        .map(|s| s.to_string_lossy().to_string())
        .unwrap_or_default();
    let ext = p
        .extension()
        .map(|e| format!(".{}", e.to_string_lossy().to_lowercase()))
        .unwrap_or_default();
    let modified = iso(meta.modified().unwrap_or(std::time::UNIX_EPOCH));
    let created = iso(meta.created().unwrap_or(std::time::UNIX_EPOCH));
    let accessed = iso(meta.accessed().unwrap_or(std::time::UNIX_EPOCH));
    Ok(ok(
        json!({
            "name": name,
            "path": absolute,
            "type": if is_file { "file" } else { "directory" },
            "size": meta.len(),
            "size_human": format_size(meta.len()),
            "extension": if is_file { Value::String(ext) } else { Value::Null },
            "modified": modified,
            "created": created,
            "accessed": accessed,
            "is_hidden": hidden(&name),
        }),
        Some(&absolute),
    ))
}

/// Real implementation: directory tree (depth-limited).
pub fn get_directory_tree(args: &Value) -> Result<Value, String> {
    let path = arg(args, "path");
    let max_depth = args.get("max_depth").and_then(Value::as_u64).unwrap_or(3) as i64;
    if path.is_empty() {
        return Err("get_directory_tree requires `path`".into());
    }
    fn build(p: &Path, depth: i64, max_depth: i64) -> Value {
        if depth > max_depth {
            return json!({"name": p.file_name().map(|s| s.to_string_lossy().to_string()).unwrap_or_default(), "truncated": true});
        }
        let mut children = Vec::new();
        if let Ok(rd) = fs::read_dir(p) {
            let mut entries: Vec<_> = rd.flatten().collect();
            entries.sort_by_key(|e| {
                let is_dir = e.file_type().map(|t| t.is_dir()).unwrap_or(false);
                (is_dir, e.file_name().to_string_lossy().to_lowercase())
            });
            for entry in entries {
                let ename = entry.file_name().to_string_lossy().to_string();
                if hidden(&ename) {
                    continue;
                }
                if entry.file_type().map(|t| t.is_dir()).unwrap_or(false) {
                    children.push(build(&entry.path(), depth + 1, max_depth));
                } else {
                    children.push(json!({
                        "name": ename,
                        "type": "file",
                        "size": entry.metadata().map(|m| m.len()).unwrap_or(0),
                    }));
                }
            }
        }
        json!({
            "name": p.file_name().map(|s| s.to_string_lossy().to_string()).unwrap_or_default(),
            "type": "directory",
            "children": children,
        })
    }
    let tree = build(Path::new(path), 1, max_depth);
    Ok(ok(json!(tree), Some(path)))
}

/// Real implementation: files modified within `hours` (newest first).
pub fn get_recent_files(args: &Value) -> Result<Value, String> {
    let directory = arg(args, "directory");
    let limit = args.get("limit").and_then(Value::as_u64).unwrap_or(10) as usize;
    let hours = args.get("hours").and_then(Value::as_u64).unwrap_or(24) as i64;
    if directory.is_empty() {
        return Err("get_recent_files requires `directory`".into());
    }
    let p = Path::new(directory);
    let now = std::time::SystemTime::now();
    let cutoff = now
        .checked_sub(std::time::Duration::from_secs((hours * 3600).max(0) as u64))
        .unwrap_or(now);
    let mut recent = Vec::new();
    for entry in walk(p) {
        if !entry.is_file() {
            continue;
        }
        if let Ok(m) = entry.metadata() {
            if let Ok(modified) = m.modified() {
                if modified > cutoff {
                    recent.push(json!({
                        "name": entry.file_name().map(|s| s.to_string_lossy().to_string()).unwrap_or_default(),
                        "path": entry.to_string_lossy().to_string(),
                        "modified": iso(modified),
                        "size": m.len(),
                    }));
                }
            }
        }
    }
    // Sort by modified desc.
    recent.sort_by(|a, b| {
        b["modified"]
            .as_str()
            .unwrap_or("")
            .cmp(a["modified"].as_str().unwrap_or(""))
    });
    recent.truncate(limit.max(1));
    Ok(ok(json!({"files": recent}), Some(directory)))
}

/// Real implementation: search files by name pattern (auto-wildcard like
/// Python: plain names become `*name*`).
pub fn search_files(args: &Value) -> Result<Value, String> {
    let query = arg(args, "query");
    let root = arg(args, "root_dir");
    if query.is_empty() {
        return Err("search_files requires `query`".into());
    }
    let root = if root.is_empty() { "." } else { root };
    let pattern =
        if query.contains('*') || query.contains('?') || query.contains('[') || query.contains(']')
        {
            query.to_string()
        } else {
            format!("*{query}*")
        };
    let glob = glob::Pattern::new(&pattern).map_err(|e| e.to_string())?;
    let base = Path::new(root);
    let mut matches = Vec::new();
    for entry in walk(base) {
        if entry.is_file() {
            if let Some(name) = entry.file_name().and_then(|s| s.to_str()) {
                if glob.matches(name) {
                    let meta = entry.metadata().ok();
                    matches.push(json!({
                        "name": name.to_string(),
                        "path": entry.to_string_lossy().to_string(),
                        "size": meta.map(|m| m.len()).unwrap_or(0),
                        "directory": entry.parent().map(|d| d.to_string_lossy().to_string()).unwrap_or_default(),
                    }));
                }
            }
        }
    }
    matches.sort_by(|a, b| {
        a["name"]
            .as_str()
            .unwrap_or("")
            .to_lowercase()
            .cmp(&b["name"].as_str().unwrap_or("").to_lowercase())
    });
    Ok(ok(json!({"results": matches}), Some(root)))
}

/// Real implementation: search files by content.
pub fn search_by_content(args: &Value) -> Result<Value, String> {
    let directory = arg(args, "directory");
    let query = arg(args, "query");
    if directory.is_empty() || query.is_empty() {
        return Err("search_by_content requires `directory` and `query`".into());
    }
    let query_lc = query.to_lowercase();
    let mut matches = Vec::new();
    for entry in walk(Path::new(directory)) {
        // Skip binary (null byte heuristic like _is_binary).
        if entry.is_file() {
            let bytes = match fs::read(&entry) {
                Ok(b) => b,
                Err(_) => continue,
            };
            if bytes[..bytes.len().min(1024)].contains(&0) {
                continue;
            }
            let content = String::from_utf8_lossy(&bytes).to_string();
            let content_lc = content.to_lowercase();
            if content_lc.contains(&query_lc) {
                let lines: Vec<(usize, &str)> = content
                    .lines()
                    .enumerate()
                    .filter(|(_, l)| l.to_lowercase().contains(&query_lc))
                    .take(5)
                    .collect();
                matches.push(json!({
                    "name": entry.file_name().map(|s| s.to_string_lossy().to_string()).unwrap_or_default(),
                    "path": entry.to_string_lossy().to_string(),
                    "matches": content_lc.matches(&query_lc).count(),
                    "lines": lines.iter().map(|(i, l)| json!([i, l.trim()])).collect::<Vec<_>>(),
                }));
            }
        }
    }
    Ok(ok(json!({"results": matches}), Some(directory)))
}

/// Simple recursive walk, skipping hidden entries.
fn walk(dir: &Path) -> Vec<std::path::PathBuf> {
    let mut out = Vec::new();
    if let Ok(rd) = fs::read_dir(dir) {
        for entry in rd.flatten() {
            if hidden(&entry.file_name().to_string_lossy()) {
                continue;
            }
            if entry.file_type().map(|t| t.is_dir()).unwrap_or(false) {
                out.extend(walk(&entry.path()));
            } else {
                out.push(entry.path());
            }
        }
    }
    out
}

/// Internal helper for glob matching used by `search_files`.
mod glob {
    pub struct Pattern {
        parts: Vec<Part>,
    }
    enum Part {
        Literal(String),
        Wildcards,
    }
    impl Pattern {
        pub fn new(pattern: &str) -> Result<Self, String> {
            let mut parts = Vec::new();
            let mut lit = String::new();
            for c in pattern.chars() {
                if c == '*' || c == '?' {
                    if !lit.is_empty() {
                        parts.push(Part::Literal(lit.clone()));
                        lit.clear();
                    }
                    parts.push(Part::Wildcards);
                } else {
                    lit.push(c);
                }
            }
            if !lit.is_empty() {
                parts.push(Part::Literal(lit));
            }
            Ok(Pattern { parts })
        }
        pub fn matches(&self, name: &str) -> bool {
            // Greedy scan: Wildcards consumes up to the next literal.
            // Implemented as a small backtracking matcher.
            self.match_from(&self.parts, name.as_bytes(), 0)
        }
        fn match_from(&self, parts: &[Part], s: &[u8], mut pos: usize) -> bool {
            for (i, part) in parts.iter().enumerate() {
                match part {
                    Part::Literal(l) => {
                        let b = l.as_bytes();
                        if pos + b.len() > s.len() || &s[pos..pos + b.len()] != b {
                            return false;
                        }
                        pos += b.len();
                    }
                    Part::Wildcards => {
                        // Try to consume 0.. remaining before the next literal.
                        let next = parts.get(i + 1);
                        match next {
                            Some(Part::Literal(l)) => {
                                let needle = l.as_bytes();
                                // Try each occurrence of the next literal so the
                                // wildcard can match greedily with backtracking.
                                let max = s.len().saturating_sub(needle.len());
                                for j in pos..=max {
                                    if &s[j..j + needle.len()] == needle {
                                        if self.match_from(&parts[i + 2..], s, j + needle.len()) {
                                            return true;
                                        }
                                    }
                                }
                                return false;
                            }
                            _ => {
                                return true; // trailing wildcard
                            }
                        }
                    }
                }
            }
            pos == s.len()
        }
    }
}
