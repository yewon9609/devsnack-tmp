#!/usr/bin/env python3
"""Story reel (9:16 motion graphics + big burned-in subtitles), clauder-style.
Usage: python3 tools/make_story_reel.py story.json OUT_DIR  -> OUT_DIR/story_reel.mp4

story.json:
{"scenes": [
  {"type": "hero", "dur": 3.5, "svg": "path.svg", "label": "...", "title": "line1\\n[[line2]]", "mascot": {...},
   "subs": ["phrase 1", "phrase 2"]},
  {"type": "panel", "dur": 5, "label": "ENGINE", "panel": {...renderer panel...}, "subs": [...]},
  {"type": "checklist", "dur": 5, "label": "...", "items": [["ok", "text"], ["no", "text"]], "subs": [...]},
  {"type": "warn", "dur": 4, "label": "...", "head": "...", "text": "...", "subs": [...]},
  {"type": "outro", "dur": 3.5, "head": "...", "text": "...", "subs": [...]}
]}
Subtitles are spread evenly over the scene. No voice; add music in the Instagram app.
"""
import json, os, pathlib, subprocess, sys, shutil, html as H
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import devsnack_render as R

W, HGT, FPS = 1080, 1920, 30
ACC, BG, DEEP, TX, BODY, MUTED, LINE, PANEL, BOX = R.ACC, R.BG, R.DEEP, R.TX, R.BODY, R.MUTED, R.LINE, R.PANEL, R.BOX
MONO, SANS = R.MONO, R.SANS

EXTRA_CSS = """<style>
@keyframes subshow { 0%, 99.9% { opacity: 1 } 100% { opacity: 0 } }
@keyframes subpop { 0% { transform: scale(1.18) } 60% { transform: scale(.97) } 100% { transform: none } }
.sub { position: absolute; left: 60px; right: 60px; text-align: center; opacity: 0; animation-name: subshow; animation-timing-function: linear; animation-fill-mode: none }
.sub .subtxt { display: inline-block; animation: subpop .14s ease-out both; animation-delay: inherit }
.subtxt { font-size: 78px; font-weight: 700; line-height: 1.25; color: #FFF3C4; -webkit-text-stroke: 12px #121110; paint-order: stroke fill; letter-spacing: -0.02em }
@keyframes chk { 0% { transform: scale(0) rotate(-20deg) } 70% { transform: scale(1.3) } 100% { transform: none } }
.chk { animation: chk .4s steps(5) both }
@keyframes shake { 0%,100% { transform: translateX(0) } 25% { transform: translateX(-10px) } 75% { transform: translateX(10px) } }
.shake { animation: shake .4s steps(4) 3 }
@keyframes grow { from { transform: scaleX(0) } to { transform: none } }
.grow { transform-origin: left; animation: grow .4s steps(6) both }
@keyframes strike { from { transform: scaleX(0) } to { transform: none } }
.strike { transform-origin: left; animation: strike .3s steps(5) both }
@keyframes lit { from { } to { background: #D97757; color: #121110; border-color: #D97757 } }
.lit { animation: lit .2s steps(2) both }
</style>"""


def bg_layer(seed):
    return (f'<div class="grid" style="position: absolute; inset: 0; opacity: .5; background-image: radial-gradient({LINE} 2px, transparent 2px); background-size: 36px 36px"></div>'
            + R.fx_layer(seed, 540, 640).replace('height: 120px', 'height: 160px'))


def label_html(text, top=230):
    if not text:
        return ''
    return (f'<div class="in-left" style="position: absolute; left: 70px; top: {top}px; {MONO}; font-size: 30px; font-weight: 700; color: {TX}; letter-spacing: .12em">'
            f'<span style="color: {ACC}">✳</span>&nbsp;{H.escape(text)}</div>')


def subs_html(subs, dur, top=1300, times=None):
    if not subs:
        return ''
    if times:
        return ''.join(f'<div class="sub" style="top: {top}px; animation-delay: {a:.2f}s; animation-duration: {max(b - a, .25):.2f}s"><span class="subtxt">{R.esc(x)}</span></div>'
                       for x, (a, b) in zip(subs, times))
    seg = dur / len(subs)
    return ''.join(f'<div class="sub" style="top: {top}px; animation-delay: {i * seg + 0.1:.2f}s; animation-duration: {seg - 0.05:.2f}s"><span class="subtxt">{R.esc(s)}</span></div>'
                   for i, s in enumerate(subs))


