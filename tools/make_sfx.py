#!/usr/bin/env python3
"""8-bit sound effects timeline for a story reel (make_story_reel.py JSON).
Usage: python3 tools/make_sfx.py story.json out_sfx.wav
Writes a mono 44.1kHz wav the length of the reel with SFX placed on scene/widget/subtitle events.
"""
import json, sys, wave, struct, math, random

SR = 44100
FPS = 30


def sq(f, t):
    return 1.0 if (t * f) % 1 < 0.5 else -1.0


def tone(freqs, dur, vol=0.5, wave_='sq', decay=6.0):
    """freqs: list of (start_frac, freq) steps or a single float; returns samples."""
    n = int(dur * SR); out = []
    if isinstance(freqs, (int, float)):
        freqs = [(0, freqs)]
    for i in range(n):
        t = i / SR; frac = i / n
        f = [fq for st, fq in freqs if st <= frac][-1]
        v = sq(f, t) if wave_ == 'sq' else math.sin(2 * math.pi * f * t)
        env = math.exp(-decay * t) * min(1, i / 60) * min(1, (n - i) / 200)
        out.append(v * env * vol)
    return out


def sweep(f0, f1, dur, vol=0.4, wave_='sq'):
    n = int(dur * SR); out = []; ph = 0
    for i in range(n):
        f = f0 + (f1 - f0) * i / n; ph += f / SR
        v = (1 if ph % 1 < .5 else -1) if wave_ == 'sq' else math.sin(2 * math.pi * ph)
        out.append(v * vol * min(1, i / 60) * min(1, (n - i) / 300))
    return out


def noise(dur, vol=0.3, lp=0.15, decay=8):
    random.seed(1); n = int(dur * SR); out = []; y = 0
    for i in range(n):
        y += lp * (random.uniform(-1, 1) - y)
        out.append(y * vol * 3 * math.exp(-decay * i / SR) * min(1, (n - i) / 300))
    return out


SFX = {
    'pop': lambda: tone([(0, 660), (.4, 990)], .08, .28),
    'blip': lambda: tone(1320, .06, .22, decay=20),
    'pass': lambda: tone([(0, 880), (.5, 1320)], .1, .22),
    'coin': lambda: tone([(0, 988), (.3, 1319)], .22, .3, decay=9),
    'powerup': lambda: sum_([tone([(0, 523), (.2, 659), (.4, 784), (.6, 1047), (.8, 1319)], .42, .3, decay=2.5)]),
    'whoosh': lambda: noise(.22, .35, .35, 9),
    'step': lambda: noise(.05, .25, .08, 40),
    'stop': lambda: tone([(0, 220), (.5, 165)], .25, .35, decay=4),
    'rumble': lambda: noise(.9, .45, .04, 2.5),
    'fanfare': lambda: tone([(0, 523), (.15, 659), (.3, 784), (.5, 1047), (.7, 784), (.82, 1047)], .9, .3, decay=1.6),
    'bubble': lambda: sweep(500, 900, .07, .22, 'sin'),
    'check': lambda: tone([(0, 784), (.33, 988), (.66, 1319)], .3, .25, decay=4),
    'rise': lambda: sweep(300, 1200, .9, .12, 'sin'),
}
for _k, _r in enumerate([1.0, 1.12, 1.26, 1.5]):
    SFX[f'powerup{_k}'] = (lambda r: lambda: tone([(0, 523 * r), (.25, 659 * r), (.5, 784 * r), (.75, 1047 * r)], .32, .3, decay=3))(_r)
for _k, _r in enumerate([1.0, 1.2, 1.4]):
    SFX[f'bubble{_k}'] = (lambda r: lambda: sweep(500 * r, 900 * r, .07, .22, 'sin'))(_r)



# ---- NES-style (original patterns, not copied from any game) ----
def pulse(notes, step, vol=0.3, duty=0.25, tail=0.0, decay=0.0, tri=False):
    """notes: list of freqs (0 = rest), each lasting `step` seconds; NES-ish pulse/triangle."""
    out = []; ph = 0.0
    for j, f in enumerate(notes):
        n = int(step * SR) + (int(tail * SR) if j == len(notes) - 1 else 0)
        for i in range(n):
            if f <= 0:
                out.append(0.0); continue
            ph += f / SR; x = ph % 1
            v = (4 * abs(x - .5) - 1) if tri else (1.0 if x < duty else -1.0)
            env = math.exp(-decay * i / SR) if decay else 1.0
            out.append(v * vol * env * min(1, i / 40) * min(1, (n - i) / 120))
    return out


