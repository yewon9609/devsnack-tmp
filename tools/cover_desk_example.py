import sys, pathlib
sys.path.insert(0, '/home/claude/devsnack-tmp/tools')
import devsnack_render as R
ACC = R.ACC
TITLES = [
    ("AI TIP", "이력서 100번 쓰고", "<span class='hl'>또 떨어졌다면</span>"),
    ("AI TIP", "만든 사람은", "<span class='hl'>이걸로 취업했어요</span>"),
    ("AI TIP", "서류 광탈 끝내는", "<span class='hl'>무료 AI 비서</span>"),
]
def page(label, l1, l2):
    chips = ''.join(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{s}px;height:{s*0.8}px;border-radius:40%;background:radial-gradient(circle at 35% 30%,#7A4A2A,#3B2010)"></div>' for x, y, s in [(70,80,46),(190,60,38),(250,150,44),(110,190,40),(200,240,30),(60,250,28)])
    cookie = f'''<div style="position:absolute;left:150px;top:1010px;width:330px;height:330px">
      <div style="position:absolute;inset:0;border-radius:50%;background:radial-gradient(circle at 35% 30%,#F6C27A,#D9914A 55%,#A8642A);box-shadow:inset -20px -26px 40px rgba(90,40,10,.45),0 30px 40px rgba(0,0,0,.45)"></div>
      {chips}
      <div style="position:absolute;left:40px;top:120px;width:250px;height:70px;display:flex;justify-content:space-between">
        <div style="width:110px;height:70px;border:12px solid #1C1A19;border-radius:18px;background:rgba(255,255,255,.18);box-sizing:border-box"></div>
        <div style="width:110px;height:70px;border:12px solid #1C1A19;border-radius:18px;background:rgba(255,255,255,.18);box-sizing:border-box"></div></div>
      <div style="position:absolute;left:150px;top:138px;width:30px;height:12px;background:#1C1A19"></div>
      <div style="position:absolute;left:78px;top:142px;font:900 40px/1 sans-serif;color:#1C1A19">&gt;</div><div style="position:absolute;left:222px;top:142px;font:900 40px/1 sans-serif;color:#1C1A19">&lt;</div>
      <div style="position:absolute;left:120px;top:225px;width:90px;height:34px;border-bottom:12px solid #1C1A19;border-radius:0 0 60px 60px"></div></div>'''
    laptop = f'''<div style="position:absolute;left:420px;top:1150px;width:400px;height:230px;transform:perspective(900px) rotateX(8deg) rotateY(-14deg)">
      <div style="position:absolute;inset:0;border-radius:24px;background:linear-gradient(135deg,#E9E6E1,#BDB8B0);box-shadow:inset -10px -14px 24px rgba(0,0,0,.25),0 26px 30px rgba(0,0,0,.45)"></div>
      <div style="position:absolute;left:40px;top:40px;padding:10px 18px;background:{ACC};border-radius:14px;transform:rotate(-8deg);font:900 30px/1 'Pretendard',sans-serif;color:#1F1E1D">career-ops</div>
      <div style="position:absolute;left:230px;top:110px;padding:8px 16px;background:#1F1E1D;border-radius:14px;transform:rotate(6deg);font:900 26px/1 monospace;color:#F2C14E">AI 취업비서</div>
      <div style="position:absolute;left:70px;top:140px;width:70px;height:70px;border-radius:50%;background:#5FD38D;transform:rotate(-6deg);font:900 26px/70px sans-serif;color:#1F1E1D;text-align:center">GO</div></div>'''
    monitor = f'''<div style="position:absolute;left:90px;top:300px;width:900px;height:760px;border-radius:56px;background:linear-gradient(160deg,#F1ECE4,#CFC7BB 70%,#B7AEA0);box-shadow:inset -18px -24px 40px rgba(0,0,0,.25),inset 14px 14px 30px rgba(255,255,255,.6),0 40px 60px rgba(0,0,0,.5)">
      <div style="position:absolute;left:60px;top:56px;right:60px;bottom:120px;border-radius:34px;background:radial-gradient(circle at 40% 30%,#2E2A27,#141211);box-shadow:inset 0 0 40px rgba(0,0,0,.8)">
        <div style="position:absolute;left:54px;top:40px;font:700 34px/1 'JetBrains Mono',monospace;color:#8A847B;letter-spacing:.1em">JOB QUEST</div>
        <div style="position:absolute;left:54px;top:110px;right:54px;padding:26px 30px;border-radius:20px;background:#F4F1EA;color:#1F1E1D;box-shadow:0 10px 0 rgba(0,0,0,.35)">
          <div style="font:900 40px/1.1 'Pretendard',sans-serif">B사 · 서버 개발</div>
          <div style="display:flex;align-items:center;justify-content:space-between;margin-top:18px"><span style="font:900 86px/1 'JetBrains Mono',monospace;color:#2FA765">4.6<span style="font-size:40px;color:#8A847B"> / 5</span></span>
          <span style="padding:8px 20px;border:8px solid #2FA765;color:#2FA765;border-radius:14px;font:900 52px/1 'Pretendard',sans-serif;transform:rotate(-8deg)">지원 GO</span></div></div>
        <div style="position:absolute;left:54px;top:400px;right:54px;padding:20px 30px;border-radius:20px;background:#3A3532;color:#BFB8AD;display:flex;justify-content:space-between;align-items:center;font:800 36px/1 'Pretendard',sans-serif">
          <span>A사 · 백엔드 <span style="font-family:'JetBrains Mono';color:#E5534B">3.2</span></span><span style="padding:6px 14px;border:6px solid #E5534B;color:#E5534B;border-radius:12px;transform:rotate(6deg)">비추</span></div>
      </div>
      <div style="position:absolute;right:80px;bottom:44px;width:34px;height:34px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#FFB08A,{ACC})"></div>
      <div style="position:absolute;left:80px;bottom:52px;width:240px;height:16px;border-radius:8px;background:rgba(0,0,0,.18)"></div></div>'''
    props = f'''<div style="position:absolute;left:860px;top:1080px;width:150px;height:190px;border-radius:20px 20px 36px 36px;background:linear-gradient(90deg,#E8E3DB,#BEB6AA);box-shadow:0 20px 30px rgba(0,0,0,.4)">
        <div style="position:absolute;right:-48px;top:40px;width:60px;height:80px;border:16px solid #CFC7BB;border-left:none;border-radius:0 40px 40px 0"></div></div>
      <div style="position:absolute;left:30px;top:1260px;width:190px;height:240px;background:#F4F1EA;transform:rotate(-10deg);box-shadow:0 18px 24px rgba(0,0,0,.4)">
        <div style="position:absolute;left:28px;top:70px;padding:6px 14px;border:7px solid #E5534B;color:#E5534B;font:900 40px/1 'Pretendard',sans-serif;transform:rotate(-14deg)">불합격</div></div>'''
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">{R.font_css()}<style>body{{margin:0}} .hl{{color:{ACC}}}</style></head><body>
<div style="width:1080px;height:1920px;position:relative;overflow:hidden;background:#2A2522;{R.SANS};color:#fff;word-break:keep-all">
 <div style="position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.05) 2px,transparent 2px),linear-gradient(90deg,rgba(255,255,255,.05) 2px,transparent 2px);background-size:60px 60px"></div>
 <div style="position:absolute;inset:0;background:radial-gradient(ellipse at 50% 35%,rgba(217,119,87,.28),rgba(0,0,0,0) 60%)"></div>
 <div style="position:absolute;left:-40px;right:-40px;top:1240px;height:700px;background:linear-gradient(#C9824E,#8E5530);box-shadow:inset 0 30px 40px rgba(255,220,180,.25)"></div>
 {monitor}{props}{laptop}{cookie}
 <div style="position:absolute;left:0;right:0;top:1180px;bottom:0;background:linear-gradient(rgba(18,17,16,0),rgba(18,17,16,.92) 38%,#121110)"></div>
 <div style="position:absolute;left:70px;top:1415px;font:700 40px/1 'Pretendard',sans-serif;color:#E9E3D9;letter-spacing:.02em">{label}</div>
 <h1 style="position:absolute;left:66px;right:40px;top:1475px;margin:0;font-size:112px;line-height:1.14;font-weight:900;letter-spacing:-0.045em;text-shadow:0 6px 20px rgba(0,0,0,.6)">{l1}<br>{l2}</h1>
</div></body></html>'''
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    exe = R.chrome(); b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
    pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    for i, t in enumerate(TITLES, 1):
        f = pathlib.Path(f'/home/claude/cover2/c{i}.html'); f.write_text(page(*t), encoding='utf-8')
        pg.goto(f'file://{f}'); pg.wait_for_timeout(400); pg.screenshot(path=f'/home/claude/cover2/cover{i}.png')
    b.close()
