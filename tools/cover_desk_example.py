import sys, pathlib
sys.path.insert(0, '/home/claude/devsnack-tmp/tools')
import devsnack_render as R
ACC = R.ACC; DEEP = '#121110'
P = 10

def svg(cells, w, h, p=P):
    """cells: dict (x,y)->color"""
    r = ''.join(f'<rect x="{x*p}" y="{y*p}" width="{p}" height="{p}" fill="{c}"/>' for (x, y), c in cells.items())
    return f'<svg width="{w*p}" height="{h*p}" viewBox="0 0 {w*p} {h*p}" shape-rendering="crispEdges" style="display:block">{r}</svg>'

def box(w, h, fill, hi, lo, out=DEEP, notch=2):
    c = {}
    for y in range(h):
        for x in range(w):
            # notched corners
            if (x < notch and y < notch - x) or (x >= w - notch and y < notch - (w - 1 - x)) or (x < notch and y >= h - (notch - x)) or (x >= w - notch and y >= h - (notch - (w - 1 - x))):
                continue
            edge = x == 0 or y == 0 or x == w - 1 or y == h - 1 or (x < notch and y in (notch - x, h - 1 - (notch - x))) or (x >= w - notch and y in (notch - (w - 1 - x), h - 1 - (notch - (w - 1 - x))))
            if edge: c[(x, y)] = out
            elif x <= 2 or y <= 2: c[(x, y)] = hi
            elif x >= w - 4 or y >= h - 4: c[(x, y)] = lo
            else: c[(x, y)] = fill
    return c

def monitor():
    W, H = 86, 70
    c = box(W, H, '#E9E1D3', '#FBF6EC', '#B9AD9A')
    for y in range(6, 54):
        for x in range(7, 79):
            c[(x, y)] = '#1B1917' if y % 3 else '#211E1B'
    for x in range(6, 80): c[(x, 5)] = '#9C9282'; c[(x, 54)] = '#FBF6EC'
    for y in range(5, 55): c[(6, y)] = '#9C9282'; c[(79, y)] = '#FBF6EC'
    for x in range(10, 30): c[(x, 61)] = '#B9AD9A'
    c[(74, 61)] = ACC; c[(75, 61)] = ACC; c[(74, 62)] = '#B5543A'; c[(75, 62)] = ACC
    return svg(c, W, H)

