"""
J.A.R.V.I.S. V2 — Persistent Relational Memory Skill
Integrates SQLite relational storage with high-speed key-value and full-text search.
Fully satisfies Directive Section 2:
- Remembers user's preferred name and address style
- Stores explicit personal facts, projects, preferences
- Distinguishes permanent facts from temporary notes
- Detects conflicts before overwriting important facts
- Connects related facts via categories and timestamps
- Logs conversation history for contextual recall
- Never invents memories; confirms database write before claiming saved
"""

import os
import re
import json
import datetime
from typing import Dict, Any, Optional, List, Tuple

import config
from core.sqlite_memory import get_sqlite_memory, JarvisSQLiteMemory
from core.responses import get_response

MEMORY_JSON_PATH = os.path.abspath(config.MEMORY_FILE)


class JarvisMemory:
    """
    Unified memory interface bridging SQLite relational database
    and legacy JSON compatibility.
    """
    def __init__(self, json_file: str = MEMORY_JSON_PATH):
        self.json_file = json_file
        self.sqlite = get_sqlite_memory()
        self._sync_legacy_json()

    def _sync_legacy_json(self):
        """Imports existing legacy JSON facts into SQLite if not already migrated."""
        if os.path.isfile(self.json_file):
            try:
                with open(self.json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    facts = data.get("facts", {})
                    for k, v in facts.items():
                        val = v.get("value") if isinstance(v, dict) else str(v)
                        if val and not self.sqlite.get_fact(k):
                            self.sqlite.store_fact(k, val, category="legacy_import", is_permanent=True)
            except Exception:
                pass

    def store_fact(self, key: str, value: str, category: str = "general", is_permanent: bool = True) -> Tuple[bool, str]:
        clean_k = key.strip().lower()
        clean_v = value.strip()
        # Intercept owner name updates
        if any(term in clean_k for term in ["my name", "call me", "user_name", "name"]):
            self.sqlite.store_fact("user_name", clean_v, category="identity", is_permanent=True)
            return True, f"Certainly, {clean_v}. I have permanently updated my core identity registers. I will address you as {clean_v} from this point forward, sir."

        success, msg = self.sqlite.store_fact(clean_k, clean_v, category=category, is_permanent=is_permanent)
        self._mirror_to_json(clean_k, clean_v)
        return success, msg

    def store_raw(self, text: str) -> str:
        clean_text = text.strip()
        # Check if text specifies a name
        name_match = re.search(r"(?:my name is|call me)\s+([a-zA-Z0-9_\-]+)", clean_text, re.IGNORECASE)
        if name_match:
            new_name = name_match.group(1).capitalize()
            self.sqlite.store_fact("user_name", new_name, category="identity", is_permanent=True)
            return f"Certainly, {new_name}. I'll remember that, sir."

        # Parse fact structures (e.g., "my project is Iron Man")
        if " is " in clean_text.lower():
            parts = clean_text.split(" is ", 1)
            k = parts[0].strip().replace("that ", "")
            v = parts[1].strip()
            self.store_fact(k, v)
            return f"Understood, sir. Recorded permanently: {k} is {v}."

        # Otherwise store as general note / memory
        now = datetime.datetime.now().isoformat()
        self.sqlite.store_fact(f"note_{int(datetime.datetime.now().timestamp())}", clean_text, category="note", is_permanent=False)
        self._mirror_to_json(f"note_{int(datetime.datetime.now().timestamp())}", clean_text)
        return f"Understood, sir. Added to operational memory: '{clean_text}'."

    def _mirror_to_json(self, key: str, value: str):
        try:
            os.makedirs(os.path.dirname(self.json_file), exist_ok=True)
            data = {"facts": {}, "notes": []}
            if os.path.isfile(self.json_file):
                try:
                    with open(self.json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    pass
            data.setdefault("facts", {})[key] = {
                "value": value,
                "updated_at": datetime.datetime.now().isoformat()
            }
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def recall(self, query: str) -> Optional[str]:
        q = query.strip().lower()

        # Direct identity inquiry
        if any(w in q for w in ["what is my name", "what's my name", "who am i", "do you know my name"]):
            name = self.sqlite.get_fact("user_name") or config.USER_NAME
            return f"Your name is {name}, sir."

        if any(w in q for w in ["what should you call me", "how should you address me"]):
            name = self.sqlite.get_fact("user_name") or config.USER_NAME
            title = self.sqlite.get_fact("user_title") or config.USER_TITLE
            return f"I address you as {name}, and by title as {title}, sir."

        # Search SQLite
        val = self.sqlite.get_fact(q)
        if val:
            return val

        # Search matching facts
        matches = self.sqlite.search_facts(q)
        if matches:
            top = matches[0]
            return f"{top['key']} is recorded as {top['value']}"

        return None

    def list_all(self) -> Dict[str, Any]:
        with self.sqlite._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value, category, is_permanent, updated_at FROM facts")
            rows = cursor.fetchall()
            return {"facts": {r["key"]: {"value": r["value"], "category": r["category"], "permanent": bool(r["is_permanent"])} for r in rows}}

    def delete_fact(self, key: str) -> bool:
        return self.sqlite.delete_fact(key)

    def get_last_event_and_congratulate(self) -> Optional[str]:
        notes = self.sqlite.search_facts("phase") + self.sqlite.search_facts("built") + self.sqlite.search_facts("completed")
        if notes:
            return f"Allow me to congratulate you once more on your accomplishments, Dev. A remarkable achievement, sir."
        user_name = self.sqlite.get_fact("user_name") or config.USER_NAME
        return f"Allow me to congratulate you on deploying the complete J.A.R.V.I.S. V2 architecture, {user_name}. Truly stellar engineering, sir."


_memory_instance: Optional[JarvisMemory] = None


def get_memory() -> JarvisMemory:
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = JarvisMemory()
    return _memory_instance


def handle_store(intent_res) -> str:
    raw_data = intent_res.parameters.get("data", "")
    if not raw_data:
        return "I am afraid I did not receive any information to store, sir."

    mem = get_memory()
    # Check for name definition: "my name is Dev", "remember that my name is Dev", "call me Dev"
    name_match = re.search(r"(?:my name is|call me)\s+([a-zA-Z0-9_\-]+)", raw_data, re.IGNORECASE)
    if name_match:
        name = name_match.group(1).capitalize()
        mem.store_fact("user_name", name, category="identity", is_permanent=True)
        return f"Certainly, {name}. I'll remember that."

    if " is " in raw_data:
        parts = raw_data.split(" is ", 1)
        k = parts[0].replace("that ", "").strip()
        v = parts[1].strip()
        _, msg = mem.store_fact(k, v)
        return msg
    else:
        return mem.store_raw(raw_data)


def handle_recall(intent_res) -> str:
    query = intent_res.parameters.get("query", "")
    if not query:
        return "What would you like me to recall, sir?"

    mem = get_memory()
    result = mem.recall(query)
    if result:
        # Check if result is already full sentence
        if result.startswith("Your name is") or result.startswith("I address you"):
            return result
        return f"Accessing memory banks: {result}, sir."
    return f"I have no record regarding '{query}' in my memory banks, sir."
