# J.A.R.V.I.S. V2 & Mark VII — Master Changelog & Evolution Ledger

## Mark VII Release (Current) — Complete Voice Pipeline & Holographic Iron Man HUD

### 1. Centralized Audio Input Architecture (`core/audio_manager.py`)
- **Single Continuous Microphone Stream:** Eliminated repeated audio stream destruction and recreation. A single background worker manages `sounddevice.RawInputStream` (16000 Hz, 16-bit PCM mono).
- **Acoustic State Machine:** Implemented robust state transitions (`STANDBY`, `WAKE_DETECTED`, `LISTENING`, `PROCESSING`, `SPEAKING`, `ERROR`).
- **Hands-Free Wake-Word Detection:** Continuous low-power listener recognizing "Jarvis" and "Hey Jarvis" with Vosk grammar constraints.
- **Voice Activity Detection (VAD):** Intelligent silence timeout (1.6s) and maximum recording ceiling (12s) protecting natural pauses from premature truncation.
- **Live RMS Level Broadcasting:** Computes audio amplitude at 60 FPS and broadcasts normalized volume to the HUD for real-time waveform visualization.
- **Barge-In Speech Interruption:** Active listening for "Stop", "Wait", and "Cancel" during speech output to halt TTS immediately.
- **Echo Suppression:** Prevents J.A.R.V.I.S. from transcribing his own TTS voice.
- **Hardware Disconnect Recovery:** Graceful reconnection and re-discovery if microphone drops or default device changes.

### 2. Transparent Iron Man Holographic HUD (`core/holographic_hud.py`)
- **Genuine Desktop Transparency:** Built with `Qt.WA_TranslucentBackground`, `Qt.FramelessWindowHint`, and `Qt.WindowStaysOnTopHint` — no rectangular black or white application window.
- **Compact Stark Arc Reactor (Default):** Floats at 220x220 px in the lower-right corner with 60 FPS concentric rotating graduation rings, 10 palladium coils, fine radial ticks, and pulsating palladium core.
- **Audio-Reactive Particle Dynamics:** Reactor energy ring and breathing core pulse dynamically in real-time response to microphone sound levels.
- **Expandable Holographic Tactical Panels:** Automatically unfolds during speech recognition and query execution, rendering translucent cyan glass telemetry cards, live speech transcription, and assistant replies.
- **Dynamic Cursor Avoidance:** Automatically deflects when mouse cursor approaches within 110 pixels in compact mode.

### 3. Security Remediation
- **Telegram Bot Token Redacted:** Erased hardcoded bot token from `README.md` and `skills/telegram_backup.py`. Isolated credentials to environment variables and `config_private.py`.

---

## Version 2.0.0 — Rebuild & Master Directive Execution

### Architectural Improvements & Core Additions
1. **Floating Desktop Companion (`core/floating_companion.py`):**
   - Implemented lightweight, frameless, transparent 92x92 desktop companion with 60 FPS animated Stark Arc Reactor.
   - Built smooth dynamic cursor avoidance that repels the companion when cursor approaches.
   - Added persistent coordinate storage in `memory/companion_position.json`.
   - Built full Windows System Tray integration with right-click tactical menu.
   - Wired single-click toggle to seamlessly open and minimize the full Holographic HUD window.

2. **Offline Conversational Chat Engine (`core/chat_engine.py`):**
   - Engineered authentic Paul Bettany dialogue model operating entirely offline without LLMs.
   - Added interactive riddle bank with progressive hints, answer matching, and context tracking.
   - Added philosophical and existential inquiry responses (simulation theory, consciousness, meaning of life).
   - Added emotional venting and fatigue support.
   - Added Stark lore and Iron Man armor archives.

3. **Broad Question Parsing & Research Fix:**
   - Expanded intent parser in `core/brain.py` to recognize all natural question forms: `who`, `what`, `where`, `when`, `why`, `how`, `which`, `can you tell me`, `is it raining`.
   - Added interrogative catch-all fallback ensuring natural inquiries trigger web research rather than falling through to "clarify sir".
   - Enhanced `skills/web_search.py` with intelligent query prefix stripping for direct Wikipedia entity hits and DuckDuckGo explanatory answers for "why" questions.

4. **Slang & Typo Normalization Engine:**
   - Added `normalize_query` in `core/brain.py` and `skills/system_control.py`.
   - Normalized elongated characters (`hyyy` -> `hey`, `bruuuhhhhh` -> `bro`).
   - Added fuzzy app name resolution (`utube` -> `youtube`, `clcltr` -> `calculator`, `crome` -> `chrome`).

5. **Voice Synthesis Acceleration:**
   - Converted Piper TTS from sentence-looping multiple subprocesses to single-pass whole-phrase synthesis.
   - Implemented asynchronous non-blocking playback in `core/voice_output.py`.
   - Created pre-warmed audio cache (`voice/cache/`) achieving 0.0004s instantaneous response times for frequent phrases.

6. **Defect Remediation (Audit Issues):**
   - **ISSUE-001:** Resolved `UnboundLocalError: suggested_style` in `core/brain.py:324`.
   - **ISSUE-002:** Broadened greeting regex patterns to catch informal variants.
   - **ISSUE-003:** Added volume adjustment commands (`volume up`, `volume down`, `mute`).
   - **ISSUE-004/015:** Rewrote app launcher with Windows registry lookup, known URLs, and URI schemes.
   - **ISSUE-006/007:** Added `subprocess.CREATE_NO_WINDOW` (0x08000000) flag across speech synthesis, screenshot capture, and process launches.
   - **ISSUE-014:** Bumped project version to `2.0.0` in `config.py`.

7. **Autonomous Services & Relational SQLite Memory:**
   - Implemented `core/sqlite_memory.py` with relational schema (`facts`, `conversation_turns`, `system_flaws`, `reminders`).
   - Integrated `skills/scheduler.py` for timed notifications and morning briefings.
   - Integrated `skills/weather.py` using `wttr.in` for live meteorological telemetry without API keys.
   - Integrated `skills/project_builder.py` for autonomous prompt-to-code generation in `workspace/`.
   - Built Saturday Telegram backup engine with multi-part zip splitting (<50MB).
