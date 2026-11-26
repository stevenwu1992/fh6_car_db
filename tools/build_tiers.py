"""把调校推荐表里的「竞争力」分级匹配到本站车辆。

数据源：地平线6线上车辆调校推荐.xlsx 的 13 张分级表（R 998公路 … C 500泥地）。
每张表的第 3 行起：A 列 = 竞争力（Meta+ / Meta / T0.5 / T1 / T1.5 / T2 / T3 / 未知），
C 列 = 车辆型号。工作表名本身就是「车辆性能等级组别」。
"""
from __future__ import annotations

import json
import re
import difflib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from read_xlsx import read_xlsx  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
XLSX = ROOT / "地平线6线上车辆调校推荐.xlsx"

TIER_ORDER = ["Meta+", "Meta", "T0.5", "T1", "T1.5", "T2", "T3", "未知"]
TIER_ALIAS = {
    "meta+": "Meta+", "meta": "Meta", "t0.5": "T0.5", "t0": "T0.5",
    "t1": "T1", "t1.5": "T1.5", "t2": "T2", "t3": "T3",
    "未知": "未知", "?": "未知", "": "",
}


def norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"['’`]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def year_of(s: str) -> int | None:
    m = re.match(r"\s*((?:19|20)\d{2})\s+", s)
    return int(m.group(1)) if m else None


def main() -> None:
    data = read_xlsx(str(XLSX))
    sheets = [n for n in data if re.match(r"^[A-Z]\d?\s*\d{3}", n)]
    print("分级表:", sheets)

    payload = json.loads(
        re.search(r"const DATA\s*=\s*(.*?);\s*\n", (ROOT / "output/车辆索引.html")
                  .read_text(encoding="utf-8"), re.S).group(1))

    cars = []
    for r in payload["rows"]:
        c = dict(zip(payload["cols"], r))
        cars.append({
            "id": c["id"], "year": c["year"], "en": c["name_en"] or "",
            "zh": c["name"] or "", "code": c["code"] or "",
            "key": norm(c["name_en"] or c["name"] or ""),
        })

    entries: dict[int, list[dict]] = {}
    unmatched: list[tuple[str, str, str]] = []
    used = 0

    for sheet in sheets:
        rows = data[sheet]
        for row in rows[2:]:
            if len(row) < 3:
                continue
            tier_raw = (row[0] or "").strip()
            model = (row[2] or "").strip()
            if not model or not tier_raw:
                continue
            tier = TIER_ALIAS.get(tier_raw.lower().replace(" ", ""), None)
            if tier is None:
                continue
            y = year_of(model)
            target = norm(model)
            best, best_score = None, 0.0
            for c in cars:
                score = difflib.SequenceMatcher(None, target, c["key"]).ratio()
                if y and c["year"]:
                    score += 0.12 if abs(c["year"] - y) <= 1 else -0.25
                if score > best_score:
                    best, best_score = c, score
            if best and best_score >= 0.62:
                used += 1
                cell = lambda i: (row[i].strip() if i < len(row) and row[i] else "")
                entries.setdefault(best["id"], []).append({
                    "g": sheet, "t": tier, "m": model, "s": round(best_score, 3),
                    "d": cell(3), "diff": cell(4), "tire": cell(5), "role": cell(6),
                    "tuner": cell(7), "note": cell(9).replace("\n", " ").strip(),
                })
            else:
                unmatched.append((sheet, tier, model))

    print(f"匹配成功 {used} 行 / 未匹配 {len(unmatched)} 行 · 覆盖车辆 {len(entries)} 台")
    (ROOT / "tools/tier_map.auto.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "tools/tier_unmatched.txt").write_text(
        "\n".join(f"{s}\t{t}\t{m}" for s, t, m in unmatched), encoding="utf-8")


if __name__ == "__main__":
    main()
