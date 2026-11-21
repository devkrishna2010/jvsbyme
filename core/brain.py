"""
J.A.R.V.I.S. — Core Brain & Intent Routing Engine
=================================================
Parses user queries into structured intents, extracts parameters,
manages conversation context, and dispatches to appropriate skills.

Guiding Principles:
1. Absolute Integrity: Never pretends a task is complete when it hasn't succeeded.
2. Character Fidelity: Formal British cadence, confident wit, composed elegance.
3. Lightweight & Fast: Sub-millisecond rule & pattern routing, zero local LLM overhead.

V2 Repairs (Phase 2):
- ISSUE-001: suggested_style moved before SQLite log — no more UnboundLocalError.
- ISSUE-002: Greeting regex expanded — heyy, hi there, yo, howdy all recognized.
- ISSUE-003: Volume patterns broadened — increase/raise/lower/decrease volume work.
- ISSUE-005: Added capabilities intent, how_are_you intent, broader compliment patterns.
"""

import re
import time
import datetime
import difflib
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Callable

from core.responses import get_response
import config

# Slang, typo, and phonetic mapping to canonical keywords
SLANG_TYPO_MAP: Dict[str, str] = {
    # Greetings & Addresses
    "hy": "hey", "hyy": "hey", "he": "hey", "hii": "hi", "hiii": "hi", "heya": "hey", "hye": "hey",
    "bruh": "bro", "bruhh": "bro", "brah": "bro", "broda": "bro", "bhai": "bro", "dude": "bro",
    # Question words & Pronouns
    "wat": "what", "wht": "what", "wt": "what", "wats": "what is", "whats": "what is", "wts": "what is",
    "hw": "how", "hwo": "how", "hws": "how is", "whr": "where", "wen": "when",
    "u": "you", "ya": "you", "ur": "your", "urs": "yours", "r": "are",
    # Courtesies & banters
    "plz": "please", "pls": "please", "plez": "please",
    "thx": "thanks", "thnx": "thanks", "thanx": "thanks", "ty": "thank you", "tysm": "thank you so much",
    "sry": "sorry", "k": "ok", "kk": "ok",
    # Actions & Verbs
    "opn": "open", "opnd": "open", "lnch": "launch", "strt": "start",
    "sho": "show", "shw": "show", "tl": "tell", "tll": "tell",
    "remnd": "remind", "rmnd": "remind",
    "clc": "calculator", "cal": "calculator", "calclatr": "calculator", "calculater": "calculator",
    # Media & Apps
    "yt": "youtube", "utube": "youtube", "youtub": "youtube",
    "gogl": "google", "googl": "google", "goggl": "google",
    "spotfy": "spotify", "spotif": "spotify",
    "dscrd": "discord", "discor": "discord",
    "tg": "telegram", "telegrm": "telegram",
    "watsapp": "whatsapp", "wapp": "whatsapp",
    "notepd": "notepad",
    # System Controls
    "vol": "volume", "volum": "volume", "vlm": "volume", "vlume": "volume",
    "inc": "increase", "incres": "increase", "increse": "increase",
    "dec": "decrease", "decres": "decrease", "decrese": "decrease",
    "mut": "mute", "scrn": "screen", "scrnshot": "screenshot", "ss": "screenshot",
    # Topics & Telemetry
    "wether": "weather", "weathr": "weather", "temprature": "temperature", "temp": "temperature",
    "tme": "time", "dte": "date", "stts": "status", "stat": "status", "diag": "diagnostics",
    "tday": "today", "2day": "today", "tmrw": "tomorrow", "2mrw": "tomorrow",
}

CANONICAL_KEYWORDS: List[str] = [
    "calculator", "youtube", "chrome", "spotify", "notepad", "discord", "telegram",
    "weather", "temperature", "diagnostics", "status", "telemetry", "volume",
    "screenshot", "computer", "shutdown", "briefing", "reminder", "calculate",
    "increase", "decrease", "louder", "quieter", "silence", "protocol"
]