def desk():
    W, H = 112, 74; c = {}
    for y in range(H):
        for x in range(W):
            c[(x, y)] = '#F0A76B' if y < 2 else ('#C9824E' if y < 6 else ('#A8683C' if (y // 9) % 2 else '#B5733F'))
    for x in range(W): c[(x, 6)] = '#7A4A28'
    return svg(c, W, H)

def laptop():
    W, H = 44, 22
    c = box(W, H, '#C9C4BC', '#EDEAE4', '#9E988F', notch=2)
    return svg(c, W, H)

def mug():
    W, H = 16, 18; c = box(13, 18, '#E9E1D3', '#FBF6EC', '#B9AD9A', notch=1)
    for y in range(5, 12):
        c[(13, y)] = DEEP if y in (5, 11) else None; c[(15, y)] = DEEP
        if y in (5, 11): c[(14, y)] = DEEP
    c = {k: v for k, v in c.items() if v}
    for y in range(6, 11): c[(14, y)] = '#B9AD9A'
    return svg(c, W, H)

def paper():
    W, H = 20, 26; c = box(W, H, '#F4F1EA', '#FFFFFF', '#D8D2C6', notch=1)
    for x in range(3, 11): c[(x, 3)] = ACC; c[(x, 4)] = ACC
    for row in (8, 11, 14, 17):
        for x in range(3, 15 if row != 17 else 10): c[(x, row)] = '#BDB6A9'
    return svg(c, W, H)

glasses = R.pixel_svg(["KKKKKK..KKKKKK", "KWWWWKKKKWWWWK", "KWKKWK..KWKKWK", "KKKKKK..KKKKKK"], 16)

def label(x, y, text, bg, fg, size, rot=0):
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;padding:8px 16px;background:{bg};color:{fg};border:5px solid {DEEP};'
            f'box-shadow:6px 6px 0 {DEEP};font:900 {size}px/1 \'Pretendard\',sans-serif;transform:rotate({rot}deg)">{text}</div>')

TITLES = [("이력서 100번 쓰고", "또 떨어졌다면"), ("만든 사람은", "이걸로 취업했어요"), ("서류 광탈 끝내는", "무료 AI 비서")]

def page(l1, l2):
    stars = ''.join(f'<div style="position:absolute;left:{x}px;top:{y}px;width:10px;height:10px;background:#3A3430"></div>' for x in range(30, 1080, 120) for y in range(40, 1150, 120))
    screen = f'''<div style="position:absolute;left:205px;top:340px;width:670px">
      <div style="font:700 34px/1 'JetBrains Mono',monospace;color:#8A847B;letter-spacing:.12em">&gt; JOB QUEST</div>
      <div style="margin-top:26px;padding:22px 26px;background:#F4F1EA;color:{DEEP};border:6px solid #000;box-shadow:8px 8px 0 #000">
        <div style="font:900 40px/1.1 'Pretendard',sans-serif">B사 · 서버 개발</div>
        <div style="display:flex;align-items:center;justify-content:space-between;margin-top:14px">
          <span style="font:800 84px/1 'JetBrains Mono',monospace;color:#2FA765">4.6<span style="font-size:38px;color:#8A847B"> /5</span></span>
          <span style="padding:6px 18px;border:7px solid #2FA765;color:#2FA765;font:900 50px/1 'Pretendard',sans-serif;transform:rotate(-7deg)">지원 GO</span></div></div>
      <div style="margin-top:28px;padding:16px 26px;background:#2E2A27;border:6px solid #000;display:flex;justify-content:space-between;align-items:center;font:800 36px/1 'Pretendard',sans-serif;color:#BFB8AD">
        <span>A사 · 백엔드 <span style="font-family:'JetBrains Mono';color:#E5534B">3.2</span></span>
        <span style="padding:4px 12px;border:6px solid #E5534B;color:#E5534B;transform:rotate(6deg)">비추</span></div></div>'''
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">{R.font_css()}<style>body{{margin:0}} .hl{{color:{ACC}}}</style></head><body>
<div style="width:1080px;height:1920px;position:relative;overflow:hidden;background:#24201D;{R.SANS};color:#fff;word-break:keep-all">
 {stars}
 <div style="position:absolute;left:-20px;top:1180px">{desk()}</div>
 <div style="position:absolute;left:110px;top:240px">{monitor()}</div>
 {screen}
 <div style="position:absolute;left:840px;top:1010px">{mug()}</div>
 <div style="position:absolute;left:40px;top:1110px;transform:rotate(-8deg)">{paper()}
   <div style="position:absolute;left:24px;top:110px;padding:4px 10px;border:6px solid #E5534B;color:#E5534B;font:900 38px/1 'Pretendard',sans-serif;transform:rotate(-14deg)">불합격</div></div>
 <div style="position:absolute;left:470px;top:1080px">{laptop()}
   {label(30, 40, 'career-ops', ACC, DEEP, 30, -6)}{label(220, 110, 'AI 취업비서', '#1F1E1D', '#F2C14E', 26, 5)}{label(40, 130, 'GO', '#5FD38D', DEEP, 28, -4)}</div>
 <div style="position:absolute;left:210px;top:930px">{R.mascot('happy', 17)}</div>
 <div style="position:absolute;left:226px;top:1020px">{glasses}</div>
 <div style="position:absolute;left:0;right:0;top:1250px;bottom:0;background:linear-gradient(rgba(18,17,16,0),rgba(18,17,16,.9) 30%,#121110)"></div>
 <div style="position:absolute;left:70px;top:1430px;font:700 40px/1 'JetBrains Mono',monospace;color:#E9E3D9">AI TIP</div>
 <h1 style="position:absolute;left:66px;right:40px;top:1490px;margin:0;font-size:112px;line-height:1.14;font-weight:900;letter-spacing:-0.045em">{l1}<br><span class="hl">{l2}</span></h1>
</div></body></html>'''

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    exe = R.chrome(); b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
    pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    for i, t in enumerate(TITLES, 1):
        f = pathlib.Path(f'/home/claude/cover3/c{i}.html'); f.write_text(page(*t), encoding='utf-8')
        pg.goto(f'file://{f}'); pg.wait_for_timeout(400); pg.screenshot(path=f'/home/claude/cover3/cover{i}.png')
    b.close()
