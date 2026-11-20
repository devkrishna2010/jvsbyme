# J.A.R.V.I.S. — Phase 0 Complete Project Audit
**Generated:** 2026-11-20 | **Baseline Commit:** `2061c2a`
**Auditor:** spinach | **Status:** 41/41 tests passing at audit time

---

## Summary

| Category | Count |
|---|---|
| CRITICAL bugs | 1 |
| HIGH severity | 4 |
| MODERATE severity | 5 |
| LOW severity | 5 |
| INFO / style | 3 |

---

## Module Dependency Map

```
main.py
├── config.py
├── core/brain.py
│   ├── core/responses.py
│   ├── skills/memory.py          → memory/jarvis_memory.json
│   ├── skills/web_search.py      → requests, bs4
│   ├── skills/system_control.py  → ctypes, subprocess
│   ├── skills/scheduler.py       → core/voice_output.py
│   ├── skills/weather.py         → requests
│   ├── skills/system_diagnostics.py → psutil
│   ├── core/self_improvement.py  → memory/daily_flaws_and_improvements.txt
│   ├── skills/protocols.py
│   ├── skills/telegram_backup.py
│   ├── skills/project_builder.py
│   ├── skills/google_suite.py
│   └── core/emotion_detector.py
│       └── core/sqlite_memory.py → memory/jarvis_memory.db
├── core/voice_output.py
│   └── voice/text_to_speech.py
│       ├── voice/voice_profiles.py
│       ├── voice/speech_director.py
│       ├── voice/audio_processor.py
│       └── voice/audio_cache.py
├── core/voice_input.py           → vosk, sounddevice
├── core/hands_free_listener.py   → core/wake_word.py
├── core/hud_terminal.py
├── core/desktop_gui.py           → PyQt5 (all above)
├── skills/scheduler.py
└── skills/system_diagnostics.py
```

---

## Issue Registry

---

### ISSUE-001 — CRITICAL
**File:** `core/brain.py` · `process_query()` · Line 324
**Actual Cause:**  
`suggested_style` is referenced on line 324 (inside a `try/except` block logging the assistant turn to SQLite) but is not assigned until line 329. This is an `UnboundLocalError` on every single query. The `except Exception: pass` silently swallows it, so the assistant turn is **never logged** to conversation history.

```python
# BUG: suggested_style used before assignment
mem_db.log_turn("assistant", response_text, intent=intent_res.intent, style=suggested_style)  # line 324
...
suggested_style = intent_res.suggested_style   # line 329 — too late
```

**User-Visible Symptom:** Conversation history in the memory panel shows only user turns, never assistant turns. Memory inspector is half-broken.  
**Severity:** CRITICAL  
**Proposed Repair:** Move `suggested_style = intent_res.suggested_style` to before the SQLite try/except block (before line 319).  
**Risk:** Zero — purely a reordering of two independent assignments.

---

### ISSUE-002 — HIGH
**File:** `core/brain.py` · `parse_intent()` · Lines 158-160
**Actual Cause:**  
Greeting regex is `^(hey|hello|hi|good morning|good afternoon|good evening)\b`. Requires exact spelling at start of string. Inputs like `"heyy"`, `"heyyy"`, `"hi there"`, `"hey there"`, `"yo"`, `"sup"` all fall through to `unknown` (confidence 0.30).

**User-Visible Symptom:** Typing "heyy" or "hi there" gets "Could you rephrase that, sir?" — embarrassing for a first impression.  
**Severity:** HIGH  
**Proposed Repair:** Expand regex to `r"^(hey+|hello+|hi+|hiya|yo|sup|howdy|good (morning|afternoon|evening|day))\b"` and also catch `"hey jarvis"` etc.  
**Risk:** Minimal — greeting intent is a catch-all for any matched greeting, no side effects.

---

### ISSUE-003 — HIGH
**File:** `core/brain.py` · `parse_intent()` · Lines 244-258
**Actual Cause:**  
Volume patterns only match exact phrases `"volume up"`, `"louder"`, `"volume down"`, `"quieter"`, `"mute"`. Natural variants like `"increase volume"`, `"raise the volume"`, `"turn it up"`, `"turn up the volume"`, `"decrease volume"`, `"lower the volume"` → `unknown`.

**User-Visible Symptom:** User says "increase volume" → JARVIS says "Could you rephrase?" for a basic PC control.  
**Severity:** HIGH  
**Proposed Repair:** Replace fixed string checks with flexible regex: `r"\b(increase|raise|turn up|boost|crank)\b.*\bvolume\b"` etc.  
**Risk:** Minimal — isolated intent checks.

---

### ISSUE-004 — HIGH
**File:** `skills/system_control.py` · `launch_application()` · Lines 42-60
**Actual Cause:**  
`KNOWN_APPS` has no entry for `"youtube"`, `"spotify"`, `"discord"`, `"telegram"`, `"whatsapp"`, `"settings"`, `"control panel"`, `"word"`, `"excel"`, or any URL-based app. When `app_name="youtube"`:
1. `os.startfile("youtube")` → `FileNotFoundError`
2. `subprocess.Popen("youtube", shell=True)` → `FileNotFoundError` again
3. Returns `True` (success!) from the except clause even though nothing launched.

