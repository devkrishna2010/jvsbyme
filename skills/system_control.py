"""
J.A.R.V.I.S. — System Control Skill
Provides native Windows controls:
- Application launching (with URL support, registry resolution, and CREATE_NO_WINDOW)
- Volume adjustments (Up, Down, Mute) — broadened aliases
- Workstation locking
- Screenshot capture

V2 Repairs (Phase 2):
- ISSUE-004: Added URL-based entries (youtube, twitch, github, etc.) — opened in default browser.
- ISSUE-004: Added winreg-based application path resolution for installed programs.
- ISSUE-004: Replaced shell=True subprocess with CREATE_NO_WINDOW to prevent CMD flash.
- ISSUE-004/009: Process creation verified before reporting success.
- ISSUE-007: Screenshot subprocess also uses CREATE_NO_WINDOW.
"""

import os
import sys
import subprocess
import datetime
import ctypes
import webbrowser
from typing import Dict, Optional, Tuple

from core.responses import get_response
import config

# Windows-only process creation flag to suppress CMD window
CREATE_NO_WINDOW = 0x08000000

# Common Windows application mapping
# Values starting with http(s):// are opened in the default browser.
KNOWN_APPS: Dict[str, str] = {
    # System tools
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "files": "explorer.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "registry editor": "regedit.exe",
    "regedit": "regedit.exe",
    "paint": "mspaint.exe",
    "mspaint": "mspaint.exe",
    "snipping tool": "snippingtool.exe",
    "snip": "snippingtool.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
    "windows settings": "ms-settings:",
    "device manager": "devmgmt.msc",
    "disk management": "diskmgmt.msc",
    "event viewer": "eventvwr.msc",
    "wordpad": "wordpad.exe",
    "clock": "ms-clock:",
    "calendar": "outlookcal:",
    "photos": "ms-photos:",
    "weather app": "bingweather:",
    "store": "ms-windows-store:",
    "microsoft store": "ms-windows-store:",
    # Browsers
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "browser": "msedge.exe",
    "firefox": "firefox.exe",
    "opera": "opera.exe",
    # Developer tools
    "vs code": "code.cmd",
    "vscode": "code.cmd",
    "visual studio code": "code.cmd",
    "code": "code.cmd",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "terminal": "wt.exe",
    "windows terminal": "wt.exe",
    "powershell": "powershell.exe",
    "git bash": "git-bash.exe",
    "android studio": "studio64.exe",
    # Microsoft Office
    "word": "winword.exe",
    "microsoft word": "winword.exe",
    "excel": "excel.exe",
    "microsoft excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "microsoft powerpoint": "powerpnt.exe",
    "outlook": "outlook.exe",
    "microsoft outlook": "outlook.exe",
    # Communication
    "discord": "Discord.exe",
    "telegram": "Telegram.exe",
    "whatsapp": "WhatsApp.exe",
    "slack": "slack.exe",
    "teams": "Teams.exe",
    "microsoft teams": "Teams.exe",
    "zoom": "Zoom.exe",
    # Media
    "spotify": "Spotify.exe",
    "vlc": "vlc.exe",
    "media player": "wmplayer.exe",
    "windows media player": "wmplayer.exe",
    "netflix": "https://www.netflix.com",
    # URLs — opened in default browser
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://www.github.com",
    "stackoverflow": "https://www.stackoverflow.com",
    "stack overflow": "https://www.stackoverflow.com",
    "twitter": "https://www.twitter.com",
    "x": "https://www.x.com",
    "instagram": "https://www.instagram.com",
    "reddit": "https://www.reddit.com",
    "twitch": "https://www.twitch.tv",
    "linkedin": "https://www.linkedin.com",
    "chatgpt": "https://chat.openai.com",
    "openai": "https://www.openai.com",
    # Games / launchers
    "steam": "steam.exe",
    "epic games": "EpicGamesLauncher.exe",
    "epic": "EpicGamesLauncher.exe",
}


def _resolve_app_path(exe: str) -> Optional[str]:
    """
    Attempts to find the full path to an executable via:
    1. Direct known system path.
    2. Windows registry App Paths key.
    3. PATH environment resolution.
    Returns the full path string, or None if unresolvable.
    """
    # ms- URI schemes — just return as-is for ShellExecute
    if exe.startswith("ms-") or exe.endswith(":"):
        return exe

    # Already absolute
    if os.path.isabs(exe) and os.path.isfile(exe):
        return exe

    # Check common install locations
    search_dirs = [
        r"C:\Windows\System32",
        r"C:\Windows",
        r"C:\Windows\SysWOW64",
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs"),
        os.path.expandvars(r"%APPDATA%"),
    ]
    for d in search_dirs:
        candidate = os.path.join(d, exe)
        if os.path.isfile(candidate):
            return candidate

    # Windows registry App Paths
    try:
        import winreg
        reg_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\\" + exe
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(root, reg_key) as k:
                    path, _ = winreg.QueryValueEx(k, "")
                    if path and os.path.isfile(path):
                        return path
            except FileNotFoundError:
                continue
    except Exception:
        pass

    # Try shutil which
    import shutil
    found = shutil.which(exe)
    if found:
        return found

    return None


