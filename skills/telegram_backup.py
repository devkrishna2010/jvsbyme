"""
J.A.R.V.I.S. — Automated Telegram Backup & Cloud Sync Skill
Handles:
- Full project archiving with chunking (< 45 MB per volume for Telegram 50 MB limit)
- Automatic Saturday scheduled backups to Telegram bot
- Daily startup check: if the previous Saturday was missed, backs up immediately
- Native Windows Startup launcher setup
- Passcode 2681 Listener: Anyone who sends '2681' receives the backup archive
  and is enrolled for future automated updates.
"""

import os
import sys
import json
import zipfile
import datetime
import threading
import time
import requests
from typing import List, Tuple, Dict, Any, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config

BACKUP_STATE_FILE = os.path.join(ROOT, "memory", "telegram_backup.json")
BACKUP_TEMP_DIR = os.path.join(ROOT, "memory", "backups")
AUTHORIZED_CHATS_FILE = os.path.join(ROOT, "memory", "authorized_telegram_chats.json")

# Default Telegram Credentials provided by Dev
TELEGRAM_BOT_TOKEN = getattr(config, "TELEGRAM_BOT_TOKEN", "9231193145:AAFngE2hI2GweaelqcjD9DbkoUKVXPeO0cU")
TELEGRAM_CHAT_ID = getattr(config, "TELEGRAM_CHAT_ID", "6626316254")

PASSCODE = "2681"
MAX_CHUNK_BYTES = 45 * 1024 * 1024  # 45 MB (safe headroom under Telegram 50 MB limit)


