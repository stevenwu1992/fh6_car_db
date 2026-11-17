"""把 .swatchbin 解出来的 PNG 素材整理成网页用资源。

输入：
    C:\\Users\\STWU\\Pictures\\【FH666】\\FH6数据网站\\Thumbnail\\Swatchbin Converter
    其中 ``thumbnail_<ID>_Big.png`` 是透明底车辆图，``L_Manu_Logo_<CODE>.png`` 是白色品牌标识。

输出（output/assets/）：
    car/{Id}.webp        卡片用，宽 420，透明
    car/big/{Id}.webp    详情页用，宽 900，透明
    make/{CODE}.webp     品牌标识，高 96，白色
    img/hero.webp        头图背景
    img/logo.webp        页头 logo（FH6 标识 + 字标）
    img/mark.png         站点图标（FH 方标）

用法：
    python build_assets.py           # 增量
    python build_assets.py --force   # 全部重做
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
DB = ROOT / "output" / "FH6_车辆数据库_中文版.sqlite"
SRC = Path(r"C:\Users\STWU\Pictures\【FH666】\FH6数据网站\Thumbnail\Swatchbin Converter")
HERO = Path(r"C:\Users\STWU\Pictures\forzahorizon6 2026-10-30 03-46-02_8.jpg")
LOGO = Path(r"C:\Users\STWU\Pictures\Forza logo\Forza_Horizon_6_logo 白.png")

OUT = ROOT / "output" / "assets"
CAR = OUT / "car"
CAR_BIG = CAR / "big"
MAKE = OUT / "make"
IMG = OUT / "img"

CARD_W = 420
BIG_W = 900
MAKE_H = 96

# 这些品牌标自带暗色适配（彩色徽记 / 描边），反相会破坏品牌色，暗色主题直接用原图。
# Subaru 的蓝色星徽 + 银色描边在深底上本身可辨识，反相后会变成橙黄色。
DARK_NATIVE: set[str] = {"SUB"}


def index_source() -> dict[str, Path]:
    """文件名小写 → 路径，Windows 下用它兜住大小写不一致。"""
    return {p.name.lower(): p for p in SRC.glob("*.png")}


def trim(im: Image.Image, pad: int = 6) -> Image.Image:
    """按 alpha 裁掉四周空白。"""
    box = im.getchannel("A").getbbox()
    if not box:
        return im
    x0, y0, x1, y1 = box
    return im.crop((max(0, x0 - pad), max(0, y0 - pad),
                    min(im.width, x1 + pad), min(im.height, y1 + pad)))


def save(im: Image.Image, path: Path, width: int | None = None,
         height: int | None = None, quality: int = 82) -> int:
    w, h = im.size
    if width and w > width:
        im = im.resize((width, max(1, round(h * width / w))), Image.LANCZOS)
    elif height and h > height:
        im = im.resize((max(1, round(w * height / h)), height), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "WEBP", quality=quality, method=6)
    return path.stat().st_size


def inkify_white(path: Path, ink: tuple[int, int, int] = (17, 17, 20)) -> bool:
    """把「白色品牌标」的白色像素换成墨色——浅底页面上白标等于看不见。

    只在整块标以白色为主（>55% 近白像素）时动手，彩色标（法拉利盾、兰博基尼）保持原样。
    幂等：已经转过的标不再满足阈值，直接跳过。
    """
    im = Image.open(path).convert("RGBA")
    arr = np.array(im).astype(np.int16)
    alpha = arr[..., 3]
    solid = alpha > 150
    if solid.sum() == 0:
        return False
    rgb = arr[..., :3]
    mn, mx = rgb.min(2), rgb.max(2)
    bright = (mn > 185) & ((mx - mn) < 28)
    if bright[solid].mean() < 0.55:
        return False
    m = bright & (alpha > 0)
    arr[m, 0], arr[m, 1], arr[m, 2] = ink
    Image.fromarray(arr.astype(np.uint8), "RGBA").save(path, "WEBP", quality=90, method=6)
    return True


def main() -> int:
    force = "--force" in sys.argv
    idx = index_source()
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row

    # ── 车辆缩略图 ──
    cars = list(con.execute("SELECT Id, Thumbnail FROM Data_Car ORDER BY Id"))
    hit = miss = 0
    bytes_ = 0
    missing: list[int] = []
    for car in cars:
        cid = car["Id"]
        small, big = CAR / f"{cid}.webp", CAR_BIG / f"{cid}.webp"
        if small.exists() and big.exists() and not force:
            hit += 1
            continue
        stem = (car["Thumbnail"] or "").replace("\\", "/").rsplit("/", 1)[-1].rsplit(".", 1)[0]
        src = idx.get(f"{stem}_big.png".lower()) or idx.get(f"{stem}.png".lower())
        if not src:
            miss += 1
            missing.append(cid)
            continue
        im = Image.open(src).convert("RGBA")
        im = trim(im)
        bytes_ += save(im, small, width=CARD_W, quality=80)
        bytes_ += save(im, big, width=BIG_W, quality=82)
        hit += 1
    print(f"车辆图 {hit}/{len(cars)} · 缺 {miss} · {bytes_/1048576:.1f} MB")
    if missing:
        print("  无图车辆 ID：", ",".join(map(str, missing)))

    # ── 品牌标识 ──
    # 文件按「车辆资源名前三位」命名：AZM_AZ1_93 → Manu_Logo_AZM.png。
    # 同码还有 L_Manu_Logo_*.png（大图）与 *_Badge.png，优先用 Manu_Logo_ 本体。
    # 导出时统一到 190×110 画布：按 sqrt(w*h)=160 归一视觉面积，极端比例按画布收边，
    # 这样页面上所有品牌标视觉大小一致。深色单色标（AMG/奥迪/GR 这类）另存一份反相版供暗色主题用。
    plain: dict[str, Path] = {}
    large: dict[str, Path] = {}
    for name, path in idx.items():
        m = re.fullmatch(r"(l_)?manu_logo_([a-z0-9]+)\.png", name)
        if not m:
            continue
        code = m.group(2).upper()
        (large if m.group(1) else plain)[code] = path
    logos = {**large, **plain}

    LOGO_CANVAS = (190, 110)
    LOGO_AREA = 160.0
    made = 0
    for code, src in sorted(logos.items()):
        dst = MAKE / f"{code}.webp"
        if dst.exists() and not force:
            continue
        im = trim(Image.open(src).convert("RGBA"), pad=2)
        w, h = im.size
        sc = min(LOGO_AREA / max(1.0, (w * h) ** 0.5), LOGO_CANVAS[0] / w, LOGO_CANVAS[1] / h)
        im = im.resize((max(1, round(w * sc)), max(1, round(h * sc))), Image.LANCZOS)
        canvas = Image.new("RGBA", LOGO_CANVAS, (0, 0, 0, 0))
        canvas.alpha_composite(im, ((LOGO_CANVAS[0] - im.width) // 2, (LOGO_CANVAS[1] - im.height) // 2))
        save(canvas, dst, quality=90)

        made += 1
    missing = sorted(set(r[0] for r in con.execute("SELECT ManufacturerCode FROM List_CarMake")) - set(logos))
    print(f"品牌标识 {len(list(MAKE.glob('*.webp')))} 个（本次新导出 {made}）"
          + (f" · 无文件 {','.join(missing)}" if missing else ""))

    # ── 头图 ──
    hero_dst = IMG / "hero.webp"
    if force or not hero_dst.exists():
        im = Image.open(HERO).convert("RGB")
        save(im, hero_dst, width=2560, quality=82)
        print(f"头图 {im.size[0]}x{im.size[1]} → {hero_dst.stat().st_size/1024:.0f} KB")

    # ── 页头 logo：裁掉大片留白，保留品牌色 ──
    logo_dst = IMG / "logo.webp"
    if force or not logo_dst.exists():
        im = trim(Image.open(LOGO).convert("RGBA"), pad=8)
        save(im, logo_dst, width=760, quality=92)
        print(f"logo {im.size} → {logo_dst.stat().st_size/1024:.0f} KB")

    # ── 站点图标：取左侧 F 方标裁成正方形 ──
    mark_dst = IMG / "mark.png"
    if force or not mark_dst.exists():
        im = Image.open(LOGO).convert("RGBA")
        a = np.array(im.getchannel("A"))
        # F 方标在最左，约有 40% 宽度；从 alpha 列密度找分界
        cols = (a > 40).sum(axis=0)
        cut = next((x for x in range(int(im.width * .12), int(im.width * .6)) if cols[x] == 0),
                   int(im.width * .4))
        part = trim(im.crop((0, 0, cut, im.height)), pad=10)
        side = max(part.size)
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.paste(part, ((side - part.width) // 2, (side - part.height) // 2))
        canvas.resize((128, 128), Image.LANCZOS).save(mark_dst, "PNG", optimize=True)
        print(f"站点图标 128×128 · {mark_dst.stat().st_size/1024:.0f} KB")

    # ── 深色站点标：浅底页头 / 页脚用 ──
    ink_dst = IMG / "mark-ink.png"
    if force or not ink_dst.exists():
        mk = Image.open(mark_dst).convert("RGBA")
        ink = Image.new("RGBA", mk.size, (17, 17, 20, 255))
        ink.putalpha(mk.getchannel("A"))
        ink.save(ink_dst, "PNG", optimize=True)
        print(f"深色站点标 128×128 · {ink_dst.stat().st_size/1024:.0f} KB")

    # ── 白色品牌标转墨色 ──
    turned = sum(inkify_white(p) for p in sorted(MAKE.glob("*.webp")))
    if turned:
        print(f"品牌标转墨色 {turned} 个")

    # ── 暗色反相标：深色单色标（AMG/奥迪/GR 这类）转白，供暗色主题直接用 ──
    dark_dir = MAKE / "d"
    dark_dir.mkdir(parents=True, exist_ok=True)
    # 清掉历史生成的、现已判定不该反相的标
    for code in DARK_NATIVE:
        stale = dark_dir / f"{code}.webp"
        if stale.exists():
            stale.unlink()
    n_dark = 0
    for lp in sorted(MAKE.glob("*.webp")):
        if lp.stem.upper() in DARK_NATIVE:
            continue
        arr = np.array(Image.open(lp).convert("RGBA")).astype(float)
        op = arr[..., 3] > 140
        if not op.any():
            continue
        rgb = arr[..., :3][op]
        lum = float((rgb @ np.array([.299, .587, .114])).mean())
        mx, mn = rgb.max(1), rgb.min(1)
        sat = float(np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0).mean())
        if lum < 115 and sat < 0.32:
            inv = np.dstack([255 - arr[..., :3], arr[..., 3]]).astype(np.uint8)
            Image.fromarray(inv, "RGBA").save(dark_dir / lp.name, "WEBP", quality=90, method=6)
            n_dark += 1
    print(f"暗色反相标 {n_dark} 个")

    print(f"资源目录 {OUT} · "
          f"{len(list(CAR.glob('*.webp')))} 卡图 / {len(list(CAR_BIG.glob('*.webp')))} 大图 / "
          f"{len(list(MAKE.glob('*.webp')))} 品牌")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