def chrome(inner, sc, dur):
    return f'''<div style="width: {W}px; height: {HGT}px; position: relative; overflow: hidden; background: {DEEP}; color: {TX}; {SANS}; word-break: keep-all">
{bg_layer(sc.get('label', '') + str(dur))}
<div style="position: absolute; left: 70px; right: 70px; top: 90px; display: flex; justify-content: space-between; {MONO}; font-size: 30px"><span style="color: {ACC}; font-weight: 700">&gt; devsnack</span><span style="color: {MUTED}">@devsnack.kr</span></div>
{inner}
{subs_html(sc.get('subs', []), dur, sc.get('sub_top', 1330), sc.get('sub_times'))}
</div>'''


def widget(w):
    if not w:
        return ''
    t, d0 = w['type'], w.get('delay', 2.0)
    box = f'position: absolute; left: 70px; right: 70px; top: {w.get("top", 870)}px'
    if t == 'widths':  # responsive check: bars per viewport width get PASS
        rows = ''
        for i, px in enumerate(w['items']):
            d = d0 + i * 0.35
            rows += f'''<div style="display: flex; align-items: center; gap: 22px; margin-bottom: 16px"><span style="width: 110px; {MONO}; font-size: 28px; color: {BODY}; text-align: right">{px}</span>
<div style="flex: 1; height: 44px; background: {LINE}; border-radius: 10px; overflow: hidden"><div class="grow" style="animation-delay: {d:.2f}s; height: 100%; width: {int(px) / 1440 * 100:.0f}%; background: {BOX}"></div></div>
<span class="in-pop" style="animation-delay: {d + .3:.2f}s; width: 120px; padding: 6px 0; text-align: center; background: #7BC47F; color: {DEEP}; border-radius: 10px; {MONO}; font-size: 26px; font-weight: 700">PASS</span></div>'''
        return f'<div style="{box}"><div class="in-fade" style="animation-delay: {d0 - .3:.2f}s; {MONO}; font-size: 26px; color: {MUTED}; margin-bottom: 18px">headless Chrome check</div>{rows}</div>'
    if t == 'avoid':  # anti-pattern list, the highlighted one gets struck
        rows = ''
        for i, (txt, hot) in enumerate(w['items']):
            d = d0 + i * 0.3
            strike = f'<div class="strike" style="animation-delay: {d + .35:.2f}s; position: absolute; left: -6px; right: -6px; top: 50%; height: 6px; background: #E5534B"></div>'
            rows += f'<div class="in-left" style="animation-delay: {d:.2f}s; display: flex; align-items: center; gap: 20px; padding: 18px 26px; margin-bottom: 14px; border-radius: 16px; background: {"rgba(229,83,75,.16)" if hot else PANEL}; border: 2px solid {"#E5534B" if hot else BOX}; font-size: 38px; font-weight: 700; color: {TX if hot else BODY}"><span style="color: #E5534B">✕</span><span style="position: relative">{H.escape(txt)}{strike}</span></div>'
        return f'<div style="{box}"><div class="in-fade" style="animation-delay: {d0 - .3:.2f}s; {MONO}; font-size: 28px; color: #E5534B; font-weight: 700; margin-bottom: 18px">AVOID (Anti-patterns)</div>{rows}</div>'
    if t == 'grill':  # AI asks questions in chat bubbles
        rows = ''.join(f'<div class="in-up" style="animation-delay: {d0 + i * 0.55:.2f}s; display: flex; gap: 18px; align-items: flex-start; margin-bottom: 16px"><span style="flex: none; width: 56px; height: 56px; border-radius: 50%; background: {ACC}; color: {DEEP}; display: flex; align-items: center; justify-content: center; font-size: 30px; font-weight: 700">AI</span><span style="padding: 18px 26px; background: {PANEL}; border: 2px solid {BOX}; border-radius: 6px 24px 24px 24px; font-size: 36px; color: {TX}">{H.escape(q)}</span></div>' for i, q in enumerate(w['items']))
        return f'<div style="{box}">{rows}</div>'
    if t == 'pipeline':  # slash commands light up in sequence
        chips = ''.join(f'<span class="lit" style="animation-delay: {d0 + i * w.get('step', 0.3):.2f}s; display: inline-block; margin: 0 14px 18px 0; padding: 16px 26px; border-radius: 16px; border: 2px solid {BOX}; background: {PANEL}; color: {MUTED}; {MONO}; font-size: 36px; font-weight: 700">{H.escape(c)}</span>' for i, c in enumerate(w['items']))
        return f'<div style="{box}">{chips}</div>'
    return ''


