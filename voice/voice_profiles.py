"""
J.A.R.V.I.S. — Voice Profiles
Configurable audio profiles with exact parametric EQ curves and acoustic settings:
- Cinematic mode: Fuller, warmer playback with targeted low-mid presence
- Normal mode: Natural voice without extra bass
- Night mode: Lower volume and controlled bass
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class VoiceProfile:
    name: str
    length_scale: float = 1.10
    noise_scale: float = 0.35
    noise_w: float = 0.50
    sentence_silence: float = 0.25
    
    # Parametric EQ adjustments in dB matching user curve
    eq_80_100_db: float = 0.0      # 80–100 Hz (sub-chest thump)
    eq_120_160_db: float = 0.0     # 120–160 Hz (fundamental body)
    eq_200_250_db: float = 0.0     # 200–250 Hz (warmth)
    eq_300_400_db: float = 0.0     # 300–400 Hz (boxiness / mud cut)
    eq_2k_4k_db: float = 0.0       # 2–4 kHz (clarity preservation)
    
    # Acoustic & Output controls
    ambience_mix: float = 0.08      # Spatial early reflection level
    stereo_spread: float = 0.12     # Stereo field width
    master_gain: float = 0.95       # Master volume level (0.0 to 1.0)
    limiter_ceiling: float = 0.95   # Anti-clipping safety ceiling
    add_breath: bool = True         # Subtle human breath intake


PROFILES: Dict[str, VoiceProfile] = {
    # ── CINEMATIC MODE: Fuller, warmer playback ───────────────────
    "cinematic": VoiceProfile(
        name="cinematic",
        length_scale=1.12,
        noise_scale=0.33,
        noise_w=0.48,
        sentence_silence=0.28,
        # Exact requested audio curve:
        eq_80_100_db=2.0,           # +2 dB at 80–100 Hz
        eq_120_160_db=3.0,          # +3 dB at 120–160 Hz
        eq_200_250_db=1.0,          # +1 dB at 200–250 Hz
        eq_300_400_db=-1.0,         # -1 dB at 300–400 Hz (cuts mud)
        eq_2k_4k_db=0.0,            # 0 dB at 2–4 kHz (preserved clarity)
        ambience_mix=0.15,
        stereo_spread=0.20,
        master_gain=0.95,
        limiter_ceiling=0.95,
        add_breath=True,
    ),

    # ── NORMAL MODE: Natural voice without extra bass ─────────────
    "normal": VoiceProfile(
        name="normal",
        length_scale=1.08,
        noise_scale=0.35,
        noise_w=0.50,
        sentence_silence=0.22,
        eq_80_100_db=0.0,
        eq_120_160_db=0.0,
        eq_200_250_db=0.0,
        eq_300_400_db=0.0,
        eq_2k_4k_db=0.0,
        ambience_mix=0.04,
        stereo_spread=0.08,
        master_gain=0.95,
        limiter_ceiling=0.95,
        add_breath=True,
    ),

    # ── NIGHT MODE: Lower volume and controlled bass ──────────────
    "night": VoiceProfile(
        name="night",
        length_scale=1.06,
        noise_scale=0.32,
        noise_w=0.48,
        sentence_silence=0.20,
        eq_80_100_db=-3.0,          # Controlled bass for late night
        eq_120_160_db=-1.5,
        eq_200_250_db=0.0,
        eq_300_400_db=-1.0,
        eq_2k_4k_db=0.5,            # Clear intelligibility at low volume
        ambience_mix=0.0,           # Intimate dry audio
        stereo_spread=0.0,
        master_gain=0.68,           # Controlled soft listening volume
        limiter_ceiling=0.72,
        add_breath=False,
    ),

    # Aliases
    "standard": None,
    "witty": None,
    "alert": None,
}

# Link aliases
PROFILES["standard"] = PROFILES["normal"]

PROFILES["witty"] = VoiceProfile(
    name="witty",
    length_scale=1.06,
    noise_scale=0.36,
    noise_w=0.50,
    sentence_silence=0.18,
    eq_80_100_db=1.0,
    eq_120_160_db=2.0,
    eq_200_250_db=0.5,
    eq_300_400_db=-1.0,
    eq_2k_4k_db=0.8,
    ambience_mix=0.06,
    stereo_spread=0.10,
    master_gain=0.95,
    limiter_ceiling=0.95,
    add_breath=True,
)

PROFILES["alert"] = VoiceProfile(
    name="alert",
    length_scale=1.02,
    noise_scale=0.28,
    noise_w=0.45,
    sentence_silence=0.15,
    eq_80_100_db=0.0,
    eq_120_160_db=1.0,
    eq_200_250_db=0.0,
    eq_300_400_db=-1.0,
    eq_2k_4k_db=1.5,
    ambience_mix=0.02,
    stereo_spread=0.04,
    master_gain=0.98,
    limiter_ceiling=0.96,
    add_breath=False,
)


def get_profile(name: str = "cinematic") -> VoiceProfile:
    """Return profile by name or fallback to cinematic."""
    key = name.lower().strip()
    return PROFILES.get(key, PROFILES["cinematic"])
