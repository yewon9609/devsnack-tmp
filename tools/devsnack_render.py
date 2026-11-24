#!/usr/bin/env python3
"""devsnack carousel renderer v3 (dark, pixel-art, every card animated, adaptive deep/roundup).
Usage: python3 tools/devsnack_render.py content.json OUT_DIR
content.json:
{
 "mode": "deep" | "roundup",
 "date": "2026.11.23 MON",
 "cover": {"tag": "NEWS · 대형 장애", "title": "델타항공 전 노선이\\n[[자동화 시스템]]에 멈췄다",
           "icon": "plane", "icon2": "warn", "bubble": "수동 계산 중...", "mood": "sweat"},
 "slides": [   # deep: 3-5 steps of one issue / roundup: 2-5 issues
   {"tag": "무슨 일?", "title": "...", "sub": "orange subtitle", "body": ["line", "line"],
    "panel": {"type": "icon", "icon": "server", "caption": "..."}
           | {"type": "terminal", "lines": ["$ ...", "> ..."]}
           | {"type": "stat", "num": "3시간", "label": "..."},
    "src": "GeekNews"}],
 "more": [{"t": "...", "s": "HN 391"}],   # optional, roundup outro list
 "caption": "..."
}
Icons: plane, warn, server, robot, box, chart, shield, lock, db, rocket, chip, book.
Moods: happy, sweat, shock.
Cover scene (optional, replaces the cover icon): "scene": {"type": "badge", "org": "NVIDIA", "name": "JENSEN HUANG", "role": "CEO", "from": "RESIGNED", "to": "RETURNED"}
  -> staff ID card with a generic silhouette; stamp "from" flips to "to" (people/role-change stories, never a real photo).
Layout: content "layout": "split" (default; top = moving screen, bottom = dark text) | "classic".
Panel "ticker": {"type":"ticker","symbol":"NVDA","label":"엔비디아","change":"31%","notes":["..."]}  stock card + notifications sliding in.
Panel "lineup": {"type":"lineup","label":"...","items":["Blink","WebKit","Gecko"],"new":"Ladybird","caption":"..."}  new entrant drops in.
Panel "inbox": {"type":"inbox","app":"Kagi Mail","new":["Kagi","Welcome"],"mails":[["a","b"]],"tags":["..."]}  new mail slides in.
Prefer these scene panels over "terminal" (terminal only for real commands).
Panel "browser": {"type": "browser", "url": "ladybird.org", "badge": "NEW ENGINE"} -> address typed, page loads block by block (browsers, web services, launches).
Panel "chart": {"type": "chart", "values": [..], "labels": [..], "num": "+31%", "label": "..."} -> rising bars (only real numbers).
Cover "mascot": cookie (default) | gpu | server | robot  -> pick the character that fits the story (vary it; no brand logos).
Icons also: person (generic silhouette), trend.  [[text]] in titles = orange highlight.
"""
import json, os, random, re, sys, pathlib, html as H

ACC = '#D97757'; BG = '#1F1E1D'; DEEP = '#121110'; TX = '#F0EEE6'; BODY = '#C2C0B6'; MUTED = '#8F8D85'
LINE = '#3A3836'; PANEL = '#2A2826'; BOX = '#4A4744'
HANDLE = '@devsnack.kr'; BRAND = 'devsnack'
MONO = "font-family: 'JetBrains Mono', monospace"
SANS = "font-family: 'IBM Plex Sans KR', sans-serif"

PAL = {'K': '#141110', 'C': '#C98A4B', 'L': '#E3AE6E', 'D': '#5A3A22', 'W': '#F0EEE6', 'O': ACC, 'R': '#E5534B',
       'G': '#8F8D85', 'g': '#4A4744', 'h': '#5E5A56', 'B': '#6FA8DC', 'Y': '#F2C14E', 'N': '#7BC47F', 'P': '#E59AA8'}

ICONS = {
 'plane': [".KK.................", ".KWK................", ".KWWK.......KK......", ".KWWWKKKKKKKWWKKKKK.",
           "..KWWWWWWWWWWWWWWWWK", "..KWBWBWBWBWBWWWWWBBK", "...KKKKKWWWWWKKKKKKK.", "........KWWWK........",
           ".........KWWK........", "..........KK........."],
 'warn': ["......KK......", ".....KYYK.....", ".....KYYK.....", "....KYKKYK....", "....KYKKYK....", "...KYYKKYYK...",
          "...KYYKKYYK...", "..KYYYYYYYYK..", "..KYYYKKYYYK..", ".KYYYYYYYYYYK.", "KKKKKKKKKKKKKK"],
 'server': [".KKKKKKKKKKKK.", ".KhhhhhhhhhhK.", ".KhNhhhhhOhhK.", ".KhhhhhhhhhhK.", ".KKKKKKKKKKKK.", ".KhhhhhhhhhhK.",
            ".KhNhhhhhRhhK.", ".KhhhhhhhhhhK.", ".KKKKKKKKKKKK.", ".KhhhhhhhhhhK.", ".KhNhhhhhNhhK.", ".KhhhhhhhhhhK.",
            ".KKKKKKKKKKKK."],
 'robot': ["......KK......", "......KO......", "...KKKKKKKK...", "..KWWWWWWWWK..", "..KWBBWWBBWK..", "..KWBBWWBBWK..",
           "..KWWWWWWWWK..", "..KWWKKKKWWK..", "...KKKKKKKK...", "..KhhhhhhhhK..", ".KKhOhhhhOhKK.", "..KhhhhhhhhK..",
           "..KKKKKKKKKK.."],
 'box': ["..KKKKKKKKKK..", ".KYYYYKKYYYYK.", "KYYYYYKKYYYYYK", "KKKKKKKKKKKKKK", "KLLLLLKKLLLLLK", "KLLLLLKKLLLLLK",
         "KLLLLLLLLLLLLK", "KLLLLLLLLLLLLK", "KKKKKKKKKKKKKK"],
 'chart': ["K.............", "K..........OO.", "K.........O...", "K....O...O....", "K...O.O.O.....", "K..O...O......",
           "K.O...........", "KKKKKKKKKKKKKK"],
 'shield': ["..KKKKKKKKKK..", ".KBBBBBBBBBBK.", ".KBBBBWWBBBBK.", ".KBBBWWWWBBBK.", ".KBBBBWWBBBBK.", ".KBBBBWWBBBBK.",
            "..KBBBBBBBBK..", "...KBBBBBBK...", "....KBBBBK....", ".....KKKK....."],
 'lock': ["....KKKKK.....", "...KG...GK....", "...KG...GK....", "..KKKKKKKKK...", "..KYYYYYYYK...", "..KYYYKYYYK...",
          "..KYYYKYYYK...", "..KYYYYYYYK...", "..KKKKKKKKK..."],
 'db': ["..KKKKKKKKKK..", ".KBBBBBBBBBBK.", ".KKKKKKKKKKKK.", ".KBBBBBBBBBBK.", ".KBBBBBBBBNBK.", ".KKKKKKKKKKKK.",
        ".KBBBBBBBBBBK.", ".KBBBBBBBBNBK.", "..KKKKKKKKKK.."],
 'rocket': [".....KK.....", "....KWWK....", "...KWWWWK...", "...KWBBWK...", "...KWBBWK...", "...KWWWWK...", "..KKWWWWKK..",
            ".KOKWWWWKOK.", ".KOKKKKKKOK.", "....KYYK....", ".....KK....."],
 'chip': ["..K.K.K.K.K...", ".KKKKKKKKKKK..", "KKhhhhhhhhhKK.", ".KhOOOOOOOhK..", "KKhOhhhhhOhKK.", ".KhOhhhhhOhK..",
          "KKhOOOOOOOhKK.", ".KhhhhhhhhhK..", ".KKKKKKKKKKK..", "..K.K.K.K.K..."],
 'person': ["....GGGG....", "...GGGGGG...", "...GGGGGG...", "...GGGGGG...", "....GGGG....", "............", "..GGGGGGGG..", ".GGGGGGGGGG.", "GGGGGGGGGGGG", "GGGGGGGGGGGG"],
 'trend': ["..........KK", ".........KOK", "........KOOK", "...K...KOK..", "..KOK.KOK...", ".KOKOKOK....", "KOK.KOK.....", "KK...K......"],
 'book': ["KKKKKKKKKKKKK.", "KWWWWWKWWWWWK.", "KWGGGWKWGGGWK.", "KWWWWWKWWWWWK.", "KWGGGWKWGGGWK.", "KWWWWWKWWWWWK.",
          "KKKKKKKKKKKKK."],
}