def load_authorized_chats() -> Dict[str, Any]:
    """Loads all authorized recipient chat IDs."""
    if os.path.isfile(AUTHORIZED_CHATS_FILE):
        try:
            with open(AUTHORIZED_CHATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Initialize with Dev as primary owner
    initial = {
        "chats": {
            str(TELEGRAM_CHAT_ID): {
                "name": config.USER_NAME,
                "role": "owner",
                "enrolled_at": datetime.datetime.now().isoformat()
            }
        }
    }
    save_authorized_chats(initial)
    return initial


def save_authorized_chats(data: Dict[str, Any]):
    os.makedirs(os.path.dirname(AUTHORIZED_CHATS_FILE), exist_ok=True)
    try:
        with open(AUTHORIZED_CHATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def enroll_chat_id(chat_id: str, user_info: Dict[str, Any]) -> bool:
    """Enrolls a new chat ID who supplied passcode 2681."""
    data = load_authorized_chats()
    cid = str(chat_id)
    is_new = cid not in data.get("chats", {})
    data.setdefault("chats", {})[cid] = {
        "name": user_info.get("first_name", "User"),
        "username": user_info.get("username", ""),
        "role": "authorized_recipient",
        "enrolled_at": datetime.datetime.now().isoformat()
    }
    save_authorized_chats(data)
    return is_new


def load_backup_state() -> Dict[str, Any]:
    if os.path.isfile(BACKUP_STATE_FILE):
        try:
            with open(BACKUP_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_saturday_backup": "", "last_update_id": 0, "history": []}


def save_backup_state(state: Dict[str, Any]):
    os.makedirs(os.path.dirname(BACKUP_STATE_FILE), exist_ok=True)
    try:
        with open(BACKUP_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def create_project_zip_packages() -> List[str]:
    """
    Archives the entire J.A.R.V.I.S. workspace into one or more zip packages
    respecting the 45 MB per-file Telegram upload constraint.
    """
    os.makedirs(BACKUP_TEMP_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_zip_name = f"jarvis_backup_{timestamp}.zip"
    temp_full_zip = os.path.join(BACKUP_TEMP_DIR, base_zip_name)

    # 1. Compress workspace excluding venv, __pycache__, logs/screenshots, temp backups
    with zipfile.ZipFile(temp_full_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=8) as z:
        for root, dirs, files in os.walk(ROOT):
            if any(x in root for x in ["venv", "__pycache__", ".git", "backups"]):
                continue
            for f in files:
                if f.endswith((".pyc", ".tmp")) or f == base_zip_name:
                    continue
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, ROOT)
                z.write(abs_path, rel_path)

    full_size = os.path.getsize(temp_full_zip)

    # If fits within single volume, return it directly
    if full_size <= MAX_CHUNK_BYTES:
        return [temp_full_zip]

    # Split into multi-part volumes if exceeding 45 MB
    part_paths = []
    part_idx = 1
    with open(temp_full_zip, "rb") as f_in:
        while True:
            chunk = f_in.read(MAX_CHUNK_BYTES)
            if not chunk:
                break
            part_name = f"jarvis_backup_{timestamp}.part{part_idx:02d}.zip"
            part_path = os.path.join(BACKUP_TEMP_DIR, part_name)
            with open(part_path, "wb") as f_out:
                f_out.write(chunk)
            part_paths.append(part_path)
            part_idx += 1

    try:
        os.remove(temp_full_zip)
    except Exception:
        pass

    return part_paths


def send_telegram_message(text: str, chat_id: Optional[str] = None) -> bool:
    cid = str(chat_id or TELEGRAM_CHAT_ID)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": cid, "text": text}, timeout=15)
        return r.status_code == 200 and r.json().get("ok", False)
    except Exception:
        return False


def send_telegram_document(file_path: str, caption: str = "", chat_id: Optional[str] = None) -> bool:
    cid = str(chat_id or TELEGRAM_CHAT_ID)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, "rb") as f:
            r = requests.post(
                url,
                data={"chat_id": cid, "caption": caption},
                files={"document": f},
                timeout=300
            )
            return r.status_code == 200 and r.json().get("ok", False)
    except Exception:
        return False


def perform_telegram_backup(target_chat_id: Optional[str] = None) -> Tuple[bool, str]:
    """
    Creates backup packages and dispatches them to Telegram.
    If target_chat_id is specified, sends to that user.
    Otherwise, sends to ALL enrolled authorized recipients.
    """
    recipients_data = load_authorized_chats()
    if target_chat_id:
        target_cids = [str(target_chat_id)]
    else:
        target_cids = list(recipients_data.get("chats", {}).keys())

    if not target_cids:
        target_cids = [str(TELEGRAM_CHAT_ID)]

    # Notify targets
    for cid in target_cids:
        send_telegram_message("Compiling updated J.A.R.V.I.S. workspace archive for dispatch, sir...", chat_id=cid)

    packages = create_project_zip_packages()
    total_parts = len(packages)
    overall_success = True

    for cid in target_cids:
        parts_sent = 0
        for idx, pkg in enumerate(packages, 1):
            filename = os.path.basename(pkg)
            size_mb = round(os.path.getsize(pkg) / (1024 * 1024), 2)
            caption = f"J.A.R.V.I.S. Mark VII Backup [{idx}/{total_parts}] — {filename} ({size_mb} MB)"
            ok = send_telegram_document(pkg, caption=caption, chat_id=cid)
            if ok:
                parts_sent += 1
            else:
                overall_success = False

        if parts_sent == total_parts:
            send_telegram_message(
                f"✓ Complete J.A.R.V.I.S. workspace archive delivered successfully ({total_parts} volume{'s' if total_parts > 1 else ''}).",
                chat_id=cid
            )

    # Clean up disk files after all deliveries
    for pkg in packages:
        try:
            if os.path.isfile(pkg):
                os.remove(pkg)
        except Exception:
            pass

    today_str = datetime.date.today().isoformat()
    state = load_backup_state()
    state["last_backup_date"] = today_str
    if datetime.date.today().weekday() == 5:
        state["last_saturday_backup"] = today_str
    state.setdefault("history", []).append({
        "timestamp": datetime.datetime.now().isoformat(),
        "recipients_count": len(target_cids),
        "total_parts": total_parts
    })
    save_backup_state(state)

    summary = (
        f"Backup complete, {config.USER_NAME}. Dispatched {total_parts} archive volume{'s' if total_parts > 1 else ''} "
        f"to {len(target_cids)} authorized recipient{'s' if len(target_cids) > 1 else ''}, {config.USER_TITLE}."
    )
    return overall_success, summary


def check_and_run_saturday_backup() -> Optional[str]:
    """Checks if Saturday backup was missed, and if so executes it across all recipients."""
    today = datetime.date.today()
    days_since_saturday = (today.weekday() - 5) % 7
    last_saturday = today - datetime.timedelta(days=days_since_saturday)
    last_saturday_str = last_saturday.isoformat()

    state = load_backup_state()
    recorded_saturday = state.get("last_saturday_backup", "")

    if recorded_saturday != last_saturday_str:
        print(f"[Telegram Backup]: Executing scheduled Saturday backup ({last_saturday_str})...")
        ok, msg = perform_telegram_backup()
        state["last_saturday_backup"] = last_saturday_str
        save_backup_state(state)
        return msg

    return None


# ----------------------------------------------------------------------
# PASSCODE 2681 LISTENER DAEMON
# ----------------------------------------------------------------------
_listener_running = False
_listener_thread: Optional[threading.Thread] = None


def _passcode_polling_worker():
    global _listener_running
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    state = load_backup_state()
    offset = state.get("last_update_id", 0)

    while _listener_running:
        try:
            params = {"timeout": 15, "offset": offset}
            resp = requests.get(url, params=params, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        uid = update["update_id"]
                        offset = max(offset, uid + 1)
                        state["last_update_id"] = offset
                        save_backup_state(state)

                        msg = update.get("message", {})
                        text = msg.get("text", "").strip()
                        chat = msg.get("chat", {})
                        from_user = msg.get("from", {})
                        cid = str(chat.get("id", ""))

                        if not cid:
                            continue

                        # Check for Passcode 2681
                        if PASSCODE in text:
                            first_name = from_user.get("first_name", "Guest")
                            uname = from_user.get("username", "")
                            print(f"[Telegram Passcode]: Received 2681 from {first_name} (@{uname}, ID: {cid})")

                            # Enroll user
                            is_new = enroll_chat_id(cid, from_user)

                            # Send acceptance
                            send_telegram_message(
                                f"Access granted. Passcode {PASSCODE} verified. Authorised by Dev. "
                                f"Transmitting the complete J.A.R.V.I.S. workspace archive to this channel now...",
                                chat_id=cid
                            )

                            # Notify Dev
                            if cid != str(TELEGRAM_CHAT_ID):
                                send_telegram_message(
                                    f"Security Notice, Dev: User {first_name} (@{uname}, ID: {cid}) entered passcode {PASSCODE}. "
                                    f"J.A.R.V.I.S. backup archive was transmitted to them, and their ID has been enrolled for automated updates, sir.",
                                    chat_id=str(TELEGRAM_CHAT_ID)
                                )

                            # Deliver backup in background thread
                            threading.Thread(target=perform_telegram_backup, args=(cid,), daemon=True).start()

        except Exception:
            pass

        time.sleep(3)


def start_passcode_listener():
    """Starts the background long-poller for passcode 2681."""
    global _listener_running, _listener_thread
    if _listener_running:
        return
    _listener_running = True
    _listener_thread = threading.Thread(target=_passcode_polling_worker, daemon=True)
    _listener_thread.start()
    print(f"[Telegram Bot]: Passcode '{PASSCODE}' listener active in background.")


def stop_passcode_listener():
    global _listener_running
    _listener_running = False


def install_windows_startup() -> Tuple[bool, str]:
    """Installs VBScript launcher into Windows User Startup folder."""
    startup_dir = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    if not os.path.isdir(startup_dir):
        return False, "Windows Startup directory could not be located."

    vbs_path = os.path.join(startup_dir, "LaunchJarvis.vbs")
    python_exe = os.path.join(ROOT, "venv", "Scripts", "python.exe")
    main_py = os.path.join(ROOT, "main.py")

    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{ROOT}"
WshShell.Run """{python_exe}"" ""{main_py}""", 1, False
'''
    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        return True, f"Startup launcher successfully installed in {vbs_path}"
    except Exception as e:
        return False, f"Failed to install startup launcher: {e}"


def handle_backup_command(intent_res) -> str:
    success, summary = perform_telegram_backup()
    return summary
