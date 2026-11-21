# J.A.R.V.I.S — Just A Rather Very Intelligent System

> *"Good morning, sir. All systems are online."*

A personal AI assistant inspired by Tony Stark's JARVIS from the Iron Man films.  
Built for Windows, optimised for 4 GB RAM, 100% offline-capable for core features.

---

## Project Structure

```
Jarvis/
├── core/
│   ├── responses.py       # Authentic JARVIS response library (1000+ lines)
│   ├── voice_input.py     # Speech recognition (Vosk — offline)
│   ├── voice_output.py    # Text-to-speech (pyttsx3 — Windows SAPI)
│   └── brain.py           # Core decision/routing logic
├── skills/
│   ├── web_search.py      # Web search + scraping
│   ├── system_control.py  # App launching, volume, screenshots
│   └── memory.py          # Persistent memory (JSON)
├── memory/
│   └── jarvis_memory.json # Stored facts and preferences
├── assets/
│   └── voice_model/       # Vosk speech model (download separately)
├── logs/
│   └── jarvis.log         # Runtime logs
├── tests/
│   └── test_imports.py    # Dependency verification
├── config.py              # Public configuration
├── config_private.py      # 🔒 Private credentials (NOT committed — .gitignored)
├── requirements.txt       # Python dependencies
├── main.py                # Entry point
└── README.md
```

---

## Phase 1 — Setup ✅
- [x] Python 3.14 confirmed
- [x] Virtual environment (`venv`) created
- [x] All core dependencies installed
- [x] Project structure created
- [x] Authentic response library built (1000+ authentic JARVIS lines)
- [x] Config with credential isolation
- [x] `.gitignore` protecting private data

## Phase 2 — Voice Pipeline & Audio Architecture ✅
- [x] Vishal Rao Piper JARVIS High model installed (`voice/models/jarvis/`)
- [x] 3-Layer Parallel Acoustic Engine (Core Voice + Warmth EQ Compression + Workshop Echo)
- [x] Sub-octave chest rumble bass synthesis
- [x] Multi-mode switching (Cinematic, Normal, Night)
- [x] Offline Speech Recognition with Vosk (`vosk-model-small-en-us-0.15`)
- [x] Zero-ducking bit-perfect hardware audio playback via `sounddevice`
- [x] Phase 2 verification suite passed (RAM footprint ~229 MB, well under 4 GB limit)

## Phase 3 — Cognitive Brain & Intent Routing ✅
- [x] Deterministic sub-millisecond intent classification engine (`core/brain.py`)
- [x] Parameter extraction (math expressions, voice modes, search queries, app targets)
- [x] Multi-turn conversation context tracking and repetition recall
- [x] Strict honesty enforcement (zero faked task completions)
- [x] Safe mathematical computation sandbox
- [x] Phase 3 verification suite passed (100% tests passed at ~0.18 ms latency)

## Phase 4 — Core Skills (Web Search, System Control & Persistent Memory) ✅
- [x] Persistent Memory engine (`skills/memory.py` saving to `memory/jarvis_memory.json`)
- [x] Windows System Control (`skills/system_control.py` — apps, volume, lock, native screenshot)
- [x] Offline-safe Web Search & Scraper (`skills/web_search.py` via DuckDuckGo HTML)
- [x] End-to-end Brain-to-Skill integration verified in `tests/test_skills.py`

## Phase 5 — Wake Word Detection Engine ✅
- [x] Vosk grammar-constrained acoustic listener for "Jarvis" (`core/wake_word.py`)
- [x] Ultra low CPU overhead (< 2% CPU, < 70 MB RAM)
- [x] Verified zero false positives with targeted grammar model

## Phase 6 — Scheduler, Reminders & Briefing ✅
- [x] Background reminder monitoring thread (`skills/scheduler.py` saving to `memory/reminders.json`)
- [x] Dynamic morning and evening intelligence briefings
- [x] Automatic spoken alerts upon scheduled task arrival

## Phase 7 — Hands-Free Autonomous Daemon & Stark HUD Telemetry ✅
- [x] Continuous hands-free loop (`core/hands_free_listener.py` with `python main.py --wake`)
- [x] Live environmental and meteorological intelligence (`skills/weather.py`)
- [x] Real-time Stark Industries hardware telemetry (`skills/system_diagnostics.py` — CPU, RAM, Disk, Battery, Uptime)
- [x] Multi-mode launcher in `main.py` (Console, Autonomous Wake, Status, Briefing)
- [x] Comprehensive test suite passed (`tests/test_phase7.py`)
- [x] Hardware speaker preview completed with Vishal Rao 3-Layer acoustic architecture

## Phase 8 — Autonomous Flaw Detection & Continuous Improvement ✅
- [x] Flaw detection monitor (`core/self_improvement.py`) tracking unhandled queries, latency spikes, and exceptions
- [x] Daily self-diagnostic audit saved to `memory/daily_flaws_and_improvements.txt`
- [x] User addressing updated: named as "Dev", addressed primarily as "sir"
- [x] Test suite passed (`tests/test_phase8.py`) with 0 errors
- [x] Hardware speaker preview delivered with Vishal Rao 3-Layer acoustic architecture

## Phase 9 — Vocal Emotion Detection & Adaptive Affective Modulation ✅
- [x] Affective emotion detection engine (`core/emotion_detector.py`) classifying happy, angry, sad, freaky, and neutral
- [x] Dynamic voice profile tuning (`soothing`, `composed`, `triage`, `witty`)
- [x] Empathetic dialogue framing and tonal matching in `core/brain.py`
- [x] Test suite passed (`tests/test_phase9.py`) with 0 errors
- [x] Hardware speaker preview delivered with Vishal Rao 3-Layer acoustic architecture