MASCOT = {
 'base': ["....KKKKKKK.....", "..KKLLLLLLLKK...", ".KLLCCCCCCCLLK..", ".KLCCDCCCCCCLK..", "KLCCCCCCCDCCCLK.",
          "KLCCWKCCCWKCCLK.", "KLCCKKCCCKKCCLK.", "KLCDCCCCCCCDCLK.", "KLCCCCMMMCCCCLK.", "KLCCCCCCCCCCCLK.",
          ".KLCCDCCCCDCLK..", ".KLLCCCCCCCLLK..", "..KKLLLLLLLKK...", "....KKKKKKK....."],
}
CHARS = {
 'gpu': ["KKKKKKKKKKKKKKKKKK..", "KhhhhhhhhhhhhhhhhKK.", "KhGGGGGhhhhGGGGGhKOK", "KGGhhhGGhhGGhhhGGKOK",
         "KGhhKhhGhhGhhKhhGKOK", "KGGhhhGGhhGGhhhGGKOK", "KhGGGGGhhhhGGGGGhKOK", "KhhhhhhhhhhhhhhhhKOK",
         "KhhhWKhhhhhhWKhhhKOK", "KhhhKKhhhhhhKKhhhKOK", "KhhhhhhhKKKhhhhhhKK.", "KKKKKKKKKKKKKKKKKK..",
         ".KOKOKOKOKOK........"],
 'server': ["KKKKKKKKKKKKKK", "KhhhhhhhhhhhhK", "KhWKhhhhhWKhhK", "KhKKhhhhhKKhhK", "KhhhhKKKKhhhhK", "KKKKKKKKKKKKKK",
            "KhNhhhhhhhOhhK", "KhhhhhhhhhhhhK", "KKKKKKKKKKKKKK", "KhNhhhhhhhRhhK", "KKKKKKKKKKKKKK"],

}
CHARS['robot'] = ICONS['robot']
MOUTH = {'happy': "KLCCCKCCCKCCCLK.", 'sweat': "KLCCCCKKKCCCCLK.", 'shock': "KLCCCCKKKCCCCLK."}


def pixel_svg(rows, size, extra=''):
    w = max(len(r) for r in rows)
    out = [f'<svg width="{w*size}" height="{len(rows)*size}" viewBox="0 0 {w} {len(rows)}" shape-rendering="crispEdges" aria-hidden="true" {extra}>']
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in PAL:
                out.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{PAL[ch]}"/>')
    out.append('</svg>')
    return ''.join(out)


def mascot(mood, size):
    rows = list(MASCOT['base'])
    rows[8] = MOUTH.get(mood, MOUTH['happy'])
    if mood == 'shock':
        rows[5] = "KLCWWKCCCWWKCLK."; rows[6] = "KLCWKKCCCWKKCLK."
    svg = pixel_svg(rows, size)
    if mood == 'sweat':
        drop = pixel_svg([".K.", "KBK", "KBK", ".K."], size)
        svg = f'<div style="position: relative; display: inline-block">{svg}<div class="drop" style="position: absolute; right: {-size*2}px; top: {size*2}px">{drop}</div></div>'
    return svg


def font_css():
    repo = pathlib.Path(__file__).resolve().parent.parent / 'fonts' / 'fonts.css'
    if repo.exists():
        return f'<link rel="stylesheet" href="file://{repo}">'
    for root in [os.path.expanduser('~/ds_fonts/node_modules/@fontsource'), '/home/claude/render/node_modules/@fontsource']:
        if os.path.isdir(root):
            fs = ['ibm-plex-sans-kr/400.css', 'ibm-plex-sans-kr/500.css', 'ibm-plex-sans-kr/700.css', 'jetbrains-mono/500.css', 'jetbrains-mono/700.css']
            return ''.join(f'<link rel="stylesheet" href="file://{root}/{f}">' for f in fs)
    sys.exit('fonts missing')


def esc(s):
    s = H.escape(s)
    s = re.sub(r'\[\[(.+?)\]\]', rf'<span class="hl" style="color: {ACC}">\1</span>', s)
    return re.sub(r'\*\*(.+?)\*\*', rf'<b style="color: {TX}">\1</b>', s)


def br(s): return '<br>'.join(esc(x) for x in s.split('\n'))


def lines_in(text, base=0.25, step=0.14):
    return ''.join(f'<span class="in-up" style="display: block; animation-delay: {base + i * step:.2f}s">{esc(x)}</span>' for i, x in enumerate(text.split('\n')))


