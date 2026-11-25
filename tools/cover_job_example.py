import sys, pathlib, random
sys.path.insert(0, '/home/claude/devsnack-tmp/tools')
import devsnack_render as R
from make_story_reel import ITEMS
ACC, DEEP, TX = R.ACC, R.DEEP, R.TX
rnd = random.Random(4)
stars = ''.join(f'<div style="position:absolute;left:{rnd.randint(0,1070)}px;top:{rnd.randint(40,900)}px;width:{rnd.choice([6,8,10])}px;height:{rnd.choice([6,8,10])}px;background:{rnd.choice(["#FFF3C4","#C9B6FF","#FFFFFF"])};opacity:{rnd.choice([.5,.8,1])}"></div>' for _ in range(60))
sky = ''
for b in range(9):
    x = b * 125 - 20; h = rnd.randint(260, 520)
    sky += f'<div style="position:absolute;left:{x}px;top:{1080-h}px;width:118px;height:{h}px;background:#241B36"></div>'
    for r in range(h // 60):
        for c in range(3):
            if rnd.random() < .35:
                sky += f'<div style="position:absolute;left:{x+14+c*34}px;top:{1080-h+24+r*60}px;width:20px;height:26px;background:{rnd.choice(["#F2C14E","#D97757"])};opacity:.7"></div>'
def card(x, y, r, company, score, ok):
    col = '#5FD38D' if ok else '#E5534B'
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:300px;padding:22px 24px;background:#F4F1EA;border:7px solid {DEEP};box-shadow:10px 10px 0 rgba(0,0,0,.45);transform:rotate({r}deg);color:{DEEP}">'
            f'<div style="font-size:30px;font-weight:900">{company}</div>'
            f'<div style="margin-top:10px;height:10px;width:200px;background:#C9C3B8"></div><div style="margin-top:10px;height:10px;width:150px;background:#C9C3B8"></div>'
            f'<div style="display:flex;align-items:center;justify-content:space-between;margin-top:18px">'
            f'<span style="{R.MONO};font-size:44px;font-weight:900;color:{col}">{score}</span>'
            f'<span style="padding:6px 14px;border:6px solid {col};color:{col};font-size:34px;font-weight:900;transform:rotate(-8deg)">{"지원 GO" if ok else "비추"}</span></div></div>')
cards = card(70, 360, -9, 'A사 · 백엔드', '3.2', False) + card(690, 330, 8, 'C사 · 서버', '2.8', False) + card(390, 220, -2, 'B사 · 개발', '4.6', True)
glass = R.pixel_svg(["....KKKK.....", "..KKWWWWKK...", ".KWWBBBBWWK..", "KWWB....BWWK.", "KWB......BWK.", "KWB......BWK.", "KWWB....BWWK.", ".KWWBBBBWWK..", "..KKWWWWKKK..", "....KKKK.KOK.", ".........KOOK", "..........KOK", "...........K."], 17)
cookie = R.mascot('happy', 20)
bubble = (f'<div style="position:absolute;left:560px;top:760px;background:#FFFFFF;color:{DEEP};font-size:70px;font-weight:900;padding:14px 30px;border:9px solid {DEEP};box-shadow:10px 10px 0 {ACC}">여기만 넣어!</div>')
spark = lambda x, y, s: f'<div style="position:absolute;left:{x}px;top:{y}px;width:{s}px;height:{s}px;background:#F2C14E;clip-path:polygon(50% 0,62% 38%,100% 50%,62% 62%,50% 100%,38% 62%,0 50%,38% 38%)"></div>'
html = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">{R.font_css()}<style>body{{margin:0}}</style></head><body>
<div style="width:1080px;height:1920px;position:relative;overflow:hidden;background:linear-gradient(#120E1E,#1E1630 45%,#1F1E1D 62%);color:{TX};{R.SANS};word-break:keep-all">
{stars}{sky}
<div style="position:absolute;left:0;right:0;top:980px;height:140px;background:linear-gradient(rgba(31,30,29,0),#1F1E1D)"></div>
<div style="position:absolute;left:0;right:0;top:1110px;bottom:0;background:#1F1E1D"></div>
<div style="position:absolute;left:310px;top:420px;width:460px;height:460px;border-radius:50%;background:radial-gradient(rgba(242,193,78,.35),rgba(242,193,78,0) 70%)"></div>
{cards}
<div style="position:absolute;left:200px;top:660px">{cookie}</div>
<div style="position:absolute;left:520px;top:530px">{R.pixel_svg(['...KK...', '..KYYK..', '.KYYYYK.', 'KYYYYYYK', 'KKKYYKKK', '..KYYK..', '..KYYK..', '..KYYK..', '..KKKK..'], 16)}</div>
{bubble}
{spark(150,720,46)}{spark(930,860,38)}{spark(560,150,34)}{spark(90,980,30)}
<div style="position:absolute;left:70px;top:1150px;padding:10px 28px;background:{ACC};color:{DEEP};border-radius:999px;{R.MONO};font-size:38px;font-weight:900">AI TIP</div>
<h1 style="position:absolute;left:70px;right:50px;top:1245px;margin:0;font-size:118px;line-height:1.16;font-weight:900;letter-spacing:-0.045em">이력서 <span style="color:{ACC}">붙을 곳에만</span><br>넣는 방법</h1>
<div style="position:absolute;left:72px;top:1555px;font-size:42px;font-weight:700;color:#BFB8AD">무료 AI 취업 비서 · 별 8만 개</div>
<div style="position:absolute;right:70px;bottom:90px;{R.MONO};font-size:30px;color:#8A847B">@devsnack.kr</div>
</div></body></html>'''
pathlib.Path('/home/claude/cover/cover.html').write_text(html, encoding='utf-8')
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    exe = R.chrome(); b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
    pg = b.new_page(viewport={'width': 1080, 'height': 1920}); pg.goto('file:///home/claude/cover/cover.html'); pg.wait_for_timeout(500)
    pg.screenshot(path='/home/claude/cover/cover.png'); b.close()