ITEMS = {
 'palette': ["....KKKKKK....", "..KKWWWWWWKK..", ".KWWRRWWBBWWK.", "KWWWRRWWBBWWWK", "KWYYWWWWWWWWWK", "KWYYWWWKKWNNWK",
             "KWWWWWKggKNNWK", "KWWWWWWKKWWWWK", ".KWWOOWWWWWWK.", "..KWOOWWWWKK..", "...KKWWWKK....", ".....KKKK....."],
 'book': ["KKKKKKKKKKKKK.", "KOOOOOKBBBBBK.", "KOWWWOKBWWWBKK", "KOOOOOKBBBBBKY", "KOWWOOKBWWBBKY", "KOOOOOKBBBBBKY",
          "KOWWWOKBWWWBKY", "KOOOOOKBBBBBKY", "KKKKKKKKKKKKKY", ".YYYYYYYYYYYYY"],
 'qmark': ["..KKKKKKKKKK..", ".KWWWWWWWWWWK.", "KWWWWKKKWWWWWK", "KWWWKOOOKWWWWK", "KWWWWWWOKWWWWK", "KWWWWWOKWWWWWK",
           "KWWWWWOKWWWWWK", "KWWWWWWWWWWWWK", "KWWWWWOKWWWWWK", ".KWWWWWWWWWWK.", "..KKKKWWKKKK..", "......KWK.....", "......KK......"],
 'shield': ["..KKKKKKKKKK..", ".KBBBBBBBBBBK.", ".KBBBBWWBBBBK.", ".KBBBWWWWBBBK.", ".KBBWWNWWWBBK.", ".KBBWNNNWWBBK.",
            "..KBBWNWWBBK..", "..KBBBWWBBBK..", "...KBBBBBBK...", "....KBBBBK....", ".....KKKK....."],
}
FLAME = [["...O...", "..OYO..", ".OYYYO.", ".OYWYO.", "..OYO..", "..KgK..", "..KgK..", "..KgK.."],
         ["..O....", "..OYO..", ".OYYYO.", ".OYWYO.", "..OYO..", "..KgK..", "..KgK..", "..KgK.."]]

GAME_CSS = """<style>
@keyframes flick { 0%,49% { opacity: 1 } 50%,100% { opacity: 0 } }
.f1 { animation: flick .5s steps(1) infinite } .f2 { animation: flick .5s steps(1) infinite reverse }
@keyframes slotfill { 0% { transform: scale(0) } 60% { transform: scale(1.35) } 100% { transform: none } }
.slotfill { animation: slotfill .45s steps(5) both }
@keyframes ring { 0% { box-shadow: 0 0 0 0 rgba(242,193,78,.9) } 100% { box-shadow: 0 0 0 26px rgba(242,193,78,0) } }
.ring { animation: ring .8s steps(6) infinite }
@keyframes doorL { to { transform: perspective(900px) rotateY(80deg) } }
@keyframes doorR { to { transform: perspective(900px) rotateY(-80deg) } }
.doorL { transform-origin: left; animation: doorL .9s steps(8) both } .doorR { transform-origin: right; animation: doorR .9s steps(8) both }
@keyframes shine { from { opacity: 0 } to { opacity: 1 } }
.shine { animation: shine .9s steps(6) both }
@keyframes itemget { 0% { transform: translateY(80px) scale(.2); opacity: 0 } 60% { transform: translateY(-20px) scale(1.15); opacity: 1 } 100% { transform: none; opacity: 1 } }
.itemget { animation: itemget .6s steps(7) both }
@keyframes walk { from { transform: translateX(-260px) } to { transform: none } }
.walk { animation: walk 1s steps(8) both }
</style>"""


def bricks():
    return (f'<div style="position: absolute; inset: 0; background-color: #1A1715; '
            f'background-image: linear-gradient(#0F0D0C 4px, transparent 4px), linear-gradient(90deg, #0F0D0C 4px, transparent 4px), linear-gradient(90deg, #0F0D0C 4px, transparent 4px); '
            f'background-size: 120px 60px, 120px 120px, 120px 120px; background-position: 0 0, 0 0, 60px 60px; opacity: .9"></div>'
            f'<div style="position: absolute; inset: 0; background: radial-gradient(ellipse at 50% 45%, rgba(217,119,87,.10), rgba(0,0,0,.55) 75%)"></div>')


