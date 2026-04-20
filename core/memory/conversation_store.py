"""Conversation memory store for BISSI.

Persists chat history to SQLite for long-term memory.
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from utils.helpers import expand_path, ensure_dir, now_iso


class ConversationStore:
    """SQLite-based conversation storage."""
    
    def __init__(self, db_path: Union[str, Path] = "~/.bissi/conversations.db"):
        """Initialize conversation store.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = expand_path(db_path)
        ensure_dir(self.db_path.parent)
        self._init_db()
    
    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    archived INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(conversations)").fetchall()
            }
            if "archived" not in columns:
                conn.execute(
                    "ALTER TABLE conversations ADD COLUMN archived INTEGER NOT NULL DEFAULT 0"
                )
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)
            
            conn.commit()
    
    def create_conversation(self, title: Optional[str] = None) -> int:
        """Create new conversation thread.
        
        Args:
            title: Optional conversation title
            
        Returns:
            Conversation ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO conversations (title) VALUES (?)",
                (title or f"Conversation {now_iso()}",)
            )
            conn.commit()
            return cursor.lastrowid

    def update_conversation_title(self, conversation_id: int, title: str) -> bool:
        """Update conversation title.
        
        Args:
            conversation_id: Conversation to update
            title: New title
            
        Returns:
            True if updated successfully
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (title, conversation_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def save_message(self, 
                     conversation_id: int,
                     role: str,
                     content: str,
                     metadata: Optional[Dict] = None) -> int:
        """Save message to conversation.
        
        Args:
            conversation_id: Target conversation ID
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Optional additional data (tool calls, etc.)
            
        Returns:
            Message ID
        """
        with sqlite3.connect(self.db_path) as conn:
            # Update conversation timestamp
            conn.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,)
            )
            
            # Insert message
            cursor = conn.execute(
                """INSERT INTO messages (conversation_id, role, content, metadata)
                   VALUES (?, ?, ?, ?)""",
                (conversation_id, role, content, json.dumps(metadata) if metadata else None)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_history(self, 
                    conversation_id: int,
                    limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history.
        
        Args:
            conversation_id: Conversation to retrieve
            limit: Maximum number of messages (None for all)
            
        Returns:
            List of messages with role, content, timestamp
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if limit:
                # Get last N messages (most recent), then re-order ascending
                query = f"""SELECT role, content, metadata, timestamp FROM (
                              SELECT role, content, metadata, timestamp
                              FROM messages
                              WHERE conversation_id = ?
                              ORDER BY timestamp DESC
                              LIMIT {limit}
                          ) ORDER BY timestamp ASC"""
            else:
                query = """SELECT role, content, metadata, timestamp
                          FROM messages
                          WHERE conversation_id = ?
                          ORDER BY timestamp"""
            
            rows = conn.execute(query, (conversation_id,)).fetchall()
            
            return [
                {
                    'role': row['role'],
                    'content': row['content'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else None,
                    'timestamp': row['timestamp']
                }
                for row in rows
            ]
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of recent conversations.
        
        Args:
            limit: Number of conversations to return
            
        Returns:
            List of conversation summaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            rows = conn.execute(
                """SELECT c.id, c.title, c.created_at, c.updated_at,
                          c.archived,
                          COUNT(m.id) as message_count,
                          (SELECT content FROM messages WHERE conversation_id = c.id 
                           ORDER BY id ASC LIMIT 1) as first_message
                    FROM conversations c
                    LEFT JOIN messages m ON c.id = m.conversation_id
                    WHERE c.archived = 0
                    GROUP BY c.id
                    ORDER BY c.updated_at DESC
                    LIMIT ?""",
                (limit,)
            ).fetchall()
            
            return [
                {
                    'id': row['id'],
                    'title': row['title'],
                    'archived': row['archived'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'message_count': row['message_count'],
                    'first_message': row['first_message']
                }
                for row in rows
            ]
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete conversation and all its messages.
        
        Args:
            conversation_id: Conversation to delete
            
        Returns:
            True if deleted successfully
        """
        with sqlite3.connect(self.db_path) as conn:
            # Delete messages first (foreign key constraint)
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            
            # Delete conversation
            cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            conn.commit()
            
            return cursor.rowcount > 0

    def archive_conversation(self, conversation_id: int) -> bool:
        """Archive a conversation without deleting messages.

        Args:
            conversation_id: Conversation to archive

        Returns:
            True if archived successfully
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE conversations SET archived = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def export_conversation(self, 
                            conversation_id: int,
                            format: str = 'json') -> Union[str, Dict]:
        """Export conversation to file format.
        
        Args:
            conversation_id: Conversation to export
            format: 'json' or 'txt'
            
        Returns:
            Exported data as string or dict
        """
        history = self.get_history(conversation_id)
        
        if format == 'json':
            return {
                'conversation_id': conversation_id,
                'messages': history,
                'exported_at': now_iso()
            }
        
        elif format == 'txt':
            lines = []
            for msg in history:
                lines.append(f"[{msg['timestamp']}] {msg['role'].upper()}")
                lines.append(msg['content'])
                lines.append("-" * 40)
            return '\n'.join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def search_conversations(self, query: str) -> List[Dict[str, Any]]:
        """Search for conversations containing specific text.
        
        Args:
            query: Search text
        Returns:
            Matching conversations with context
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            rows = conn.execute(
                """SELECT DISTINCT c.id, c.title, c.updated_at
                   FROM conversations c
                   JOIN messages m ON c.id = m.conversation_id
                   WHERE m.content LIKE ?
                   ORDER BY c.updated_at DESC""",
                (f'%{query}%',)
            ).fetchall()
            
            return [
                {
                    'id': row['id'],
                    'title': row['title'],
                    'updated_at': row['updated_at']
                }
                for row in rows
            ]
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics.
        
        Returns:
            Dictionary with conversation and message counts
        """
        with sqlite3.connect(self.db_path) as conn:
            conv_count = conn.execute(
                "SELECT COUNT(*) FROM conversations"
            ).fetchone()[0]
            
            msg_count = conn.execute(
                "SELECT COUNT(*) FROM messages"
            ).fetchone()[0]
            
            return {
                'conversations': conv_count,
                'messages': msg_count
            }
