# J.A.R.V.I.S. V2 — Saturday Backup & Telegram Delivery Guide

## Overview
J.A.R.V.I.S. includes an autonomous backup engine (`skills/telegram_backup.py`) designed to compress the entire project directory and transmit it directly to the designated Telegram chat.

---

## Configuration & Credentials

- **Target Telegram Chat ID:** `6626316254`
- **Schedule:** Every Saturday at 12:00 PM (Noon) local time.
- **Missed Backup Detection:** On startup, J.A.R.V.I.S. checks the timestamp in `memory/last_telegram_backup.json`. If a Saturday was missed, it offers to perform the archive immediately.

---

## Zip Splitting & Archive Specifications

1. **Size Limit:** Telegram Bot API limits standard document uploads to **50 MB** per file.
2. **Multi-Part Splitting:**
   - If the compressed archive exceeds 45 MB, the archiver automatically partitions the zip into multipart chunks (`jarvis_backup_part1.zip`, `jarvis_backup_part2.zip`, etc.).
   - Each chunk is under 45 MB and uploaded sequentially with part headers.
3. **Excluded Directories:**
   To minimize payload size, temporary and non-essential caches are excluded:
   - `venv/` (can be recreated via requirements.txt)
   - `__pycache__/`
   - `.git/`
   - `assets/piper/` (large binary models)

---

## Manual Backup Trigger

You can trigger an immediate backup at any time through:
1. Spoken / Chat Command: `Send backup to Telegram` or `Telegram backup`
2. Terminal command:
```powershell
venv\Scripts\python.exe -c "from skills.telegram_backup import perform_backup_and_dispatch; perform_backup_and_dispatch()"
```

---

## Restoration Instructions

To restore from a backup:
1. Download all backup archive parts sent by the Telegram Bot.
2. If multipart, extract `part1.zip` (it will automatically merge the remaining parts).
3. Open terminal in the extracted folder and restore dependencies:
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
4. Run `run_jarvis_silent.vbs` or `python main.py`.
