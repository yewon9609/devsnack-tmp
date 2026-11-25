import math
PAL = {'K': '#3B2414', 'C': '#E9A95C', 'L': '#F7CF8A', 'D': '#C4813F', 'H': '#6B3A1E', 'h': '#8A4F2A', 'E': '#1C1412', 'W': '#FFFFFF', 'B': '#F49A8C'}

def grid(mood='happy'):
    N = 22; g = [['.'] * N for _ in range(N)]
    cx = cy = (N - 1) / 2; r = N / 2 - .3
    for y in range(N):
        for x in range(N):
            d = math.hypot(x - cx, y - cy)
            if d <= r:
                g[y][x] = 'C'
                if d > r - 1.15: g[y][x] = 'K'
                elif (x - cx) + (y - cy) < -9: g[y][x] = 'L'
                elif (x - cx) + (y - cy) > 8.5 and d > r - 3.2: g[y][x] = 'D'
    # chips
    for (x, y) in [(5, 4), (6, 4), (5, 5), (14, 3), (15, 3), (16, 6), (17, 6), (16, 7), (4, 15), (5, 15), (15, 16), (16, 16), (16, 17), (10, 18), (11, 18), (9, 3)]:
        if g[y][x] in 'CLD': g[y][x] = 'H'
    for (x, y) in [(6, 5), (15, 4), (17, 7), (5, 16), (16, 17)]:
        if g[y][x] == 'H': g[y][x] = 'h'
    # eyes 2x3 with highlight
    for ex in (7, 13):
        for yy in (9, 10, 11):
            for xx in (ex, ex + 1): g[yy][xx] = 'E'
        g[9][ex] = 'W'
        if mood == 'sweat': g[9][ex + 1] = 'W'
    # blush
    for (x, y) in [(4, 12), (5, 12), (16, 12), (17, 12)]: g[y][x] = 'B'
    # mouth
    if mood == 'happy':
        for (x, y) in [(9, 13), (12, 13), (10, 14), (11, 14)]: g[y][x] = 'E'
    elif mood == 'sweat':
        for (x, y) in [(9, 14), (10, 13), (11, 13), (12, 14)]: g[y][x] = 'E'
    elif mood == 'shock':
        for (x, y) in [(10, 13), (11, 13), (10, 14), (11, 14)]: g[y][x] = 'E'
    return [''.join(r) for r in g]

def svg(mood='happy', p=12):
    p = max(1, round(p))
    rows = grid(mood); n = len(rows)
    r = ''.join(f'<rect x="{x*p}" y="{y*p}" width="{p}" height="{p}" fill="{PAL[c]}"/>' for y, row in enumerate(rows) for x, c in enumerate(row) if c != '.')
    return f'<svg width="{n*p}" height="{n*p}" viewBox="0 0 {n*p} {n*p}" shape-rendering="crispEdges" style="display:block">{r}</svg>'

if __name__ == '__main__':
    html = '<html><body style="margin:0;background:#24201D;display:flex;gap:40px;padding:40px">' + ''.join(svg(m, 16) for m in ('happy', 'sweat', 'shock')) + '</body></html>'
    open('/home/claude/mascot/preview.html', 'w').write(html)
