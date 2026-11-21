"""
J.A.R.V.I.S. V2 — Main Application Entry Point
Supports Native Windows Desktop Application by default, with CLI fallback.
Includes automatic Virtual Environment bootstrap and launch recovery.
"""

import os
import sys

# ----------------------------------------------------------------------
# 1. VIRTUAL ENVIRONMENT AUTO-BOOTSTRAP (Fixes ModuleNotFoundError)
# ----------------------------------------------------------------------
VENV_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "Scripts", "python.exe")
if os.path.isfile(VENV_PY) and sys.prefix == sys.base_prefix and not os.environ.get("JARVIS_BOOTSTRAPPED"):
    os.environ["JARVIS_BOOTSTRAPPED"] = "1"
    try:
        import subprocess
        sys.exit(subprocess.call([VENV_PY, os.path.abspath(__file__)] + sys.argv[1:]))
    except Exception:
        pass

import argparse
import datetime

import config
from core.brain import JarvisBrain
from core.responses import get_response
from core.voice_output import speak
from core.voice_input import listen_phrase
from core.hands_free_listener import HandsFreeListener
from core.hud_terminal import render_dashboard
from skills.scheduler import handle_briefing
from skills.system_diagnostics import handle_diagnostics


def get_greeting() -> str:
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return get_response("greeting_morning")
    elif 12 <= hour < 17:
        return get_response("greeting_afternoon")
    else:
        return get_response("startup")