def torch(x, y):
    a = R.pixel_svg(FLAME[0], 14, 'class="f1" style="position: absolute; left: 0; top: 0"')
    b = R.pixel_svg(FLAME[1], 14, 'class="f2" style="position: absolute; left: 0; top: 0"')
    glow = f'<div style="position: absolute; left: -110px; top: -110px; width: 320px; height: 320px; border-radius: 50%; background: radial-gradient(rgba(242,150,60,.28), rgba(242,150,60,0) 70%)"></div>'
    return f'<div style="position: absolute; left: {x}px; top: {y}px; width: 98px; height: 112px">{glow}{a}{b}</div>'


def hud(stage, got, total=4):
    hearts = '<span style="color: #E5534B">♥♥♥</span>'
    return (f'<div style="position: absolute; left: 70px; right: 70px; top: 90px; display: flex; justify-content: space-between; {MONO}; font-size: 34px; font-weight: 700">'
            f'{hearts}<span style="color: {TX}; letter-spacing: .12em">{H.escape(stage)}</span><span style="color: #F2C14E">★ {got:02d}/{total:02d}</span></div>')


def slots(icons, filled, active=None, top=190, delay=0.0):
    out = ''
    for i, ic in enumerate(icons):
        on = i < filled
        is_new = (active == i)
        inner = (f'<div class="{"slotfill" if is_new else ""}" style="animation-delay: {delay:.2f}s">{R.pixel_svg(ITEMS[ic], 8)}</div>' if on
                 else f'<span style="{MONO}; font-size: 72px; font-weight: 700; color: #E5534B">?</span>')
        bd = '#F2C14E' if is_new else ('#E5534B' if not on else BOX)
        out += (f'<div class="{"ring" if is_new else ""}" style="width: 180px; height: 150px; box-sizing: border-box; border: 6px solid {bd}; background: rgba(18,17,16,.85); '
                f'display: flex; align-items: center; justify-content: center">{inner}</div>')
    return f'<div style="position: absolute; left: 70px; right: 70px; top: {top}px; display: flex; justify-content: space-between">{out}</div>'


def door(x, y, w=380, h=470, opening=None):
    plank = ''.join(f'<div style="position: absolute; left: {k * (w // 4)}px; top: 0; width: 6px; height: 100%; background: #3A2414"></div>' for k in range(1, 4))
    knob = f'<div style="position: absolute; right: 34px; top: {h // 2}px; width: 22px; height: 22px; background: #F2C14E; border: 4px solid {DEEP}"></div>'
    if opening is None:
        leaf = f'<div style="position: absolute; inset: 0; background: #6B4226; border: 8px solid {DEEP}; box-sizing: border-box">{plank}{knob}</div>'
    else:
        half = f'position: absolute; top: 0; width: 50%; height: 100%; background: #6B4226; border: 8px solid {DEEP}; box-sizing: border-box'
        leaf = (f'<div class="shine" style="animation-delay: {opening:.2f}s; position: absolute; inset: 0; background: linear-gradient(#FFF3C4, #F2C14E)"></div>'
                f'<div class="doorL" style="animation-delay: {opening:.2f}s; {half}; left: 0"></div><div class="doorR" style="animation-delay: {opening:.2f}s; {half}; right: 0"></div>')
    frame = f'<div style="position: absolute; left: -30px; top: -30px; right: -30px; bottom: 0; background: #2A2522; border: 8px solid {DEEP}"></div>'
    return f'<div style="position: absolute; left: {x}px; top: {y}px; width: {w}px; height: {h}px">{frame}{leaf}</div>'


