#!/usr/bin/env python3
"""devsnack Instagram carousel publisher.

Usage:
  python3 tools/ig_publish.py check   --token-file F --ig-id ID
  python3 tools/ig_publish.py publish --token-file F --ig-id ID --dir OUT --base-url URL
                                      --caption-file OUT/caption.txt --marker posted/YYYYMMDD

- check: verifies graph.facebook.com is reachable and the token works. Exit 0 ok,
  2 = network blocked, 3 = token invalid/expired. Prints one JSON line.
- publish: every card devsnack_NN becomes a carousel child in order. If devsnack_NN.mp4
  exists it is uploaded as VIDEO; if that child fails (ERROR / timeout) it falls back to
  devsnack_NN.jpg as IMAGE. All video children are created first and polled together.
  Then CAROUSEL container -> media_publish -> permalink.
  Right after media_publish succeeds the --marker file is written (duplicate guard).
  Refuses to run if the marker already exists.
  Files must already be reachable at BASE_URL/<filename>.
The token is only ever read from the file and passed to curl via @file; it is never printed.
"""
import argparse, json, os, pathlib, subprocess, sys, time

API = 'https://graph.facebook.com/v27.0'


def curl(method, path, token_file, data=None):
    cmd = ['curl', '-sS', '--max-time', '60', '-w', '\n%{http_code}']
    if method == 'GET':
        cmd += ['-G']
    else:
        cmd += ['-X', 'POST']
    for k, v in (data or {}).items():
        cmd += ['--data-urlencode', f'{k}={v}']
    cmd += ['--data-urlencode', f'access_token@{token_file}', f'{API}/{path}']
    r = subprocess.run(cmd, capture_output=True, text=True)
    body, _, code = r.stdout.rpartition('\n')
    try:
        j = json.loads(body) if body.strip() else {}
    except ValueError:
        j = {'raw': body[:300]}
    return int(code or 0), j, r.stderr[-300:]


def err(j):
    e = j.get('error') if isinstance(j, dict) else None
    return f"{e.get('code')}: {e.get('message')}" if e else json.dumps(j)[:300]


def check(a):
    code, j, se = curl('GET', a.ig_id, a.token_file, {'fields': 'username'})
    if code == 0 or code in (403, 407) and 'error' not in j:
        print(json.dumps({'ok': False, 'reason': 'network', 'detail': (se or str(j))[:200]}, ensure_ascii=False)); sys.exit(2)
    if code != 200:
        print(json.dumps({'ok': False, 'reason': 'token', 'detail': err(j)}, ensure_ascii=False)); sys.exit(3)
    print(json.dumps({'ok': True, 'username': j.get('username')}, ensure_ascii=False))


def status(cid, a):
    code, j, _ = curl('GET', cid, a.token_file, {'fields': 'status_code,status'})
    return j.get('status_code', 'ERROR' if code != 200 else 'IN_PROGRESS'), j.get('status', '')


def create(a, kind, url):
    d = {'is_carousel_item': 'true'}
    if kind == 'VIDEO':
        d.update(media_type='VIDEO', video_url=url)
    else:
        d.update(image_url=url)
    code, j, _ = curl('POST', f'{a.ig_id}/media', a.token_file, d)
    return j.get('id'), (None if j.get('id') else err(j))


def publish(a):
    marker = pathlib.Path(a.marker)
    if marker.exists():
        print(json.dumps({'ok': False, 'reason': 'already_posted', 'marker': str(marker)})); sys.exit(4)
    out = pathlib.Path(a.dir)
    cards = sorted({p.stem for p in out.glob('devsnack_*.jpg')})
    if not cards:
        sys.exit('no cards')
    base = a.base_url.rstrip('/')
    kids, notes = {}, []
    # 1) create all children (videos first-class, image fallback)
    for c in cards:
        if (out / f'{c}.mp4').exists():
            cid, e = create(a, 'VIDEO', f'{base}/{c}.mp4')
            if cid:
                kids[c] = ('VIDEO', cid); continue
            notes.append(f'{c}: video create failed ({e}) -> image')
        cid, e = create(a, 'IMAGE', f'{base}/{c}.jpg')
        if not cid:
            print(json.dumps({'ok': False, 'stage': 'child', 'card': c, 'detail': e}, ensure_ascii=False)); sys.exit(5)
        kids[c] = ('IMAGE', cid)
    # 2) poll all videos together, every 15s, max 8 min
    deadline = time.time() + 480
    pending = {c for c, (k, _) in kids.items() if k == 'VIDEO'}
    while pending and time.time() < deadline:
        time.sleep(15)
        for c in list(pending):
            st, detail = status(kids[c][1], a)
            if st == 'FINISHED':
                pending.discard(c)
            elif st == 'ERROR':
                pending.discard(c); kids[c] = ('RETRY', None); notes.append(f'{c}: video ERROR ({detail}) -> image')
    for c in pending:
        kids[c] = ('RETRY', None); notes.append(f'{c}: video timeout -> image')
    for c, (k, _) in list(kids.items()):
        if k == 'RETRY':
            cid, e = create(a, 'IMAGE', f'{base}/{c}.jpg')
            if not cid:
                print(json.dumps({'ok': False, 'stage': 'fallback', 'card': c, 'detail': e}, ensure_ascii=False)); sys.exit(5)
            kids[c] = ('IMAGE', cid)
    # 3) carousel container
    caption = pathlib.Path(a.caption_file).read_text(encoding='utf-8')
    code, j, _ = curl('POST', f'{a.ig_id}/media', a.token_file,
                      {'media_type': 'CAROUSEL', 'children': ','.join(kids[c][1] for c in cards), 'caption': caption})
    car = j.get('id')
    if not car:
        print(json.dumps({'ok': False, 'stage': 'carousel', 'detail': err(j), 'notes': notes}, ensure_ascii=False)); sys.exit(5)
    deadline = time.time() + 300
    while True:
        st, detail = status(car, a)
        if st == 'FINISHED': break
        if st == 'ERROR' or time.time() > deadline:
            print(json.dumps({'ok': False, 'stage': 'carousel_status', 'detail': f'{st} {detail}', 'notes': notes}, ensure_ascii=False)); sys.exit(5)
        time.sleep(10)
    # 4) publish (once)
    code, j, _ = curl('POST', f'{a.ig_id}/media_publish', a.token_file, {'creation_id': car})
    mid = j.get('id')
    if not mid:
        print(json.dumps({'ok': False, 'stage': 'publish', 'detail': err(j), 'notes': notes}, ensure_ascii=False)); sys.exit(5)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({'media_id': mid, 'time': time.strftime('%Y-%m-%dT%H:%M:%S%z')}))
    _, j, _ = curl('GET', mid, a.token_file, {'fields': 'permalink'})
    kinds = {c: kids[c][0] for c in cards}
    print(json.dumps({'ok': True, 'media_id': mid, 'permalink': j.get('permalink'), 'kinds': kinds, 'notes': notes}, ensure_ascii=False))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['check', 'publish'])
    ap.add_argument('--token-file', required=True); ap.add_argument('--ig-id', required=True)
    ap.add_argument('--dir'); ap.add_argument('--base-url'); ap.add_argument('--caption-file'); ap.add_argument('--marker')
    a = ap.parse_args()
    check(a) if a.cmd == 'check' else publish(a)
