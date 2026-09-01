//! Conversation store (mirrors `core/memory/conversation_store.py` + the
//! `/conversations` API surface).
//!
//! Scaffold uses a single JSON file under `~/.bissi/conversations.json`.
//! A later port may replace this with `rusqlite` to match the existing
//! `conversations.db`.

use std::collections::HashMap;
use std::fs;
use std::sync::RwLock;

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

use crate::config;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Conversation {
    pub id: i64,
    pub title: String,
    pub archived: bool,
    pub messages: Vec<Value>,
}

pub struct ConversationStore {
    path: std::path::PathBuf,
    inner: RwLock<HashMap<i64, Conversation>>,
    /// Next id for new conversations (reserved — `create` is wired once the
    /// chat flow persists a new conversation when no id is supplied).
    #[allow(dead_code)]
    next_id: RwLock<i64>,
}

impl ConversationStore {
    pub fn new() -> Self {
        let path = config::data_dir().join("conversations.json");
        let (map, next) = Self::load(&path);
        Self {
            path,
            inner: RwLock::new(map),
            next_id: RwLock::new(next),
        }
    }

    fn load(path: &std::path::Path) -> (HashMap<i64, Conversation>, i64) {
        let mut next = 1;
        let map = fs::read_to_string(path)
            .ok()
            .and_then(|s| serde_json::from_str::<Vec<Conversation>>(&s).ok())
            .unwrap_or_default()
            .into_iter()
            .map(|c| {
                if c.id >= next {
                    next = c.id + 1;
                }
                (c.id, c)
            })
            .collect();
        (map, next)
    }

    pub fn save(&self) {
        let list: Vec<Conversation> = self
            .inner
            .read()
            .expect("poisoned")
            .values()
            .cloned()
            .collect();
        if let Some(dir) = self.path.parent() {
            let _ = fs::create_dir_all(dir);
        }
        if let Ok(s) = serde_json::to_string(&list) {
            let _ = fs::write(&self.path, s);
        }
    }

    /// Create a new empty conversation and return its id (reserved for the
    /// new-chat path; not yet called by the agent loop, which currently
    /// creates no conversation when the client omits `conversation_id`).
    #[allow(dead_code)]
    pub fn create(&self) -> i64 {
        let id = {
            let mut next = self.next_id.write().expect("poisoned");
            let id = *next;
            *next += 1;
            id
        };
        self.inner.write().expect("poisoned").insert(
            id,
            Conversation { id, title: String::new(), archived: false, messages: vec![] },
        );
        id
    }

    pub fn list(&self, limit: usize) -> Vec<Value> {
        let mut rows: Vec<Conversation> = self
            .inner
            .read()
            .expect("poisoned")
            .values()
            .cloned()
            .filter(|c| !c.archived)
            .collect();
        rows.sort_by(|a, b| b.id.cmp(&a.id));
        rows.truncate(limit);
        rows.into_iter()
            .map(|c| json!({"id": c.id, "title": c.title, "archived": c.archived}))
            .collect()
    }

    pub fn history(&self, id: i64) -> Option<Value> {
        self.inner
            .read()
            .expect("poisoned")
            .get(&id)
            .map(|c| json!({"id": c.id, "title": c.title, "messages": c.messages}))
    }

    pub fn delete(&self, id: i64) -> bool {
        let removed = self.inner.write().expect("poisoned").remove(&id).is_some();
        self.save();
        removed
    }

    pub fn rename(&self, id: i64, title: &str) -> bool {
        let mut map = self.inner.write().expect("poisoned");
        match map.get_mut(&id) {
            Some(c) => {
                c.title = title.to_string();
                self.save();
                true
            }
            None => false,
        }
    }

    pub fn archive(&self, id: i64) -> bool {
        let mut map = self.inner.write().expect("poisoned");
        match map.get_mut(&id) {
            Some(c) => {
                c.archived = true;
                self.save();
                true
            }
            None => false,
        }
    }
}

impl Default for ConversationStore {
    fn default() -> Self {
        Self::new()
    }
}
