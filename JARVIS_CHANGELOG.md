# J.A.R.V.I.S. V2 — Master Changelog & Evolution Ledger

## Version 2.0.0 (Current Release) — Complete Rebuild & Master Directive Execution

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