def normalize_query(text: str) -> str:
    """
    Normalizes typos, elongated character spam (e.g. hyyy -> hey, bruuuhhhhh -> bro),
    and common colloquial slang expressions.
    """
    raw = text.strip()
    low = raw.lower().strip()
    low = re.sub(r"[!?.,;:]+$", "", low).strip()
    # Collapse 3 or more repeated letters to 1 (e.g. hyyy -> hy, bruuuhhhhh -> bruh, heyyyy -> hey)
    low = re.sub(r"([a-zA-Z])\1{2,}", r"\1", low)
    words = low.split()
    norm_words = []
    for w in words:
        if w in SLANG_TYPO_MAP:
            norm_words.append(SLANG_TYPO_MAP[w])
        else:
            if len(w) >= 4:
                matches = difflib.get_close_matches(w, CANONICAL_KEYWORDS, n=1, cutoff=0.74)
                if matches:
                    norm_words.append(matches[0])
                    continue
            norm_words.append(w)
    return " ".join(norm_words)


def is_pure_greeting(norm: str) -> bool:
    """Checks if the query consists purely of greeting words and informal address tokens."""
    words = norm.split()
    salutations = {
        "hey", "hi", "hello", "hiya", "howdy", "yo", "sup", "bro", "jarvis",
        "there", "good", "morning", "afternoon", "evening", "day", "wassup",
        "buddy", "man"
    }
    return len(words) > 0 and all(w in salutations for w in words)


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
        self.skill_registry["how_are_you"] = self._handle_how_are_you
        self.skill_registry["capabilities"] = self._handle_capabilities
        self.skill_registry["status"] = self._handle_status
        self.skill_registry["identity"] = self._handle_identity
        self.skill_registry["mode_switch"] = self._handle_mode_switch
        self.skill_registry["calculation"] = self._handle_calculation
        self.skill_registry["banter"] = self._handle_banter
        self.skill_registry["repeat"] = self._handle_repeat
        self.skill_registry["emotion_check"] = self._handle_emotion_check
        self.skill_registry["congratulate"] = self._handle_congratulate
        self.skill_registry["chat"] = self._handle_chat

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
        except ImportError:
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
        Normalizes slang, typos, and elongated characters before routing.
        """
        raw = text.strip()
        norm = normalize_query(raw)

        # 1. Pure greetings (e.g. 'hyyy', 'bruuuhhhhh', 'hey bro', 'yo jarvis')
        if is_pure_greeting(norm):
            return IntentResult("greeting", 0.92, {}, raw, "cinematic")

        # 2. Check for leading salutations and strip to reveal actionable commands
        # e.g. "bruuuhhhhh open clcltr" -> "open calculator"
        stripped = re.sub(r"^(?:hey|hi|hello|hiya|howdy|yo|sup|bro|jarvis|please|pls|sir)\s+", "", norm).strip()
        if stripped and stripped != norm:
            res = self._match_intent_patterns(stripped, raw)
            if res.intent != "unknown":
                return res

        # 3. Standard intent matching on normalized query
        return self._match_intent_patterns(norm, raw)

    def _match_intent_patterns(self, low: str, raw: str) -> IntentResult:
        """Core deterministic pattern matching on normalized input."""

        # 1. Mode Switching
        if any(w in low for w in ["cinematic mode", "cinema mode"]):
            return IntentResult("mode_switch", 0.98, {"mode": "cinematic"}, raw, "cinematic")
        if any(w in low for w in ["normal mode", "standard mode"]):
            return IntentResult("mode_switch", 0.98, {"mode": "normal"}, raw, "normal")
        if any(w in low for w in ["night mode", "quiet mode", "sleep mode"]):
            return IntentResult("mode_switch", 0.98, {"mode": "night"}, raw, "night")

        # Protocols (Stark Automated Routines) — before generic "focus mode" to avoid eating it
        if "protocol" in low or any(w in low for w in ["coding mode", "movie mode", "lockdown"]):
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
            elif "coding" in low:
                target = "workshop"
            return IntentResult("protocol", 0.95, {"protocol": target}, raw, "cinematic")

        # Focus mode on/off — explicit, before generic protocol sweep
        if re.search(r"\bfocus\s+mode\s+off\b|\bdisable\s+focus\b|\bfocus\s+off\b", low):
            return IntentResult("mode_switch", 0.96, {"mode": "normal"}, raw, "normal")
        if re.search(r"\bfocus\s+mode\b|\bfocus\s+on\b|\benable\s+focus\b", low):
            return IntentResult("protocol", 0.95, {"protocol": "workshop"}, raw, "cinematic")

        # 2. Shutdown / Standby
        if any(w in low for w in ["shutdown", "shut down", "power down", "good night jarvis", "exit jarvis", "quit jarvis", "go to sleep jarvis"]):
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

        # 5. Greetings — broad, handles typos (heyy, heyyy), variants (hi there, yo, howdy)
        if re.search(r"^(hey+|hello+|hi+|hiya|howdy|yo|sup|greetings|wassup|what('?s)?\s+up)\b", low):
            return IntentResult("greeting", 0.90, {}, raw, "cinematic")
        if re.search(r"^(good\s+(morning|afternoon|evening|day))\b", low):
            return IntentResult("greeting", 0.92, {}, raw, "cinematic")
        if re.search(r"^(hey|hi|hello|howdy)\s+(jarvis|there|man|bro|buddy)\b", low):
            return IntentResult("greeting", 0.92, {}, raw, "cinematic")

        # 6. How are you — separate from system status
        if re.search(r"\b(how are you|how('?s| is) it going|how are you doing|are you (okay|ok|fine|good)|you (good|okay|ok|doing well))\b", low):
            return IntentResult("how_are_you", 0.92, {}, raw, "witty")

        # 7. Capabilities / Help
        if re.search(r"\b(what can you do|what are your (capabilities|skills|features|commands)|help me|show me (what you can|your commands)|what (commands|functions) do you (have|know)|what do you (do|know))\b", low):
            return IntentResult("capabilities", 0.95, {}, raw, "cinematic")
        if low.strip() in ["help", "commands", "features", "capabilities"]:
            return IntentResult("capabilities", 0.95, {}, raw, "cinematic")

        # 8. Weather & Environmental Sensors
        if re.search(r"\b(weather|temperature|forecast|climate|how('s| is) it outside|outside temp|raining|rain outside|is it raining|will it rain|snowing|umbrella|sunny outside)\b", low):
            loc_match = re.search(r"\b(?:in|for|at)\s+([a-zA-Z\s]+)", raw, re.IGNORECASE)
            loc = loc_match.group(1).strip() if loc_match else None
            return IntentResult("weather", 0.94, {"location": loc}, raw, "cinematic")

        # 9. Status & Telemetry
        if any(w in low for w in ["detect flaw", "flaw", "flaws", "what should we improve", "what to improve", "self reflection", "self diagnostic audit", "system improvements"]):
            return IntentResult("flaws_audit", 0.95, {}, raw, "cinematic")

        if any(w in low for w in ["check status", "all green", "systems check"]) or low.strip() == "status":
            return IntentResult("status", 0.92, {}, raw, "cinematic")

        if any(w in low for w in ["telemetry", "hardware", "cpu", "ram", "battery", "diagnostic"]):
            return IntentResult("diagnostics", 0.95, {}, raw, "cinematic")

        if "status" in low:
            return IntentResult("status", 0.92, {}, raw, "cinematic")

        # 10. Emotion & Mood Inquiries
        if re.search(r"\b(how do i sound|what is my mood|detect my emotion|check my tone|what tone do you detect|am i happy|am i angry|am i sad)\b", low):
            return IntentResult("emotion_check", 0.95, {}, raw, "witty")

        # 11. Milestone Congratulation & Achievements
        if any(w in low for w in ["congratulate me", "what did i achieve", "celebrate milestone", "what did we accomplish", "last event", "congratulate"]):
            return IntentResult("congratulate", 0.95, {}, raw, "witty")

        # 12. Telegram Project Backup
        if any(w in low for w in ["backup to telegram", "telegram backup", "backup now", "send backup"]):
            return IntentResult("telegram_backup", 0.95, {}, raw, "cinematic")

        # 13. Identity
        if re.search(r"^(?:who are you|what are you|what is your name|your name|what does jarvis stand for)\s*(?:jarvis)?\??$", low):
            return IntentResult("identity", 0.95, {}, raw, "witty")

        # Barge-in / Interruption (Section 6)
        if re.search(r"\b(?:wait|stop|pause|hold on|cancel speech|quiet|shh)\b", low):
            return IntentResult("barge_in", 0.98, {}, raw, "alert")

        # Autonomous Project Builder (Section 18)
        build_match = re.search(r"\b(?:build|create|code|develop|generate)\s+(?:me\s+)?(?:a\s+)?(.+?(?:game|app|calculator|project|script|program|dashboard|tool))", raw, re.IGNORECASE)
        if build_match:
            return IntentResult("build_project", 0.95, {"prompt": raw}, raw, "cinematic")

        # 14. Memory Recall
        if re.search(r"\b(?:what is my name|what's my name|who am i|do you know my name)\b", low):
            return IntentResult("memory_recall", 0.98, {"query": "user_name"}, raw, "normal")

        recall_match = re.search(r"\b(?:what do you remember about|recall|what is my|do you remember|do you know my)\s+(.+)", raw, re.IGNORECASE)
        if recall_match:
            return IntentResult("memory_recall", 0.88, {"query": recall_match.group(1).strip().rstrip("?")}, raw, "normal")

        # 15. Memory Store
        if re.search(r"\b(?:call me|my name is)\s+([a-zA-Z0-9_\-]+)", raw, re.IGNORECASE):
            return IntentResult("memory_store", 0.95, {"data": raw}, raw, "normal")

        rem_match = re.search(r"\b(?:remember|save|note that|record that)\s+(?:that\s+)?(.+)", raw, re.IGNORECASE)
        if rem_match:
            return IntentResult("memory_store", 0.90, {"data": rem_match.group(1).strip()}, raw, "normal")

        # 16. Reminders & Scheduler
        if re.search(r"\b(?:remind me to|set a reminder|create reminder)\b", low):
            return IntentResult("reminder", 0.95, {}, raw, "normal")

        # 17. Morning / Daily Briefing
        if any(w in low for w in ["morning brief", "daily brief", "briefing", "give me the brief"]):
            return IntentResult("morning_briefing", 0.95, {}, raw, "cinematic")

        # 18. Conversational Chat Engine (Boredom, Philosophy, Companionship, Lore, Trivia)
        try:
            from core.chat_engine import get_chat_engine
            chat_match = get_chat_engine().handle_conversational_query(raw, self.context)
            if not chat_match and low != raw.lower():
                chat_match = get_chat_engine().handle_conversational_query(low, self.context)
            if chat_match:
                chat_text, chat_style = chat_match
                return IntentResult("chat", 0.95, {"response": chat_text, "style": chat_style}, raw, chat_style)
        except Exception:
            pass

        # 19. Web Search (Explicit + Natural Factual Questions)
        search_match = re.search(
            r"\b(?:search(?: the web for| for)?|google|look up|find info on|find information on|browse for)\s+(.+)",
            raw, re.IGNORECASE
        )
        if search_match:
            return IntentResult("web_search", 0.90, {"query": search_match.group(1).strip()}, raw, "normal")

        factual_match = re.search(
            r"\b(?:tell me about|who (?:is|was|were|are|created|built|invented|discovered|wrote)|"
            r"explain|what(?:'s| is| was| were| are) happening in|"
            r"why (?:is|was|were|are|do|does|did)|"
            r"when (?:is|was|were|did|will)|"
            r"where (?:is|was|were|are|can i find)|"
            r"which (?:is|are|was|were|country|city|state|animal|planet|car)|"
            r"how (?:does|do|did|is|was|are|can|many|much|far|old|tall|long))\s+(.+)",
            raw, re.IGNORECASE
        )
        if factual_match and not any(k in low for k in ["how are you", "how's it going", "what is my name", "what time", "what date"]):
            return IntentResult("web_search", 0.92, {"query": raw.rstrip("?")}, raw, "cinematic")

        what_is_match = re.search(r"^(?:what is|what's|what was|what are|what were)\s+([a-zA-Z0-9\s]{3,})\??$", raw, re.IGNORECASE)
        if what_is_match and not any(k in low for k in ["my name", "time", "date", "status", "weather", "today"]):
            return IntentResult("web_search", 0.90, {"query": what_is_match.group(1).strip()}, raw, "cinematic")

        # 19. System Control — Volume (broadened patterns)
        if re.search(r"\b(increase|raise|turn up|boost|crank up)\b.*\bvolume\b|\bvolume\s+up\b|\blouder\b|\bturn it up\b", low):
            return IntentResult("system_control", 0.92, {"action": "volume_up"}, raw, "normal")
        if re.search(r"\b(decrease|lower|reduce|turn down|drop)\b.*\bvolume\b|\bvolume\s+down\b|\bquieter\b|\bturn it down\b", low):
            return IntentResult("system_control", 0.92, {"action": "volume_down"}, raw, "normal")
        if re.search(r"\b(mute|silence|shut up|no sound)\b", low):
            return IntentResult("system_control", 0.92, {"action": "mute"}, raw, "normal")
        if re.search(r"\b(unmute|restore sound|sound on|audio on)\b", low):
            return IntentResult("system_control", 0.92, {"action": "mute"}, raw, "normal")  # toggle
        if "lock" in low and re.search(r"\b(pc|computer|system|screen|workstation|machine)\b", low):
            return IntentResult("system_control", 0.95, {"action": "lock"}, raw, "alert")
        if "screenshot" in low or "capture screen" in low or "take a screenshot" in low or "grab screen" in low:
            return IntentResult("system_control", 0.92, {"action": "screenshot"}, raw, "normal")

        # 20. Application Launch — after volume/lock to avoid conflicts
        app_match = re.search(r"\b(?:open|launch|start|run|load)\s+([a-zA-Z0-9][a-zA-Z0-9\s]{1,30})", low, re.IGNORECASE)
        if app_match:
            app_candidate = app_match.group(1).strip()
            # Exclude vague words that shouldn't map to apps
            if not re.match(r"^(a |an |the |my |this |that |up|down|more|less)$", app_candidate, re.I):
                return IntentResult("app_launch", 0.88, {"app": app_candidate}, raw, "cinematic")

        # 21. Repeat Last
        if any(w in low for w in ["repeat", "what did you say", "pardon", "say that again", "say it again"]):
            return IntentResult("repeat", 0.95, {}, raw, "normal")

        # 22. Jokes / Banter / Wit
        if any(w in low for w in ["tell me a joke", "be funny", "make me laugh", "say something funny", "joke"]):
            return IntentResult("banter", 0.92, {"type": "joke"}, raw, "witty")
        if any(w in low for w in ["tea", "ambulance"]):
            return IntentResult("banter", 0.98, {"type": "tea_ambulance"}, raw, "witty")
        # Compliments / gratitude — broadened
        if re.search(r"\b(thank you|thanks|good (job|work|one)|well done|great (job|work)|nice (work|job|one)|brilliant|amazing|awesome|perfect|excellent)\b", low):
            return IntentResult("banter", 0.92, {"type": "compliment"}, raw, "witty")

        # 23. General Interrogative Fallback -> Web Search
        # Any question or query that wasn't claimed by earlier skills should be researched
        # rather than rejected with "Could you clarify, sir?"
        if (
            re.search(r"^(?:who|what|where|when|why|how|which|can you tell me|do you know|is it|are there|does|did|will|would|can)\b", low)
            or raw.endswith("?")
        ):
            words = low.split()
            if len(words) >= 3 and not any(w in low for w in ["open", "launch", "volume", "shutdown", "exit", "focus", "protocol"]):
                return IntentResult("web_search", 0.85, {"query": raw.rstrip("?")}, raw, "cinematic")

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

        # FIX ISSUE-001: suggested_style must be assigned BEFORE the SQLite log that uses it
        suggested_style = intent_res.suggested_style

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
                from core.chat_engine import get_chat_engine
                chat_match = get_chat_engine().handle_conversational_query(query, self.context)
                if chat_match:
                    response_text, suggested_style = chat_match
                else:
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
            return get_response("greeting_evening")

    def _handle_how_are_you(self, res: IntentResult) -> str:
        return get_response("how_are_you")

    def _handle_capabilities(self, res: IntentResult) -> str:
        return (
            "I am capable of quite a broad range of tasks, sir. Here is a summary: "
            "Voice and text commands; opening any application or website; web research on any topic; "
            "setting reminders and delivering briefings; system controls including volume, screenshots, and PC lock; "
            "persistent memory for facts and preferences; weather reports; autonomous project building; "
            "self-diagnostic audits; and automated backups to Telegram. "
            "Simply ask, and I shall do my best, sir."
        )

    def _handle_chat(self, res: IntentResult) -> str:
        return res.parameters.get("response", "I am here, sir. At your disposal.")

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
