"""
J.A.R.V.I.S. — Core Brain & Intent Routing Engine
=================================================
Parses user queries into structured intents, extracts parameters,
manages conversation context, and dispatches to appropriate skills.

Guiding Principles:
1. Absolute Integrity: Never pretends a task is complete when it hasn't succeeded.
2. Character Fidelity: Formal British cadence, confident wit, composed elegance.
3. Lightweight & Fast: Sub-millisecond rule & pattern routing, zero local LLM overhead.
"""

import re
import time
import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Callable

from core.responses import get_response
import config


@dataclass
class IntentResult:
    intent: str
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    raw_query: str = ""
    suggested_style: str = "cinematic"


@dataclass
class ConversationContext:
    last_intent: Optional[str] = None
    last_query: Optional[str] = None
    last_response: Optional[str] = None
    last_parameters: Dict[str, Any] = field(default_factory=dict)
    pending_confirmation_action: Optional[Callable] = None
    turn_count: int = 0
    user_emotion: str = "neutral"


class JarvisBrain:
    def __init__(self):
        self.context = ConversationContext()
        self.skill_registry: Dict[str, Callable] = {}
        self._register_default_skills()

    def _register_default_skills(self):
        """Register built-in handlers and Phase 4 skills."""
        self.skill_registry["time"] = self._handle_time
        self.skill_registry["date"] = self._handle_date
        self.skill_registry["greeting"] = self._handle_greeting
        self.skill_registry["status"] = self._handle_status
        self.skill_registry["identity"] = self._handle_identity
        self.skill_registry["mode_switch"] = self._handle_mode_switch
        self.skill_registry["calculation"] = self._handle_calculation
        self.skill_registry["banter"] = self._handle_banter
        self.skill_registry["repeat"] = self._handle_repeat
        self.skill_registry["emotion_check"] = self._handle_emotion_check
        self.skill_registry["congratulate"] = self._handle_congratulate

        # Phase 4 & Phase 6 Skills
        try:
            from skills.memory import handle_store, handle_recall
            from skills.web_search import handle_search
            from skills.system_control import handle_app_launch, handle_system_action
            from skills.scheduler import handle_reminder, handle_briefing
            from skills.weather import handle_weather_query
            from skills.system_diagnostics import handle_diagnostics
            from core.self_improvement import handle_flaws_check
            from skills.protocols import handle_protocol
            self.skill_registry["memory_store"] = handle_store
            self.skill_registry["memory_recall"] = handle_recall
            self.skill_registry["web_search"] = handle_search
            self.skill_registry["app_launch"] = handle_app_launch
            self.skill_registry["system_control"] = handle_system_action
            self.skill_registry["reminder"] = handle_reminder
            self.skill_registry["morning_briefing"] = handle_briefing
            self.skill_registry["weather"] = handle_weather_query
            self.skill_registry["diagnostics"] = handle_diagnostics
            self.skill_registry["flaws_audit"] = handle_flaws_check
            self.skill_registry["protocol"] = handle_protocol
            from skills.telegram_backup import handle_backup_command
            self.skill_registry["telegram_backup"] = handle_backup_command
            from skills.project_builder import handle_project_build
            self.skill_registry["build_project"] = handle_project_build
            from skills.google_suite import handle_google_suite
            self.skill_registry["google_suite"] = handle_google_suite
        except ImportError as e:
            pass

    def register_skill(self, intent_name: str, handler: Callable):
        """Allows external skills to hook into brain intent dispatch."""
        self.skill_registry[intent_name] = handler

    # ------------------------------------------------------------------
    # INTENT PARSING & PATTERN MATCHING
    # ------------------------------------------------------------------
    def parse_intent(self, text: str) -> IntentResult:
        """
        Parses raw text and extracts intent, confidence, and parameters.
        Zero memory overhead; deterministic and accurate.
        """
        raw = text.strip()
        low = raw.lower()

        # 1. Mode Switching
        if any(w in low for w in ["cinematic mode", "cinema mode"]):
            return IntentResult("mode_switch", 0.98, {"mode": "cinematic"}, raw, "cinematic")
        if any(w in low for w in ["normal mode", "standard mode"]):
            return IntentResult("mode_switch", 0.98, {"mode": "normal"}, raw, "normal")
        if any(w in low for w in ["night mode", "quiet mode", "sleep mode"]):
            return IntentResult("mode_switch", 0.98, {"mode": "night"}, raw, "night")

        # Protocols (Stark Automated Routines)
        if "protocol" in low or any(w in low for w in ["coding mode", "focus mode", "movie mode", "lockdown"]):
            proto_match = re.search(r"\b(?:initiate|engage|run|execute|activate|start)?\s*([a-zA-Z\s_]+)\s+protocol\b", low)
            target = "workshop"
            if proto_match:
                p_raw = proto_match.group(1).strip()
                if "clean slate" in p_raw or "lockdown" in p_raw:
                    target = "lockdown"
                elif "cinema" in p_raw or "movie" in p_raw:
                    target = "cinema"
                elif "night" in p_raw or "bedtime" in p_raw:
                    target = "night_owl"
                elif "workshop" in p_raw or "coding" in p_raw:
                    target = "workshop"
                else:
                    target = p_raw
            elif "movie" in low or "cinema" in low:
                target = "cinema"
            elif "lockdown" in low:
                target = "lockdown"
            elif "night" in low or "bedtime" in low:
                target = "night_owl"
            elif "coding" in low or "focus" in low:
                target = "workshop"
            return IntentResult("protocol", 0.95, {"protocol": target}, raw, "cinematic")

        # 2. Shutdown / Standby
        if any(w in low for w in ["shutdown", "shut down", "power down", "good night", "exit", "quit", "go to sleep"]):
            return IntentResult("shutdown", 0.95, {}, raw, "cinematic")

        # 3. Time & Date
        if re.search(r"\b(what time|time is it|the time|current time|clock)\b", low):
            return IntentResult("time", 0.95, {}, raw, "normal")
        if re.search(r"\b(what('s| is) the date|today('s)? date|what day is it)\b", low):
            return IntentResult("date", 0.95, {}, raw, "normal")

        # 4. Basic Math / Calculation
        calc_match = re.search(r"(?:calculate|what is|compute|solve)?\s*([0-9\.\s\+\-\*\/\^\(\)]+[0-9])", low)
        if calc_match and any(op in calc_match.group(1) for op in ["+", "-", "*", "/", "^"]):
            expr = calc_match.group(1).replace("^", "**").strip()
            return IntentResult("calculation", 0.90, {"expression": expr}, raw, "normal")

        # 7. Greetings (check before general how are you status)
        if re.search(r"^(hey|hello|hi|good morning|good afternoon|good evening)\b", low):
            return IntentResult("greeting", 0.90, {}, raw, "cinematic")

        # 8. Weather & Environmental Sensors
        if re.search(r"\b(weather|temperature|forecast|climate|how('s| is) it outside|outside temp)\b", low):
            loc_match = re.search(r"\b(?:in|for|at)\s+([a-zA-Z\s]+)", raw, re.IGNORECASE)
            loc = loc_match.group(1).strip() if loc_match else None
            return IntentResult("weather", 0.94, {"location": loc}, raw, "cinematic")

        # 9. Status & Telemetry
        if any(w in low for w in ["detect flaw", "flaw", "flaws", "what should we improve", "what to improve", "self reflection", "self diagnostic audit", "system improvements"]):
            return IntentResult("flaws_audit", 0.95, {}, raw, "cinematic")

        if any(w in low for w in ["check status", "how are you", "all green", "systems check"]) or low.strip() == "status":
            return IntentResult("status", 0.92, {}, raw, "cinematic")

        if any(w in low for w in ["telemetry", "hardware", "cpu", "ram", "battery", "diagnostic"]):
            return IntentResult("diagnostics", 0.95, {}, raw, "cinematic")

        if "status" in low:
            return IntentResult("status", 0.92, {}, raw, "cinematic")

        # 9. Emotion & Mood Inquiries
        if re.search(r"\b(how do i sound|what is my mood|detect my emotion|check my tone|what tone do you detect|am i happy|am i angry|am i sad)\b", low):
            return IntentResult("emotion_check", 0.95, {}, raw, "witty")

        # 10. Milestone Congratulation & Achievements
        if any(w in low for w in ["congratulate me", "what did i achieve", "celebrate milestone", "what did we accomplish", "last event", "congratulate"]):
            return IntentResult("congratulate", 0.95, {}, raw, "witty")

        # 11. Telegram Project Backup
        if any(w in low for w in ["backup to telegram", "telegram backup", "backup now", "send backup"]):
            return IntentResult("telegram_backup", 0.95, {}, raw, "cinematic")

        # 12. Identity
        if any(w in low for w in ["who are you", "what are you", "your name", "what does jarvis stand for"]):
            return IntentResult("identity", 0.95, {}, raw, "witty")

        # Barge-in / Interruption (Section 6)
        if re.search(r"\b(?:wait|stop|pause|hold on|cancel speech|quiet|shh)\b", low):
            return IntentResult("barge_in", 0.98, {}, raw, "alert")

        # Autonomous Project Builder (Section 18)
        build_match = re.search(r"\b(?:build|create|code|develop|generate)\s+(?:me\s+)?(?:a\s+)?(.+?(?:game|app|calculator|project|script|program|dashboard|tool))", raw, re.IGNORECASE)
        if build_match:
            return IntentResult("build_project", 0.95, {"prompt": raw}, raw, "cinematic")

        # 10. Memory Recall (checked before Memory Store so "what do you remember" routes correctly)
        if re.search(r"\b(?:what is my name|what's my name|who am i|do you know my name)\b", low):
            return IntentResult("memory_recall", 0.98, {"query": "user_name"}, raw, "normal")

        recall_match = re.search(r"\b(?:what do you remember about|recall|what is my|do you remember|do you know my)\s+(.+)", raw, re.IGNORECASE)
        if recall_match:
            return IntentResult("memory_recall", 0.88, {"query": recall_match.group(1).strip().rstrip("?")}, raw, "normal")

        # 11. Memory Store
        if re.search(r"\b(?:call me|my name is)\s+([a-zA-Z0-9_\-]+)", raw, re.IGNORECASE):
            return IntentResult("memory_store", 0.95, {"data": raw}, raw, "normal")

        rem_match = re.search(r"\b(?:remember|save|note that|record that)\s+(?:that\s+)?(.+)", raw, re.IGNORECASE)
        if rem_match:
            return IntentResult("memory_store", 0.90, {"data": rem_match.group(1).strip()}, raw, "normal")

        # 12. Reminders & Scheduler
        if re.search(r"\b(?:remind me to|set a reminder|create reminder)\b", low):
            return IntentResult("reminder", 0.95, {}, raw, "normal")

        # 13. Morning / Daily Briefing
        if any(w in low for w in ["morning brief", "daily brief", "briefing", "give me the brief"]):
            return IntentResult("morning_briefing", 0.95, {}, raw, "cinematic")

        # 14. Web Search (Explicit + Natural Factual Questions - Section 3 & 10)
        search_match = re.search(r"\b(?:search(?: the web for| for)?|google|look up|find info on)\s+(.+)", raw, re.IGNORECASE)
        if search_match:
            return IntentResult("web_search", 0.90, {"query": search_match.group(1).strip()}, raw, "normal")

        factual_match = re.search(r"\b(?:tell me about|who is|explain|what(?:'s| is) happening in|how does)\s+(.+)", raw, re.IGNORECASE)
        if factual_match:
            return IntentResult("web_search", 0.92, {"query": factual_match.group(1).strip().rstrip("?")}, raw, "cinematic")

        what_is_match = re.search(r"^(?:what is|what's|what are)\s+([a-zA-Z0-9\s]{3,})\??$", raw, re.IGNORECASE)
        if what_is_match and not any(k in low for k in ["my name", "time", "date", "status", "weather", "today"]):
            return IntentResult("web_search", 0.90, {"query": what_is_match.group(1).strip()}, raw, "cinematic")

        # 10. System Control (Volume, Lock, Apps)
        if "volume up" in low or "louder" in low:
            return IntentResult("system_control", 0.92, {"action": "volume_up"}, raw, "normal")
        if "volume down" in low or "quieter" in low:
            return IntentResult("system_control", 0.92, {"action": "volume_down"}, raw, "normal")
        if "mute" in low:
            return IntentResult("system_control", 0.92, {"action": "mute"}, raw, "normal")
        if "lock" in low and ("pc" in low or "computer" in low or "system" in low or "screen" in low):
            return IntentResult("system_control", 0.95, {"action": "lock"}, raw, "alert")
        if "screenshot" in low or "capture screen" in low:
            return IntentResult("system_control", 0.92, {"action": "screenshot"}, raw, "normal")

        app_match = re.search(r"\b(?:open|launch|start)\s+([a-zA-Z0-9\s]+)", raw, re.IGNORECASE)
        if app_match and not any(k in low for k in ["file", "tab", "window"]):
            app_name = app_match.group(1).strip()
            return IntentResult("app_launch", 0.88, {"app": app_name}, raw, "cinematic")

        # 11. Repeat Last
        if any(w in low for w in ["repeat", "what did you say", "pardon", "say that again"]):
            return IntentResult("repeat", 0.95, {}, raw, "normal")

        # 12. Jokes / Banter / Wit
        if any(w in low for w in ["tell me a joke", "be funny", "make me laugh"]):
            return IntentResult("banter", 0.92, {"type": "joke"}, raw, "witty")
        if any(w in low for w in ["tea", "ambulance"]):
            return IntentResult("banter", 0.98, {"type": "tea_ambulance"}, raw, "witty")
        if any(w in low for w in ["thank you", "thanks", "good job", "well done"]):
            return IntentResult("banter", 0.92, {"type": "compliment"}, raw, "witty")

        # Fallback Unknown
        return IntentResult("unknown", 0.30, {}, raw, "normal")

    # ------------------------------------------------------------------
    # DISPATCH & EXECUTION
    # ------------------------------------------------------------------
    def process_query(self, query: str, audio_data: Optional[Any] = None) -> Tuple[str, str]:
        """
        Main cognitive pipeline:
        1. Parses intent.
        2. Dispatches to handler or skill.
        3. Analyzes emotional prosody & semantics.
        4. Dynamically shifts vocal tone & empathetic framing.
        5. Tracks flaws & latency for continuous self-improvement.
        6. Returns (response_text, suggested_voice_style).
        """
        t0 = time.time()
        intent_res = self.parse_intent(query)
        self.context.last_query = query
        self.context.last_intent = intent_res.intent
        self.context.last_parameters = intent_res.parameters
        self.context.turn_count += 1

        # Check registered skill handlers
        handler = self.skill_registry.get(intent_res.intent)
        exec_error = None
        try:
            if intent_res.intent == "barge_in":
                from core.voice_output import stop_speaking
                stop_speaking()
                response_text = "Certainly, Dev. Were you asking something, or shall I continue, sir?"
            elif handler:
                response_text = handler(intent_res)
            elif intent_res.intent == "shutdown":
                response_text = get_response("shutdown")
            elif intent_res.intent == "unknown":
                response_text = get_response("unknown")
            else:
                response_text = f"I have recognized the command for {intent_res.intent}, sir."
        except Exception as e:
            exec_error = str(e)
            response_text = f"An internal exception occurred in module {intent_res.intent}, sir: {e}"

        # Context-aware Initiative & Suggestions (Section 4)
        if intent_res.intent == "build_project" and not exec_error:
            response_text += " Shall I conduct unit diagnostics on the codebase or schedule a follow-up review for you, Dev?"

        # Log conversation turn in SQLite Relational Memory (Section 2)
        try:
            from core.sqlite_memory import get_sqlite_memory
            mem_db = get_sqlite_memory()
            mem_db.log_turn("user", query, intent=intent_res.intent, emotion=getattr(self.context, "user_emotion", "neutral"))
            mem_db.log_turn("assistant", response_text, intent=intent_res.intent, style=suggested_style)
        except Exception:
            pass

        # Affective Emotion Detection & Tonal Modulation
        suggested_style = intent_res.suggested_style
        try:
            from core.emotion_detector import get_emotion_detector
            emo = get_emotion_detector().detect_emotion(query, audio_data=audio_data)
            self.context.user_emotion = emo.primary_emotion

            if emo.primary_emotion in ["happy", "angry", "sad", "freaky"] and emo.confidence >= 0.40:
                suggested_style = emo.suggested_voice_style
                if intent_res.intent in ["greeting", "status", "banter", "unknown"] and emo.empathetic_note:
                    response_text = f"{emo.empathetic_note} {response_text}"
        except Exception:
            pass

        latency_ms = (time.time() - t0) * 1000.0

        # Self-improvement telemetry recording
        try:
            from core.self_improvement import get_flaw_detector
            get_flaw_detector().record_query_event(
                query=query,
                intent=intent_res.intent,
                confidence=intent_res.confidence,
                latency_ms=latency_ms,
                error=exec_error
            )
        except Exception:
            pass

        self.context.last_response = response_text
        return response_text, suggested_style

    # ------------------------------------------------------------------
    # BUILT-IN CORE HANDLERS
    # ------------------------------------------------------------------
    def _handle_emotion_check(self, res: IntentResult) -> str:
        from core.emotion_detector import get_emotion_detector
        emo = get_emotion_detector().detect_emotion(res.raw_query)
        note = f" {emo.empathetic_note}" if emo.empathetic_note else ""
        return (
            f"According to my acoustic and semantic analysis, Dev, your tone reflects a "
            f"predominantly {emo.primary_emotion} emotional state with {int(emo.confidence * 100)} percent "
            f"confidence, sir.{note}"
        ).strip()

    def _handle_congratulate(self, res: IntentResult) -> str:
        from skills.memory import get_memory
        mem = get_memory()
        msg = mem.get_last_event_and_congratulate()
        return msg or "Allow me to congratulate you, Dev. As always, a great pleasure watching you work, sir."
    def _handle_time(self, res: IntentResult) -> str:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        return get_response("time", time=current_time)

    def _handle_date(self, res: IntentResult) -> str:
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        return get_response("date", date=current_date)

    def _handle_greeting(self, res: IntentResult) -> str:
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            return get_response("greeting_morning")
        elif 12 <= hour < 17:
            return get_response("greeting_afternoon")
        else:
            return get_response("startup")

    def _handle_status(self, res: IntentResult) -> str:
        return get_response("system_status")

    def _handle_identity(self, res: IntentResult) -> str:
        return get_response("who_are_you")

    def _handle_mode_switch(self, res: IntentResult) -> str:
        mode = res.parameters.get("mode", "cinematic")
        config.DEFAULT_VOICE_STYLE = mode
        if mode == "cinematic":
            return "Cinematic mode engaged, sir. Fuller workshop resonance and deep acoustics active."
        elif mode == "night":
            return "Night mode active, sir. Output volume subdued and low-frequency resonance controlled."
        else:
            return "Normal mode active, sir. Standard natural profile restored."

    def _handle_calculation(self, res: IntentResult) -> str:
        expr = res.parameters.get("expression", "")
        # Safe math evaluation (numbers and basic arithmetic symbols only)
        if not re.match(r"^[0-9\.\s\+\-\*\/\(\)\%]+$", expr):
            return "I am afraid that mathematical expression contains invalid characters, sir."
        try:
            # Strictly evaluated in safe restricted namespace
            result = eval(expr, {"__builtins__": {}}, {})
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return get_response("calculation", result=str(result))
        except ZeroDivisionError:
            return "Division by zero is mathematically undefined, sir. Even for me."
        except Exception:
            return "I was unable to compute that expression accurately, sir."

    def _handle_banter(self, res: IntentResult) -> str:
        b_type = res.parameters.get("type", "joke")
        if b_type == "tea_ambulance":
            return "Would you care for some tea, sir, or should I simply call an ambulance?"
        elif b_type == "compliment":
            return get_response("compliment")
        else:
            return get_response("humour")

    def _handle_repeat(self, res: IntentResult) -> str:
        if self.context.last_response:
            return f"{get_response('repeat')} {self.context.last_response}"
        return "I have not spoken recently, sir."

