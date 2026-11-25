#!/usr/bin/env python3
"""Narration with exact subtitle sync, using Typecast word timestamps.
Usage: python3 tools/voice_timed.py story.json lines.json WORK_DIR out_story.json [--voice Hyunjun]
- Reads the whole script in ONE request (natural flow), steady 'normal' tone.
- Shrinks every pause using the word timings (silence removal), keeping a known time map.
- Splits audio per scene at line boundaries and times each subtitle to the word it starts with.
- Evens out speaking rate between lines.
Key: ~/.devsnack/typecast_key (never printed)."""
import json, sys, re, base64, io, wave, pathlib, argparse, urllib.request, subprocess
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument('story'); ap.add_argument('lines'); ap.add_argument('work'); ap.add_argument('out')
ap.add_argument('--voice', default='Hyunjun'); ap.add_argument('--tempo', type=float, default=1.1); ap.add_argument('--model', default='ssfm-v31')
ap.add_argument('--even', action='store_true'); ap.add_argument('--gap', type=float, default=0.16); ap.add_argument('--sentence-gap', type=float, default=0.24)
a = ap.parse_args()
KEY = pathlib.Path('~/.devsnack/typecast_key').expanduser().read_text().strip()
W = pathlib.Path(a.work); W.mkdir(parents=True, exist_ok=True)
story = json.load(open(a.story, encoding='utf-8')); spec = json.load(open(a.lines, encoding='utf-8'))
L = list(spec['lines'])
if spec.get('hook'): L[0] = spec['hook'] + ' ' + L[0]


def api(path, body=None):
    r = urllib.request.Request('https://api.typecast.ai' + path, method='POST' if body else 'GET', data=json.dumps(body).encode() if body else None,
                               headers={'X-API-KEY': KEY, 'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(r, timeout=180).read())


vid = next(v['voice_id'] for v in api('/v2/voices') if v['voice_name'].lower() == a.voice.lower())
res = api('/v1/text-to-speech/with-timestamps?granularity=word', {
    'voice_id': vid, 'text': ' '.join(L), 'model': a.model, 'language': 'kor',
    'prompt': {'emotion_type': 'preset', 'emotion_preset': 'normal', 'emotion_intensity': 1.0},
    'output': {'audio_format': 'wav', 'audio_tempo': a.tempo}})
raw = base64.b64decode(res['audio'])
with wave.open(io.BytesIO(raw)) as wf:
    sr = wf.getframerate(); ch = wf.getnchannels()
    x = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
    if ch > 1: x = x.reshape(-1, ch).mean(1).astype(np.int16)
words = res['words']
tokens = [t for line in L for t in line.split()]
if len(tokens) != len(words):
    sys.exit(f'token mismatch: script {len(tokens)} vs audio {len(words)}')
line_of = [i for i, line in enumerate(L) for _ in line.split()]

# --- condense: never cut inside speech; only shorten long pauses, keeping both edges and crossfading ---
def xfade(p, q, n):
    if n <= 0 or len(p) < n or len(q) < n: return np.concatenate([p, q])
    r = np.linspace(0, 1, n)
    mid = (p[-n:].astype(np.float32) * (1 - r) + q[:n].astype(np.float32) * r).astype(np.int16)
    return np.concatenate([p[:-n], mid, q[n:]])
fade = int(0.012 * sr)
out = x[:max(0, int((words[0]['start'] - 0.03) * sr))][-int(0.03 * sr):].copy()  # tiny lead-in
shift = int((words[0]['start'] - 0.03) * sr) - len(out)  # original index of out[0] = shift
newpos = []; removed = 0
pos = int(max(0, words[0]['start'] - 0.03) * sr)  # original cursor
out = np.zeros(0, dtype=np.int16); base = pos
for k, w in enumerate(words):
    ws = int(w['start'] * sr)
    if k > 0:
        pe = int(words[k - 1]['end'] * sr)
        gap = (ws - pe) / sr
        cap = a.sentence_gap if re.search(r'[.!?]$', words[k - 1]['text']) else a.gap
        if gap > cap:
            half = int(cap / 2 * sr)
            out = np.concatenate([out, x[pos:pe + half]])
            out = xfade(out, x[ws - half:ws], fade); pos = ws
    newpos.append((len(out) + (ws - pos)) / sr)
y = np.concatenate([out, x[pos:min(len(x), int((words[-1]['end'] + 0.25) * sr))]])
# --- per line: cut, even out rate, time subtitles ---
def spoken_len(s):
    return len(re.sub(r'[\[\]\s,.!?…"\'/·]', '', s)) or 1

nl = len(L); starts = [newpos[line_of.index(i)] for i in range(nl)] + [len(y) / sr]
rates = []
for i in range(nl):
    idx = [k for k in range(len(words)) if line_of[k] == i]
    speech = sum(words[k]['end'] - words[k]['start'] for k in idx)
    rates.append(sum(len(re.findall(r'[가-힣A-Za-z0-9]', words[k]['text'])) for k in idx) / max(speech, .3))
target = sorted(rates)[nl // 2]
for i, sc in enumerate(story['scenes']):
    a0, a1 = int(starts[i] * sr), int(starts[i + 1] * sr)
    seg = W / f'raw{i + 1}.wav'
    with wave.open(str(seg), 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(y[a0:a1].tobytes())
    k = max(.88, min(1.15, target / rates[i])) if a.even else 1.0; k = 1.0 if abs(k - 1) < .03 else k
    out = W / f'scene{i + 1}.wav'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(seg), '-af', f'atempo={k:.4f}', '-ar', '44100', str(out)], check=True)
    dur = (a1 - a0) / sr / k
    idx = [j for j in range(len(words)) if line_of[j] == i]
    wl = [spoken_len(words[j]['text']) for j in idx]; wc = np.cumsum([0] + wl)
    subs = sc['subs']; sl = [spoken_len(s) for s in subs]; scum = np.cumsum([0] + sl) * (wc[-1] / sum(sl))
    st_times = []
    for q in range(len(subs)):
        j = int(np.argmin(np.abs(wc[:-1] - scum[q])))
        if st_times and j <= st_times[-1][0]: j = min(st_times[-1][0] + 1, len(idx) - 1)
        st_times.append((j, (newpos[idx[j]] - starts[i]) / k))
    t = [max(0.0, s - 0.04) for _, s in st_times]; t[0] = 0.0
    sc['sub_times'] = [[round(p, 3), round(q, 3)] for p, q in zip(t, t[1:] + [dur])]
    sc['audio'] = str(out); sc['audio_offset'] = 0; sc['dur'] = round(dur, 3)
    if sc.get('widget') and 'widget_at' in sc:
        sc['widget']['delay'] = round(t[sc['widget_at']], 2)
json.dump(story, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('scenes', [s['dur'] for s in story['scenes']], 'total', round(sum(s['dur'] for s in story['scenes']), 2), 'rates', [round(r, 1) for r in rates])