def launch_application(app_name: str) -> Tuple[bool, str]:
    """
    Launches an application on Windows.
    - Resolves URLs → default browser.
    - Resolves ms- URI schemes → ShellExecute.
    - Resolves known apps and registry paths → subprocess with CREATE_NO_WINDOW.
    - Never pretends an app is open if the launch failed.
    """
    clean_name = app_name.strip().lower()

    # Remove common trailing noise words
    for noise in [" please", " now", " up", " for me"]:
        if clean_name.endswith(noise):
            clean_name = clean_name[: -len(noise)].strip()

    target = KNOWN_APPS.get(clean_name, clean_name)

    # 1. URL-based target → open in default browser
    if target.startswith("http://") or target.startswith("https://"):
        try:
            webbrowser.open(target)
            return True, get_response("opening_app")
        except Exception as e:
            return False, f"I was unable to open {app_name} in the browser, sir. Error: {e}"

    # 2. ms- URI scheme (Windows Settings, etc.)
    if target.startswith("ms-") or target.endswith(":"):
        try:
            os.startfile(target)
            return True, get_response("opening_app")
        except Exception as e:
            return False, f"I was unable to open the Windows URI scheme for {app_name}, sir. Error: {e}"

    # 3. .msc console tool
    if target.endswith(".msc"):
        try:
            proc = subprocess.Popen(
                ["mmc", target],
                creationflags=CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if proc.poll() is None or proc.returncode == 0:
                return True, get_response("opening_app")
        except Exception:
            pass

    # 4. Resolve executable path
    resolved = _resolve_app_path(target)

    if resolved:
        try:
            proc = subprocess.Popen(
                [resolved],
                creationflags=CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Give it 300ms and check it hasn't immediately crashed
            import time
            time.sleep(0.3)
            if proc.poll() is None:
                return True, get_response("opening_app")
            elif proc.returncode == 0:
                return True, get_response("opening_app")
            else:
                return False, f"I launched {app_name} but it exited immediately with code {proc.returncode}, sir."
        except Exception as e:
            return False, f"I was unable to launch '{app_name}', sir. Error: {e}"

    # 5. Last resort — ShellExecute via os.startfile on whatever the user typed
    try:
        os.startfile(target)
        return True, get_response("opening_app")
    except Exception as e:
        return False, (
            f"I was unable to locate or launch '{app_name}', sir. "
            f"I do not have it in my application registry. "
            f"If you tell me the exact path, I can add it. Error: {e}"
        )


def adjust_volume(action: str) -> Tuple[bool, str]:
    """
    Controls Windows volume via virtual key codes (VK_VOLUME_UP, VK_VOLUME_DOWN, VK_VOLUME_MUTE).
    """
    VK_VOLUME_MUTE = 0xAD
    VK_VOLUME_DOWN = 0xAE
    VK_VOLUME_UP   = 0xAF

    user32 = ctypes.windll.user32

    if action == "volume_up":
        # Press 5 times for a noticeable step
        for _ in range(5):
            user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
            user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
        return True, get_response("volume_up")

    elif action == "volume_down":
        for _ in range(5):
            user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
            user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
        return True, get_response("volume_down")

    elif action == "mute":
        user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
        user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
        return True, get_response("volume_mute")

    return False, "Unknown volume command, sir."


def lock_system() -> Tuple[bool, str]:
    """Locks the Windows workstation instantly."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return True, get_response("lock")
    except Exception as e:
        return False, f"Unable to engage workstation lock, sir: {e}"


def capture_screenshot() -> Tuple[bool, str]:
    """
    Captures primary screen using .NET Graphics without heavy external Python imaging libraries.
    Saves output into logs/screenshots/.
    Uses CREATE_NO_WINDOW to suppress any PowerShell window flash.
    """
    shot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "screenshots")
    os.makedirs(shot_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = os.path.join(shot_dir, f"screenshot_{timestamp}.png")

    ps_script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "Add-Type -AssemblyName System.Drawing; "
        "$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
        "$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height; "
        "$gfx = [System.Drawing.Graphics]::FromImage($bmp); "
        "$gfx.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size); "
        f"$bmp.Save('{target_path}', [System.Drawing.Imaging.ImageFormat]::Png); "
        "$gfx.Dispose(); "
        "$bmp.Dispose()"
    )

    try:
        res = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
        )
        if os.path.isfile(target_path):
            return True, f"{get_response('screenshot')} Stored as screenshot_{timestamp}.png."
        return False, f"Screenshot capture failed: {res.stderr}"
    except Exception as e:
        return False, f"Screenshot command encountered an error: {e}"


# Intent handler bridges
def handle_app_launch(intent_res) -> str:
    app_name = intent_res.parameters.get("app", "")
    if not app_name:
        return "Which application shall I open, sir?"
    success, msg = launch_application(app_name)
    return msg


def handle_system_action(intent_res) -> str:
    action = intent_res.parameters.get("action", "")
    if action in ["volume_up", "volume_down", "mute"]:
        _, msg = adjust_volume(action)
        return msg
    elif action == "lock":
        _, msg = lock_system()
        return msg
    elif action == "screenshot":
        _, msg = capture_screenshot()
        return msg
    return "System action could not be identified, sir."
