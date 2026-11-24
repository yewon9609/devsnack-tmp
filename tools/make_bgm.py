#!/usr/bin/env python3
"""Original 8-bit (chiptune) background music, generated from code, so there is no licensing issue.
Usage: python3 tools/make_bgm.py OUT.wav SECONDS [SEED]
SEED (e.g. the date 20261123) picks the progression, tempo and melody so each day sounds a little different."""
import random, sys, wave
import numpy as np

SR = 44100
out, secs = sys.argv[1], float(sys.argv[2])
rng = random.Random(sys.argv[3] if len(sys.argv) > 3 else 'devsnack')

# chord roots as semitones from C, simple pop progressions (major key)
PROGS = [[0, 7, 9, 5], [0, 9, 5, 7], [9, 5, 0, 7], [0, 5, 9, 7], [5, 7, 0, 9]]
prog = rng.choice(PROGS)
bpm = rng.choice([100, 104, 108, 112, 116])
key = rng.choice([0, 2, -3, 5])          # transpose: C, D, A(low), F
beat = 60 / bpm
step = beat / 2                           # 8th notes
SCALE = [0, 2, 4, 5, 7, 9, 11]


def hz(semi):  # semitones from C4
    return 261.63 * 2 ** ((semi + key) / 12)


def tone(freq, dur, kind, vol):
    n = int(SR * dur)
    t = np.arange(n) / SR
    ph = (freq * t) % 1.0
    if kind == 'square':
        w = np.where(ph < 0.25, 1.0, -1.0)          # 25% pulse = classic NES lead
    elif kind == 'tri':
        w = 4 * np.abs(ph - 0.5) - 1
    else:
        w = np.where(ph < 0.5, 1.0, -1.0)
    env = np.minimum(1, t / 0.005) * np.exp(-t * (3 if kind == 'tri' else 6))
    return w * env * vol


def noise(dur, vol):
    n = int(SR * dur)
    env = np.exp(-np.arange(n) / SR * 60)
    return np.random.default_rng(rng.randint(0, 9999)).uniform(-1, 1, n) * env * vol


total = int(SR * secs)
mix = np.zeros(total + SR)


def put(sig, at):
    i = int(at * SR)
    if i >= len(mix): return
    sig = sig[: len(mix) - i]
    mix[i:i + len(sig)] += sig


# one 4-bar motif reused with small variations -> catchy, not random noise
motif = []
for bar in range(4):
    for s in range(8):
        if rng.random() < 0.7:
            motif.append((bar, s, rng.choice([0, 2, 4, 2, 4, 7]), rng.choice([1, 1, 2])))

t0, bar_len = 0.0, step * 8
bars = int(secs / bar_len) + 1
for b in range(bars):
    root = prog[b % 4]
    chord = [root, root + 4 if root in (0, 5, 7) else root + 3, root + 7]
    start = b * bar_len
    section = (b // 8) % 2                  # A / B sections every 8 bars
    # bass: root on beats, octave bounce
    for s in range(8):
        put(tone(hz(root - 24 + (12 if s % 2 else 0)), step * 0.9, 'tri', 0.28), start + s * step)
    # arpeggio
    for s in range(8):
        put(tone(hz(chord[s % 3] + 12), step * 0.5, 'pulse', 0.06), start + s * step)
    # lead melody (rests in the first 2 bars as an intro)
    if b >= 2:
        for (mb, s, deg, ln) in motif:
            if mb == b % 4:
                semi = root + SCALE[(deg + (2 if section else 0)) % 7] + 12
                put(tone(hz(semi), step * ln * 0.95, 'square', 0.11), start + s * step)
    # drums: hi-hat every 8th, "snare" noise on 2 and 4
    for s in range(8):
        put(noise(0.03, 0.05), start + s * step)
        if s in (2, 6):
            put(noise(0.12, 0.12), start + s * step)

mix = mix[:total]
fade = int(SR * 1.5)
mix[:int(SR * 0.3)] *= np.linspace(0, 1, int(SR * 0.3))
mix[-fade:] *= np.linspace(1, 0, fade)
mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.5     # leave headroom; the reel sits at a calm level
pcm = (mix * 32767).astype('<i2')
with wave.open(out, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print(out, f'{bpm}bpm', 'prog', prog)
