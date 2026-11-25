#!/usr/bin/env python3
"""Typecast narration for a story reel. Key is read from ~/.devsnack/typecast_key (never printed).
Usage: python3 tools/typecast_tts.py lines.json OUT_DIR [--voice 진헌] [--tempo 1.1]
lines.json: {"hook": "잠깐만요!" (optional, loud toneup), "lines": ["scene1 text", ...]}
Writes OUT_DIR/scene{N}.wav; if hook is given it is generated separately and prepended to scene1."""
import json, os, sys, pathlib, urllib.request, urllib.error, subprocess, argparse

ap = argparse.ArgumentParser(); ap.add_argument('lines'); ap.add_argument('out')
ap.add_argument('--voice', default='Hyunjun'); ap.add_argument('--model', default='ssfm-v31'); ap.add_argument('--emotion', default='normal'); ap.add_argument('--rate', type=float, default=0); ap.add_argument('--tempo', type=float, default=1.1)
a = ap.parse_args()
KEY = pathlib.Path('~/.devsnack/typecast_key').expanduser().read_text().strip()
OUT = pathlib.Path(a.out); OUT.mkdir(parents=True, exist_ok=True)
spec = json.load(open(a.lines, encoding='utf-8'))


def req(method, path, body=None):
    r = urllib.request.Request('https://api.typecast.ai' + path, method=method, data=json.dumps(body).encode() if body else None,
                               headers={'X-API-KEY': KEY, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(r, timeout=120) as resp:
        return resp.read()


vid = None
for path in ('/v2/voices', '/v1/voices'):
    try:
        data = json.loads(req('GET', path))
    except urllib.error.HTTPError:
        continue
    items = data if isinstance(data, list) else data.get('voices', data.get('result', []))
    for v in items:
        if a.voice.lower() == (v.get('voice_name') or v.get('name') or '').lower():
            vid = v['voice_id']; break
    if vid: break
if not vid: sys.exit(f'{a.voice} voice not found')


def tts(text, prompt, dest):
    body = {'voice_id': vid, 'text': text, 'model': a.model, 'language': 'kor', 'prompt': prompt,
            'output': {'audio_format': 'wav', 'audio_tempo': a.tempo}}
    dest.write_bytes(req('POST', '/v1/text-to-speech', body))


L = spec['lines']
full = ((spec.get('hook') + ' ') if spec.get('hook') else '') + ' '.join(L)
tts(full, {'emotion_type': 'smart'} if a.emotion == 'smart' else {'emotion_type': 'preset', 'emotion_preset': a.emotion, 'emotion_intensity': 1.0}, OUT / '_full.wav')
import re
d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(OUT / '_full.wav')]))
log = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(OUT / '_full.wav'), '-af', 'silencedetect=n=-40dB:d=0.15', '-f', 'null', '-'], capture_output=True, text=True).stderr
ss = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]; se = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
mids = [((a + b) / 2, b - a) for a, b in zip(ss, se) if 0.05 < a and b < d - 0.05]
chars = [len(re.sub(r'\s', '', ((spec.get('hook') + ' ') if (i == 0 and spec.get('hook')) else '') + t)) for i, t in enumerate(L)]
cuts = []; used = set()
for k in range(1, len(L)):
    exp = d * sum(chars[:k]) / sum(chars)
    cand = sorted((m for m in mids if m[0] not in used and (not cuts or m[0] > cuts[-1] + 0.5)), key=lambda m: abs(m[0] - exp) - 0.8 * m[1])
    c = cand[0][0]; used.add(c); cuts.append(c)
bounds = [0.0] + cuts + [d]
for i in range(len(L)):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(OUT / '_full.wav'), '-ss', f'{bounds[i]:.3f}', '-to', f'{bounds[i + 1]:.3f}', str(OUT / f'scene{i + 1}.wav')], check=True)
# even out speaking rate between lines (syllables per voiced second)
rates = []
for i in range(len(L)):
    seg = OUT / f'scene{i + 1}.wav'
    lg = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(seg), '-af', 'silencedetect=n=-34dB:d=0.08', '-f', 'null', '-'], capture_output=True, text=True).stderr
    sd = sum(float(x) for x in re.findall(r'silence_duration: ([\d.]+)', lg))
    dd = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(seg)]))
    syl = len(re.findall(r'[가-힣]', (('잠깐만요' if i == 0 and spec.get('hook') else '') + L[i]))) + 2 * len(re.findall(r'[A-Za-z0-9]', L[i]))
    rates.append(syl / max(dd - sd, .5))
target = a.rate or sorted(rates)[len(rates) // 2]
for i, r in enumerate(rates):
    k = max(.85, min(1.2, target / r))
    if abs(k - 1) > .03:
        seg = OUT / f'scene{i + 1}.wav'; tmp = OUT / '_t.wav'
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(seg), '-af', f'atempo={k:.3f}', str(tmp)], check=True); tmp.replace(seg)
print('cuts', [round(c, 2) for c in cuts], 'total', round(d, 2), 'rates', [round(r, 1) for r in rates], 'target', round(target, 1))
