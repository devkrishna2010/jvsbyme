# J.A.R.V.I.S. V2 — Master Architectural Specification

## Executive Overview
**J.A.R.V.I.S. (Just A Rather Very Intelligent System) Version 2.0.0** is an offline-first, lightweight, highly responsive personal assistant and PC tactical interface engineered specifically for Windows 11.

It adheres strictly to the **Zero-Cloud-AI / Zero-Local-LLM** mandate: all cognition, natural language routing, emotional prosody detection, conversational companionship, PC automation, and project building operate through deterministic, lightweight, low-resource Python 3.14 algorithms, SQLite relational storage, and open-source offline models.

---

## High-Level System Architecture

```
                    +-------------------------------------------------------+
                    |                   USER INTERFACES                     |
                    |  • Floating Arc-Reactor Companion (core/floating_...) |
                    |  • Holographic Tactical HUD Window (core/desktop_gui) |
                    |  • Windows System Tray & Notifications                |
                    |  • Terminal HUD Dashboard (core/hud_terminal)        |
                    +-------------------------------------------------------+
                                                |
                                                v
                    +-------------------------------------------------------+
                    |           ACOUSTIC & COGNITIVE INTAKE PIPELINE        |
                    |  • Vosk Offline STT (voice/speech_to_text)           |
                    |  • Slang & Typo Normalizer (core/brain.py)           |
                    |  • Deterministic Intent Router (core/brain.py)        |
                    |  • Emotional Prosody Detector (core/emotion_detector) |
                    +-------------------------------------------------------+
                                                |
                     +--------------------------+--------------------------+
                     |                          |                          |
                     v                          v                          v
+-------------------------------+ +----------------------------+ +-------------------------------+
|     AUTOMATION & SYSTEM       | |    INTELLIGENCE & CHAT     | |     MEMORY & TELEMETRY        |
| • App Launcher & URL Engine   | | • Offline Chat Engine      | | • SQLite Relational DB        |
| • Sound & Volume Master       | |   (Boredom, Riddles, Lore) | |   (memory/jarvis_memory.db)   |
| • Screenshot & Lock Subsystem | | • Extractive Web Research  | | • Hardware Telemetry Engine   |
| • Stark Automated Protocols   | |   (Wikipedia + DDG Lite)   | |   (CPU, RAM, Disk, Uptime)    |
| • Autonomous Project Builder  | | • Meteorological Sensors   | | • Scheduler & Reminders       |
|   (workspace/ generation)     | |   (wttr.in Weather Engine) | | • Self-Improvement Flaw Log   |
+-------------------------------+ +----------------------------+ +-------------------------------+
                                                |
                                                v
                    +-------------------------------------------------------+
                    |             ACOUSTIC SYNTHESIS PIPELINE               |
                    |  • Single-Pass Piper TTS (voice/text_to_speech)      |
                    |  • Pre-Warmed Microsecond Audio Cache (voice/cache)   |
                    |  • Non-Blocking Asynchronous Audio Thread             |
                    |  • Barge-In Immediate Interruption Controller         |
                    +-------------------------------------------------------+
```

---

## Core Components & Module Index

### 1. Cognitive Brain & Intent Dispatch (`core/brain.py`)
- **Intent Parsing:** Multi-stage hierarchical matching engine. Evaluates greetings, mode changes, Stark protocols, volume/system controls, autonomous project building, memory operations, conversational chat, weather sensors, and natural question research.
- **Typo & Slang Normalization:** `normalize_query` handles elongated characters (`hyyy` -> `hey`, `bruuuhhhhh` -> `bro`), common acronyms (`utube` -> `youtube`, `clcltr` -> `calculator`), and punctuation stripping.
- **Interrogative Catch-All:** Routes natural language inquiries (`who`, `what`, `where`, `when`, `why`, `how`, `which`) to extractive search rather than returning unknown errors.

### 2. Conversational Chat Engine (`core/chat_engine.py`)
- Provides authentic, offline companionship voiced in Paul Bettany's British cadence.
- Interactive riddles with hint systems and state tracking.
- Philosophical reflections on consciousness, simulation theory, and human nature.
- Stark Industries lore and Iron Man armor archives.
- Emotional comfort and decompression dialogue for stress and fatigue.

### 3. Floating Arc Reactor Companion (`core/floating_companion.py`)
- 92x92 transparent frameless widget with 60 FPS animated Arc Reactor.
- Draggable across multi-monitor displays with coordinate persistence (`memory/companion_position.json`).
- Smooth dynamic cursor avoidance to prevent obstructing the user's workspace.
- Left-click toggles full Holographic HUD; right-click opens system tactical menu.
- System tray icon with notifications and quick actions.

### 4. Holographic Tactical HUD Window (`core/desktop_gui.py`)
- Native Windows Desktop application built in PyQt5 with custom Stark dark glass stylesheet.
- Central 60 FPS liquid particle core reacting dynamically to speech amplitude.
- Real-time hardware telemetry display (CPU load, RAM consumption, free disk space, system uptime).
- Memory Bank visual browser and editor (search, add, delete persistent facts).
- Scheduler and active reminders manager.

### 5. Extractive Web Research Engine (`skills/web_search.py`)
- Multi-source extractive factual research without paid APIs or external LLMs.
- Queries Wikipedia REST API summary endpoint for encyclopedic topics with automatic question prefix stripping.
- Scrapes DuckDuckGo HTML Lite for explanatory inquiries ("why is the sky blue", current affairs).
- Zero tracking, clean text extraction.

### 6. Acoustic Engine & Piper TTS (`voice/text_to_speech.py` & `core/voice_output.py`)
- High-fidelity offline speech synthesis using `voice/models/jarvis/en_GB-jarvis-high.onnx`.
- Accelerated single-pass synthesis eliminating multi-subprocess invocation latency.
- Microsecond pre-warmed audio cache (`voice/cache/`) for top frequent assistant lines.
- Asynchronous non-blocking playback thread allowing UI and cognition to respond instantly.
- Immediate barge-in audio interruption support.

### 7. Relational SQLite Memory Bank (`core/sqlite_memory.py`)
- ACID-compliant transactional persistence in `memory/jarvis_memory.db`.
- Automatic table schema initialization (`facts`, `conversation_turns`, `system_flaws`, `reminders`).
- Conflict detection and audit trail on updated memory facts.

### 8. Autonomous Project Builder (`skills/project_builder.py`)
- Generates working Python applications in `workspace/` from natural language prompts.
- Built-in templates: 2D Arcade Games, Tactical Calculators, Automation Utilities.
- Compiles abstract syntax tree (AST) to verify code validity before disk deployment.

### 9. Autonomous Maintenance & Telegram Backup (`skills/telegram_backup.py` & `core/self_improvement.py`)
- Scheduled Saturday backup compressing project repository into multi-part zip archives (<50MB).
- Uploads directly to Telegram Chat ID `6626316254` using Bot API.
- Continuous flaw detection logging operational latencies, missed intents, and proposed architectural upgrades to `memory/daily_flaws_and_improvements.txt`.