def fx_layer(seed, cx=540, cy=330):
    """Pixel burst from (cx, cy) at entrance + twinkling sparks + drifting scanline."""
    random.seed(str(seed) + 'fx'); out = []
    for k in range(18):
        ang = k / 18 * 6.283 + random.random() * 0.3; dist = random.randint(220, 420)
        import math
        dx, dy = int(math.cos(ang) * dist), int(math.sin(ang) * dist * 0.7)
        sz = random.choice([10, 14, 18]); col = random.choice([ACC, ACC, TX, '#F2C14E'])
        out.append(f'<div class="burst" style="position: absolute; left: {cx}px; top: {cy}px; width: {sz}px; height: {sz}px; background: {col}; --dx: {dx}px; --dy: {dy}px; animation-delay: {0.35 + random.random() * 0.15:.2f}s"></div>')
    for k in range(14):
        x, y = random.randint(40, 1020), random.randint(120, 1250)
        out.append(f'<div class="spark" style="position: absolute; left: {x}px; top: {y}px; width: 8px; height: 8px; background: {random.choice([ACC, TX])}; animation-delay: -{random.random() * 2.4:.2f}s"></div>')
    out.append(f'<div class="scan" style="position: absolute; left: 0; right: 0; height: 120px; background: linear-gradient(to bottom, rgba(217,119,87,0), rgba(217,119,87,.07), rgba(217,119,87,0))"></div>')
    return '<div style="position: absolute; inset: 0; pointer-events: none; overflow: hidden">' + ''.join(out) + '</div>'


def header(n, total):
    return f'''<div style="display: flex; justify-content: space-between; align-items: center; {MONO}; font-size: 26px; letter-spacing: 0.04em; position: relative">
<span style="color: {ACC}; font-weight: 700">&gt; {BRAND}</span><span style="color: {TX}">{n:02d} / {total:02d}</span></div>'''


def footer(n, total):
    pct = n / total * 100; prev = (n - 1) / total * 100
    return f'''<div style="margin-top: 40px; display: flex; align-items: center; justify-content: space-between">
<span style="{MONO}; font-size: 24px; color: {MUTED}">{HANDLE}</span>
<div style="width: 280px; height: 6px; background: {LINE}; border-radius: 3px; overflow: hidden"><div class="grow" style="--from: {prev:.0f}%; --to: {pct:.0f}%; width: {pct:.0f}%; height: 6px; background: {ACC}"></div></div></div>'''


