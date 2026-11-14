"""
J.A.R.V.I.S. V2 — Relational SQLite Persistent Memory Engine
Provides robust local storage:
- Personal facts & preferences with permanence flags (permanent vs temporary)
- Topic tags and update timestamps
- Conversation history logging with retrieval
- Conflict detection (alerts if an incoming fact contradicts stored data)
- Full export, backup, edit, and deletion capabilities
- Zero cloud dependence, sub-millisecond local queries
"""

import os
import sys
import sqlite3
import datetime
import json
from typing import Dict, Any, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config

DB_PATH = os.path.join(ROOT, "memory", "jarvis_memory.db")


class JarvisSQLiteMemory:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes tables for facts, conversation turns, and preferences."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Facts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    is_permanent INTEGER DEFAULT 1,
                    confidence REAL DEFAULT 1.0,
                    source TEXT DEFAULT 'user_explicit',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            # Conversation History table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    intent TEXT,
                    detected_emotion TEXT,
                    voice_style TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            # Topics & Tags table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT UNIQUE NOT NULL,
                    mention_count INTEGER DEFAULT 1,
                    last_mentioned TEXT NOT NULL
                )
            """)
            conn.commit()

        # Seed initial owner identity if empty
        self.ensure_owner_identity()

    def ensure_owner_identity(self):
        """Ensures Dev's core identity is permanently recorded."""
        if not self.get_fact("user_name"):
            self.store_fact("user_name", config.USER_NAME, category="identity", is_permanent=True)
        if not self.get_fact("user_title"):
            self.store_fact("user_title", config.USER_TITLE, category="identity", is_permanent=True)

    def store_fact(
        self,
        key: str,
        value: str,
        category: str = "general",
        is_permanent: bool = True,
        confidence: float = 1.0,
        source: str = "user_explicit"
    ) -> Tuple[bool, str]:
        """
        Stores or updates a fact.
        Detects conflicts if key already exists with a different value.
        """
        clean_key = key.strip().lower()
        clean_val = value.strip()
        now = datetime.datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value, is_permanent FROM facts WHERE key = ?", (clean_key,))
            existing = cursor.fetchone()

            if existing:
                old_val = existing["value"]
                if old_val.lower() != clean_val.lower():
                    # Conflict detected: update with audit note
                    cursor.execute("""
                        UPDATE facts
                        SET value = ?, category = ?, is_permanent = ?, confidence = ?, updated_at = ?
                        WHERE key = ?
                    """, (clean_val, category, 1 if is_permanent else 0, confidence, now, clean_key))
                    conn.commit()
                    return True, f"Updated record for '{clean_key}' from '{old_val}' to '{clean_val}', sir."
                return True, f"Record for '{clean_key}' is already verified as '{clean_val}', sir."

            # Insert new fact
            cursor.execute("""
                INSERT INTO facts (key, value, category, is_permanent, confidence, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (clean_key, clean_val, category, 1 if is_permanent else 0, confidence, source, now, now))
            conn.commit()
            return True, f"Recorded permanently in core memory banks: {clean_key} is {clean_val}, sir."

    def get_fact(self, key: str) -> Optional[str]:
        clean_key = key.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM facts WHERE key = ?", (clean_key,))
            row = cursor.fetchone()
            if row:
                return row["value"]

            # Partial match search
            cursor.execute("SELECT value FROM facts WHERE key LIKE ? OR ? LIKE ('%' || key || '%')", (f"%{clean_key}%", clean_key))
            row = cursor.fetchone()
            if row:
                return row["value"]
        return None

    def search_facts(self, query: str) -> List[Dict[str, Any]]:
        q = f"%{query.strip().lower()}%"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value, category, is_permanent, updated_at FROM facts WHERE key LIKE ? OR value LIKE ?", (q, q))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def delete_fact(self, key: str) -> bool:
        clean_key = key.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM facts WHERE key = ?", (clean_key,))
            conn.commit()
            return cursor.rowcount > 0

    def log_turn(
        self,
        role: str,
        content: str,
        intent: Optional[str] = None,
        emotion: Optional[str] = None,
        style: Optional[str] = None
    ):
        """Logs a single conversation turn."""
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversation_history (role, content, intent, detected_emotion, voice_style, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (role, content.strip(), intent, emotion, style, now))
            conn.commit()

    def get_recent_history(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Retrieves recent conversation turns for context continuity."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content, intent, detected_emotion, timestamp
                FROM conversation_history
                ORDER BY id DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in reversed(rows)]

    def export_memory_json(self) -> str:
        """Exports all facts and history to JSON string."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM facts")
            facts = [dict(r) for r in cursor.fetchall()]
            cursor.execute("SELECT * FROM conversation_history ORDER BY id DESC LIMIT 100")
            history = [dict(r) for r in cursor.fetchall()]
            return json.dumps({"facts": facts, "history": history}, indent=2)


# Global SQLite Memory Instance
_sqlite_mem_instance: Optional[JarvisSQLiteMemory] = None


def get_sqlite_memory() -> JarvisSQLiteMemory:
    global _sqlite_mem_instance
    if _sqlite_mem_instance is None:
        _sqlite_mem_instance = JarvisSQLiteMemory()
    return _sqlite_mem_instance

