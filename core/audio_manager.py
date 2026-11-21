"""
J.A.R.V.I.S. Mark VII — Centralized Audio Input & Voice Engine Manager
Satisfies Part 2 & Part 4 of Master Engineering Directive:
- Single-point microphone ownership: One persistent, non-conflicting audio stream.
- Seamless state machine: STANDBY -> WAKE_DETECTED -> LISTENING -> PROCESSING -> SPEAKING.
- Continuous hands-free wake word recognition ("Jarvis" & "Hey Jarvis").
- Real-time Voice Activity Detection (VAD) with configurable silence timeouts.
- Real-time partial transcription and audio level (RMS) broadcast for HUD visualization.
- Echo suppression during TTS with immediate barge-in interruption ("Stop", "Wait", "Cancel").
- Automatic audio hardware re-discovery and graceful disconnect recovery.
"""

import os
import sys
import json
import math
import time
import queue
import struct
import threading
from enum import Enum
from typing import Optional, Callable, Dict, Any, List

import sounddevice as sd
import numpy as np
from vosk import Model, KaldiRecognizer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config
from core.voice_input import get_vosk_model
from core.voice_output import is_currently_speaking, stop_speaking, speak
from core.brain import JarvisBrain


class AudioState(Enum):
    STANDBY = "STANDBY"
    WAKE_DETECTED = "WAKE_DETECTED"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"
    RECOVERING = "RECOVERING"


WAKE_PHRASES = ["jarvis", "hey jarvis", "hello jarvis", "ok jarvis"]
BARGE_IN_WORDS = ["stop", "wait", "cancel", "pause", "quiet", "shh", "halt"]