def game_html(sc):
    t, dur = sc['type'], sc['dur']
    icons = sc.get('icons', ['palette', 'book', 'qmark', 'shield'])
    base = bricks() + torch(90, 640) + torch(892, 640)
    if t == 'g_intro':
        banner = (f'<div class="in-pop" style="animation-delay: .3s; position: absolute; left: 110px; right: 110px; top: 400px; padding: 26px 0; text-align: center; '
                  f'background: {DEEP}; border: 6px solid {TX}; font-size: 54px; font-weight: 700">{R.esc(sc.get("banner", ""))}</div>')
        inner = (hud(sc.get('stage', 'STAGE 1-1'), 0) + banner + door(350, 640) +
                 f'<div class="walk" style="position: absolute; left: 160px; top: 930px">{R.mascot("sweat", 12)}</div>' +
                 f'<div style="position: absolute; left: 0; right: 0; top: 1110px; height: 40px; background: #2A2522; border-top: 8px solid {DEEP}"></div>' +
                 slots(icons, 0, top=1200))
        sc.setdefault('sub_top', 1480)
    elif t == 'g_item':
        k = sc['idx']
        get = (f'<div class="itemget" style="animation-delay: .05s; position: absolute; left: 50%; top: 400px; margin-left: -{len(ITEMS[icons[k]][0]) * 13 // 2}px">{R.pixel_svg(ITEMS[icons[k]], 13)}</div>'
               f'<div class="in-pop" style="animation-delay: .3s; position: absolute; left: 0; right: 0; top: 590px; text-align: center; {MONO}; font-size: 40px; font-weight: 700; color: #F2C14E; letter-spacing: .1em">ITEM GET!</div>'
               f'<div class="in-up" style="animation-delay: .4s; position: absolute; left: 0; right: 0; top: 650px; text-align: center; font-size: 76px; font-weight: 700; letter-spacing: -0.03em">{R.esc(sc["name"])}</div>')
        card = (f'<div class="in-panel" style="animation-delay: .65s; position: absolute; left: 70px; right: 70px; top: 790px; box-sizing: border-box; padding: 26px 34px; background: rgba(18,17,16,.92); border: 4px solid {BOX}; '
                f'display: flex; align-items: center; justify-content: space-between">'
                f'<span style="{MONO}; font-size: 28px; color: {BODY}">{H.escape(sc["repo"].split("/")[0])}/<b style="color: {TX}">{H.escape(sc["repo"].split("/")[1])}</b></span>'
                f'<span class="pop" style="padding: 8px 20px; border: 3px solid #F2C14E; {MONO}; font-size: 34px; font-weight: 700; color: #F2C14E">★ {R.count_html(sc["stars"])}</span></div>')
        w = dict(sc.get('widget') or {}); w.setdefault('top', 930)
        inner = hud(sc.get('stage', 'STAGE 1-1'), k + 1) + slots(icons, k + 1, k, delay=.25) + get + card + widget(w if sc.get('widget') else None)
        sc.setdefault('sub_top', 1480)
    elif t == 'g_outro':
        inner = (hud(sc.get('stage', 'STAGE 1-1'), 4) + slots(icons, 4) + door(350, 560, opening=.5) +
                 f'<div class="in-pop" style="animation-delay: 1.3s; position: absolute; left: 0; right: 0; top: 400px; text-align: center; {MONO}; font-size: 60px; font-weight: 700; color: #F2C14E; letter-spacing: .08em">STAGE CLEAR!</div>'
                 f'<div class="walk" style="animation-delay: .9s; position: absolute; left: 440px; top: 850px">{R.mascot("happy", 12)}</div>'
                 f'<div style="position: absolute; left: 0; right: 0; top: 1030px; height: 40px; background: #2A2522; border-top: 8px solid {DEEP}"></div>'
                 f'<div class="in-up" style="animation-delay: 1.6s; position: absolute; left: 70px; right: 70px; top: 1120px; text-align: center; font-size: 56px; font-weight: 700; line-height: 1.3">{R.br(sc.get("head", ""))}</div>')
        sc.setdefault('sub_top', 1480)
    return f"""<div style="width: {W}px; height: {HGT}px; position: relative; overflow: hidden; background: {DEEP}; color: {TX}; {SANS}; word-break: keep-all">
{base}{inner}
<div style="position: absolute; right: 70px; bottom: 60px; {MONO}; font-size: 26px; color: {MUTED}">@devsnack.kr</div>
{subs_html(sc.get('subs', []), dur, sc.get('sub_top', 1480), sc.get('sub_times'))}
</div>"""


