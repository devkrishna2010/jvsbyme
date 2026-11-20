# ============================================================
#  J.A.R.V.I.S  —  config.py
#  Public configuration only. Keep all secrets in config_private.py
#  config_private.py is listed in .gitignore and NEVER committed.
# ============================================================

import os

# ------------------------------------------------------------------
# IDENTITY
# ------------------------------------------------------------------
JARVIS_NAME        = "JARVIS"
USER_NAME          = "Dev"
USER_TITLE         = "sir"          # Default address ("sir", with "Dev" used in personal/milestone context)
ASSISTANT_VERSION  = "2.0.0"

# ------------------------------------------------------------------
# VOICE / TTS SETTINGS (J.A.R.V.I.S. Cinematic Engine)
# ------------------------------------------------------------------
PIPER_MODEL_PATH    = os.path.join("voice", "models", "jarvis", "en_GB-jarvis-high.onnx")
PIPER_CONFIG_PATH   = os.path.join("voice", "models", "jarvis", "en_GB-jarvis-high.onnx.json")
DEFAULT_VOICE_STYLE = "cinematic"  # cinematic | normal | night | witty | alert
ENABLE_VOICE_DSP    = True         # 3-layer architecture + sub-octave rumble + workshop echo
USE_AUDIO_CACHE     = True         # Cache repeated speech to eliminate latency and save CPU

# pyttsx3 fallback settings (if offline neural engine is disabled)
PREFERRED_VOICE_GENDER = "male"
PREFERRED_VOICE_LANG   = "en"
PREFERRED_VOICE_NAME   = "David"
SPEECH_RATE   = 185
SPEECH_VOLUME = 0.95

# ------------------------------------------------------------------
# SPEECH RECOGNITION (VOSK)
# ------------------------------------------------------------------
# High accuracy desktop model: vosk-model-en-us-0.22-lgraph (128 MB)
# Fallback small model: vosk-model-small-en-us-0.15 (40 MB)
VOSK_MODEL_PATH = os.path.join("assets", "voice_model", "vosk-model-en-us-0.22-lgraph")
if not os.path.isdir(VOSK_MODEL_PATH):
    VOSK_MODEL_PATH = os.path.join("assets", "voice_model", "vosk-model-small-en-us-0.15")
VOSK_SAMPLE_RATE = 16000           # Hz — required by vosk model

# ------------------------------------------------------------------
# WAKE WORD
# ------------------------------------------------------------------
WAKE_WORD = "jarvis"               # Lowercase; spoken to activate listening

# ------------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------------
LOG_DIR      = "logs"
LOG_FILENAME = "jarvis.log"
LOG_LEVEL    = "INFO"              # DEBUG | INFO | WARNING | ERROR

# ------------------------------------------------------------------
# MEMORY
# ------------------------------------------------------------------
MEMORY_FILE = os.path.join("memory", "jarvis_memory.json")

# ------------------------------------------------------------------
# PRIVATE CREDENTIALS — load from config_private.py if it exists
# This file is .gitignored. Create it locally with your API keys.
# ------------------------------------------------------------------
# Template for config_private.py:
#
#   NEWS_API_KEY       = "your_newsapi_key_here"
#   WEATHER_API_KEY    = "your_openweather_key_here"
#   OPENAI_API_KEY     = "your_openai_key_here"   # optional, for Phase 3+
#
# Usage in this file:
try:
    from config_private import *          # noqa: F401, F403
except ImportError:
    # config_private.py not found — credentials will be unavailable
    NEWS_API_KEY     = ""
    WEATHER_API_KEY  = ""
    OPENAI_API_KEY   = ""

# ------------------------------------------------------------------
# FEATURE FLAGS
# ------------------------------------------------------------------
ENABLE_VOICE_INPUT   = True
ENABLE_VOICE_OUTPUT  = True
ENABLE_WEB_SEARCH    = True
ENABLE_MEMORY        = True
ENABLE_DEBUG_PRINTS  = False

