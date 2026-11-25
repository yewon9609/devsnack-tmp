#!/usr/bin/env python3
"""Attach per-scene narration to a story JSON: trims silences, times subtitles to speech, sets scene durations.
Usage: python3 tools/align_voice.py story.json VOICE_DIR(scene1.wav..) WORK_DIR out_story.json
Widget delays: set "widget_at": <subtitle index> on a scene to start its widget when that subtitle appears."""
import json, re, subprocess, sys, pathlib

story, vdir, work, out = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), sys.argv[4]
work.mkdir(parents=True, exist_ok=True)
NUM = {'0': '영', '1': '일', '2': '이', '3': '삼', '4': '사', '5': '오', '6': '육', '7': '칠', '8': '팔', '9': '구'}
OFF = 0.0
st = json.load(open(story, encoding='utf-8'))
for i, sc in enumerate(st['scenes']):
    src = vdir / f'scene{i + 1}.wav'; f = work / f's{i + 1}.wav'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(src), '-af',
                    'silenceremove=start_periods=1:start_threshold=-34dB:start_silence=0.02:stop_periods=-1:stop_duration=0.12:stop_threshold=-34dB:stop_silence=0.07',
                    '-ar', '44100', str(f)], check=True)
    d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(f)]))
    log = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(f), '-af', 'silencedetect=n=-40dB:d=0.05', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ss = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]; se = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
    segs = []; t = 0
    for a, b in zip(ss, se):
        if a > t + 0.01: segs.append((t, a))
        t = b
    if t < d - 0.01: segs.append((t, d))
    total = sum(b - a for a, b in segs)

    def at(fr):
        x = fr * total
        for a, b in segs:
            if x <= b - a: return a + x
            x -= b - a
        return segs[-1][1]
    subs = sc['subs']
    import wave, numpy as np
    with wave.open(str(f)) as wf:
        sr = wf.getframerate(); x = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32)
        if wf.getnchannels() > 1: x = x.reshape(-1, wf.getnchannels()).mean(1)
    hop = int(sr * 0.01)
    rms = np.array([np.sqrt(np.mean(x[k:k + hop] ** 2) + 1e-9) for k in range(0, len(x) - hop, hop)])
    db = 20 * np.log10(rms / 32768 + 1e-9)
    db = np.convolve(db, np.ones(3) / 3, mode='same')
    voiced = np.where(db > -34)[0]
    t0v, t1v = (voiced[0] / 100, voiced[-1] / 100) if len(voiced) else (0, d)
    # valleys: local minima of the envelope, with their depth relative to the surroundings
    valleys = []
    for k in range(5, len(db) - 5):
        if db[k] == db[k - 5:k + 6].min():
            depth = min(db[k - 8:k].max() if k >= 8 else db[:k].max(), db[k + 1:k + 9].max()) - db[k]
            if depth > 4: valleys.append((k / 100, depth))
    def weight(s):
        core = re.sub(r'[\[\]\s"\'/…]', '', ''.join(NUM.get(c, c) for c in s))
        return len(re.sub(r'[,.!?]', '', core)) + 2.5 * len(re.findall(r'[,.!?]', core)) or 1
    w = [weight(s) for s in subs]
    cum = [sum(w[:k]) / sum(w) for k in range(len(w) + 1)]
    exp = [t0v + c * (t1v - t0v) for c in cum[:-1]]
    starts = [t0v]
    for k in range(1, len(subs)):
        cands = [(abs(v - exp[k]) - 0.04 * dep, v) for v, dep in valleys if starts[-1] + 0.25 < v < (exp[k + 1] if k + 1 < len(exp) else t1v) and abs(v - exp[k]) < 0.5]
        starts.append(min(cands)[1] if cands else max(exp[k], starts[-1] + 0.25))
    starts = [s + OFF for s in starts]
    starts = [max(0, s - 0.06) for s in starts]
    dur = round(d + OFF + 0.03, 2)
    sc['sub_times'] = [[round(a, 2), round(b, 2)] for a, b in zip(starts, starts[1:] + [dur])]
    sc['audio'] = str(f); sc['audio_offset'] = OFF; sc['dur'] = dur
    if sc.get('widget') and 'widget_at' in sc:
        sc['widget']['delay'] = round(starts[sc['widget_at']], 2)
    print(i, dur)
json.dump(st, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