def scene_html(sc):
    if 'dur' not in sc:
        sc['dur'] = round(len(sc.get('subs', [])) * sc.get('pace', 0.62) + 0.5, 2)
    t, dur = sc['type'], sc['dur']
    if t.startswith('g_'):
        return game_html(sc)
    if t == 'hero':
        svg = pathlib.Path(sc['svg']).read_text(encoding='utf-8') if sc.get('svg') else ''
        m = sc.get('mascot') or {}
        hero = ''
        if m:
            hat = R.pixel_svg(["....YYYYYY....", "...YYYYYYYY...", "..YYYYYYYYYY..", "YYYYYYYYYYYYYY"], 12) if m.get('hat') else ''
            hero = f'<div class="bob" style="position: absolute; left: {m.get("x", 470)}px; top: {m.get("y", 640)}px">{hat}<div style="margin-top: -10px">{R.mascot(m.get("mood", "happy"), 12)}</div></div>'
            if m.get('bubble'):
                hero += f'<div class="in-pop" style="animation-delay: .6s; position: absolute; left: {m.get("x", 470) + 180}px; top: {m.get("y", 640) - 30}px; background: {TX}; color: {DEEP}; {MONO}; font-weight: 700; font-size: 34px; padding: 14px 22px; border: 6px solid {DEEP}; box-shadow: 6px 6px 0 {ACC}">{H.escape(m["bubble"])}</div>'
        title = R.lines_in(sc.get('title', ''), 0.3, 0.2)
        inner = f'''<div class="in-fade" style="position: absolute; left: 0; top: 200px; width: {W}px; height: 680px; overflow: hidden">{svg}</div>{hero}
<div style="position: absolute; left: 0; right: 0; top: 860px; height: 80px; background: linear-gradient(to bottom, rgba(18,17,16,0), {DEEP})"></div>
{label_html(sc.get('label'), 960)}
<h1 style="position: absolute; left: 70px; right: 70px; top: 1010px; margin: 0; font-size: 104px; line-height: 1.18; font-weight: 700; letter-spacing: -0.035em; overflow: hidden">{title}</h1>'''
        sc.setdefault('sub_top', 1560)
        return chrome(inner, sc, dur)
    if t == 'panel':
        inner = f'''{label_html(sc.get('label'))}
<div class="in-panel" style="position: absolute; left: 50%; top: 320px; width: 904px; margin-left: -452px"><div style="transform: scale(1.05); transform-origin: top center"><div class="glow">{R.panel(sc['panel'])}</div></div></div>
<div class="in-up" style="animation-delay: .5s; position: absolute; left: 70px; right: 70px; top: 880px; font-size: 44px; font-weight: 700; color: {TX}">{R.esc(sc.get('caption', ''))}</div>'''
        return chrome(inner, sc, dur)
    if t == 'checklist':
        rows = ''
        for i, (k, txt) in enumerate(sc['items']):
            ok = k == 'ok'
            mark = f'<span class="chk" style="animation-delay: {0.5 + i * 0.6:.2f}s; flex: none; width: 76px; height: 76px; border-radius: 16px; background: {"#7BC47F" if ok else "#E5534B"}; color: {DEEP}; display: flex; align-items: center; justify-content: center; font-size: 50px; font-weight: 700">{"✓" if ok else "✕"}</span>'
            rows += f'<div class="in-left" style="animation-delay: {0.35 + i * 0.6:.2f}s; display: flex; align-items: center; gap: 30px; padding: 30px 34px; margin-bottom: 24px; background: {PANEL}; border: 2px solid {BOX}; border-radius: 24px; font-size: 44px; font-weight: 700; color: {TX if ok else BODY}">{mark}<span>{R.esc(txt)}</span></div>'
        inner = f'''{label_html(sc.get('label'))}<div style="position: absolute; left: 70px; right: 70px; top: 320px">{rows}</div>'''
        return chrome(inner, sc, dur)
    if t == 'slop':
        cards = ''
        for i in range(3):
            cards += f'''<div class="dropin" style="animation-delay: {0.2 + i * 0.35:.2f}s; position: absolute; left: {70 + i * 40}px; top: {300 + i * 150}px; width: 820px; height: 420px; box-sizing: border-box; border-radius: 22px; overflow: hidden; background: #FFFFFF; box-shadow: 0 20px 50px rgba(0,0,0,.55)">
<div style="height: 44px; background: #EEE; display: flex; align-items: center; gap: 10px; padding: 0 18px"><span style="width: 14px; height: 14px; border-radius: 50%; background: #E5534B"></span><span style="width: 14px; height: 14px; border-radius: 50%; background: #F2C14E"></span><span style="width: 14px; height: 14px; border-radius: 50%; background: #7BC47F"></span><span style="margin-left: 14px; {MONO}; font-size: 20px; color: #888">my-app-{i + 1}.vercel.app</span></div>
<div style="height: 376px; background: linear-gradient(135deg, #6D5BF5, #A855F7 55%, #EC4899); padding: 44px 50px; box-sizing: border-box; color: #FFF">
<div style="font-size: 50px; font-weight: 700; line-height: 1.15">Build faster<br>with AI ✨</div>
<div style="margin-top: 18px; font-size: 24px; opacity: .85">The all-in-one platform for modern teams</div>
<div style="display: flex; gap: 16px; margin-top: 30px"><span style="padding: 14px 28px; background: #FFF; color: #6D5BF5; border-radius: 999px; font-size: 24px; font-weight: 700">Get Started</span><span style="padding: 14px 28px; border: 2px solid #FFF; border-radius: 999px; font-size: 24px">Learn more</span></div></div></div>'''
        stamp = f'<div class="in-pop" style="animation-delay: 1.6s; position: absolute; right: 70px; top: 760px; padding: 16px 30px; border: 8px solid #E5534B; color: #E5534B; font-size: 64px; font-weight: 700; transform: rotate(-10deg); background: rgba(18,17,16,.85)">다 똑같음</div>'
        title = R.lines_in(sc.get('title', ''), 1.9, 0.2)
        inner = f'''{cards}{stamp}<div style="position: absolute; left: 0; right: 0; top: 940px; height: 140px; background: linear-gradient(to bottom, rgba(18,17,16,0), {DEEP} 70%)"></div>
<h1 style="position: absolute; left: 70px; right: 70px; top: 1040px; margin: 0; font-size: 100px; line-height: 1.18; font-weight: 700; letter-spacing: -0.035em">{title}</h1>'''
        sc.setdefault('sub_top', 1580)
        return chrome(inner, sc, dur)
    if t == 'repo':
        feats = ''.join(f'<div class="in-left" style="animation-delay: {sc.get('feat_delay', 1.0) + i * 0.35:.2f}s; display: flex; gap: 18px; align-items: flex-start; margin-bottom: 22px; font-size: 40px; line-height: 1.35; color: {TX}"><span style="color: {ACC}; flex: none">▸</span><span>{R.esc(f)}</span></div>' for i, f in enumerate(sc.get('feats', [])))
        inner = f'''<div class="in-pop" style="position: absolute; left: 70px; top: 230px; width: 130px; height: 130px; background: {ACC}; color: {DEEP}; border-radius: 26px; box-shadow: 0 10px 0 #9C4F35; display: flex; align-items: center; justify-content: center; {MONO}; font-size: 76px; font-weight: 700">{sc['rank']}</div>
<div class="in-left" style="animation-delay: .15s; position: absolute; left: 230px; right: 70px; top: 238px; font-size: 64px; font-weight: 700; line-height: 1.15; letter-spacing: -0.03em">{R.br(sc['name'])}</div>
<div class="in-panel" style="animation-delay: .35s; position: absolute; left: 70px; right: 70px; top: 440px; box-sizing: border-box; padding: 40px 44px; background: {PANEL}; border: 2px solid {BOX}; border-radius: 28px">
<div style="display: flex; align-items: center; gap: 18px; {MONO}; font-size: 30px; color: {BODY}"><span style="width: 52px; height: 52px; border-radius: 12px; background: {BOX}; display: flex; align-items: center; justify-content: center; color: {TX}">⌂</span><span>{H.escape(sc['repo'].split('/')[0])}/<b style="color: {TX}">{H.escape(sc['repo'].split('/')[1])}</b></span></div>
<div style="margin-top: 26px; font-size: 32px; color: {MUTED}; line-height: 1.45">{H.escape(sc.get('desc', ''))}</div>
<div style="display: flex; align-items: center; gap: 18px; margin-top: 30px"><span class="pop" style="padding: 12px 26px; background: rgba(242,193,78,.15); border: 2px solid #F2C14E; border-radius: 999px; {MONO}; font-size: 36px; font-weight: 700; color: #F2C14E">★ {R.count_html(sc['stars'])}</span><span style="{MONO}; font-size: 24px; color: {MUTED}">GitHub stars</span></div></div>
<div style="position: absolute; left: 80px; right: 70px; top: 900px">{feats}</div>{widget(sc.get('widget'))}'''
        return chrome(inner, sc, dur)
    if t == 'warn':
        icon = R.pixel_svg(R.ICONS[sc.get('icon', 'warn')], 22)
        inner = f'''{label_html(sc.get('label'))}
<div class="in-pop" style="position: absolute; left: 50%; top: 330px; margin-left: -154px"><div class="shake" style="animation-delay: .6s">{icon}</div></div>
<div class="in-up" style="animation-delay: .5s; position: absolute; left: 70px; right: 70px; top: 640px; text-align: center; font-size: 84px; font-weight: 700; line-height: 1.2">{R.br(sc.get('head', ''))}</div>
<div class="in-up" style="animation-delay: .8s; position: absolute; left: 70px; right: 70px; top: 880px; text-align: center; font-size: 42px; color: {BODY}; line-height: 1.45">{R.br(sc.get('text', ''))}</div>'''
        return chrome(inner, sc, dur)
    if t == 'outro':
        inner = f'''<div class="bob" style="position: absolute; left: 50%; top: 360px; margin-left: -144px">{R.mascot('happy', 18)}</div>
<div class="in-up" style="animation-delay: .3s; position: absolute; left: 70px; right: 70px; top: 700px; text-align: center; font-size: 84px; font-weight: 700; line-height: 1.2">{R.br(sc.get('head', ''))}</div>
<div class="in-pop" style="animation-delay: .7s; position: absolute; left: 140px; right: 140px; top: 960px; padding: 34px; background: {ACC}; color: {DEEP}; border-radius: 24px; text-align: center; font-size: 44px; font-weight: 700">{R.br(sc.get('text', ''))}</div>'''
        sc.setdefault('sub_top', 1330)
        return chrome(inner, sc, dur)
    raise SystemExit(f'unknown scene type {t}')