Also: `subprocess.Popen(exe, shell=True)` with `shell=True` creates a CMD window flash.

**User-Visible Symptom:** "Open YouTube" → JARVIS says "Launching, sir" but nothing opens. Completely broken.  
**Severity:** HIGH  
**Proposed Repair:**  
- Add URL-based entries to KNOWN_APPS (`youtube → https://youtube.com`, etc.)  
- Add `webbrowser.open(url)` path in launcher for http(s):// URLs  
- Add `winreg` path resolution for installed apps  
- Replace `shell=True` with `creationflags=subprocess.CREATE_NO_WINDOW`  
- Verify process actually created before returning success  
**Risk:** Medium — changes launch path; needs testing. No existing feature is removed.

---

### ISSUE-005 — HIGH
**File:** `core/brain.py` · `parse_intent()` · Full function
**Actual Cause:**  
No intent pattern exists for:  
- `"what can you do"` / `"help"` / `"what are your capabilities"` / `"what commands do you know"` → `unknown`  
- `"how are you doing"` → `unknown` (only exact `"how are you"` matches `status`)  
- `"open a new tab"` / `"new tab"` → wrongly matches `app_launch` ("open" regex)  
- `"good job"`, `"well done"` only match if `"good job"` is in `low` — but `"great job"`, `"nice work"` → `unknown`  

**User-Visible Symptom:** Asking "what can you do?" → JARVIS is baffled. Asking "great job" → no compliment response.  
**Severity:** HIGH  
**Proposed Repair:** Add `capabilities` intent handler with `help` / `what can you do` patterns. Broaden compliment patterns. Fix "how are you doing" → route to `how_are_you` response.  
**Risk:** Low.

---

### ISSUE-006 — MODERATE
**File:** `voice/text_to_speech.py` · `_synthesize_single_phrase()` · Line 57
**Actual Cause:**  
`subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, cwd=PIPER_DIR)` has no `creationflags`. On Windows, every Piper synthesis call briefly flashes a CMD console window.

**User-Visible Symptom:** Faint CMD window blink every time JARVIS speaks.  
**Severity:** MODERATE  
**Proposed Repair:** Add `creationflags=subprocess.CREATE_NO_WINDOW` (Windows only: `if sys.platform == "win32"`).  
**Risk:** Zero — only affects process window visibility.

---

### ISSUE-007 — MODERATE
**File:** `skills/system_control.py` · `capture_screenshot()` · Line 126
**Actual Cause:**  
`subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)` — no `creationflags=CREATE_NO_WINDOW`. Flashes a PowerShell window during screenshot capture.

**User-Visible Symptom:** Blue PowerShell window blinks when taking a screenshot.  
**Severity:** MODERATE  
**Proposed Repair:** Add `creationflags=subprocess.CREATE_NO_WINDOW`.  
**Risk:** Zero.

---

### ISSUE-008 — MODERATE
**File:** `core/desktop_gui.py` · Multiple SQLite operations
**Actual Cause:**  
`ResourceWarning: unclosed database` observed during test run. SQLite connections opened inside the GUI's data-loading methods are not explicitly closed.

**User-Visible Symptom:** Memory leak in long sessions; potential database lock contention.  
**Severity:** MODERATE  
**Proposed Repair:** Use context managers (`with conn:`) consistently — already done in `sqlite_memory.py` but GUI may open its own connections. Verify and patch.  
**Risk:** Low — only affects cleanup path.

---

### ISSUE-009 — MODERATE
**File:** `skills/system_control.py` · `launch_application()` · Line 52-58
**Actual Cause:**  
The function returns `True, get_response("opening_app")` from the second `except` block even when `subprocess.Popen` raises an exception — it checks `except Exception as e2` but only references `e2` in the error message, never re-raises. Actually on closer inspection the second except returns False correctly. But the **first** `os.startfile` path returns `True` immediately after calling `os.startfile` without verifying the process actually started — `os.startfile` is non-blocking and returns no PID.

**User-Visible Symptom:** JARVIS says "Done, sir" for apps that failed to open.  
**Severity:** MODERATE  
**Proposed Repair:** Use `subprocess.Popen` with process existence verification (`proc.poll() is None`) instead of `os.startfile` for apps in KNOWN_APPS.  
**Risk:** Low.

---

### ISSUE-010 — LOW
**File:** `core/brain.py` · `parse_intent()` · Lines 109-140
**Actual Cause:**  
Protocol detection runs before shutdown detection, and uses `any(w in low for w in ["coding mode", "focus mode", ...])`. If the user types `"focus mode off"`, the brain routes to `protocol` intent (not `focus_mode_off`), because `"focus mode"` matches the protocol list.

