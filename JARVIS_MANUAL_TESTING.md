# J.A.R.V.I.S. V2 — Interactive Acceptance & Manual Testing Guide

This guide allows paneer (Dev) to systematically verify every feature of J.A.R.V.I.S. V2.

---

## 1. Launching J.A.R.V.I.S.

You can launch J.A.R.V.I.S. in several ways depending on your preferred workflow:

### Mode A: Silent Desktop Companion (Zero CMD Window)
Double-click `run_jarvis_silent.vbs` or run in terminal:
```powershell
venv\Scripts\pythonw.exe main.py --companion
```
- A glowing Stark Arc Reactor companion widget will appear in the bottom-right corner of your screen.
- A matching icon will appear in your Windows System Tray (near the clock).
- Move your mouse towards the companion widget: it will gently glide away (cursor avoidance).
- Click on the companion icon: the full Holographic Tactical HUD Window will smoothly open.
- Click the close button (X) on the HUD: it minimizes back into the floating companion without exiting.

### Mode B: Full Tactical HUD Desktop Window
Run:
```powershell
venv\Scripts\python.exe main.py
```
- Launches both the floating Arc Reactor companion and the Holographic HUD with particle physics, memory manager, and real-time hardware telemetry.

### Mode C: Terminal Interactive Mode
Run:
```powershell
venv\Scripts\python.exe main.py --cli
```
- Interactive console with Stark dashboard for quick keyboard testing.

---

## 2. Interactive Acceptance Test Scenarios

### Test 1: Slang & Elongated Words
Type or speak the following phrases:
1. `hyyy` -> J.A.R.V.I.S. responds with Stark morning/afternoon greeting.
2. `bruuuhhhhh what time is it` -> J.A.R.V.I.S. reports the exact local time.
3. `yo jarvis open utube` -> J.A.R.V.I.S. opens YouTube in your browser.
4. `open clcltr` -> J.A.R.V.I.S. launches Windows Calculator.

### Test 2: Natural Questions & Web Research (Zero "Clarify Sir")
Ask any of the following questions:
1. `Why is the sky blue?` -> Retrieves atmospheric Rayleigh scattering explanation.
2. `Who was Albert Einstein?` -> Retrieves historical biography of Einstein from Wikipedia.
3. `Where is Paris?` -> Reports Paris as the capital of France.
4. `When did World War 2 end?` -> Reports September 1945 treaty dates.
5. `How does an engine work?` -> Explains internal combustion principles.
6. `Is it raining outside?` -> Fetches real-time weather telemetry for your local area.

### Test 3: Conversational Companionship & Boredom
1. `I'm bored` -> J.A.R.V.I.S. suggests workshops, projects, riddles, or science topics.
2. `Tell me a riddle` -> J.A.R.V.I.S. poses an interactive riddle.
3. Try answering the riddle (e.g. `is it an echo?` or `hint please`).
4. `What is the meaning of life?` -> J.A.R.V.I.S. shares philosophical reflection.
5. `I'm tired` -> J.A.R.V.I.S. offers advice on rest and recharge cycles.

### Test 4: Persistent Relational Memory
1. Say: `Remember that my favorite project is Iron Man Mark VII`
2. Say: `What do you remember about my favorite project?`
3. J.A.R.V.I.S. recalls the fact from SQLite memory.
4. Say: `Remember that my favorite project is Mark VIII`
5. J.A.R.V.I.S. detects the conflict, logs the change, and updates the record.

### Test 5: System Controls & Hardware Telemetry
1. `Volume up` / `Volume down` / `Mute`
2. `Take a screenshot` -> Captures desktop screenshot to `logs/screenshots/`.
3. `System diagnostics` or `Telemetry` -> Reports CPU load, RAM usage, and uptime.

### Test 6: Autonomous Project Builder
1. `Build me a 2D racing game in Python`
2. J.A.R.V.I.S. creates a playable Pygame racing script in `workspace/`.
