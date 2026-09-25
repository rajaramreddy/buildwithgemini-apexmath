import numpy as np
import wave
import struct

def make_lofi_track(output_filename="lofi_track.wav", num_bars=28, bpm=86):
    sr = 44100
    beat_dur = 60.0 / bpm
    bar_dur = beat_dur * 4.0
    total_dur = bar_dur * num_bars
    total_samples = int(total_dur * sr)
    t = np.linspace(0, total_dur, total_samples, endpoint=False)

    # Chords (frequencies in Hz)
    # Progression: Dm9 -> G13 -> Cmaj9 -> Am9
    progression = [
        [146.83, 174.61, 220.00, 261.63, 329.63], # D3, F3, A3, C4, E4 (Dm9)
        [98.00, 174.61, 246.94, 329.63, 392.00],  # G2, F3, B3, E4, G4 (G13)
        [130.81, 164.81, 196.00, 246.94, 293.66], # C3, E3, G3, B3, D4 (Cmaj9)
        [110.00, 196.00, 261.63, 329.63, 493.88], # A2, G3, C4, E4, B4 (Am9)
    ]
    bass_roots = [73.42, 49.00, 65.41, 55.00] # D2, G1, C2, A1

    audio_left = np.zeros(total_samples)
    audio_right = np.zeros(total_samples)

    # 1. Warm Rhodes / Electric Piano Chords
    for bar_idx in range(num_bars):
        chord_idx = bar_idx % 4
        chord_freqs = progression[chord_idx]
        bar_start = int(bar_idx * bar_dur * sr)

        # Strumming pattern: play chord on beat 0 and beat 2
        for strum_beat in [0.0, 2.0]:
            strum_start = bar_start + int(strum_beat * beat_dur * sr)
            chord_len = int(beat_dur * 2.2 * sr)
            if strum_start + chord_len > total_samples:
                chord_len = total_samples - strum_start
            
            ct = np.linspace(0, chord_len / sr, chord_len, endpoint=False)
            env = np.exp(-ct * 1.8) * (1.0 - np.exp(-ct * 80.0))
            
            # Subtle tremolo LFO (4.5 Hz)
            lfo = 1.0 + 0.15 * np.sin(2 * np.pi * 4.5 * ct)

            chord_sig = np.zeros(chord_len)
            for f in chord_freqs:
                # Add fundamental + gentle 2nd harmonic + slight detune for stereo width
                chord_sig += 0.5 * np.sin(2 * np.pi * f * ct)
                chord_sig += 0.2 * np.sin(2 * np.pi * (f * 2) * ct)
                chord_sig += 0.1 * np.sin(2 * np.pi * (f * 3) * ct)

            audio_left[strum_start:strum_start + chord_len] += chord_sig * env * lfo * 0.22
            audio_right[strum_start:strum_start + chord_len] += chord_sig * env * (2.0 - lfo) * 0.22

    # 2. Warm Sub Bass
    for bar_idx in range(num_bars):
        root = bass_roots[bar_idx % 4]
        bar_start = int(bar_idx * bar_dur * sr)
        # Upbeat bass pattern: hit on 0, 1.75, 2.5
        for b_beat, b_len_beats in [(0.0, 1.5), (1.75, 0.6), (2.5, 1.3)]:
            b_start = bar_start + int(b_beat * beat_dur * sr)
            b_samples = int(b_len_beats * beat_dur * sr)
            if b_start + b_samples > total_samples:
                b_samples = total_samples - b_start
            bt = np.linspace(0, b_samples / sr, b_samples, endpoint=False)
            b_env = np.exp(-bt * 2.0) * (1.0 - np.exp(-bt * 60.0))
            b_sig = np.sin(2 * np.pi * root * bt) + 0.3 * np.sin(2 * np.pi * (root * 2) * bt)
            b_sig = np.tanh(b_sig * 1.2) * 0.35 * b_env
            audio_left[b_start:b_start + b_samples] += b_sig
            audio_right[b_start:b_start + b_samples] += b_sig

    # 3. Drums: Kick, Snare, Hi-Hat (Boom-Bap Upbeat Lo-Fi)
    for bar_idx in range(num_bars):
        bar_start = int(bar_idx * bar_dur * sr)

        # Kick drum hits: beat 0 and beat 2.5
        for k_beat in [0.0, 2.5]:
            k_start = bar_start + int(k_beat * beat_dur * sr)
            k_len = int(0.35 * sr)
            if k_start + k_len > total_samples:
                k_len = total_samples - k_start
            kt = np.linspace(0, k_len / sr, k_len, endpoint=False)
            k_freq = 140.0 * np.exp(-kt * 28.0) + 42.0
            k_phase = 2 * np.pi * np.cumsum(k_freq) / sr
            k_sig = np.sin(k_phase) * np.exp(-kt * 12.0) * 0.45
            audio_left[k_start:k_start + k_len] += k_sig
            audio_right[k_start:k_start + k_len] += k_sig

        # Snare hits: beat 1.0 and beat 3.0 (2 and 4 in 4/4)
        for s_beat in [1.0, 3.0]:
            s_start = bar_start + int(s_beat * beat_dur * sr)
            s_len = int(0.22 * sr)
            if s_start + s_len > total_samples:
                s_len = total_samples - s_start
            st = np.linspace(0, s_len / sr, s_len, endpoint=False)
            tone = np.sin(2 * np.pi * 185.0 * st) * np.exp(-st * 25.0) * 0.25
            noise = (np.random.rand(s_len) * 2 - 1) * np.exp(-st * 18.0) * 0.3
            s_sig = tone + noise
            audio_left[s_start:s_start + s_len] += s_sig
            audio_right[s_start:s_start + s_len] += s_sig

        # Hi-Hats: 8th notes with lo-fi swing
        for hat_idx in range(8):
            h_beat = hat_idx * 0.5 + (0.04 if hat_idx % 2 == 1 else 0.0) # swing
            h_start = bar_start + int(h_beat * beat_dur * sr)
            h_len = int(0.06 * sr)
            if h_start + h_len > total_samples:
                h_len = total_samples - h_start
            ht = np.linspace(0, h_len / sr, h_len, endpoint=False)
            h_vel = 0.18 if hat_idx % 2 == 1 else 0.12 # upbeat accent
            h_noise = (np.random.rand(h_len) * 2 - 1) * np.exp(-ht * 65.0) * h_vel
            audio_left[h_start:h_start + h_len] += h_noise * 0.9
            audio_right[h_start:h_start + h_len] += h_noise * 1.1

    # 4. Lo-Fi Vinyl Crackle & Ambient Warmth
    vinyl = (np.random.normal(0, 0.015, total_samples))
    pop_indices = np.random.choice(total_samples, size=int(total_dur * 12), replace=False)
    vinyl[pop_indices] += np.random.uniform(-0.08, 0.08, size=len(pop_indices))
    audio_left += vinyl * 0.5
    audio_right += vinyl * 0.5

    # 5. Master Limiting and Fade Out
    fade_len = int(3.0 * sr)
    fade = np.ones(total_samples)
    fade[-fade_len:] = np.linspace(1.0, 0.0, fade_len)
    audio_left *= fade
    audio_right *= fade

    # Normalize gently
    max_val = max(np.max(np.abs(audio_left)), np.max(np.abs(audio_right)), 1e-6)
    audio_left = (audio_left / max_val) * 0.82
    audio_right = (audio_right / max_val) * 0.82

    # Write WAV file
    with wave.open(output_filename, "w") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2) # 16-bit
        wav.setframerate(sr)
        
        left_int = (audio_left * 32767).astype(np.int16)
        right_int = (audio_right * 32767).astype(np.int16)
        interleaved = np.empty((total_samples * 2,), dtype=np.int16)
        interleaved[0::2] = left_int
        interleaved[1::2] = right_int
        wav.writeframes(interleaved.tobytes())

    print(f"Generated {output_filename} ({total_dur:.1f}s, 44.1kHz stereo)")

if __name__ == "__main__":
    make_lofi_track("/config/Desktop/BuildWithGemini/lofi_beat.wav", num_bars=28, bpm=86)
