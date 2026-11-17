"""从 Forza 的 .swatchbin 贴图包里导出车辆缩略图与车企 logo。

`.swatchbin` 是 burG 容器：0x14 起的块表里第一项偏移 0x8C 指向 BC7 像素数据，
宽高在 0x4C / 0x50。全量 691 张缩略图与 96 个品牌标识都用这个规则解码。

用法：
    python extract_assets.py            # 增量导出（已存在则跳过）
    python extract_assets.py --force    # 全部重导
"""

from __future__ import annotations

import io
import sqlite3
import struct
import sys
import zipfile
from pathlib import Path

import numpy as np
import texture2ddecoder
from PIL import Image

ROOT = Path(__file__).resolve().parent
DB = ROOT / "output" / "FH6_车辆数据库_中文版.sqlite"
SRC = Path(r"C:\Users\STWU\Pictures\【FH666】\FH6数据网站\Thumbnail")
OUT = ROOT / "output" / "assets"
CAR_DIR = OUT / "car"
MAKE_DIR = OUT / "make"

# 缩略图保留原分辨率（670×376），详情抽屉里刚好铺满且不放大
CAR_W = 660
MAKE_H = 220


# ── 解码 ────────────────────────────────────────────────────────────
def decode(buf: bytes) -> Image.Image:
    """把 swatchbin 字节解成 RGBA 图。"""
    if buf[:4] != b"burG":
        raise ValueError("不是 burG 容器")
    width, height = struct.unpack_from("<II", buf, 0x4C)
    off, size = struct.unpack_from("<II", buf, 0x20)
    payload = buf[off:off + size]
    raw = texture2ddecoder.decode_bc7(payload, width, height)
    return Image.frombytes("RGBA", (width, height), raw)


def trim(im: Image.Image, pad: int = 4) -> Image.Image | None:
    """按 alpha 裁掉空白，四周留一点空隙；整张空白则返回 None。"""
    a = np.array(im.getchannel("A"))
    if a.max() < 24:
        return None
    ys, xs = np.where(a > 8)
    if len(xs) < 400:          # 只剩零星几个像素，当作没有图
        return None
    x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad)
    x1, y1 = min(im.width, xs.max() + 1 + pad), min(im.height, ys.max() + 1 + pad)
    return im.crop((x0, y0, x1, y1))


def to_webp(im: Image.Image, path: Path, target_w: int | None = None,
            target_h: int | None = None, quality: int = 84) -> int:
    """等比缩放到目标宽或高后存 WebP，返回字节数。"""
    w, h = im.size
    if target_w and w > target_w:
        im = im.resize((target_w, max(1, round(h * target_w / w))), Image.LANCZOS)
    elif target_h and h > target_h:
        im = im.resize((max(1, round(w * target_h / h)), target_h), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "WEBP", quality=quality, method=6)
    return path.stat().st_size


# ── 索引 zip ────────────────────────────────────────────────────────
def index_zips() -> dict[str, tuple[zipfile.ZipFile, str]]:
    """小写文件名 → (压缩包, 包内真实名)。"""
    table: dict[str, tuple[zipfile.ZipFile, str]] = {}
    for zp in sorted(SRC.glob("RC*.zip")):
        zf = zipfile.ZipFile(zp)
        for name in zf.namelist():
            table[name.lower()] = (zf, name)
    return table


def main() -> int:
    force = "--force" in sys.argv
    idx = index_zips()
    print(f"压缩包索引 {len(idx)} 个条目")

    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row

    # ── 车辆缩略图 ──
    cars = list(con.execute("SELECT Id, Thumbnail, MakeID FROM Data_Car ORDER BY Id"))
    ok = skip = blank = miss = 0
    total = 0
    for car in cars:
        dst = CAR_DIR / f"{car['Id']}.webp"
        if dst.exists() and not force:
            ok += 1
            continue
        raw_name = (car["Thumbnail"] or "").replace("\\", "/").rsplit("/", 1)[-1]
        stem = raw_name.rsplit(".", 1)[0]
        entry = (idx.get(f"{stem}_big.swatchbin".lower())
                 or idx.get(f"{stem}.swatchbin".lower()))
        if not entry:
            miss += 1
            continue
        zf, arc = entry
        try:
            im = trim(decode(zf.read(arc)))
        except Exception as exc:                       # noqa: BLE001
            print(f"  解码失败 {arc}: {exc}")
            miss += 1
            continue
        if im is None:
            blank += 1
            continue
        total += to_webp(im, dst, target_w=CAR_W)

    print(f"车辆图 已有/成功 {ok} · 新导出 {ok and ''}{len(list(CAR_DIR.glob('*.webp')))} · "
          f"空白 {blank} · 缺失 {miss} · 合计 {total/1048576:.1f} MB")

    # ── 品牌 logo ──
    makes = list(con.execute("SELECT ID, ManufacturerCode FROM List_CarMake ORDER BY ID"))
    m_ok = m_miss = 0
    for mk in makes:
        code = mk["ManufacturerCode"]
        dst = MAKE_DIR / f"{code}.webp"
        if dst.exists() and not force:
            m_ok += 1
            continue
        entry = (idx.get(f"manu_logo_{code}.swatchbin".lower())
                 or idx.get(f"l_manu_logo_{code}.swatchbin".lower())
                 or idx.get(f"manu_logo_{code}_badge.swatchbin".lower()))
        if not entry:
            print(f"  品牌 {code} 无 logo")
            m_miss += 1
            continue
        zf, arc = entry
        im = trim(decode(zf.read(arc)), pad=2)
        if im is None:
            m_miss += 1
            continue
        to_webp(im, dst, target_h=MAKE_H, quality=90)
        m_ok += 1
    print(f"品牌 logo 成功 {m_ok} · 缺失 {m_miss}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
