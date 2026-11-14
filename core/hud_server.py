"""
J.A.R.V.I.S. V2 — Micro Tactical HUD Web Server & Full API Bridge (Section 7)
Serves the holographic Stark Arc Reactor & 3D Parallax Interface
with live endpoints for:
- Telemetry & hardware status
- Interactive command execution (chat & push-to-talk)
- Real-time SQLite Memory bank viewing & editing
- Reminder management & scheduling
- Voice profile switching
- Audio amplitude & speaking state
Zero external dependencies (uses standard library http.server).
"""

import os
import sys
import json
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Optional, Dict, Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config
from skills.system_diagnostics import get_system_telemetry
from core.voice_output import is_currently_speaking, speak
from core.sqlite_memory import get_sqlite_memory

HUD_DIR = os.path.join(ROOT, "assets", "hud")

# Shared state
_hud_state = {
    "status": "online",
    "mode": config.DEFAULT_VOICE_STYLE,
    "emotion": "composed",
    "last_query": "",
    "last_reply": "",
    "is_listening": False
}


def update_hud_state(key: str, val: Any):
    _hud_state[key] = val


class JarvisHUDHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HUD_DIR, **kwargs)

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/telemetry":
            telemetry = get_system_telemetry()
            data = {
                "status": _hud_state["status"],
                "mode": config.DEFAULT_VOICE_STYLE,
                "emotion": _hud_state["emotion"],
                "last_query": _hud_state["last_query"],
                "last_reply": _hud_state["last_reply"],
                "cpu_percent": telemetry["cpu_percent"],
                "ram_percent": telemetry["ram_percent"],
                "uptime": telemetry["uptime"],
                "disk_free_gb": telemetry["disk_free_gb"],
                "is_speaking": is_currently_speaking(),
                "is_listening": _hud_state.get("is_listening", False)
            }
            self._send_json(data)

        elif self.path == "/api/audio_state":
            self._send_json({
                "is_speaking": is_currently_speaking(),
                "is_listening": _hud_state.get("is_listening", False),
                "amplitude": 0.85 if is_currently_speaking() else 0.15
            })

        elif self.path == "/api/memory":
            mem = get_sqlite_memory()
            facts = mem.search_facts("")
            recent_turns = mem.get_recent_history(15)
            self._send_json({"facts": facts, "history": recent_turns})

        elif self.path == "/api/reminders":
            from skills.scheduler import get_scheduler
            sched = get_scheduler()
            reminders = sched.get_active_reminders()
            self._send_json({"reminders": reminders})

        else:
            super().do_GET()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            payload = json.loads(post_data)
        except Exception:
            payload = {}

        if self.path == "/api/command":
            query = payload.get("command", "").strip()
            voice_out = payload.get("speak", False)
            if not query:
                self._send_json({"error": "Empty command"}, 400)
                return

            from core.brain import JarvisBrain
            brain = JarvisBrain()
            reply, style = brain.process_query(query)

            _hud_state["last_query"] = query
            _hud_state["last_reply"] = reply
            _hud_state["mode"] = style

            if voice_out and reply:
                threading.Thread(target=speak, args=(reply, style, False), daemon=True).start()

            self._send_json({
                "success": True,
                "query": query,
                "reply": reply,
                "style": style
            })

        elif self.path == "/api/memory/add":
            k = payload.get("key", "").strip()
            v = payload.get("value", "").strip()
            cat = payload.get("category", "general").strip()
            if not k or not v:
                self._send_json({"error": "Key and value required"}, 400)
                return
            mem = get_sqlite_memory()
            success, msg = mem.store_fact(k, v, category=cat)
            self._send_json({"success": success, "message": msg})

        elif self.path == "/api/memory/delete":
            k = payload.get("key", "").strip()
            mem = get_sqlite_memory()
            deleted = mem.delete_fact(k)
            self._send_json({"success": deleted, "key": k})

        elif self.path == "/api/reminders/add":
            text = payload.get("text", "").strip()
            delay = float(payload.get("delay_seconds", 60.0))
            if not text:
                self._send_json({"error": "Reminder text required"}, 400)
                return
            from skills.scheduler import get_scheduler
            sched = get_scheduler()
            rem_id = sched.schedule_reminder(text, delay)
            self._send_json({"success": True, "reminder_id": rem_id})

        elif self.path == "/api/reminders/cancel":
            rem_id = payload.get("reminder_id")
            from skills.scheduler import get_scheduler
            sched = get_scheduler()
            ok = sched.cancel_reminder(rem_id)
            self._send_json({"success": ok})

        elif self.path == "/api/settings/voice":
            style = payload.get("style", "cinematic").strip()
            config.DEFAULT_VOICE_STYLE = style
            _hud_state["mode"] = style
            self._send_json({"success": True, "style": style})

        else:
            self._send_json({"error": "Unknown endpoint"}, 404)

    def log_message(self, format, *args):
        pass


class JarvisHUDServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self.running = False

    def start(self, in_background: bool = True):
        try:
            self.server = HTTPServer((self.host, self.port), JarvisHUDHandler)
            self.running = True
            if in_background:
                self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
                self._thread.start()
            else:
                self.server.serve_forever()
            return True, f"http://{self.host}:{self.port}"
        except Exception as e:
            return False, f"HUD server error: {e}"

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.running = False


_hud_server_instance: Optional[JarvisHUDServer] = None


def get_hud_server(port: int = 8080) -> JarvisHUDServer:
    global _hud_server_instance
    if _hud_server_instance is None:
        _hud_server_instance = JarvisHUDServer(port=port)
    return _hud_server_instance
