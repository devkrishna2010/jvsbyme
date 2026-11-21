"""
J.A.R.V.I.S. V2 — Voice Output & Barge-In Audio Controller
Bridges core assistant operations with the cinematic 3-layer TTS engine.
Supports styles: cinematic, normal, night, witty, alert.
Satisfies Section 6 (Barge-in voice interruption).
"""

import os
import sys
import threading
from typing import Optional

from voice.text_to_speech import JarvisTTS
from voice.voice_profiles import get_profile
import config

_tts_instance: Optional[JarvisTTS] = None
_tts_lock = threading.Lock()
_is_speaking = False


def get_tts() -> JarvisTTS:
    """Singleton getter for JarvisTTS engine."""
    global _tts_instance
    if _tts_instance is None:
        with _tts_lock:
            if _tts_instance is None:
                _tts_instance = JarvisTTS(use_cache=config.USE_AUDIO_CACHE)
    return _tts_instance


def is_currently_speaking() -> bool:
    """Returns True if J.A.R.V.I.S. is currently producing voice output."""
    return _is_speaking


def stop_speaking():
    """Immediately terminates ongoing speech playback (Barge-in)."""
    global _is_speaking
    _is_speaking = False
    tts = get_tts()
    tts.stop_playback()


def speak(
    text: str,
    style: Optional[str] = None,
    block: bool = True
) -> str:
    """
    Main speech output function for J.A.R.V.I.S.
    
    Parameters:
    - text: Spoken dialogue string.
    - style: Optional voice profile override ('cinematic', 'normal', 'night', 'witty', 'alert').
             Defaults to config.DEFAULT_VOICE_STYLE ('cinematic').
    - block: Whether to wait until speech playback completes before returning.
    
    Returns:
    - Path to generated WAV file.
    """
    global _is_speaking
    if not config.ENABLE_VOICE_OUTPUT:
        print(f"[{config.JARVIS_NAME}]: {text}")
        return ""

    resolved_style = style or config.DEFAULT_VOICE_STYLE
    tts = get_tts()

    # Fast path: check if cached already
    cached_path = None
    if tts.cache and tts.cache.has(text, resolved_style):
        cached_path = tts.cache.get_path(text, resolved_style)

    def _speech_worker():
        global _is_speaking
        try:
            _is_speaking = True
            wav_to_play = cached_path or tts.synthesize(
                text=text,
                style=resolved_style,
                apply_effects=config.ENABLE_VOICE_DSP
            )
            tts.play(wav_to_play)
        finally:
            _is_speaking = False

    if block:
        _speech_worker()
        return cached_path or tts.synthesize(text=text, style=resolved_style, apply_effects=config.ENABLE_VOICE_DSP)
    else:
        # Truly non-blocking: synthesis & playback run entirely in background thread
        t = threading.Thread(target=_speech_worker, daemon=True)
        t.start()
        return cached_path or ""


def request_user_input(prompt: str = "I require your input or authorization, Dev.") -> str:
    """Spoken prompt when J.A.R.V.I.S. requires input, command, or parameter from the user."""
    full_speech = f"Pardon the interruption, {config.USER_TITLE}. {prompt}"
    print(f"[{config.JARVIS_NAME} (User Input Request)]: {full_speech}")
    speak(full_speech, style="alert", block=True)
    return full_speech
