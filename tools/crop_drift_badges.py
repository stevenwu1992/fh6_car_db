"""把 8 个分级徽章从素材图里切出来，白底转透明，输出到 output/assets/tier/。"""
from PIL import Image
import pathlib
from collections import deque

SRC = pathlib.Path(r"C://Users//STWU//.workbuddy//clipboard-images//clipboard-2026-11-26T10-06-38-162Z-e9d05d68.jpg")
OUT = pathlib.Path("output/assets/tier/drift")
NAMES = [["s", "a", "b", "c"], ["d", "t2", "t3", "unknown"]]

OUT.mkdir(parents=True, exist_ok=True)
im = Image.open(SRC).convert("RGB")
W, H = im.size
px = im.load()

def is_bg(p):
    r, g, b = p
    mx, mn = max(p), min(p)
    return mn > 232 and (mx - mn) < 14   # 近白且低饱和

# 逐列/逐行统计前景像素，按空白带切出 4 列 2 行
cols = [any(not is_bg(px[x, y]) for y in range(H)) for x in range(W)]
rows = [any(not is_bg(px[x, y]) for x in range(W)) for y in range(H)]

def bands(flags, min_gap=6):
    out, start = [], None
    gap = 0
    for i, f in enumerate(flags):
        if f:
            if start is None:
                start = i
            gap = 0
        elif start is not None:
            gap += 1
            if gap >= min_gap:
                out.append((start, i - gap))
                start = None
    if start is not None:
        out.append((start, len(flags) - 1))
    return out

cb, rb = bands(cols), bands(rows)

def even(n, total, lo, hi):
    span = (hi - lo) / n
    return [(round(lo + i * span), round(lo + (i + 1) * span) - 1) for i in range(n)]

# 浅色徽章（黄 C / 灰 未知）与背景对比度低，行列分带可能粘连，退回等分
if len(cb) != 4 or len(rb) != 2:
    x0, x1 = (cb[0][0], cb[-1][1]) if cb else (0, W - 1)
    y0, y1 = (rb[0][0], rb[-1][1]) if rb else (0, H - 1)
    cb, rb = even(4, W, x0, x1), even(2, H, y0, y1)
    print("等分兜底 → 列:", cb, "行:", rb)
print("列带:", cb)
print("行带:", rb)
assert len(cb) == 4 and len(rb) == 2, "网格识别失败"

for ri, (y0, y1) in enumerate(rb):
    for ci, (x0, x1) in enumerate(cb):
        pad = 4
        box = (max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad + 1), min(H, y1 + pad + 1))
        cell = im.crop(box).convert("RGBA")
        w, h = cell.size
        data = cell.load()
        # 白底转透明：从中性色的边缘开始 BFS，把白/灰阴影按亮度换算成 alpha，
        # 这样叠在深色背景上不会出现白色方块，也不会吃掉按钮里的白字
        w, h = cell.size
        data = cell.load()
        neutral = lambda p: (max(p[:3]) - min(p[:3])) <= 14
        seen = [[False] * h for _ in range(w)]
        q = deque()
        for x in range(w):
            q.append((x, 0)); q.append((x, h - 1))
        for y in range(h):
            q.append((0, y)); q.append((w - 1, y))
        while q:
            x, y = q.popleft()
            if not (0 <= x < w and 0 <= y < h) or seen[x][y]:
                continue
            r, g, b, a = data[x, y]
            if not neutral((r, g, b)) or min(r, g, b) < 150:
                continue
            seen[x][y] = True
            lum = round(0.299 * r + 0.587 * g + 0.114 * b)
            data[x, y] = (0, 0, 0, max(0, 255 - lum))
            q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
        bbox = cell.getbbox()
        if bbox:
            cell = cell.crop(bbox)
        name = NAMES[ri][ci]
        cell.save(OUT / f"{name}.png", optimize=True)
        print(f"  {name:<10} {box} → {cell.size}")