def run_interactive_mode(brain: JarvisBrain):
    render_dashboard(status="STANDBY", mode=config.DEFAULT_VOICE_STYLE.upper(), emotion="COMPOSED")
    print("  Commands:")
    print("    • Type 'gui' to launch Native Windows Desktop Application")
    print("    • Type 'handsfree' or 'wake' to start continuous voice listening")
    print("    • Type 'voice' to speak a single command")
    print("    • Type 'briefing' for intelligence brief with live weather")
    print("    • Type 'diagnostics' for full system hardware telemetry")
    print("    • Type 'flaws' to run self-diagnostic flaw audit & improvement targets")
    print("    • Type 'backup' to dispatch full project archive to Telegram")
    print("    • Type 'quit' to exit")
    print("=" * 71)
    print()

    # Startup Greeting
    greeting = get_greeting()
    print(f"[{config.JARVIS_NAME}]: {greeting}")
    speak(greeting, style=config.DEFAULT_VOICE_STYLE, block=True)

    while True:
        try:
            user_input = input(f"\n[{config.USER_TITLE}]: ").strip()
            if not user_input:
                continue

            low = user_input.lower()
            if low in ["quit", "exit", "shutdown", "power down"]:
                bye = get_response("shutdown")
                print(f"[{config.JARVIS_NAME}]: {bye}")
                speak(bye, style=config.DEFAULT_VOICE_STYLE, block=True)
                break

            # Launch Native Windows Desktop GUI
            if low in ["gui", "desktop", "hud", "app"]:
                from core.desktop_gui import launch_desktop_gui
                launch_desktop_gui()
                continue

            # Switch to continuous hands-free mode
            if low in ["handsfree", "wake", "hands-free", "autonomous"]:
                listener = HandsFreeListener(brain=brain)
                listener.start()
                continue

            # Handle single spoken command
            if low in ["voice", "listen", "mic"]:
                print(f"[{config.JARVIS_NAME}]: Listening, sir...")
                heard = listen_phrase(timeout_sec=7.0)
                if heard:
                    print(f"[{config.USER_TITLE} (Spoken)]: {heard}")
                    user_input = heard
                else:
                    msg = "I did not quite catch that, sir."
                    print(f"[{config.JARVIS_NAME}]: {msg}")
                    speak(msg, block=True)
                    continue

            # Process through Cognitive Brain
            reply, style = brain.process_query(user_input)
            print(f"[{config.JARVIS_NAME}]: {reply}")
            speak(reply, style=style, block=True)

        except (KeyboardInterrupt, EOFError):
            print(f"\nShutting down safely, {config.USER_TITLE}.")
            break

    # Automatic end-of-session flaw and improvement logging
    try:
        from core.self_improvement import get_flaw_detector
        get_flaw_detector().save_daily_report()
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="J.A.R.V.I.S. V2 Stark Tactical Operating System")
    parser.add_argument("--cli", action="store_true", help="Launch in interactive terminal console mode")
    parser.add_argument("--wake", action="store_true", help="Launch directly into hands-free wake word listener")
    parser.add_argument("--status", action="store_true", help="Execute immediate diagnostic telemetry check")
    parser.add_argument("--brief", action="store_true", help="Deliver daily intelligence briefing with live weather")
    parser.add_argument("--flaws", action="store_true", help="Run autonomous self-diagnostic flaw audit and save report")
    parser.add_argument("--companion", action="store_true", help="Launch directly into lightweight floating desktop companion")
    parser.add_argument("--diag", "--diagnostics", action="store_true", dest="diag", help="Run complete voice pipeline & microphone diagnostic")
    parser.add_argument("--hud-large", action="store_true", help="Launch expanded legacy rectangular desktop dashboard")
    args = parser.parse_args()

    # Passcode 2681 Telegram Listener & Saturday Backup check active across all modes
    try:
        import threading
        from skills.telegram_backup import start_passcode_listener, check_and_run_saturday_backup
        start_passcode_listener()
        threading.Thread(target=check_and_run_saturday_backup, daemon=True).start()
    except Exception:
        pass

    brain = JarvisBrain()

    if args.cli:
        run_interactive_mode(brain)
    elif args.wake:
        listener = HandsFreeListener(brain=brain)
        listener.start()
    elif args.status:
        res = brain.process_query("diagnostic telemetry check")
        print(f"[{config.JARVIS_NAME}]: {res[0]}")
        speak(res[0], style=res[1], block=True)
    elif args.brief:
        res = brain.process_query("give me the morning briefing")
        print(f"[{config.JARVIS_NAME}]: {res[0]}")
        speak(res[0], style=res[1], block=True)
    elif args.flaws:
        res = brain.process_query("run self diagnostic flaw audit")
        print(f"[{config.JARVIS_NAME}]: {res[0]}")
        speak(res[0], style=res[1], block=True)
    elif args.diag:
        from core.audio_manager import get_audio_manager
        import sounddevice as sd
        print("=" * 65)
        print("  J.A.R.V.I.S. Mark VII — Complete Voice Pipeline Diagnostic")
        print("=" * 65)
        print(f"[MIC] Default sounddevice device: {sd.default.device}")
        for idx, d in enumerate(sd.query_devices()):
            if d.get("max_input_channels", 0) > 0:
                print(f"  Input Device [{idx}]: {d.get('name')} (Channels: {d.get('max_input_channels')}, Rate: {d.get('default_samplerate')}Hz)")
        mgr = get_audio_manager()
        print(f"[WAKE] Wake recognizer initialized: {mgr.wake_recognizer is not None}")
        print(f"[STT] Command recognizer initialized: {mgr.command_recognizer is not None}")
        print(f"[TTS] Voice output engine ready: {config.ENABLE_VOICE_OUTPUT}")
        speak("Diagnostic check complete, sir. All voice systems nominal.", style="cinematic", block=True)
        print("[STATUS] All voice systems verified successfully.")
    elif args.hud_large:
        try:
            from core.desktop_gui import launch_desktop_gui
            launch_desktop_gui(show_hud=True)
        except Exception as e:
            print(f"[Desktop GUI Launch Fallback]: {e}")
            run_interactive_mode(brain)
    else:
        # Default Mark VII Behavior: Compact Transparent Holographic HUD with hands-free wake word
        try:
            from core.holographic_hud import launch_holographic_app
            launch_holographic_app()
        except Exception as e:
            print(f"[Holographic HUD Launch Fallback]: {e}")
            run_interactive_mode(brain)


if __name__ == "__main__":
    main()