**User-Visible Symptom:** "Focus mode off" triggers a protocol response instead of the focus-off handler.  
**Severity:** LOW  
**Proposed Repair:** Add `focus_mode_off` and `focus_mode_on` to separate intent checks before protocol matching.  
**Risk:** Minimal.

---

### ISSUE-011 — LOW
**File:** `skills/scheduler.py` · `generate_morning_briefing()` · Line 97
**Actual Cause:**  
`get_response("morning_briefing")` is called at line 97. The key exists in RESPONSES. However the returned string is a bare phrase like `"Good morning, sir. Here is your daily intelligence brief."` which is then followed by another sentence starting `"It is {time_str} on..."` — the join is grammatically correct but repetitive if the time is already said in the startup greeting.

**User-Visible Symptom:** Briefing sounds slightly odd but functional.  
**Severity:** LOW  
**Proposed Repair:** Minor wording adjustment. Non-critical.  
**Risk:** Zero.

---

### ISSUE-012 — LOW
**File:** `core/brain.py` · `parse_intent()` · Line 256
**Actual Cause:**  
App launch regex: `r"\b(?:open|launch|start)\s+([a-zA-Z0-9\s]+)"` with exclusion `not any(k in low for k in ["file", "tab", "window"])`. However the exclusion uses `any(k in low ...)` which checks if `"file"` appears *anywhere* in `low`. So "open file manager" would be excluded but so would "open profile file". The filter is imprecise.

**User-Visible Symptom:** Some valid app launch commands may be incorrectly excluded.  
**Severity:** LOW  
**Proposed Repair:** Narrow the exclusion to specific short phrases using word-boundary regex.  
**Risk:** Low.

---

### ISSUE-013 — LOW
**File:** `core/emotion_detector.py` (not yet read in full)
**Actual Cause:**  
Emotion detection referenced in `brain.py` process_query but module not read. Import wrapped in try/except. If the module has issues they are silently swallowed.

**User-Visible Symptom:** Emotion-aware vocal style may never activate.  
**Severity:** LOW  
**Proposed Repair:** Verify module loads cleanly; add logging instead of bare pass on failure.  
**Risk:** Low.

---

### ISSUE-014 — INFO
**File:** `config.py` · Line 15
**Actual Cause:** `ASSISTANT_VERSION = "1.0.0"` — this is V2 architecture.  
**Proposed Repair:** Update to `"2.0.0"`.

---

### ISSUE-015 — INFO
**File:** `skills/system_control.py` · `KNOWN_APPS`
**Actual Cause:** Missing common apps: YouTube (URL), Spotify, Discord, Telegram, WhatsApp, Microsoft Settings, Control Panel, Word, Excel, PowerPoint, Paint, Snipping Tool, Registry Editor.  
**Severity:** INFO/HIGH combined with ISSUE-004.

---

### ISSUE-016 — INFO
**File:** `core/brain.py` · `parse_intent()` · Lines 143-144
**Actual Cause:** Shutdown intent fires on `"exit"` and `"quit"` which are also valid shell-level exits in `run_interactive_mode`. Handled correctly there but could cause confusion if users type these in the GUI.  
**Severity:** INFO — currently handled.

---

## Repair Priority Order

| Priority | Issue | File | Action |
|---|---|---|---|
| 1 | ISSUE-001 | brain.py | Move `suggested_style` assignment before SQLite try/except |
| 2 | ISSUE-002 | brain.py | Expand greeting regex |
| 3 | ISSUE-003 | brain.py | Expand volume control patterns |
| 4 | ISSUE-005 | brain.py | Add capabilities intent + fix how-are-you |
| 5 | ISSUE-004/015 | system_control.py | Expand KNOWN_APPS, add URL launcher, fix shell=True |
| 6 | ISSUE-006 | text_to_speech.py | Add CREATE_NO_WINDOW to Piper subprocess |
| 7 | ISSUE-007 | system_control.py | Add CREATE_NO_WINDOW to screenshot subprocess |
| 8 | ISSUE-009 | system_control.py | Verify process creation before reporting success |
| 9 | ISSUE-010 | brain.py | Focus mode intent ordering fix |
| 10 | ISSUE-014 | config.py | Version bump to 2.0.0 |

---

## Test Coverage Assessment

| Module | Test File | Coverage |
|---|---|---|
| brain.py | test_brain.py, test_v2.py | Intent routing — basic |
| sqlite_memory.py | test_phase9.py | CRUD operations |
| system_control.py | test_skills.py | Partial |
| telegram_backup.py | test_telegram.py | Full |
| scheduler.py | test_phase8.py | Reminder parsing |
| self_improvement.py | test_phase7.py | Flaw detection |
| desktop_gui.py | test_v2.py | Instantiation only |
| voice/* | voice/tests/ | Synthesis + cache |

No test covers: Piper CMD flash, `suggested_style` NameError, `open youtube` failure.

---

*Audit complete. Proceeding to Phase 2 repairs.*