def main():
    story = json.load(open(sys.argv[1], encoding='utf-8'))
    out = pathlib.Path(sys.argv[2]).resolve(); out.mkdir(parents=True, exist_ok=True)
    css = R.font_css()
    from playwright.sync_api import sync_playwright
    parts = []
    with sync_playwright() as p:
        exe = R.chrome(); b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = b.new_page(viewport={'width': W, 'height': HGT})
        for si, sc in enumerate(story['scenes']):
            f = out / f'_scene{si}.html'
            f.write_text(f'<!doctype html><html lang="ko"><head><meta charset="utf-8">{css}<style>body{{margin:0}}</style>{R.ANIM_CSS}{EXTRA_CSS}{GAME_CSS}</head><body>{scene_html(sc)}</body></html>', encoding='utf-8')
            pg.goto(f'file://{f}'); pg.wait_for_timeout(400)
            fr = out / f'_f{si}'; fr.mkdir(exist_ok=True)
            n = int(sc['dur'] * FPS)
            for k in range(n):
                pg.evaluate(f"() => document.getAnimations().forEach(a => {{ a.pause(); a.currentTime = {k * 1000 / FPS}; }})")
                pg.screenshot(path=str(fr / f'{k:04d}.png'))
            if si == 0:
                pg.evaluate("() => document.getAnimations().forEach(a => { a.pause(); a.currentTime = 2500; })")
                pg.screenshot(path=str(out / 'story_cover.png'))
            seg = out / f'_seg{si}.mp4'
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(fr / '%04d.png'),
                            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', str(FPS), str(seg)], check=True)
            shutil.rmtree(fr); f.unlink(); parts.append(seg)
        b.close()
    lst = out / '_list.txt'; lst.write_text(''.join(f"file '{x}'\n" for x in parts))
    if any(sc.get('audio') for sc in story['scenes']):
        aparts = []
        for si, sc in enumerate(story['scenes']):
            a = out / f'_a{si}.wav'
            src = ['-i', sc['audio']] if sc.get('audio') else ['-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono']
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *src, '-af', f"adelay={int(sc.get('audio_offset', 0) * 1000)}:all=1,apad,aresample=44100",
                            '-ac', '1', '-t', f"{int(sc['dur'] * FPS) / FPS:.4f}", str(a)], check=True)
            aparts.append(a)
        alst = out / '_alist.txt'; alst.write_text(''.join(f"file '{x}'\n" for x in aparts))
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(alst), str(out / '_audio.wav')], check=True)
        ain = ['-i', str(out / '_audio.wav')]
    else:
        ain = ['-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo']
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(lst),
                    *ain, '-shortest', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k',
                    '-movflags', '+faststart', str(out / 'story_reel.mp4')], check=True)
    for x in parts: x.unlink()
    lst.unlink()
    print(out / 'story_reel.mp4')


if __name__ == '__main__':
    main()
