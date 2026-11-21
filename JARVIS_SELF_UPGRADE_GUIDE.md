# J.A.R.V.I.S. V2 — Autonomous Self-Upgrade & Flaw Mitigation Guide

## Architecture Overview
J.A.R.V.I.S. V2 implements continuous operational telemetry and self-improvement staging (`core/self_improvement.py`).
Rather than applying arbitrary or unverified code changes directly to production files, J.A.R.V.I.S. uses a staged patching pipeline:

```
[Operational Flaw Detected] (high latency, unrecognized intent, unhandled exception)
                           │
                           ▼
[Flaw Database] (memory/jarvis_memory.db & memory/daily_flaws_and_improvements.txt)
                           │
                           ▼
[Self-Improvement Engine] Generates proposed patch in staging/
                           │
                           ▼
[Automated Verification] Executes unittest suite against staged copy
                           │
                           ▼
[Architect Approval] Dev reviews upgrade summary and confirms promotion
                           │
                           ▼
[Atomic Promotion] Changes applied cleanly; rollback snapshot preserved
```

---

## Flaw Detection System

During everyday use, `core/brain.py` logs operational telemetry to SQLite:
- **Query Latency:** Execution times exceeding 4.0s are flagged for caching or algorithmic optimization.
- **Unrecognized Commands:** Queries falling through to fallback handlers are recorded to expand regex patterns.
- **Subprocess Failures:** External application launch issues or audio hardware hiccups are captured with full stack traces.

### Inspecting Flaw Reports
You can ask J.A.R.V.I.S.:
- `Check flaws`
- `What should we improve?`
- `Run self diagnostic audit`

Or inspect the daily log file:
`memory/daily_flaws_and_improvements.txt`

---

## Staging & Promotion Safety Rules

1. **Never Overwrite Without Backup:** A full snapshot of the modified module is written to `memory/backups/` before any patch is promoted.
2. **Automated Regression Guard:** The patch must pass all unit tests in `tests/` before it is marked eligible for promotion.
3. **No Autonomous Self-Destruction:** Critical infrastructure files (`config.py`, `sqlite_memory.py`, security verifications) cannot be modified without explicit confirmation.