## Phase 10 — Stark Workshop Automation & Workflow Protocols ✅
- [x] Multi-action protocol execution engine (`skills/protocols.py`)
- [x] Built-in protocols: `workshop`, `cinema`, `lockdown`, `night_owl`
- [x] Custom user protocol persistence in `memory/protocols.json`
- [x] Sub-millisecond cognitive routing in `core/brain.py`
- [x] Comprehensive test suite passed (`tests/test_phase10.py`) with 0 errors
- [x] Hardware speaker preview delivered with Vishal Rao 3-Layer acoustic architecture

## Phase 11 — Real-Time Audio Visualizer & Holographic Arc Reactor HUD ✅
- [x] Terminal Stark Tactical HUD dashboard (`core/hud_terminal.py`) with CPU/RAM gauges and spectrum VU meter
- [x] Micro Web HUD server (`core/hud_server.py`) serving holographic 3D Arc Reactor and canvas waveform (`assets/hud/index.html`)
- [x] Real-time `/api/telemetry` polling with zero extra RAM overhead (< 15 MB)
- [x] Integrated into `main.py` with `python main.py --hud`
- [x] Comprehensive test suite passed (`tests/test_phase11.py`) with 0 errors
- [x] Hardware speaker preview delivered with Vishal Rao 3-Layer acoustic architecture

## Phase 12 — Telegram Cloud Backup, Saturday Automation & Windows Startup ✅
- [x] Project zip compilation and automatic chunking (`skills/telegram_backup.py`) under Telegram's 50 MB threshold
- [x] Direct dispatch to Telegram bot (`<CONFIGURED_IN_PRIVATE_CONFIG>`) to chat `6626316254`
- [x] Automatic Saturday scheduled backup engine (`check_and_run_saturday_backup`)
- [x] Daily startup check: if the prior Saturday backup was missed, runs immediately
- [x] Native Windows User Startup launcher installed (`LaunchJarvis.vbs`) for auto-boot with PC
- [x] All 30 unit tests verified with 0 errors across the repository

---

## Publishing to GitHub

To publish this project to GitHub without committing secrets or heavy binary weights:

### 1. Ensure Git is Installed
Download and install Git for Windows from: https://git-scm.com/download/win

### 2. Verify `.gitignore`
The included `.gitignore` already protects your private API keys (`config_private.py`), virtual environment (`venv/`), voice weights, logs, and temporary backup zips.

### 3. Initialize and Commit
Open PowerShell in the `Jarvis` directory:
```powershell
git init
git add .
git commit -m "feat: Initial release of J.A.R.V.I.S. Mark VII for Windows"
```

### 4. Link to GitHub Repository
Create a new repository named `Jarvis` on GitHub (https://github.com/new), then run:
```powershell
git branch -M main
git remote add origin https://github.com/<your-username>/Jarvis.git
git push -u origin main
```

---

## Setup Instructions

### 1. Activate the virtual environment
```powershell
# From the Jarvis project directory:
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies
```powershell
python -m pip install -r requirements.txt
```

### 3. Download the Vosk speech model
Download the small English model (40 MB — suitable for 4 GB RAM):
```
https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
```
Extract it into: `assets/voice_model/vosk-model-small-en-us-0.15/`

### 4. Configure private credentials (optional for Phase 1)
```powershell
# Create config_private.py (this file is .gitignored):
New-Item config_private.py
```
Add your API keys to that file — see the template in `config.py`.

### 5. Run JARVIS
```powershell
python main.py
```

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| vosk | 0.3.45 | Offline speech recognition |
| sounddevice | 0.5.6 | Microphone input |
| pyttsx3 | 2.99 | Text-to-speech (Windows SAPI) |
| requests | 2.34.2 | Web requests |
| beautifulsoup4 | 4.15.0 | HTML parsing |

---

## Voice Model

JARVIS uses the **Windows SAPI "David"** voice (built into Windows) via `pyttsx3`.  
No additional downloads required for TTS.

For speech recognition, download the Vosk small model (see setup above).

---

## Privacy & Security

- `config_private.py` is listed in `.gitignore` and **will never be committed**.
- API keys, tokens, and credentials live exclusively in `config_private.py`.
- The `venv/` directory is also excluded from Git.
- Logs are excluded from version control.

---

## Roadmap

- **Phase 1** — Setup, structure, response library ✅
- **Phase 2** — Voice input (Vosk) + 3-Layer Acoustic TTS (Piper Vishal Rao) ✅
- **Phase 3** — Command routing (brain.py) ✅
- **Phase 4** — Skills: web search, system control, memory ✅
- **Phase 5** — Wake word detection (`core/wake_word.py`) ✅
- **Phase 6** — Schedule, reminders, morning briefing ✅
- **Phase 7** — Autonomous hands-free daemon, weather & HUD telemetry ✅
- **Phase 8** — Autonomous flaw detection, self-improvement & custom addressing (Dev/sir) ✅
- **Phase 9** — Vocal emotion detection & adaptive affective modulation (happy, angry, sad, freaky) ✅
- **Phase 10** — Stark workshop automation & multi-action protocol engine (workshop, cinema, lockdown, night owl) ✅
- **Phase 11** — Real-time audio visualizer & holographic Arc Reactor HUD (`python main.py --hud`) ✅
- **Phase 12** — Telegram cloud backup, automatic Saturday synchronization & Windows auto-boot ✅

---

## Inspiration

> *"I am JARVIS, sir. Just A Rather Very Intelligent System."*

---

*Built for paneer. Runs on passion and 4 GB RAM.*

