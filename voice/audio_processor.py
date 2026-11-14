"""
J.A.R.V.I.S. — Cinematic Audio Processor (Supercharged Bass, Echo & Dynamic Surround)
Includes:
1. Sub-Octave Subwoofer Synthesizer: Genuine octave-down chest rumble underneath the voice.
2. Stereo Workshop Echo: Noticeable ping-pong slapback delay (130ms L / 195ms R) simulating Tony's Malibu lab.
3. Expanded 3D Surround Soundstage: Wide holographic stereo field.
4. Human Breath & Organic Pitch Warmth: Removes sterile robotic flatness.
"""

import numpy as np
from scipy.signal import butter, sosfilt
from typing import Tuple
from voice.voice_profiles import VoiceProfile


class AudioProcessor:
    def __init__(self):
        pass

    def _apply_cleanup(self, audio: np.ndarray, sr: int) -> np.ndarray:
        # Preserve sub-bass down to 40 Hz
        sos_hp = butter(2, 40.0, 'highpass', fs=sr, output='sos')
        out = sosfilt(sos_hp, audio)
        high_cut = min(7500.0, (sr / 2.0) - 100.0)
        sos_lp = butter(4, high_cut, 'lowpass', fs=sr, output='sos')
        return sosfilt(sos_lp, out)

    def _generate_subharmonic_rumble(self, audio: np.ndarray, sr: int, mix_gain: float = 0.40) -> np.ndarray:
        """
        Synthesizes an authentic SUBWOOFER chest rumble layer:
        1. Isolates vocal fundamentals (70-220 Hz).
        2. Generates an octave-down subharmonic via half-frequency zero-crossing divider.
        3. Low-passes strictly below 140 Hz so only the pure chest-thump reaches the speakers/subwoofer.
        """
        sos_fund = butter(2, [70.0, 220.0], 'bandpass', fs=sr, output='sos')
        fund = sosfilt(sos_fund, audio)

        # Non-linear quadratic envelope follower to extract deep pitch vibration
        analytic = np.abs(fund)
        sos_env = butter(2, 110.0, 'lowpass', fs=sr, output='sos')
        low_pulse = sosfilt(sos_env, analytic)

        # Flip alternating pulses to create true sub-octave fundamental (f/2)
        zero_crossings = np.where(np.diff(np.signbit(fund)))[0]
        sub_oct = np.zeros_like(fund)
        sign = 1.0
        last_idx = 0
        for z in zero_crossings:
            sub_oct[last_idx:z] = fund[last_idx:z] * sign
            sign = -sign
            last_idx = z
        sub_oct[last_idx:] = fund[last_idx:] * sign

        # Filter strictly to warm sub-bass (50-130 Hz)
        sos_sub = butter(3, [50.0, 135.0], 'bandpass', fs=sr, output='sos')
        clean_sub = sosfilt(sos_sub, sub_oct)

        # Add warmth saturation (tape saturation)
        saturated_sub = np.tanh(clean_sub * 2.5) * 1.2

        return saturated_sub * mix_gain

    def _apply_workshop_echo_and_surround(
        self, audio: np.ndarray, sr: int, echo_level: float = 0.22, spread: float = 0.45
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Stereo Workshop Echo & 3D Surround:
        - Noticeable slapback stereo echo (L: 135ms, R: 210ms) with decay.
        - High-frequency damping for realistic architectural glass/concrete acoustics.
        - Wide stereo field spread.
        """
        # Echo delays: Left 135 ms, Right 210 ms (asymmetric Stark workshop reflection)
        del_l = int(0.135 * sr)
        del_r = int(0.210 * sr)
        max_del = del_r + int(0.150 * sr)

        padded = np.pad(audio, (0, max_del))

        # First reflection tap
        tap_l1 = np.roll(padded, del_l) * 0.42
        tap_r1 = np.roll(padded, del_r) * 0.38

        # Second reflection tap (echo feedback)
        tap_l2 = np.roll(padded, int(del_l * 1.85)) * 0.20
        tap_r2 = np.roll(padded, int(del_r * 1.75)) * 0.16

        echo_l = tap_l1 + tap_l2
        echo_r = tap_r1 + tap_r2

        # Damping filter on echo so it's warm and cinematic, not harsh
        sos_echo_lp = butter(2, 3200.0, 'lowpass', fs=sr, output='sos')
        echo_l = sosfilt(sos_echo_lp, echo_l)
        echo_r = sosfilt(sos_echo_lp, echo_r)

        # Center direct voice
        direct_l = np.pad(audio, (0, max_del))
        direct_r = np.pad(audio, (0, max_del))

        # Mix dry + echo
        out_l = direct_l + (echo_l * echo_level)
        out_r = direct_r + (echo_r * echo_level)

        # Widen stereo soundstage
        stereo_diff = (out_l - out_r) * spread
        out_l = out_l + stereo_diff
        out_r = out_r - stereo_diff

        return out_l, out_r

    def generate_human_breath(self, sr: int, duration_sec: float = 0.20, intensity: float = 0.16) -> np.ndarray:
        """Organic human breath intake envelope before speech."""
        n_samples = int(duration_sec * sr)
        if n_samples <= 0:
            return np.zeros(0, dtype=np.float32)

        noise = np.random.normal(0, 1.0, n_samples).astype(np.float32)
        sos_breath = butter(2, [360.0, 1850.0], 'bandpass', fs=sr, output='sos')
        breath = sosfilt(sos_breath, noise)

        t = np.linspace(0, 1.0, n_samples, dtype=np.float32)
        envelope = (np.sin(np.pi * (t - 0.5)) + 1.0) / 2.0
        taper = int(0.02 * sr)
        if taper < n_samples:
            envelope[-taper:] *= np.linspace(1.0, 0.0, taper)

        return breath * envelope * intensity

    def generate_throat_clear(self, sr: int, duration_sec: float = 0.22, intensity: float = 0.14) -> np.ndarray:
        """Subtle, polite organic human throat-clear / gentle cough characteristic."""
        n_samples = int(duration_sec * sr)
        if n_samples <= 0:
            return np.zeros(0, dtype=np.float32)

        # Dual pulse representing vocal cord clearing
        noise = np.random.normal(0, 1.0, n_samples).astype(np.float32)
        sos_tc = butter(2, [280.0, 1200.0], 'bandpass', fs=sr, output='sos')
        filtered = sosfilt(sos_tc, noise)

        t = np.linspace(0, 1.0, n_samples, dtype=np.float32)
        # Double-bump envelope (hem... hem)
        env = (np.sin(2 * np.pi * t) ** 2) * np.exp(-3.5 * t)
        return filtered * env * intensity

    def master_limiter(self, signal: np.ndarray, ceiling: float = 0.96) -> np.ndarray:
        """Soft-knee limiter to prevent any distortion or clipping."""
        peak = np.max(np.abs(signal))
        if peak < 1e-5:
            return signal

        knee = 0.82 * ceiling
        out = signal.copy()
        mask = np.abs(out) > knee
        if np.any(mask):
            excess = np.abs(out[mask]) - knee
            scale = ceiling - knee
            compressed = knee + scale * np.tanh(excess / (scale + 1e-6))
            out[mask] = np.sign(out[mask]) * compressed

        return np.clip(out, -ceiling, ceiling)

    def process(
        self,
        raw_audio: np.ndarray,
        sr: int,
        profile: VoiceProfile
    ) -> Tuple[np.ndarray, int]:
        """
        Complete processing chain:
        1. Sub-octave subwoofer generator (heavy chest-thump bass)
        2. Multi-band warm EQ
        3. Human breath intake
        4. Malibu lab stereo echo + wide surround
        5. Anti-clipping limiter with zero volume fade
        """
        if raw_audio.dtype == np.int16:
            audio_f = raw_audio.astype(np.float32) / 32768.0
        else:
            audio_f = raw_audio.astype(np.float32)
            max_v = np.max(np.abs(audio_f))
            if max_v > 1.0:
                audio_f = audio_f / max_v

        # Clean DC and ultrasonic hash
        cleaned = self._apply_cleanup(audio_f, sr)

        # 1. HEAVY SUBWOOFER BASS (Sub-octave chest rumble)
        sub_rumble = self._generate_subharmonic_rumble(cleaned, sr, mix_gain=0.48)
        
        # 2. Warm low-mid EQ boost (+4dB at 110-180Hz)
        sos_warm = butter(2, [100.0, 190.0], 'bandpass', fs=sr, output='sos')
        warmth = sosfilt(sos_warm, cleaned) * 1.5

        # Sum core voice + subwoofer rumble + warmth
        bassy_voice = cleaned + sub_rumble + warmth

        # 3. Organic Human Breath / Polite Throat Clear intake at beginning
        if profile.add_breath:
            # 1 in 6 chance of polite human throat-clear, otherwise natural breath intake
            if np.random.rand() < 0.16:
                human_cue = self.generate_throat_clear(sr, duration_sec=0.22, intensity=0.14)
            else:
                human_cue = self.generate_human_breath(sr, duration_sec=0.20, intensity=0.16)
            cross = int(0.04 * sr)
            if len(bassy_voice) > cross:
                bassy_voice = np.concatenate([human_cue[:-cross], bassy_voice])

        # 4. Malibu workshop stereo echo & wide 3D surround
        echo_lvl = 0.26 if profile.name == "cinematic" else 0.14
        spread   = 0.48 if profile.name == "cinematic" else 0.28
        left_ch, right_ch = self._apply_workshop_echo_and_surround(
            bassy_voice, sr, echo_level=echo_lvl, spread=spread
        )

        # 5. Master gain and zero-distortion limiter
        left_master = self.master_limiter(left_ch * profile.master_gain, ceiling=profile.limiter_ceiling)
        right_master = self.master_limiter(right_ch * profile.master_gain, ceiling=profile.limiter_ceiling)

        # Convert to 16-bit PCM stereo
        pcm_l = (left_master * 32767.0).clip(-32768, 32767).astype(np.int16)
        pcm_r = (right_master * 32767.0).clip(-32768, 32767).astype(np.int16)

        stereo = np.column_stack((pcm_l, pcm_r))
        return stereo, sr
