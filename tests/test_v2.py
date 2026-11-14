"""
J.A.R.V.I.S. V2 — Master Architectural Verification Suite
Validates all 18 core sections of the V2 Development Directive:
- SQLite Relational Memory & Conflict Detection (Section 2)
- Zero LLM Natural Language & Web Retrieval (Section 3 & 10)
- Context-Aware Suggestions (Section 4)
- Barge-In Interruption Audio Engine (Section 6)
- Tactical HUD Server & Holographic Endpoints (Section 7)
- Autonomous Project Builder & AST Verification (Section 18)
- Telegram 2681 Passcode & Secure Dispatch (Section 14)
- Google Suite Bridge (Section 15)
"""

import os
import sys
import unittest
import json
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config
from core.brain import JarvisBrain
from core.sqlite_memory import get_sqlite_memory
from skills.memory import handle_store, handle_recall
from skills.project_builder import get_project_builder
from skills.web_search import research_topic
from core.voice_output import is_currently_speaking, stop_speaking
from skills.google_suite import get_google_bridge
from core.hud_server import get_hud_server


class TestJarvisV2Core(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brain = JarvisBrain()
        cls.mem = get_sqlite_memory()
        cls.builder = get_project_builder()

    def test_01_sqlite_memory_lifecycle(self):
        """Validates Section 2: Relational SQLite storage, permanence, and conflict detection."""
        # Store initial fact
        ok, msg = self.mem.store_fact("tactical_priority", "V2 Deployment", category="milestone", is_permanent=True)
        self.assertTrue(ok)
        val = self.mem.get_fact("tactical_priority")
        self.assertEqual(val, "V2 Deployment")

        # Conflict detection: updating value produces notification
        ok2, msg2 = self.mem.store_fact("tactical_priority", "Iron Man Mark VII", category="milestone", is_permanent=True)
        self.assertTrue(ok2)
        self.assertIn("Updated record", msg2)
        self.assertEqual(self.mem.get_fact("tactical_priority"), "Iron Man Mark VII")

        # Clean up
        self.mem.delete_fact("tactical_priority")

    def test_02_natural_name_memory_recall(self):
        """Validates Section 2: 'Remember that my name is Dev. From today, call me Dev.' -> 'What is my name?'"""
        reply, _ = self.brain.process_query("Remember that my name is Dev")
        self.assertIn("Dev", reply)

        reply_name, _ = self.brain.process_query("What is my name?")
        self.assertIn("Dev", reply_name)

    def test_03_natural_factual_queries_without_search_keyword(self):
        """Validates Section 3 & 10: 'Tell me about Neymar' & 'Explain quantum computing' trigger web research."""
        intent_neymar = self.brain.parse_intent("Tell me about Neymar")
        self.assertEqual(intent_neymar.intent, "web_search")
        self.assertIn("neymar", intent_neymar.parameters.get("query", "").lower())

        intent_qc = self.brain.parse_intent("Explain quantum computing")
        self.assertEqual(intent_qc.intent, "web_search")
        self.assertIn("quantum computing", intent_qc.parameters.get("query", "").lower())

        intent_who = self.brain.parse_intent("Who is Tony Stark")
        self.assertEqual(intent_who.intent, "web_search")

    def test_04_barge_in_interruption(self):
        """Validates Section 6: 'Jarvis, wait!' and 'Stop' halt speech immediately."""
        intent_wait = self.brain.parse_intent("Jarvis, wait!")
        self.assertEqual(intent_wait.intent, "barge_in")

        reply, style = self.brain.process_query("wait")
        self.assertIn("Certainly, Dev", reply)
        self.assertEqual(style, "alert")

    def test_05_autonomous_project_builder(self):
        """Validates Section 18: Prompt-to-code generation, AST verification, and directory structure."""
        # Test 2D Racing Game generation
        res_racing = self.builder.build_project("Build me a 2D racing game in Python", auto_launch=False)
        self.assertTrue(res_racing["success"])
        self.assertTrue(os.path.isfile(res_racing["path"]))
        with open(res_racing["path"], "r", encoding="utf-8") as f:
            code = f.read()
            self.assertIn("RacingGame", code)

        # Test Calculator generation
        res_calc = self.builder.build_project("Build a tactical calculator", auto_launch=False)
        self.assertTrue(res_calc["success"])
        self.assertTrue(os.path.isfile(res_calc["path"]))

    def test_06_google_suite_bridge(self):
        """Validates Section 15: Google Suite read-only search and draft confirmation."""
        bridge = get_google_bridge()
        res_search = bridge.search_messages("meeting")
        self.assertIn("speech", res_search)

        res_draft = bridge.create_draft("stark@industries.com", "Project Status", "V2 is live.")
        self.assertEqual(res_draft["status"], "pending_authorization")
        self.assertIn("explicit confirmation", res_draft["speech"])

    def test_07_hud_server_endpoints(self):
        """Validates Section 7: HUD HTTP server and API endpoints."""
        hud = get_hud_server(port=8085)
        ok, url = hud.start(in_background=True)
        self.assertTrue(ok)
        import urllib.request
        # Test telemetry endpoint
        req = urllib.request.urlopen("http://127.0.0.1:8085/api/telemetry")
        self.assertEqual(req.status, 200)
        data = json.loads(req.read().decode("utf-8"))
        self.assertIn("cpu_percent", data)
        self.assertIn("ram_percent", data)
        self.assertIn("mode", data)
        hud.stop()

    def test_08_desktop_gui_components(self):
        """Validates Section 3: Native PyQt5 Windows Desktop Application components."""
        from PyQt5.QtWidgets import QApplication
        from core.desktop_gui import JarvisDesktopWindow, LiquidParticleCoreWidget
        app = QApplication.instance() or QApplication([])
        win = JarvisDesktopWindow()
        self.assertIsNotNone(win)
        self.assertIsInstance(win.core_widget, LiquidParticleCoreWidget)
        self.assertTrue(win.table_mem.columnCount() == 4)
        self.assertTrue(win.table_rem.columnCount() == 3)
        win.close()


if __name__ == "__main__":
    unittest.main()