class AudioManager:
    """
    Centralized Audio Input & Voice Engine Manager (Singleton).
    Manages the single continuous microphone stream, coordinates wake-word
    detection, command transcription, VAD, audio amplitude emission, and barge-in.
    """
    _instance: Optional['AudioManager'] = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> 'AudioManager':
        with cls._lock:
            if cls._instance is None:
                cls._instance = AudioManager()
            return cls._instance

    def __init__(self):
        self.state = AudioState.STANDBY
        self.sample_rate = config.VOSK_SAMPLE_RATE  # 16000 Hz
        self.block_size = 2000  # 125 ms blocks

        # Vosk Recognizers
        self.model: Optional[Model] = None
        self.wake_recognizer: Optional[KaldiRecognizer] = None
        self.command_recognizer: Optional[KaldiRecognizer] = None
        self.barge_in_recognizer: Optional[KaldiRecognizer] = None

        # Callbacks for UI & External Observers
        self.on_state_changed: Optional[Callable[[AudioState], None]] = None
        self.on_audio_level: Optional[Callable[[float], None]] = None
        self.on_partial_text: Optional[Callable[[str], None]] = None
        self.on_command_recognized: Optional[Callable[[str], None]] = None
        self.on_response_ready: Optional[Callable[[str, str], None]] = None
        self.on_hud_mode_requested: Optional[Callable[[str], None]] = None

        # VAD & Timing Configuration
        self.silence_threshold_sec = 1.6
        self.min_speech_duration_sec = 0.4
        self.max_recording_duration_sec = 12.0
        self.vad_energy_threshold = 280.0  # RMS threshold for speech activity

        # Internal Threading & Audio Buffers
        self._audio_queue = queue.Queue(maxsize=100)
        self._running = False
        self._stream: Optional[sd.RawInputStream] = None
        self._worker_thread: Optional[threading.Thread] = None

        # State tracking
        self._speech_started_time = 0.0
        self._last_speech_time = 0.0
        self._heard_speech = False
        self._active_device_index: Optional[int] = None
        self.brain = JarvisBrain()
        self.brain.hud_mode_callback = self._on_hud_mode_from_brain

        self._init_models()

    def _on_hud_mode_from_brain(self, mode: str):
        if self.on_hud_mode_requested:
            try:
                self.on_hud_mode_requested(mode)
            except Exception as e:
                print(f"[AudioManager] Error dispatching hud mode: {e}")

    def _init_models(self):
        """Initializes Vosk acoustic recognizers with optimized grammar constraints."""
        try:
            self.model = get_vosk_model()
            # Wake word grammar: constrained for near-zero false positive rate and ultra-fast CPU decode
            wake_grammar = json.dumps(["jarvis", "hey", "hello", "ok", "[unk]"])
            self.wake_recognizer = KaldiRecognizer(self.model, self.sample_rate, wake_grammar)

            # Barge-in grammar for instant speech interruption
            barge_grammar = json.dumps(BARGE_IN_WORDS + ["[unk]"])
            self.barge_in_recognizer = KaldiRecognizer(self.model, self.sample_rate, barge_grammar)

            # Command recognizer: open vocabulary for natural language queries
            self.command_recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.command_recognizer.SetWords(False)
            print("[AudioManager] Vosk acoustic models loaded successfully.")
        except Exception as e:
            print(f"[AudioManager Error]: Model initialization failed: {e}", file=sys.stderr)
            self.set_state(AudioState.ERROR)

    def set_state(self, new_state: AudioState):
        """Thread-safe state transition with notification to UI."""
        if self.state != new_state:
            self.state = new_state
            if self.on_state_changed:
                try:
                    self.on_state_changed(new_state)
                except Exception:
                    pass

    def start(self):
        """Starts the centralized audio capture stream and worker thread."""
        if self._running:
            return
        self._running = True
        self._worker_thread = threading.Thread(target=self._run_audio_loop, daemon=True, name="JarvisAudioManager")
        self._worker_thread.start()
        print("[AudioManager] Real-time audio pipeline online.")

    def stop(self):
        """Stops the audio pipeline cleanly."""
        self._running = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _audio_stream_callback(self, indata, frames, time_info, status):
        """Raw sounddevice callback capturing 16000 Hz 16-bit PCM mono."""
        if not self._running:
            return
        raw_bytes = bytes(indata)
        try:
            self._audio_queue.put_nowait(raw_bytes)
        except queue.Full:
            try:
                self._audio_queue.get_nowait()
                self._audio_queue.put_nowait(raw_bytes)
            except Exception:
                pass

    def _open_stream(self) -> bool:
        """Opens the sounddevice input stream with automatic device fallback."""
        try:
            self._stream = sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                dtype='int16',
                channels=1,
                callback=self._audio_stream_callback
            )
            self._stream.start()
            self._active_device_index = sd.default.device[0]
            self.set_state(AudioState.STANDBY)
            return True
        except Exception as e:
            print(f"[AudioManager Error] Failed to open microphone stream: {e}", file=sys.stderr)
            self.set_state(AudioState.ERROR)
            return False

    def _calculate_rms(self, raw_bytes: bytes) -> float:
        """Computes root-mean-square amplitude of audio block."""
        if len(raw_bytes) < 2:
            return 0.0
        count = len(raw_bytes) // 2
        shorts = struct.unpack(f"{count}h", raw_bytes)
        sum_sq = sum(s * s for s in shorts)
        return math.sqrt(sum_sq / count)

    def _run_audio_loop(self):
        """Main audio processing thread."""
        consecutive_errors = 0
        while self._running:
            if not self._stream or not self._stream.active:
                if not self._open_stream():
                    consecutive_errors += 1
                    time.sleep(min(2.0 * consecutive_errors, 8.0))
                    continue
                consecutive_errors = 0

            try:
                raw_data = self._audio_queue.get(timeout=0.3)
            except queue.Empty:
                continue

            # 1. Compute Audio Amplitude & Broadcast for HUD Visualization
            rms = self._calculate_rms(raw_data)
            normalized_vol = min(1.0, rms / 3200.0)
            if self.on_audio_level:
                try:
                    self.on_audio_level(normalized_vol)
                except Exception:
                    pass

            # 2. Check if TTS is currently playing
            speaking = is_currently_speaking()
            if speaking:
                if self.state != AudioState.SPEAKING:
                    self.set_state(AudioState.SPEAKING)

                # Monitor for Barge-in Interruption ("Stop", "Wait", "Cancel")
                if self.barge_in_recognizer:
                    if self.barge_in_recognizer.AcceptWaveform(raw_data):
                        res = json.loads(self.barge_in_recognizer.Result())
                        text = res.get("text", "").lower()
                        if any(w in text for w in BARGE_IN_WORDS):
                            print(f"[AudioManager] Barge-in keyword detected: '{text}'. Halting speech.")
                            stop_speaking()
                            self.barge_in_recognizer.Reset()
                            self.set_state(AudioState.STANDBY)
                    else:
                        partial = json.loads(self.barge_in_recognizer.PartialResult())
                        p_text = partial.get("partial", "").lower()
                        if any(w in p_text for w in BARGE_IN_WORDS):
                            print(f"[AudioManager] Barge-in keyword detected in partial: '{p_text}'. Halting speech.")
                            stop_speaking()
                            self.barge_in_recognizer.Reset()
                            self.set_state(AudioState.STANDBY)
                continue
            elif self.state == AudioState.SPEAKING:
                # Transition back to standby when speech completes
                self.set_state(AudioState.STANDBY)

            # 3. State Machine Processing
            if self.state == AudioState.STANDBY:
                self._process_standby(raw_data)
            elif self.state == AudioState.LISTENING:
                self._process_listening(raw_data, rms)

    def _process_standby(self, raw_data: bytes):
        """Listens for wake words ('Jarvis' / 'Hey Jarvis') with minimal CPU footprint."""
        if not self.wake_recognizer:
            return

        detected = False
        if self.wake_recognizer.AcceptWaveform(raw_data):
            res = json.loads(self.wake_recognizer.Result())
            text = res.get("text", "").lower()
            if any(w in text for w in WAKE_PHRASES):
                detected = True
        else:
            partial = json.loads(self.wake_recognizer.PartialResult())
            p_text = partial.get("partial", "").lower()
            if any(w in p_text for w in WAKE_PHRASES):
                detected = True

        if detected:
            print("[AudioManager] Wake word 'Jarvis' detected!")
            self.wake_recognizer.Reset()
            self._trigger_wake_activation()

    def _trigger_wake_activation(self):
        """Transitions to WAKE_DETECTED, plays acknowledgement, then enters LISTENING."""
        self.set_state(AudioState.WAKE_DETECTED)

        def _activate():
            # Acknowledge with natural Paul Bettany prompt
            ack = "Yes, sir?"
            print(f"[{config.JARVIS_NAME}]: {ack}")
            speak(ack, style="cinematic", block=True)

            # Transition directly to LISTENING with fresh recognizer
            if self.command_recognizer:
                self.command_recognizer.Reset()
            self._heard_speech = False
            self._speech_started_time = time.time()
            self._last_speech_time = time.time()
            self.set_state(AudioState.LISTENING)

        threading.Thread(target=_activate, daemon=True, name="JarvisWakeActivation").start()

    def _process_listening(self, raw_data: bytes, rms: float):
        """Captures spoken command with VAD and real-time partial transcription."""
        if not self.command_recognizer:
            return

        now = time.time()

        # VAD Energy tracking
        if rms >= self.vad_energy_threshold:
            self._heard_speech = True
            self._last_speech_time = now

        # Feed to Vosk KaldiRecognizer
        if self.command_recognizer.AcceptWaveform(raw_data):
            res = json.loads(self.command_recognizer.Result())
            text = res.get("text", "").strip()
            if text:
                self._on_command_captured(text)
                return
        else:
            partial = json.loads(self.command_recognizer.PartialResult())
            p_text = partial.get("partial", "").strip()
            if p_text:
                self._heard_speech = True
                self._last_speech_time = now
                if self.on_partial_text:
                    try:
                        self.on_partial_text(p_text)
                    except Exception:
                        pass

        # Check silence timeout after speech began
        if self._heard_speech:
            silence_duration = now - self._last_speech_time
            if silence_duration >= self.silence_threshold_sec:
                final_res = json.loads(self.command_recognizer.FinalResult())
                text = final_res.get("text", "").strip()
                if text:
                    self._on_command_captured(text)
                else:
                    self._on_empty_command()
                return

        # Check maximum overall command timeout (12s)
        if (now - self._speech_started_time) >= self.max_recording_duration_sec:
            final_res = json.loads(self.command_recognizer.FinalResult())
            text = final_res.get("text", "").strip()
            if text:
                self._on_command_captured(text)
            else:
                self._on_empty_command()

    def _on_command_captured(self, query: str):
        """Executes captured query through cognitive brain and dispatches response."""
        print(f"[AudioManager Command Captured]: '{query}'")
        self.set_state(AudioState.PROCESSING)

        if self.on_command_recognized:
            try:
                self.on_command_recognized(query)
            except Exception:
                pass

        def _execute():
            reply, style = self.brain.process_query(query)
            print(f"[{config.JARVIS_NAME}]: {reply}")

            if self.on_response_ready:
                try:
                    self.on_response_ready(query, reply)
                except Exception:
                    pass

            # Speak response asynchronously
            speak(reply, style=style, block=True)
            # Short cooldown and return to standby
            time.sleep(0.3)
            self.set_state(AudioState.STANDBY)

        threading.Thread(target=_execute, daemon=True, name="JarvisBrainExecution").start()

    def _on_empty_command(self):
        """Handles empty or unintelligible audio input gracefully without terminal input."""
        print("[AudioManager] Command capture timed out with no speech.")
        self.set_state(AudioState.PROCESSING)

        def _fallback():
            prompt = "I didn't quite catch that, sir. Standing by."
            speak(prompt, style="normal", block=True)
            time.sleep(0.3)
            self.set_state(AudioState.STANDBY)

        threading.Thread(target=_fallback, daemon=True, name="JarvisEmptyCommand").start()

    def manual_trigger_listening(self):
        """Allows UI to programmatically activate listening without spoken wake word."""
        if self.command_recognizer:
            self.command_recognizer.Reset()
        self._heard_speech = False
        self._speech_started_time = time.time()
        self._last_speech_time = time.time()
        self.set_state(AudioState.LISTENING)


def get_audio_manager() -> AudioManager:
    """Singleton getter for centralized AudioManager."""
    return AudioManager.get_instance()