def stars(seed, w=1080, h=860, n=46):
    random.seed(seed); out = []
    for _ in range(n):
        x, y = random.randint(0, w // 12) * 12, random.randint(0, h // 12) * 12
        s = random.choice([6, 6, 6, 12]); op = random.choice([0.25, 0.4, 0.6])
        d = random.random() * 2.4
        out.append(f'<div class="tw" style="position: absolute; left: {x}px; top: {y}px; width: {s}px; height: {s}px; background: {TX}; opacity: {op}; animation-delay: -{d:.2f}s"></div>')
    return ''.join(out)


def cover(c, total, date):
    cv = c['cover']
    icon = ICONS.get(cv.get('icon', 'warn'), ICONS['warn'])
    icon2 = cv.get('icon2')
    iw = max(len(r) for r in icon); isz = int(360 / iw)
    side = ''
    if icon2 and icon2 in ICONS:
        side = f'<div class="pulse" style="position: absolute; left: 470px; top: 230px">{pixel_svg(ICONS[icon2], 9)}</div>'
    scene = cv.get('scene') or {}
    main_art = f'<div class="hover" style="position: absolute; left: 150px; top: {640 - len(icon)*isz}px">{pixel_svg(icon, isz)}</div>'
    if scene.get('type') == 'badge':
        side = ''
        sil = pixel_svg(ICONS['person'], 12)
        main_art = f'''<div class="bob" style="position: absolute; left: 120px; top: 150px; width: 330px">
<div style="margin: 0 auto; width: 18px; height: 70px; background: {ACC}"></div>
<div style="position: relative; box-sizing: border-box; width: 330px; padding: 26px; background: {TX}; border: 8px solid {DEEP}; box-shadow: 10px 10px 0 {ACC}; color: {DEEP}; {MONO}">
<div style="display: flex; justify-content: space-between; font-size: 20px; font-weight: 700"><span>STAFF ID</span><span style="color: {ACC}">{H.escape(scene.get('org', ''))}</span></div>
<div style="margin: 18px 0; height: 150px; background: #CFCBC2; display: flex; align-items: flex-end; justify-content: center; overflow: hidden">{sil}</div>
<div style="font-size: 28px; font-weight: 700; line-height: 1.2">{H.escape(scene.get('name', ''))}</div>
<div style="font-size: 22px; margin-top: 6px">ROLE: {H.escape(scene.get('role', ''))}</div>
<div class="st1" style="position: absolute; left: 34px; top: 150px; transform: rotate(-12deg); padding: 6px 14px; border: 5px solid #E5534B; color: #E5534B; font-size: 30px; font-weight: 700; background: rgba(240,238,230,.85)">{H.escape(scene.get('from', ''))}</div>
<div class="st2" style="position: absolute; left: 44px; top: 160px; transform: rotate(-8deg); padding: 6px 14px; border: 5px solid {ACC}; color: {ACC}; font-size: 34px; font-weight: 700; background: {TX}">{H.escape(scene.get('to', ''))}</div>
</div></div>'''
    ch = cv.get('mascot', 'cookie')
    if ch in CHARS:
        rows = CHARS[ch]; csz = int(min(340 / max(len(r) for r in rows), 260 / len(rows)))
        char_html = f'<div class="bob" style="position: absolute; left: 610px; top: {640 - len(rows) * csz + 6}px">{pixel_svg(rows, csz)}</div>'
    else:
        char_html = f'<div class="bob" style="position: absolute; left: 640px; top: {640 - 14*18 + 6}px">{mascot(cv.get('mood', 'happy'), 18)}</div>'
    bubble = ''
    if cv.get('bubble'):
        bubble = f'''<div style="position: absolute; right: 110px; top: 300px; background: {TX}; color: {DEEP}; {MONO}; font-weight: 700; font-size: 34px; padding: 18px 26px; border: 6px solid {DEEP}; box-shadow: 6px 6px 0 {ACC}"><span class="type" style="--n: {sum(2 if ord(ch) > 0x2E80 else 1 for ch in cv['bubble'])}">{H.escape(cv['bubble'])}</span></div>'''
    return f'''<div style="width: 1080px; height: 1350px; position: relative; overflow: hidden; background: {DEEP}; color: {TX}; {SANS}; word-break: keep-all">
<div style="position: absolute; inset: 0">{stars(cv.get('title', ''))}</div>
<div style="position: absolute; left: 0; right: 0; top: 640px; height: 220px; background: repeating-linear-gradient(90deg, {PANEL} 0 96px, #262422 96px 102px)"></div>
<div style="position: absolute; left: 0; right: 0; top: 640px; height: 12px; background: {LINE}"></div>
{side}
{main_art}
{char_html}
{bubble}
<div style="position: absolute; left: 0; right: 0; bottom: 0; height: 720px; background: linear-gradient(to bottom, rgba(18,17,16,0) 0%, rgba(18,17,16,0.92) 32%, {DEEP} 52%)"></div>
<div style="position: absolute; inset: 0; box-sizing: border-box; padding: 88px; display: flex; flex-direction: column">
{header(1, total)}
<div style="margin-top: auto; display: flex; align-items: center; gap: 18px">
<span style="padding: 8px 18px; border: 2px solid {TX}; border-radius: 6px; {MONO}; font-size: 24px; font-weight: 700">{H.escape(cv.get('tag', ''))}</span>
<span style="{MONO}; font-size: 24px; color: {MUTED}">{H.escape(date)}</span></div>
<h1 style="margin: 28px 0 0 0; font-size: 96px; line-height: 1.2; font-weight: 700; letter-spacing: -0.035em; overflow: hidden">{lines_in(cv['title'], 0.2, 0.18)}</h1>
<div style="margin-top: 44px; display: flex; justify-content: space-between; align-items: center; {MONO}; font-size: 26px">
<span style="color: {ACC}; font-weight: 700">&gt; {BRAND}<span class="blink" style="display: inline-block; width: 14px; height: 26px; margin-left: 8px; vertical-align: -4px; background: {ACC}"></span></span>
<span style="color: {TX}">넘겨보기 →</span></div>
</div></div>'''


def count_html(num):
    m = re.match(r'^(\D*)(\d+)(.*)$', num)
    if not m or len(m.group(2)) > 6:
        return H.escape(num)
    return f'{H.escape(m.group(1))}<span class="count" style="--to: {int(m.group(2))}"></span>{H.escape(m.group(3))}'


def panel(p):
    t = p.get('type', 'icon')
    if t == 'terminal':
        def w(l): return sum(2 if ord(ch) > 0x2E80 else 1 for ch in l)
        t0, rows = 0.45, []
        for i, l in enumerate(p['lines']):
            n = max(w(l), 1); dur = min(0.06 * n, 0.9) if l.startswith('$') else 0.25
            col = ACC if l.startswith("!") else (TX if l.startswith("$") else BODY)
            rows.append(f'<div style="height: 1.6em; white-space: pre; color: {col}"><span class="tw-line" style="--n: {n}; animation-duration: {dur:.2f}s; animation-delay: {t0:.2f}s; animation-timing-function: steps({n})">{H.escape(l)}</span></div>')
            t0 += dur + 0.18
        lines = ''.join(rows)
        lines += f'<span class="blink" style="display: inline-block; width: 16px; height: 30px; background: {ACC}; margin-top: 6px"></span>'
        inner = f'''<div style="display: flex; gap: 10px; margin-bottom: 26px"><span style="width: 16px; height: 16px; border-radius: 50%; background: #E5534B"></span><span style="width: 16px; height: 16px; border-radius: 50%; background: #F2C14E"></span><span style="width: 16px; height: 16px; border-radius: 50%; background: #7BC47F"></span></div>
<div style="{MONO}; font-size: 28px; line-height: 1.6">{lines}</div>'''
        return f'<div style="height: 440px; box-sizing: border-box; padding: 34px 40px; background: {DEEP}; border: 2px solid {BOX}; border-radius: 24px; overflow: hidden">{inner}</div>'
    if t == 'ticker':
        toasts = ''.join(f'<div class="toast" style="animation-delay: {1.1 + i * 0.55:.2f}s; display: flex; align-items: center; gap: 14px; padding: 16px 20px; margin-bottom: 14px; background: {PANEL}; border: 2px solid {BOX}; border-radius: 16px; font-size: 26px; color: {TX}"><span style="width: 14px; height: 14px; border-radius: 50%; background: {ACC}; flex: none"></span>{esc(x)}</div>' for i, x in enumerate(p.get('notes', [])))
        return f'''<div style="height: 440px; box-sizing: border-box; padding: 28px; background: {DEEP}; border: 2px solid {BOX}; border-radius: 24px; display: flex; gap: 26px; overflow: hidden">
<div style="width: 330px; flex: none; box-sizing: border-box; padding: 28px; background: {PANEL}; border-radius: 20px; display: flex; flex-direction: column">
<div style="{MONO}; font-size: 28px; color: {MUTED}">{H.escape(p.get('symbol', ''))}</div>
<div style="margin-top: 8px; font-size: 26px; color: {BODY}">{esc(p.get('label', ''))}</div>
<div class="pop" style="margin-top: auto; {MONO}; font-size: 96px; font-weight: 700; color: #7BC47F; line-height: 1">+{count_html(p.get('change', ''))}</div>
<div style="margin-top: 18px; height: 120px; position: relative">{pixel_svg(ICONS['trend'], 14, 'class="rise" style="position: absolute; right: 0; bottom: 0"')}</div></div>
<div style="flex: 1; display: flex; flex-direction: column; justify-content: center">{toasts}</div></div>'''
    if t == 'lineup':
        items = p.get('items', []); newi = p.get('new', '')
        cards = ''.join(f'<div class="in-up" style="animation-delay: {0.5 + i * 0.2:.2f}s; flex: 1; height: 190px; box-sizing: border-box; padding: 20px; background: {PANEL}; border: 2px solid {BOX}; border-radius: 18px; display: flex; flex-direction: column; justify-content: space-between"><span style="{MONO}; font-size: 20px; color: {MUTED}">ENGINE</span><span style="font-size: 32px; font-weight: 700; color: {BODY}">{H.escape(x)}</span></div>' for i, x in enumerate(items))
        cards += f'<div class="dropin" style="flex: 1.2; height: 190px; box-sizing: border-box; padding: 20px; background: {ACC}; border-radius: 18px; display: flex; flex-direction: column; justify-content: space-between; color: {DEEP}; box-shadow: 0 0 0 6px rgba(217,119,87,.3)"><span style="{MONO}; font-size: 20px; font-weight: 700">NEW ENGINE</span><span style="font-size: 34px; font-weight: 700">{H.escape(newi)}</span></div>'
        return f'''<div style="height: 440px; box-sizing: border-box; padding: 40px 36px; background: {DEEP}; border: 2px solid {BOX}; border-radius: 24px; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden">
<div style="font-size: 28px; color: {BODY}">{esc(p.get('label', ''))}</div>
<div style="display: flex; gap: 18px; align-items: flex-end">{cards}</div>
<div class="in-fade" style="animation-delay: 2.2s; {MONO}; font-size: 24px; color: {ACC}">{H.escape(p.get('caption', ''))}</div></div>'''
    if t == 'inbox':
        rows = ''.join(f'<div style="display: flex; gap: 18px; padding: 16px 22px; border-bottom: 1px solid {LINE}; font-size: 24px; color: {MUTED}"><b style="width: 170px; flex: none; color: {BODY}; font-weight: 500">{H.escape(m[0])}</b><span style="white-space: nowrap; overflow: hidden">{H.escape(m[1])}</span></div>' for m in p.get('mails', []))
        nm = p.get('new', ['', ''])
        tags = ''.join(f'<span class="in-pop" style="animation-delay: {2.0 + i * 0.3:.2f}s; display: inline-block; margin-right: 12px; padding: 8px 16px; background: {ACC}; color: {DEEP}; border-radius: 10px; font-size: 22px; font-weight: 700">{H.escape(x)}</span>' for i, x in enumerate(p.get('tags', [])))
        return f'''<div style="height: 440px; box-sizing: border-box; background: {DEEP}; border: 2px solid {BOX}; border-radius: 24px; overflow: hidden; display: flex">
<div style="width: 190px; flex: none; background: {PANEL}; padding: 26px 20px; box-sizing: border-box; {MONO}; font-size: 22px; color: {MUTED}; line-height: 2.2"><div style="color: {TX}; font-weight: 700; font-size: 26px">{H.escape(p.get('app', 'Mail'))}</div><div style="color: {ACC}">▸ Inbox</div><div>Sent</div><div>Archive</div></div>
<div style="flex: 1; position: relative">
<div class="newmail" style="display: flex; gap: 18px; padding: 18px 22px; background: rgba(217,119,87,.16); border-left: 6px solid {ACC}; font-size: 26px; color: {TX}"><b style="width: 170px; flex: none">{H.escape(nm[0])}</b><span style="white-space: nowrap; overflow: hidden">{H.escape(nm[1])}</span></div>
{rows}
<div style="position: absolute; left: 22px; bottom: 22px">{tags}</div><div style="position: absolute; right: 18px; bottom: 26px; {MONO}; font-size: 18px; color: {MUTED}; border: 1px solid {BOX}; border-radius: 8px; padding: 4px 10px">예시 화면</div></div></div>'''
    if t == 'browser':
        url = p.get('url', ''); un = len(url)
        blocks = ''.join(f'<div class="blk" style="animation-delay: {1.3 + i * 0.22:.2f}s; height: {h}px; width: {wd}%; background: {c}; margin-bottom: 14px"></div>' for i, (h, wd, c) in enumerate([(44, 70, TX), (18, 92, BOX), (18, 84, BOX), (18, 60, BOX), (90, 100, ACC)]))
        return f'''<div style="height: 440px; box-sizing: border-box; background: {DEEP}; border: 2px solid {BOX}; border-radius: 24px; overflow: hidden; position: relative">
<div style="display: flex; align-items: center; gap: 14px; padding: 18px 24px; background: {PANEL}; border-bottom: 2px solid {BOX}">
<span style="width: 16px; height: 16px; border-radius: 50%; background: #E5534B"></span><span style="width: 16px; height: 16px; border-radius: 50%; background: #F2C14E"></span><span style="width: 16px; height: 16px; border-radius: 50%; background: #7BC47F"></span>
<div style="flex: 1; margin-left: 10px; padding: 8px 16px; background: {DEEP}; border-radius: 8px; {MONO}; font-size: 24px; color: {TX}; white-space: pre"><span class="tw-line" style="--n: {un}; animation-duration: .7s; animation-delay: .4s; animation-timing-function: steps({un})">{H.escape(url)}</span></div></div>
<div style="height: 8px; background: {LINE}"><div class="load" style="height: 8px; background: {ACC}"></div></div>
<div style="padding: 30px 40px">{blocks}</div>
<div class="in-pop" style="animation-delay: 2.5s; position: absolute; right: 30px; bottom: 30px; padding: 10px 18px; background: {ACC}; color: {DEEP}; {MONO}; font-size: 26px; font-weight: 700; transform: rotate(-4deg)">{H.escape(p.get('badge', ''))}</div>
</div>'''
    if t == 'chart':
        vals = p['values']; mx = max(vals); n = len(vals); bw = int(560 / n) - 18
        bars = ''.join(f'<div style="display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 260px"><div class="{"barhi" if i == n - 1 else "bar"}" style="--h: {int(240 * v / mx)}px; width: {bw}px; background: {ACC if i == n - 1 else BOX}"></div><div style="{MONO}; font-size: 20px; color: {MUTED}; margin-top: 10px">{H.escape(str(p.get("labels", [""] * n)[i]))}</div></div>' for i, v in enumerate(vals))
        return f'''<div style="height: 440px; box-sizing: border-box; padding: 36px 40px; background: {PANEL}; border: 2px solid {BOX}; border-radius: 24px; display: flex; flex-direction: column; justify-content: space-between">
<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font-size: 30px; color: {BODY}">{esc(p.get('label', ''))}</span><span class="pop" style="{MONO}; font-size: 72px; font-weight: 700; color: {ACC}">{H.escape(p.get('num', ''))}</span></div>
<div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 18px">{bars}</div></div>'''
    if t == 'stat':
        return f'''<div style="height: 440px; box-sizing: border-box; padding: 40px; background: {PANEL}; border: 2px solid {BOX}; border-radius: 24px; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 18px">
<div class="pop" style="{MONO}; font-size: 150px; font-weight: 700; color: {ACC}; line-height: 1">{count_html(p['num'])}</div>
<div style="width: 360px; height: 10px; background: {LINE}"><div class="fill" style="height: 10px; background: {ACC}"></div></div>
<div style="font-size: 32px; color: {BODY}; text-align: center">{esc(p.get('label', ''))}</div></div>'''
    icon = ICONS.get(p.get('icon', 'warn'), ICONS['warn']); iw = max(len(r) for r in icon); sz = int(min(300 / iw, 260 / len(icon)))
    cap = f'<div style="{MONO}; font-size: 26px; color: {MUTED}; margin-top: 30px">{H.escape(p.get("caption", ""))}</div>' if p.get('caption') else ''
    return f'''<div style="height: 440px; box-sizing: border-box; background: {PANEL}; border: 2px solid {BOX}; border-radius: 24px; display: flex; flex-direction: column; justify-content: center; align-items: center; position: relative; overflow: hidden">
<div style="position: absolute; inset: 0; opacity: .5">{stars(p.get('icon', 'x'), 904, 440, 18)}</div>
<div class="bob" style="position: relative">{pixel_svg(icon, sz)}</div><div style="position: relative">{cap}</div></div>'''


def slide(s, n, total):
    body = ''.join(f'<div class="in-up" style="animation-delay: {0.62 + i * 0.12:.2f}s">{esc(b)}</div>' for i, b in enumerate(s.get('body', [])))
    tag = f'<span class="in-left" style="animation-delay: .18s; padding: 6px 16px; border: 2px solid {ACC}; border-radius: 6px; {MONO}; font-size: 22px; font-weight: 700; color: {ACC}">{H.escape(s["tag"])}</span>' if s.get('tag') else ''
    src = f'<span class="in-fade" style="animation-delay: .9s; {MONO}; font-size: 22px; color: {MUTED}">src: {H.escape(s["src"])}</span>' if s.get('src') else ''
    return f'''<div style="width: 1080px; height: 1350px; box-sizing: border-box; padding: 88px; background: {BG}; color: {TX}; {SANS}; word-break: keep-all; display: flex; flex-direction: column; position: relative; overflow: hidden">
<div class="grid" style="position: absolute; inset: 0; opacity: .5; background-image: radial-gradient({LINE} 2px, transparent 2px); background-size: 36px 36px"></div>
{fx_layer(s.get('title', n), 540, 360)}
<div style="position: relative; display: flex; flex-direction: column; flex: 1">
{header(n, total)}
<div class="in-panel" style="margin-top: 48px"><div class="glow">{panel(s.get('panel', {}))}</div></div>
<div style="margin-top: 52px; display: flex; align-items: center; gap: 20px">
<span class="in-pop" style="animation-delay: .12s; width: 64px; height: 64px; border-radius: 50%; background: {ACC}; color: {DEEP}; display: flex; align-items: center; justify-content: center; {MONO}; font-size: 32px; font-weight: 700">{n-1}</span>{tag}</div>
<h1 style="margin: 26px 0 0 0; font-size: 64px; line-height: 1.25; font-weight: 700; letter-spacing: -0.03em; overflow: hidden">{lines_in(s['title'])}</h1>
<div class="in-up" style="animation-delay: .5s; margin-top: 18px; font-size: 34px; font-weight: 700; color: {ACC}">{esc(s.get('sub', ''))}</div>
<div style="margin-top: 18px; font-size: 31px; line-height: 1.55; color: {BODY}">{body}</div>
<div style="margin-top: auto; display: flex; justify-content: flex-end">{src}</div>
{footer(n, total)}
</div></div>'''


def top_media(p):
    if p.get('type') == 'scene':
        svg = pathlib.Path(p['svg']).read_text(encoding='utf-8') if p.get('svg') else p.get('html', '')
        hero = ''
        if p.get('mascot', True):
            hat = pixel_svg(["....YYYYYY....", "...YYYYYYYY...", "..YYYYYYYYYY..", "YYYYYYYYYYYYYY"], 10) if p.get('hat') else ''
            hero = f'<div class="bob" style="position: absolute; left: {p.get("mx", 640)}px; top: {p.get("my", 470)}px">{hat and f"<div style=\'margin-left: 0; margin-bottom: -8px\'>{hat}</div>"}{mascot(p.get("mood", "happy"), 10)}</div>'
            if p.get('bubble'):
                hero += f'<div class="in-pop" style="animation-delay: .8s; position: absolute; left: {p.get("mx", 640) + 150}px; top: {p.get("my", 470) - 40}px; background: {TX}; color: {DEEP}; {MONO}; font-weight: 700; font-size: 28px; padding: 12px 18px; border: 5px solid {DEEP}; box-shadow: 5px 5px 0 {ACC}">{H.escape(p["bubble"])}</div>'
        return f'<div class="in-fade" style="position: absolute; inset: 0">{svg}</div>{hero}'
    return f'''<div class="in-panel" style="position: absolute; left: 50%; top: 140px; width: 904px; margin-left: -452px; transform-origin: top center"><div style="transform: scale(1.15); transform-origin: top center"><div class="glow">{panel(p)}</div></div></div>'''


def slide_split(s, n, total):
    """Reference-style card: top = moving 'screen' (panel scene), bottom = dark text block."""
    body = ''.join(f'<div class="in-up" style="animation-delay: {0.62 + i * 0.12:.2f}s">{esc(b)}</div>' for i, b in enumerate(s.get('body', [])))
    tag = f'<span class="in-left" style="animation-delay: .18s; padding: 6px 16px; border: 2px solid {ACC}; border-radius: 6px; {MONO}; font-size: 22px; font-weight: 700; color: {ACC}">{H.escape(s["tag"])}</span>' if s.get('tag') else ''
    src = f'<span class="in-fade" style="animation-delay: .9s; {MONO}; font-size: 22px; color: {MUTED}">src: {H.escape(s["src"])}</span>' if s.get('src') else ''
    badge = f'''<span class="in-pop" style="animation-delay: .12s; width: 84px; height: 84px; border-radius: 50%; background: radial-gradient(circle at 35% 30%, #F6B79F 0%, {ACC} 45%, #9C4A30 100%); box-shadow: inset -6px -8px 0 rgba(0,0,0,.25), 0 6px 0 #5A2A1B; color: {TX}; display: flex; align-items: center; justify-content: center; {MONO}; font-size: 44px; font-weight: 700; text-shadow: 0 3px 0 rgba(0,0,0,.35)">{n-1}</span>'''
    return f'''<div style="width: 1080px; height: 1350px; position: relative; overflow: hidden; background: {BG}; color: {TX}; {SANS}; word-break: keep-all">
<div style="position: absolute; left: 0; right: 0; top: 0; height: 660px; background: {DEEP}; overflow: hidden">
<div class="grid" style="position: absolute; inset: 0; opacity: .6; background-image: radial-gradient({LINE} 2px, transparent 2px); background-size: 36px 36px"></div>
{fx_layer(s.get('title', n), 540, 330)}
{top_media(s.get('panel', {}))}
<div style="position: absolute; left: 88px; right: 88px; top: 0; padding-top: 70px">{header(n, total)}</div>
</div>
<div style="position: absolute; left: 0; right: 0; top: 660px; height: 6px; background: linear-gradient(90deg, {ACC}, rgba(217,119,87,0))"></div>
<div style="position: absolute; left: 0; right: 0; top: 666px; bottom: 0; box-sizing: border-box; padding: 56px 88px 70px; display: flex; flex-direction: column">
<div style="display: flex; align-items: center; gap: 22px">{badge}{tag}</div>
<h1 style="margin: 30px 0 0 0; font-size: 68px; line-height: 1.22; font-weight: 700; letter-spacing: -0.03em; overflow: hidden">{lines_in(s['title'])}</h1>
<div class="in-up" style="animation-delay: .5s; margin-top: 20px; font-size: 34px; font-weight: 700; color: {ACC}">{esc(s.get('sub', ''))}</div>
<div style="margin-top: 18px; font-size: 31px; line-height: 1.55; color: {BODY}">{body}</div>
<div style="margin-top: auto; display: flex; justify-content: flex-end">{src}</div>
{footer(n, total)}
</div></div>'''


def outro(c, n, total):
    rows = c.get('more', [])[:4]
    lst = ''
    if rows:
        lst = '<div style="margin-top: 40px; font-size: 32px; color: ' + BODY + '">' + ''.join(
            f'<div class="in-left" style="animation-delay: {0.3 + i * 0.18:.2f}s; display: flex; justify-content: space-between; gap: 24px; padding: 22px 0; border-bottom: 1px solid {LINE}"><span>{esc(x["t"])}</span><span style="{MONO}; font-size: 22px; color: {MUTED}; white-space: nowrap; padding-top: 6px">{H.escape(x.get("s", ""))}</span></div>' for i, x in enumerate(rows)) + '</div>'
    head = '짧게 더 보기' if rows else '한 줄로 정리하면'
    if not rows:
        lst = '<div style="margin-top: 40px; font-size: 34px; line-height: 1.5; color: ' + BODY + '">' + ''.join(
            f'<div class="in-left" style="animation-delay: {0.2 + i * 0.18:.2f}s; display: flex; gap: 22px; padding: 20px 0; border-bottom: 1px solid {LINE}"><span style="{MONO}; color: {ACC}; font-weight: 700">{i:02d}</span><span>{esc(s.get("sub", ""))}</span></div>' for i, s in enumerate(c['slides'], 1)) + '</div>'
    return f'''<div style="width: 1080px; height: 1350px; box-sizing: border-box; padding: 88px; background: {BG}; color: {TX}; {SANS}; word-break: keep-all; display: flex; flex-direction: column; position: relative; overflow: hidden">
{header(n, total)}
<h1 style="margin: 70px 0 0 0; font-size: 72px; line-height: 1.2; font-weight: 700; letter-spacing: -0.03em">{head}</h1>
{lst}
<div style="margin-top: auto; display: flex; align-items: flex-end; gap: 30px">
<div>{mascot('happy', 14)}</div>
<div style="flex: 1; padding: 34px 38px; background: {ACC}; border-radius: 20px; color: {DEEP}">
<div style="font-size: 40px; font-weight: 700; line-height: 1.3">매일 오후 5시,<br>개발 이슈 한 입 🍪</div>
<div style="margin-top: 12px; font-size: 28px; font-weight: 700">팔로우 {HANDLE} · 저장해두고 보기</div></div></div>
{footer(n, total)}
</div>'''



ANIM_CSS = """<style>
@keyframes sway { 0%,100% { transform: rotate(-4deg) } 50% { transform: rotate(4deg) } }
.sway { animation: sway 2.4s steps(6) infinite }
@keyframes win { 0%,100% { opacity: 1 } 50% { opacity: .25 } }
.win { animation: win 1.6s steps(2) infinite }
.blinkr { animation: blink 1.2s steps(1) infinite }
@keyframes spk { 0%,100% { opacity: 0 } 30% { opacity: 1 } 60% { opacity: 0 } }
.spk { animation: spk .8s steps(3) infinite }
@keyframes toast { 0% { transform: translateX(120%); opacity: 0 } 100% { transform: none; opacity: 1 } }
.toast { opacity: 0; animation: toast .45s steps(5) both }
@keyframes rise { 0% { transform: translateY(60px); opacity: 0 } 100% { transform: none; opacity: 1 } }
.rise { animation: rise .8s steps(6) .5s both }
@keyframes dropin { 0%,40% { transform: translateY(-420px) } 52% { transform: translateY(12px) } 58% { transform: none } 100% { transform: none } }
.dropin { animation: dropin 4.8s steps(1) both; animation-timing-function: steps(12) }
@keyframes newmail { 0%,20% { transform: translateY(-100%); opacity: 0; max-height: 0 } 32% { transform: none; opacity: 1; max-height: 120px } 100% { opacity: 1; max-height: 120px } }
.newmail { animation: newmail 4.8s steps(8) both }
@keyframes twl { from { max-width: 0 } to { max-width: calc(var(--n) * 1ch) } }
.tw-line { display: inline-block; overflow: hidden; vertical-align: top; max-width: 0; animation-name: twl; animation-fill-mode: both }
@keyframes load { 0%,22% { width: 0 } 60% { width: 70% } 80%,100% { width: 100% } }
.load { animation: load 4.8s steps(10) infinite }
@keyframes blk { 0% { opacity: 0; transform: translateX(-30px) } 100% { opacity: 1; transform: none } }
.blk { opacity: 0; animation: blk .35s steps(4) both }
@property --cnt { syntax: '<integer>'; initial-value: 0; inherits: false; }
@keyframes count { from { --cnt: 0 } to { --cnt: var(--to) } }
.count { animation: count 1.1s steps(14) .35s both; counter-reset: c var(--cnt) }
.count::after { content: counter(c) }
@keyframes inup { 0% { transform: translateY(110%); opacity: 0 } 100% { transform: none; opacity: 1 } }
.in-up { animation: inup .5s steps(5) both }
@keyframes inleft { 0% { transform: translateX(-80px); opacity: 0 } 100% { transform: none; opacity: 1 } }
.in-left { display: inline-flex; animation: inleft .45s steps(5) both }
div.in-left { display: flex }
@keyframes infade { 0% { opacity: 0 } 100% { opacity: 1 } }
.in-fade { animation: infade .4s steps(4) both }
@keyframes inpop { 0% { transform: scale(0) } 70% { transform: scale(1.25) } 100% { transform: scale(1) } }
.in-pop { animation: inpop .45s steps(5) both }
@keyframes inpanel { 0% { transform: scale(.82) translateY(40px); opacity: 0 } 60% { transform: scale(1.03); opacity: 1 } 100% { transform: none; opacity: 1 } }
.in-panel { animation: inpanel .55s steps(6) .05s both }
@keyframes glow { 0%,100% { box-shadow: 0 0 0 0 rgba(217,119,87,0) } 50% { box-shadow: 0 0 0 6px rgba(217,119,87,.35) } }
.glow { border-radius: 24px; animation: glow 1.6s steps(4) 1s infinite }
@keyframes burst { 0% { transform: translate(0,0) scale(1); opacity: 0 } 5% { opacity: 1 } 100% { transform: translate(var(--dx), var(--dy)) scale(.3); opacity: 0 } }
.burst { opacity: 0; animation: burst .9s steps(7) both }
@keyframes spark { 0%,100% { opacity: 0; transform: scale(.4) } 50% { opacity: .9; transform: scale(1.2) } }
.spark { animation: spark 2.4s steps(4) infinite }
@keyframes scan { 0% { top: -120px } 100% { top: 1350px } }
.scan { animation: scan 4.8s linear infinite }
@keyframes grid { 0% { background-position: 0 0 } 100% { background-position: 36px 36px } }
.grid { animation: grid 2.4s steps(6) infinite }
@keyframes hl { 0%,100% { text-shadow: none } 50% { text-shadow: 0 0 18px rgba(217,119,87,.8) } }
.hl { animation: hl 1.2s steps(3) 1s infinite }
@keyframes st1 { 0%,40% { opacity: 1 } 41%,100% { opacity: 0 } }
.st1 { animation: st1 4.8s steps(1) infinite }
@keyframes st2 { 0%,44% { opacity: 0; transform: rotate(-8deg) scale(2.2) } 50% { opacity: 1; transform: rotate(-8deg) scale(1.15) } 54%,100% { opacity: 1; transform: rotate(-8deg) scale(1) } }
.st2 { animation: st2 4.8s steps(1) infinite }
@keyframes bar { 0% { height: 0 } 40%,100% { height: var(--h) } }
.bar { height: var(--h); animation: bar 4.8s steps(6) infinite }
@keyframes barhi { 0%,30% { height: 0 } 60%,100% { height: var(--h) } }
.barhi { height: var(--h); animation: barhi 4.8s steps(8) infinite }
@keyframes tw { 0%,100% { opacity: .15 } 50% { opacity: .8 } }
.tw { animation: tw 2.4s steps(3) infinite }
@keyframes bob { 0%,100% { transform: translateY(0) } 50% { transform: translateY(-14px) } }
.bob { animation: bob 1.2s steps(2) infinite }
@keyframes hover { 0%,100% { transform: translate(0,0) } 50% { transform: translate(18px,-12px) } }
.hover { animation: hover 2.4s steps(4) infinite }
@keyframes pulse { 0%,100% { opacity: 1 } 50% { opacity: .2 } }
.pulse { animation: pulse .8s steps(2) infinite }
@keyframes drop { 0% { transform: translateY(0); opacity: 1 } 80% { transform: translateY(54px); opacity: 0 } 100% { transform: translateY(54px); opacity: 0 } }
.drop { animation: drop 1.2s steps(6) infinite }
@keyframes type { 0% { max-width: 0 } 60%,100% { max-width: calc(var(--n) * 1ch) } }
.type { display: inline-block; overflow: hidden; white-space: nowrap; vertical-align: bottom; animation: type 2.4s steps(12) infinite }
@keyframes blink { 0%,49% { opacity: 1 } 50%,100% { opacity: 0 } }
.blink { animation: blink 1.2s steps(1) infinite }
@keyframes ln { 0% { opacity: 0 } 3% { opacity: 1 } 100% { opacity: 1 } }
.ln { opacity: 0; animation: ln 4.8s steps(1) infinite both }
@keyframes pop { 0%,100% { transform: scale(1) } 50% { transform: scale(1.06) } }
.pop { animation: pop 1.2s steps(3) infinite }
@keyframes fill { 0% { width: 0 } 50%,100% { width: 100% } }
.fill { animation: fill 2.4s steps(12) infinite }
@keyframes grow { 0% { width: var(--from) } 30%,100% { width: var(--to) } }
.grow { animation: grow 4.8s steps(8) infinite }
</style>"""


def chrome():
    for p in ['/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser']:
        if os.path.exists(p): return p
    return None


def main():
    c = json.load(open(sys.argv[1], encoding='utf-8')); out = pathlib.Path(sys.argv[2]).resolve(); out.mkdir(parents=True, exist_ok=True)
    for f in list(out.glob('devsnack_*.*')): f.unlink()
    total = 1 + len(c['slides']) + 1
    pages = [cover(c, total, c.get('date', ''))] + [(slide if c.get('layout') == 'classic' else slide_split)(s, i + 2, total) for i, s in enumerate(c['slides'])] + [outro(c, total, total)]
    css = font_css()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        exe = chrome(); b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = b.new_page(viewport={'width': 1080, 'height': 1350})
        for i, inner in enumerate(pages, 1):
            f = out / f'_{i:02d}.html'
            f.write_text(f'<!doctype html><html lang="ko"><head><meta charset="utf-8">{css}<style>body{{margin:0}}</style>{ANIM_CSS}</head><body>{inner}</body></html>', encoding='utf-8')
            pg.goto(f'file://{f}'); pg.wait_for_timeout(500)
            pg.evaluate("() => document.getAnimations().forEach(a => { a.pause(); a.currentTime = 4500; })")
            if pg.evaluate("() => { const r=document.body.firstElementChild; return r.scrollHeight > r.clientHeight + 2; }"):
                print(f'WARNING card {i:02d} overflows: shorten its text', file=sys.stderr)
            pg.screenshot(path=str(out / f'devsnack_{i:02d}.png'))
            pg.screenshot(path=str(out / f'devsnack_{i:02d}.jpg'), type='jpeg', quality=92)
            if os.environ.get('DEVSNACK_VIDEO', '1') == '1' and (i == 1 or os.environ.get('DEVSNACK_VIDEO_ALL', '1') == '1'):
                fr = out / '_frames'; fr.mkdir(exist_ok=True)
                fps, secs = 15, 4.8
                for k in range(int(fps * secs)):
                    pg.evaluate(f"() => document.getAnimations().forEach(a => {{ a.pause(); a.currentTime = {k * 1000 / fps}; }})")
                    pg.screenshot(path=str(fr / f'{k:04d}.png'))
                import subprocess
                subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', str(fr / '%04d.png'),
                                '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-shortest',
                                '-c:v', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', '30',
                                '-c:a', 'aac', '-b:a', '64k', '-movflags', '+faststart',
                                str(out / f'devsnack_{i:02d}.mp4')], check=True)
                import shutil; shutil.rmtree(fr)
            f.unlink()
        b.close()
    cap = re.sub('([0-9#*])\ufe0f?\u20e3', '\\1\ufe0f\u20e3', c.get('caption', ''))  # keycap emoji need FE0F or they render broken
    cap = re.sub(r'(?m)^출처\s*:.*\n?', '', cap)  # no source line in caption (sources stay on cards)
    cap = re.sub(r'\n{3,}', '\n\n', cap)
    # Instagram only links the first 5 hashtags; drop the rest so they don't show as plain words
    seen = 0
    def _tag(m):
        nonlocal seen
        seen += 1
        return m.group(0) if seen <= 5 else ''
    cap = re.sub(r'#[^\s#]+', _tag, cap)
    cap = re.sub(r'[ \t]+\n', '\n', cap).rstrip() + '\n'
    (out / 'caption.txt').write_text(cap, encoding='utf-8')
    print('done', total, 'cards')


if __name__ == '__main__':
    main()