def slide(f0, f1, dur, vol=0.28, duty=0.25, expo=True):
    n = int(dur * SR); out = []; ph = 0.0
    for i in range(n):
        r = i / n; f = f0 * (f1 / f0) ** r if expo else f0 + (f1 - f0) * r
        ph += f / SR
        out.append((1.0 if ph % 1 < duty else -1.0) * vol * min(1, i / 40) * min(1, (n - i) / 200))
    return out


def mix(*parts):
    n = max(len(p) for p in parts); out = [0.0] * n
    for p in parts:
        for i, v in enumerate(p):
            out[i] += v
    return out


def hz(semi):
    return 440 * 2 ** ((semi - 9) / 12) * 2  # semi 0 = C5


NES = {
    'jump': lambda: slide(260, 820, .16, .22),
    'bump': lambda: mix(pulse([hz(-24), hz(-29)], .06, .3, .5), noise(.12, .3, .3, 25)),
    'twinkle': lambda: pulse([hz(7), hz(12), hz(16), hz(19), hz(24)], .045, .2, .125, tail=.12, decay=3),
    'scale': lambda: pulse([hz(x) for x in (0, 2, 4, 5, 7, 9, 11, 12)], .05, .18, .25),
    'blipA': lambda: slide(700, 1100, .05, .18, .5),
    'blipB': lambda: slide(800, 1300, .05, .18, .5),
    'blipC': lambda: slide(900, 1500, .05, .18, .5),
    'door': lambda: mix(pulse([hz(-12), hz(-17), hz(-12), hz(-17), hz(-22)], .07, .22, .5), noise(.4, .25, .05, 5)),
    'victory': lambda: mix(pulse([hz(x) for x in (0, 4, 7, 12, 0, 16, 19, 24)], .09, .24, .25, tail=.35, decay=0),
                           pulse([hz(x - 24) for x in (0, 0, 7, 7, 5, 5, 0, 0)], .09, .26, tri=True, tail=.35)),
}
for _k, _root in enumerate([0, 2, 4, 7]):
    NES[f'item{_k}'] = (lambda r: lambda: mix(pulse([hz(r + x) for x in (0, 4, 7, 12, 16, 19, 24)], .045, .22, .25, tail=.15, decay=2),
                                               pulse([hz(r + x - 24) for x in (0, 0, 7, 7, 12, 12, 12)], .045, .22, tri=True, tail=.15)))(_root)
SFX.update(NES)


def sum_(parts):
    return parts[0]


def main():
    story = json.load(open(sys.argv[1], encoding='utf-8'))
    total = sum(int(sc['dur'] * FPS) / FPS for sc in story['scenes'])
    buf = [0.0] * int(total * SR + SR)
    cache = {}

    def put(name, t):
        s = cache.setdefault(name, SFX[name]())
        i0 = int(t * SR)
        for k, v in enumerate(s):
            if 0 <= i0 + k < len(buf):
                buf[i0 + k] += v

    t0 = 0.0
    for si, sc in enumerate(story['scenes']):
        typ = sc['type']
        if typ == 'g_intro':
            put('bump', t0 + 0.02)
            put('jump', t0 + 0.75)
        elif typ == 'g_item':
            put(f"item{sc.get('idx', 0) % 4}", t0 + 0.05)
            w = sc.get('widget') or {}
            d0 = w.get('delay', 2.0)
            n = len(w.get('items', []))
            if w.get('type') == 'widths':
                put('twinkle', t0 + d0 + (n - 1) * 0.35 + 0.3)
            elif w.get('type') == 'pipeline':
                put('scale', t0 + d0)
            elif w.get('type') == 'grill':
                for i in range(n):
                    put('blip' + 'ABC'[i % 3], t0 + d0 + i * 0.55)
        elif typ == 'g_outro':
            put('door', t0 + 0.5)
            put('victory', t0 + 1.3)
        t0 += int(sc['dur'] * FPS) / FPS
    peak = max(1e-6, max(abs(x) for x in buf))
    g = min(1.0, 0.9 / peak)
    with wave.open(sys.argv[2], 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, x * g)) * 32000)) for x in buf))
    print(sys.argv[2], f'{total:.2f}s')


if __name__ == '__main__':
    main()
