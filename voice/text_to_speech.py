"""
J.A.R.V.I.S. — Text-to-Speech Engine
Executes sequential sentence synthesis using the Vishal Rao Piper JARVIS High model,
integrating Speech Director, Audio Processor, and Audio Cache.
"""

import os
import sys
import subprocess
import tempfile
import numpy as np
from scipy.io import wavfile
from typing import Optional, List, Tuple

from voice.voice_profiles import VoiceProfile, get_profile
from voice.speech_director import SpeechDirector
from voice.audio_processor import AudioProcessor
from voice.audio_cache import AudioCache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPER_EXE = os.path.join(ROOT, "assets", "piper", "piper", "piper.exe")
PIPER_DIR = os.path.join(ROOT, "assets", "piper", "piper")
MODEL_PATH = os.path.join(ROOT, "voice", "models", "jarvis", "en_GB-jarvis-high.onnx")
CONFIG_PATH = os.path.join(ROOT, "voice", "models", "jarvis", "en_GB-jarvis-high.onnx.json")


class JarvisTTS:
    def __init__(self, use_cache: bool = True):
        self.director = SpeechDirector()
        self.processor = AudioProcessor()
        self.cache = AudioCache() if use_cache else None

        if not os.path.isfile(PIPER_EXE):
            raise FileNotFoundError(f"Piper executable missing at {PIPER_EXE}")
        if not os.path.isfile(MODEL_PATH):
            raise FileNotFoundError(f"Vishal Rao Piper JARVIS model missing at {MODEL_PATH}")

    def _synthesize_single_phrase(self, text: str, profile: VoiceProfile) -> Tuple[np.ndarray, int]:
        """
        Runs standalone Piper binary for one phrase with the profile's acoustic parameters.
        Returns (mono_audio_array, sample_rate).
        """
        temp_wav = os.path.join(tempfile.gettempdir(), f"piper_tmp_{os.getpid()}_{np.random.randint(10000, 99999)}.wav")

        cmd = [
            PIPER_EXE,
            "--model", MODEL_PATH,
            "--config", CONFIG_PATH,
            "--output_file", temp_wav,
            "--length_scale", str(profile.length_scale),
            "--noise_scale", str(profile.noise_scale),
            "--noise_w", str(profile.noise_w),
            "--sentence_silence", str(profile.sentence_silence)
        ]

        # Start process with text on stdin — CREATE_NO_WINDOW prevents CMD flash on Windows
        _flags = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW
        psi = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=PIPER_DIR,
            creationflags=_flags,
        )
        _, stderr_data = psi.communicate(input=text.encode("utf-8"))

        if psi.returncode != 0 or not os.path.isfile(temp_wav):
            err_msg = stderr_data.decode("utf-8", errors="replace")
            raise RuntimeError(f"Piper synthesis failed (exit code {psi.returncode}): {err_msg}")

        # Read wav data
        sr, data = wavfile.read(temp_wav)

        # Immediate cleanup of temporary buffer file
        try:
            os.remove(temp_wav)
        except OSError:
            pass

        return data, sr

    def synthesize(
        self,
        text: str,
        style: Optional[str] = None,
        output_file: Optional[str] = None,
        apply_effects: bool = True
    ) -> str:
        """
        Directs, sequentially synthesizes, applies surround & EQ, and returns output WAV file path.
        """
        sentences, profile = self.director.direct(text, style)

        # Check cache if whole text matches
        if self.cache and not output_file and self.cache.has(text, profile.name):
            return self.cache.get_path(text, profile.name)

        # Single-pass synthesis: eliminates repeated subprocess spawn latency.
        # Piper natively parses punctuation breaks and applies sentence silence in a single pass.
        combined_mono, sample_rate = self._synthesize_single_phrase(text, profile)

        # Smooth 4ms micro fade-in/out to prevent boundary clicks
        fade_len = int(0.004 * sample_rate)
        if len(combined_mono) > fade_len * 2:
            chunk_f = combined_mono.astype(np.float32)
            f_in = np.linspace(0.0, 1.0, fade_len)
            f_out = np.linspace(1.0, 0.0, fade_len)
            chunk_f[:fade_len] *= f_in
            chunk_f[-fade_len:] *= f_out
            combined_mono = chunk_f.astype(combined_mono.dtype)

        # Audio processing (EQ, subtle surround ambience, limiter)
        if apply_effects:
            processed_audio, out_sr = self.processor.process(combined_mono, sample_rate, profile)
        else:
            # Raw output
            processed_audio = combined_mono
            out_sr = sample_rate

        # Determine target file path
        if not output_file:
            temp_out = os.path.join(tempfile.gettempdir(), f"jarvis_speech_{np.random.randint(1000, 9999)}.wav")
            out_path = temp_out
        else:
            out_path = output_file
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

        wavfile.write(out_path, out_sr, processed_audio)

        # Cache if appropriate
        if self.cache and not output_file:
            out_path = self.cache.put(text, profile.name, out_path)

        # Release memory buffers explicitly
        del combined_mono

        return out_path

    def stop_playback(self):
        """Immediately halts active audio output (Barge-in)."""
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass

    def play(self, wav_path: str):
        """
        Play stereo audio at full, uncompromised volume without Windows Media Player ducking.
        Uses sounddevice for bit-perfect output with zero volume drops.
        """
        if not os.path.isfile(wav_path):
            return

        try:
            import sounddevice as sd
            sr, data = wavfile.read(wav_path)
            sd.play(data, sr)
            sd.wait()
            return
        except Exception:
            pass

        # Fallback to PowerShell SoundPlayer without media player ducking
        ps_cmd = (
            f"$player = New-Object System.Media.SoundPlayer '{wav_path}'; "
            f"$player.PlaySync()"
        )
        subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)

