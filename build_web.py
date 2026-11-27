"""把 FH6 车辆数据渲染成网页（GT 风格车鉴 + 数据表 + 全字段抽屉，浅色 / 深色两版）。

数据来自 `output/FH6_车辆数据库_中文版.sqlite`；页面与 `output/assets/`（车辆渲染图、
品牌标识、头图、logo）同目录，用相对路径引用，不请求外网。

车名：车型名统一取游戏语言包 `stringtables/CHT.zip`（与游戏内显示一致），品牌名中英各一套
（CHS / CHT），页面上的「中 / EN」开关切换，排序与搜索索引随之切换。

输出两份：
    output/车辆索引.html        浅色（默认）
    output/车辆索引_暗色.html   深色（首屏即暗色，页内可再切）

包含：
    1. 头图       游戏截图为底，FH6 标识 + 四组总量
    2. 车鉴       691 台车按车厂分段，等级+PI 组合牌用游戏原色
    3. 数据表     同一批车的密集视图，可点表头排序
    4. 详情抽屉   该车 **全部 151 个字段**（12 个语义分组）+ 可选轮胎配方
    5. 轮胎曲线库 41 种配方 × 92 项曲线参数
    6. 多车比对   勾选 2~4 台，字段并排对齐，性能项高亮更优值
    7. 字段说明   199 条字段字典

用法：
    python build_assets.py     # 首次：从 Swatchbin Converter 导出图片素材
    python build_web.py        # 生成两份 html
"""

from __future__ import annotations

import copy
import difflib
import json
import math
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import openpyxl
import zhconv

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build import GAME_DIR, LANG_ZIP, Localizer  # noqa: E402  复用语言包解析
from build_assets import DARK_NATIVE  # noqa: E402  暗色下直接用原图的品牌标
from PIL import Image  # noqa: E402  读缩略图尺寸，用于统一视觉大小
from dictionary import FIELD_GROUPS  # noqa: E402  字段分组顺序
from web_template import TEMPLATE  # noqa: E402  页面模板

DB = Path(__file__).resolve().parent / "output" / "FH6_车辆数据库_中文版.sqlite"
OUT = Path(__file__).resolve().parent / "output" / "车辆索引.html"
XLSX = Path(__file__).resolve().parent / "output" / "Forza Horizon 6 Car List.xlsx"

CLASS_ORDER = {0: "D", 1: "C", 2: "B", 3: "A", 4: "S1", 5: "S2", 6: "R", 7: "X"}
DRIVE = {1: "FWD", 2: "RWD", 3: "AWD"}

# 头图展示的构建元信息：游戏数据版本 + 数据源更新日期（更新数据时改这里）
GAME_VERSION = "3.483.970.0"
DATA_UPDATED = "2026/11/6"

# Excel 里没有获取方式的 11 台可驾驶车，取自官方 https://forza.net/fh6cars 的
# Collection + Add-Ons 两列。官方给的年份与数据库略有出入（用首发年），但 PI 完全一致，
# 按「年份±2 + PI 一致 + 名称相似度 ≥0.9」逐台核对后确认，不是猜的。
ACQ_PATCH: dict[int, str] = {
    641:  "Autoshow / Wheelspin",                      # 1997 Porsche 911 GT1 Strassenversion
    3031: "Autoshow / Wheelspin",                      # 1985 Porsche #185 959 Prodrive Rally Raid
    3110: "Autoshow / Wheelspin",                      # 2013 DeBerti Jeep Wrangler Unlimited
    3141: "Wheelspin / Seasonal",                      # 2019 Apollo Intensa Emozione
    3599: "Autoshow / Collection Journal",             # 2020 Gordon Murray Automotive T.50
    3657: "Autoshow / Wheelspin",                      # 2022 Rivian R1T
    3698: "Autoshow / Wheelspin",                      # 2021 Porsche Mission R
    3840: "Collection Journal / Seasonal",             # 2022 Lamborghini Huracán Sterrato
    4156: "Autoshow DLC / Italian Passion Car Pack",   # 2025 Ferrari F80
    4163: "Wheelspin / Seasonal",                      # 2013 Wuling Sunshine S Forza Edition
    4265: "Autoshow DLC / Welcome Pack",               # 2020 Mercedes-AMG GT Black Series Welcome Pack
}

# 引擎型式（List_EngineConfig）与增压后缀（List_Aspiration）。
# 游戏内 EngineName 有 16 条空串，缺名时按这些字段拼出与游戏同风格的原厂引擎名。
ENGINE_CONFIG = {1: "V", 2: "W", 3: "I", 4: "R", 5: "F", 6: "E",
                 7: "SH", 8: "PH", 9: "SPH"}
ASPIRATION_SUFFIX = {1: "", 2: "-T", 3: "-TT", 4: "-QT", 5: "-PDSC",
                     6: "-CSC", 7: "-TS", 8: ""}

# 列表页用的精简列（详情页另有全量字段）；code 是车厂代码，用来取品牌标识
# eg    = 引擎名是否由字段推断；acq = Excel 的 Acquired via 原文
# sea   = 该车加入过的赛季编号列表；cp = 是否 Car Pass 车辆
# place = EnginePlacementID（1 前置 / 2 中置 / 3 后置），驱动筛选的二级分类
COLUMNS: list[str] = [
    "id", "year", "name", "brand", "cls", "pi", "hp", "nm", "kg", "pwr",
    "t60", "tsm", "latg", "brk", "drv", "eng", "ntire", "code",
    "name_en", "brand_en", "mkid", "logo", "bk", "npc", "dt", "mh", "mh2",
    "latg120", "ctry", "eg", "acq", "sea", "cp", "place", "wide", "csc",
]


def norm_name(s: Any) -> str:
    """Excel 车名 ↔ 数据库 `年份 + 英文名` 的归一化：去重音、统一引号、只留字母数字。"""
    t = unicodedata.normalize("NFKD", str(s or ""))
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = (t.replace("’", "'").replace("‘", "'")
          .replace("“", '"').replace("”", '"')
          .lower().replace("&", " and "))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", t).split())


def read_acquisitions() -> dict[str, dict[str, Any]]:
    """读 `All Cars` 的 Acquired via（真实表头在第 2 行），返回按归一化车名索引的清单。"""
    if not XLSX.exists():
        return {}
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["All Cars"] if "All Cars" in wb.sheetnames else wb.worksheets[0]
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    wb.close()
    if not rows:
        return {}
    hdr = [str(x) if x is not None else "" for x in rows[0]]
    try:
        i_name, i_pi, i_acq = (hdr.index("Car Name"), hdr.index("FH6 PI"),
                               hdr.index("Acquired via"))
    except ValueError:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for r in rows[1:]:
        name = r[i_name] if i_name < len(r) else None
        if not name:
            continue
        text = str(name).strip()
        ym = re.match(r"\s*(\d{4})", text)
        try:
            pi = float(r[i_pi]) if r[i_pi] is not None else None
        except (TypeError, ValueError):
            pi = None
        out[norm_name(text)] = {
            "text": text, "year": int(ym.group(1)) if ym else 0, "pi": pi,
            "acq": str(r[i_acq] or "").strip() if i_acq < len(r) else "",
        }
    return out


def parse_acq(raw: str) -> tuple[str, list[int], int]:
    """`Acquired via` → (原文, 赛季编号列表, 是否 Car Pass)。

    例：`Series 1 / Series 4 / Series 7` → ([1,4,7], 0)，
        `Wheelspin / Series 5` → ([5], 0)，`Car Pass` → ([], 1)。
    """
    txt = (raw or "").strip()
    sea = sorted({int(n) for n in re.findall(r"Series\s+(\d+)", txt, flags=re.I)})
    cp = 1 if re.search(r"car\s*pass", txt, flags=re.I) else 0
    return txt, sea, cp

# 比对时「越大越好 / 越小越好」的字段（只标注有共识的性能项，避免误导）
# 注意：这里必须用 Data_Car 的真实字段名，用列表页的短键（hp/pi…）会匹配不上
BETTER_MAX = {"SimPeakPower", "SimPeakTorque", "PI", "SimLatGees60MPH", "SimTopSpeed",
              "HandlingRating", "SpeedRating", "AccelerationRating", "BrakingRating",
              "LaunchRating", "OffroadRating", "MaxUpgradeWizardPerfRating"}
BETTER_MIN = {"SimTimeTo60MPH", "SimBrakeDistance100MPH", "CurbWeight"}

# 比对「简要模式」展示的字段
CMP_BRIEF = ["Id", "Year", "ClassID", "PI", "SimPeakPower", "SimPeakTorque", "CurbWeight",
             "Displacement", "NumGears", "DriveTypeID", "EnginePlacementID",
             "SimTimeTo60MPH", "SimTopSpeed", "SimLatGees60MPH", "SimBrakeDistance100MPH",
             "HandlingRating", "SpeedRating", "AccelerationRating", "BrakingRating",
             "LaunchRating", "OffroadRating", "BaseCost", "CurbWeight"]


# 角速度 → 转速：rad/s × 60/(2π) = rpm。库里 Sim*AngVel 三个字段原始值都是 rad/s。
RADS_TO_RPM = 60.0 / (2 * math.pi)
ANGVEL_FIELDS = {"SimPeakAngVel", "SimPeakTorqueAngVel", "SimRedlineAngVel"}


def build_payload() -> dict[str, Any]:
    """抽取车辆全字段 + 轮胎配方 + 轮胎曲线，组装成前端 JSON。

    Returns:
        ``cols/rows/full/fullRows/tires/curves/...`` 组成的字典，直接序列化为 JSON。
    """
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    loc = Localizer(LANG_ZIP)

    # ---------- 全字段 schema（按 12 个分组排序） ----------
    meta_cols = {r[1]: (r[2], r[3], r[5]) for r in cur.execute(
        "SELECT 字段序号, 字段名, 中文字段名, 单位, 取值范围, 说明 FROM _字段字典 WHERE 表名='Data_Car'")}
    # 详情页分区顺序：改装件（引擎/宽体/轮胎，模板里单独渲染）之后先给关键标定，
    # 再是常规参数，最后才是「标识与本地化」「外观、涂装与展示」这类元信息。
    GROUP_ORDER = [
        "空气动力学", "轮胎摩擦与轴荷标定", "手感与电子辅助标定",
        "分类与归属", "动力总成与结构", "质量、轮胎与尺寸",
        "手工性能数据", "仿真性能（自动生成）", "五维评级", "价格、等级与解锁",
        "标识与本地化", "外观、涂装与展示",
    ]
    CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"
    strip_no = lambda s: s.split(" ", 1)[1] if " " in s else s
    _items = sorted(FIELD_GROUPS.items(),
                    key=lambda kv: GROUP_ORDER.index(strip_no(kv[0]))
                    if strip_no(kv[0]) in GROUP_ORDER else 99)
    # 重排后重新编号，避免数据里 ① 出现在中间位置
    ordered_groups = [(f"{CIRCLED[i]} {strip_no(name)}", fields)
                      for i, (name, fields) in enumerate(_items)]

    order: list[tuple[int, int, str]] = []
    group_names: list[str] = []
    for gi, (gname, fields) in enumerate(ordered_groups):
        group_names.append(gname)
        for pi, f in enumerate(fields):
            order.append((gi, pi, f))
    order.sort()

    full_schema = []
    for gi, _, f in order:
        cn, unit, desc = meta_cols.get(f, (f, "", ""))
        if f in ANGVEL_FIELDS:
            unit = "rpm"
        us = unit.split("（")[0].strip() if unit else ""
        full_schema.append({"n": f, "cn": cn, "u": unit, "s": us, "g": gi, "d": desc})

    # ---------- 轮胎曲线：41 种配方 × 92 项 ----------
    curve_cols = [d[1] for d in cur.execute("PRAGMA table_info(List_TyreCurveDB)")]
    curve_cn = {r[0]: r[1] for r in cur.execute(
        "SELECT 字段名, 中文字段名 FROM _字段字典 WHERE 表名='List_TyreCurveDB'")}
    curve_schema = [{"n": c, "cn": curve_cn.get(c, c)} for c in curve_cols]
    curves: dict[str, list[Any]] = {}
    curve_name: dict[str, str] = {}
    for row in cur.execute("SELECT * FROM List_TyreCurveDB"):
        d = dict(row)
        cid = str(d["TireCompoundID"])
        curves[cid] = [d[c] for c in curve_cols]
        curve_name[cid] = d["DisplayName"]

    # ---------- 每车可换轮胎（含档位/价格/胎压/干湿型号） ----------
    tires: dict[str, list[list[Any]]] = {}
    for r in cur.execute(
            "SELECT Ordinal, Level, TireCompoundID, TireModelName, WetTireModelName,"
            " FrontTirePressure, RearTirePressure, Price, IsStock"
            " FROM List_UpgradeTireCompound ORDER BY Ordinal, Level"):
        tires.setdefault(str(r[0]), []).append([
            r[1], r[2], r[3] or "", r[4] or "", r[5], r[6], r[7], r[8]])

    # ---------- 车辆主体 ----------
    cars = cur.execute("SELECT * FROM Data_Car ORDER BY Id").fetchall()
    eng_raw = {r[0]: (r[1] or "").strip() for r in cur.execute(
        "SELECT MediaName, EngineName FROM Data_Engine")}
    cyl_num = {r[0]: r[1] for r in cur.execute("SELECT CylinderID, Number FROM List_Cylinders")}
    rotary_cyl = {r[0] for r in cur.execute("SELECT * FROM List_Cylinders") if r[3]}
    make_code = {r[0]: (r[1] or "") for r in cur.execute(
        "SELECT ID, ManufacturerCode FROM List_CarMake")}

    def engine_of(d: dict[str, Any]) -> tuple[str, int]:
        """原厂引擎名 + 是否为推断值。

        Data_Engine.EngineName 有 16 条空串，另有 3 台街车压根没有引擎记录；
        旧逻辑用 `or "纯电"` 兜底，把这些燃油车全写成了纯电。这里改成：
        真纯电（Displacement=0 / Config=6 / Aspiration=None）仍是「纯电」，
        其余按排量 + 型式 + 缸数 + 增压方式拼出与游戏同风格的规格名。
        """
        raw = eng_raw.get(d["MediaName"], "")
        if raw:
            return raw, 0
        disp = d["Displacement"] or 0
        cfg = d["EngineConfigID"] or 0
        asp = d["AspirationTypeId"] or 0
        cyl = d["CylinderID"] or 0
        if disp <= 0 or cfg == 6 or asp == 8:
            return "纯电", 0
        letter = ENGINE_CONFIG.get(cfg, "")
        if cfg == 4 or cyl in rotary_cyl:
            letter = "R"          # 转子：2.6L R4，而不是 2.6L R4 缸
        core = f"{letter}{cyl_num.get(cyl, 0)}" if cyl_num.get(cyl) else letter
        return f"{disp / 1000:.1f}L {core}{ASPIRATION_SUFFIX.get(asp, '')}".strip(), 1

    # 引擎置换表里的原厂行也用同一份推断结果，避免出现「引擎 1234」这种占位符
    eng_by_media = {d["MediaName"]: engine_of(d)[0] for d in (dict(r) for r in cars)}

    # 品牌标：按车辆资源名前三位取（AZM_AZ1_93 → AZM → Manu_Logo_AZM.png）
    make_dir = OUT.parent / "assets" / "make"
    logo_files = {p.stem.upper() for p in make_dir.glob("*.webp")} if make_dir.exists() else set()
    logo_dark = sorted(
        p.stem.upper() for p in (make_dir / "d").glob("*.webp")
        if p.stem.upper() not in DARK_NATIVE
    ) if (make_dir / "d").exists() else []

    def media_prefix(media: str | None) -> str:
        m = re.match(r"[A-Za-z]{2,3}", media or "")
        return m.group(0).upper() if m else ""

    pref_by_make: dict[Any, Counter] = defaultdict(Counter)
    for r in cars:
        pref_by_make[r["MakeID"]][media_prefix(r["MediaName"])] += 1

    def make_logo(make_id: Any) -> str:
        """按车辆资源名前缀取标（AZM_AZ1_93 → AZM）。

        前缀与车厂代码一致时（绝大多数）直接用前缀；不一致的多是子品牌挂靠母公司
        （Abarth 的车是 FIA_…、梅赛德斯-AMG 的车是 MER_…），此时仍用车厂自己的标，
        前缀标作为兜底，避免「Abarth 段头挂 FIAT 标」。
        """
        cnt = pref_by_make.get(make_id) or Counter()
        total = sum(cnt.values())
        prefix = ""
        if total:
            cand, n = cnt.most_common(1)[0]
            if cand and n / total >= 0.6:
                prefix = cand
        code = make_code.get(make_id, "")
        for cand in ((prefix,) if prefix == code else ()) + (code, prefix):
            if cand and cand in logo_files:
                return cand
        return ""

    # 车名：车型名一律取繁体中文包（CHT，与游戏内显示一致）；品牌名中英各一套
    loc_cht = Localizer(GAME_DIR / "stringtables" / "CHT.zip")
    loc_en = Localizer(GAME_DIR / "stringtables" / "EN.zip")

    # ---------- 车辆分类（CarBuckets 两级） ----------
    buckets = []
    for bid, pid, pri in cur.execute("SELECT Id, ParentBucketId, SortPriority FROM CarBuckets"):
        buckets.append({
            "id": bid, "p": pid, "o": pri,
            "zh": loc.get("CarBuckets", "Name", bid),
            "tw": loc_cht.get("CarBuckets", "Name", bid),
            "en": loc_en.get("CarBuckets", "Name", bid),
        })
    buckets.sort(key=lambda b: (b["o"], b["id"]))
    car_bucket = {cid: bk for cid, bk in cur.execute("SELECT CarId, CarBucket FROM Data_Car_Buckets")}

    # ---------- 不可驾驶：街车 / NPC 剧情车 ----------
    npc_ids = {r[0] for r in cur.execute("SELECT Ordinal FROM UnobtainableCars")}
    traffic_ids = {r[0] for r in cur.execute("SELECT CarId FROM TrafficCars")}

    # ---------- 加入游戏的日期（ContentOffers 的 Car 类内容包） ----------
    release: dict[int, str] = {}
    for content_id, dt in cur.execute(
            "SELECT m.ContentId, m.ReleaseDateUTC FROM ContentOffersMapping m"
            " JOIN ContentOffers o ON o.Id = m.OfferId"
            " WHERE m.ReleaseDateUTC <> '' AND o.Style = 'Car'"):
        try:
            release[int(content_id)] = dt[:10]
        except (TypeError, ValueError):
            continue

    # ---------- 引擎置换（List_UpgradeEngine，Ordinal = 车辆 Id） ----------
    media_car = {r[1]: r[0] for r in cur.execute("SELECT Id, MediaName FROM Data_Car")}
    swaps: dict[str, list[list[Any]]] = {}
    for cid, lvl, eid, stock, price, mass, ename, media, pow_, tor in cur.execute(
            "SELECT u.Ordinal, u.Level, u.EngineID, u.IsStock, u.Price, u.MassDiff,"
            " e.EngineName, e.MediaName, e.[EngineGraphingMaxPower], e.[EngineGraphingMaxTorque]"
            " FROM List_UpgradeEngine u LEFT JOIN Data_Engine e ON e.EngineID = u.EngineID"
            " ORDER BY u.Ordinal, u.Level"):
        donor = media_car.get(media, 0)
        swaps.setdefault(str(cid), []).append([
            lvl, ename or eng_by_media.get(media) or f"引擎 {eid}", donor, price or 0,
            round(mass or 0), 1 if stock else 0,
            round(pow_ or 0), round(tor or 0), eid,
        ])

    # ---------- 增压升级（每个引擎能上哪些增压器、到什么等级） ----------
    # 五张分表的 Id = EngineID*1000 + Level，EngineID 指向引擎本身（原厂件或
    # 可换装件），所以按引擎聚合就能同时覆盖「原厂引擎」和「改装引擎」。
    # TurboQuad 在 FH6 数据里是空表，保留键位以免以后有数据时还要改结构。
    ASP_TABLES = [
        ("ts",  "List_UpgradeEngineTurboSingle", "单涡轮"),
        ("tt",  "List_UpgradeEngineTurboTwin",   "双涡轮"),
        ("tq",  "List_UpgradeEngineTurboQuad",   "四涡轮"),
        ("dsc", "List_UpgradeEngineDSC",         "DSC 机增"),
        ("csc", "List_UpgradeEngineCSC",         "CSC 离心机增"),
    ]
    asp_raw: dict[str, dict[str, set[int]]] = {}
    for key, table, _label in ASP_TABLES:
        for eid, lv in cur.execute(f"SELECT DISTINCT EngineID, Level FROM [{table}]"):
            asp_raw.setdefault(str(eid), {}).setdefault(key, set()).add(int(lv))
    asp: dict[str, dict[str, list[int]]] = {
        eid: {k: sorted(v) for k, v in d.items()} for eid, d in asp_raw.items()
    }

    # 车辆级汇总只看「原厂引擎」：这才是这台车本身的改装路径，不依赖换装别人
    # 的引擎。口径差异很大——CSC 按原厂引擎是 106 台，按任意可换装引擎是 428 台，
    # 后者占全库 62%，做成角标会失去区分度，所以角标用前者，详情页逐引擎展示全部。
    car_asp: dict[int, set[str]] = {}
    for cid, eid in cur.execute(
            "SELECT DISTINCT Ordinal, EngineID FROM List_UpgradeEngine WHERE IsStock = 1"):
        hit = asp.get(str(eid))
        if hit:
            car_asp.setdefault(cid, set()).update(hit)

    # ---------- 宽体套件（List_UpgradeCarBody 里 IsStock=0 的记录） ----------
    # 每车一条 IsStock=1 的原厂车身，可选套件才计入。宽度差用两张 Data_CarBody
    # 相减，正数表示真的把车身加宽了（其余是包围类套件，宽度不变）。
    wide: dict[str, list[list[Any]]] = {}
    for cid, lvl, price, stock_w, mod_w in cur.execute(
            "SELECT b.Ordinal, b.Level, b.Price, s.Width, m.Width"
            " FROM List_UpgradeCarBody b"
            " JOIN List_UpgradeCarBody sb ON sb.Ordinal = b.Ordinal AND sb.IsStock = 1"
            " LEFT JOIN Data_CarBody m ON m.Id = b.CarBodyID"
            " LEFT JOIN Data_CarBody s ON s.Id = sb.CarBodyID"
            " WHERE b.IsStock = 0"
            " ORDER BY b.Ordinal, b.Level"):
        dw = round((mod_w - stock_w) * 100) if (mod_w and stock_w) else 0
        wide.setdefault(str(cid), []).append([lvl, price or 0, dw])

    # ---------- 轮胎宽度上限（原厂车身 / 宽体车身各取最大值） ----------
    # 胎宽升级挂在具体车身上（List_UpgradeCarBody.CarBodyID），宽体换了车身，
    # 可用的胎宽档位也跟着变，所以要分开统计。
    tire_w: dict[str, dict[str, int]] = {}
    for cid, stock, fw, rw in cur.execute(
            "SELECT b.Ordinal, b.IsStock,"
            " MAX(f.FrontTireWidth), MAX(r.RearTireWidth)"
            " FROM List_UpgradeCarBody b"
            " LEFT JOIN List_UpgradeCarBodyTireWidthFront f ON f.CarBodyId = b.CarBodyID"
            " LEFT JOIN List_UpgradeCarBodyTireWidthRear r ON r.CarBodyId = b.CarBodyID"
            " GROUP BY b.Ordinal, b.IsStock"):
        rec = tire_w.setdefault(str(cid), {})
        k = "s" if stock else "w"
        rec[k + "f"] = int(fw or 0)
        rec[k + "r"] = int(rw or 0)

    # ---------- 宽体套件的完整数据变化 ----------
    # 每个套件都换成另一张 Data_CarBody，除车宽外前后轮距、轴距、离地高度也可能变；
    # 该车身可用的最大前后胎宽也要跟着换（胎宽档位挂在 CarBodyId 上）。
    # 统一按 BODY_FIELDS 的顺序打包成数组，前端按索引取，payload 体积最小。
    BODY_FIELDS = ["Width", "Length", "Height", "Wheelbase",
                   "ModelFrontTrackOuter", "ModelRearTrackOuter",
                   "ModelFrontStockRideHeight", "ModelRearStockRideHeight"]
    body_rec: dict[int, list[float]] = {}
    for bid, *vals in cur.execute(
            f"SELECT Id, {', '.join(BODY_FIELDS)} FROM Data_CarBody"):
        body_rec[bid] = [float(v or 0) for v in vals]
    tire_f = {r[0]: int(r[1] or 0) for r in cur.execute(
        "SELECT CarBodyId, MAX(FrontTireWidth) FROM List_UpgradeCarBodyTireWidthFront"
        " GROUP BY CarBodyId")}
    tire_r = {r[0]: int(r[1] or 0) for r in cur.execute(
        "SELECT CarBodyId, MAX(RearTireWidth) FROM List_UpgradeCarBodyTireWidthRear"
        " GROUP BY CarBodyId")}

    def body_row(bid: int | None) -> list[float]:
        return (body_rec.get(bid, [0.0] * len(BODY_FIELDS))
                + [tire_f.get(bid, 0), tire_r.get(bid, 0)])

    wide_full: dict[str, dict[str, Any]] = {}
    for cid, lvl, price, mass, bid, sbid in cur.execute(
            "SELECT b.Ordinal, b.Level, b.Price, b.MassDiff, b.CarBodyID, sb.CarBodyID"
            " FROM List_UpgradeCarBody b"
            " JOIN List_UpgradeCarBody sb ON sb.Ordinal = b.Ordinal AND sb.IsStock = 1"
            " WHERE b.IsStock = 0 ORDER BY b.Ordinal, b.Level"):
        rec = wide_full.setdefault(str(cid), {"s": body_row(sbid), "k": []})
        rec["k"].append([lvl, price or 0, mass or 0] + body_row(bid))

    # ---------- 空气动力学套件（尾翼升级） ----------
    # List_UpgradeRearWing 每车一条原厂（IsStock=1）+ 若干改装档；下压力/风阻曲线
    # 挂在 List_AeroPhysics（Drag0/1、Downforce0/1 是攻角滑杆两端）。
    # 同一台车常有多个只有外观差别的尾翼，性能参数完全一样，按数值去重。
    aero: dict[str, dict[str, Any]] = {}
    for cid, lvl, price, mass, ds, wis, d0, d1, f0, f1, ang, isstock in cur.execute(
            "SELECT w.Ordinal, w.Level, w.Price, w.MassDiff, w.DragScale, w.WindInstabilityScale,"
            " a.Drag0, a.Drag1, a.Downforce0, a.Downforce1, a.AngleZeroDownforce, w.IsStock"
            " FROM List_UpgradeRearWing w"
            " LEFT JOIN List_AeroPhysics a ON a.AeroPhysicsID = w.AeroPhysicsID"
            " ORDER BY w.Ordinal, w.IsStock DESC, w.Level"):
        rec = aero.setdefault(str(cid), {"s": None, "k": []})
        row = [lvl, price or 0, round(mass or 0, 2), round(ds if ds else 1, 4),
               round(wis if wis else 1, 3), round(d0 or 0, 2), round(d1 or 0, 2),
               round(f0 or 0, 2), round(f1 or 0, 2), round(ang or 0, 1)]
        if isstock:
            if rec["s"] is None:
                rec["s"] = row
            continue
        key = tuple(row[2:])
        if any(tuple(k[2:]) == key for k in rec["k"]):
            continue
        rec["k"].append(row)

    # ---------- 悬挂结构 / 后轮转向 / 转向手感 ----------
    # 三者都挂在 List_UpgradeSpringDamper 的原厂档（IsStock=1）上；
    # 具体悬挂结构要从 List_SuspensionPhysicsType.Path 的文件名里取
    # （ROAD_Wishbone.xml -> Wishbone），那一列才是真正的前后结构。
    susp_type: dict[str, dict[str, str]] = {}
    for tid, name, path in cur.execute(
            "SELECT SuspensionPhysicsTypeID, Name, Path FROM List_SuspensionPhysicsType"):
        susp_type[str(tid)] = {"n": name, "p": path or ""}

    susp: dict[str, dict[str, Any]] = {}
    for cid, fid, rid, steer, rear, ang in cur.execute(
            "SELECT s.Ordinal, fp.SuspensionPhysicsTypeID, rp.SuspensionPhysicsTypeID,"
            " s.SteeringSettingsProfileID, s.RearSteeringSettingsID, s.SteerMaxAngle"
            " FROM List_UpgradeSpringDamper s"
            " LEFT JOIN List_SpringDamperPhysics fp"
            "        ON fp.SpringDamperPhysicsID = s.FrontSpringDamperPhysicsID"
            " LEFT JOIN List_SpringDamperPhysics rp"
            "        ON rp.SpringDamperPhysicsID = s.RearSpringDamperPhysicsID"
            " WHERE s.IsStock = 1"):
        susp[str(cid)] = {"f": fid or 0, "r": rid or 0,
                          "st": steer or 0, "rs": rear or 0, "a": ang}

    rear_steer: dict[str, dict[str, Any]] = {}
    for r in cur.execute(
            "SELECT Id, Name, MaxRearSteerAngleAsFractionOfFront, LowSpeedCurveSpeedMS,"
            " HighSpeedCurveSpeedMS, MaxRearSteerAngleForCounterSteer"
            " FROM List_RearSteeringSettings"):
        rear_steer[str(r[0])] = {"n": r[1], "frac": r[2], "ls": r[3], "hs": r[4], "cs": r[5]}

    steer_set: dict[str, dict[str, Any]] = {}
    for r in cur.execute(
            "SELECT SteeringSettingsID, Name, SteerMaxAngVelTurning,"
            " SteerSpeedSensitiveMaxGees, SteerSpeedSensitiveFastSpeed"
            " FROM List_SteeringSettings"):
        steer_set[str(r[0])] = {"n": r[1], "turn": r[2], "gees": r[3], "fast": r[4]}

    # ---------- 主动驾驶模式 ----------
    # List_DrivingMode.Ordinal 直接就是车辆 Id，只有少数车型配了这套配置。
    drive_mode: dict[str, dict[str, Any]] = {}
    for row in cur.execute("SELECT * FROM List_DrivingMode"):
        d = dict(row)
        drive_mode[str(d["Ordinal"])] = {
            "id": d["DrivingModeID"],
            "mods": [k for k in ("AeroMod", "SuspensionMod", "EngineMod",
                                 "DriveTrainMod", "ChassisMod") if d[k]],
            "ov": {k: v for k, v in d.items()
                   if k.endswith("_Override") and v not in (0, 0.0, "", None)},
            "drag": d["GameDragScale"], "df": d["GameDownforceScale"],
            "dof": d["GameDownforceOffroadScale"], "dt": d["DriveType_Override"],
        }

    # ---------- 引擎统计（头图「改装引擎」一格） ----------
    # IsStock=1 是每台车的原厂引擎，IsStock=0 是可选置换引擎；按 EngineID 去重
    engine_total = cur.execute("SELECT COUNT(*) FROM Data_Engine").fetchone()[0]
    stock_engines = cur.execute(
        "SELECT COUNT(DISTINCT EngineID) FROM List_UpgradeEngine WHERE IsStock=1").fetchone()[0]
    swap_engines = cur.execute(
        "SELECT COUNT(DISTINCT EngineID) FROM List_UpgradeEngine WHERE IsStock=0").fetchone()[0]
    swap_combos = cur.execute(
        "SELECT COUNT(*) FROM List_UpgradeEngine WHERE IsStock=0").fetchone()[0]

    # ---------- 缩略图实际比例（统一视觉大小用） ----------
    # 等视觉面积：车卡目标面积 31500 px²（≈286×110），详情 242000 px²（≈780×300）
    mh_by_id: dict[int, int] = {}
    mh2_by_id: dict[int, int] = {}
    for p in (OUT.parent / "assets" / "car").glob("*.webp"):
        try:
            with Image.open(p) as im:
                ar = im.width / max(1, im.height)
        except Exception:  # noqa: BLE001
            continue
        mh_by_id[int(p.stem)] = max(96, min(158, round((31500 / ar) ** 0.5)))
        mh2_by_id[int(p.stem)] = max(180, min(300, round((242000 / ar) ** 0.5)))

    def brand_of(table: str, make_id: Any, l10n: Localizer) -> str:
        return l10n.get(table, "DisplayName", make_id) or loc.get(table, "DisplayName", make_id)

    def full_name(brand: str, brand_alt: str, model: str) -> str:
        """车型名里已含品牌就不再前缀，避免「Ford #13 Ford Mustang」。"""
        if not brand:
            return model
        low = model.lower()
        if brand.lower() in low or (brand_alt and brand_alt.lower() in low):
            return model
        return f"{brand} {model}".strip()

    # ---------- 获取途径：Excel `Acquired via` → 赛季备注 / Carpass车辆 ----------
    # 车名以「年份 + 英文名」对齐；先精确，再对剩下的用「同年 + PI 一致 + 名称相似度」
    # 一对一补匹配。PI 约束很关键，否则会把 Huracán Sterrato 挂到 Tecnica 上。
    acq_index = read_acquisitions()
    acq_map: dict[int, tuple[str, list[int], int]] = {}
    if acq_index:
        probes = []
        for r in cars:
            d = dict(r)
            cid = d["Id"]
            b_z = brand_of("List_CarMake", d["MakeID"], loc)
            b_e = brand_of("List_CarMake", d["MakeID"], loc_cht)
            model = (loc_cht.get("Data_Car", "DisplayName", cid)
                     or loc.get("Data_Car", "DisplayName", cid))
            probes.append((cid, d["Year"],
                           norm_name(f"{d['Year']} {full_name(b_e, b_z, model)}"),
                           float(d["PI"] or 0), cid in npc_ids))
        used: set[str] = set()
        rest = []
        for cid, year, key, pi, npc in probes:
            hit = acq_index.get(key)
            if hit is not None:
                used.add(key)
                acq_map[cid] = parse_acq(hit["acq"])
            else:
                rest.append((cid, year, key, pi, npc))
        by_year: dict[int, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
        for k, rec in acq_index.items():
            by_year[rec["year"]].append((k, rec))
        for cid, year, key, pi, npc in rest:
            if npc:  # 街车不参与模糊匹配，别把 Traffic 车挂到民用版上
                continue
            cand = [(k, rec) for k, rec in by_year.get(year, [])
                    if k not in used and rec["pi"] is not None and abs(rec["pi"] - pi) <= 1]
            if not cand:
                continue
            k, rec = max(cand, key=lambda kr: difflib.SequenceMatcher(None, key, kr[0]).ratio())
            if difflib.SequenceMatcher(None, key, k).ratio() < 0.55:
                continue
            used.add(k)
            acq_map[cid] = parse_acq(rec["acq"])

    # Excel 缺档的车用官方列表补全（只补还没有获取方式的车，不覆盖已有值）
    for cid, txt in ACQ_PATCH.items():
        if cid not in acq_map or not acq_map[cid][0]:
            acq_map[cid] = parse_acq(txt)

    rows: list[list[Any]] = []
    full_rows: list[list[Any]] = []
    for r in cars:
        d = dict(r)
        cid = d["Id"]
        hp = round(d["SimPeakPower"] * 100 / 745.6999)
        kg = round(d["CurbWeight"] * 100)
        brand = brand_of("List_CarMake", d["MakeID"], loc)
        brand_en = brand_of("List_CarMake", d["MakeID"], loc_cht)
        model = loc_cht.get("Data_Car", "DisplayName", cid) or loc.get("Data_Car", "DisplayName", cid)
        full = full_name(brand, brand_en, model)
        full_en = full_name(brand_en, brand, model)
        eng_label, eng_guess = engine_of(d)
        acq, sea, cp = acq_map.get(cid, ("", [], 0))
        rows.append([
            cid, d["Year"], full, brand,
            CLASS_ORDER.get(d["ClassID"], ""), d["PI"], hp,
            round(d["SimPeakTorque"] * 100), kg,
            round(hp / (kg / 1000), 1) if kg else 0,
            round(d["SimTimeTo60MPH"], 2),
            round(d["SimTopSpeed"] * 3.6),
            round(d["SimLatGees60MPH"], 2),
            round(d["SimBrakeDistance100MPH"], 1),
            DRIVE.get(d["DriveTypeID"], ""),
            eng_label,
            len(tires.get(str(cid), [])),
            make_code.get(d["MakeID"], ""),
            full_en,
            brand_en,
            d["MakeID"],
            make_logo(d["MakeID"]),
            car_bucket.get(cid, 0),
            1 if cid in npc_ids else 0,
            release.get(cid, ""),
            mh_by_id.get(cid, 110),
            mh2_by_id.get(cid, 300),
            round(d["SimLatGees120MPH"], 2),
            d["CountryID"],
            eng_guess, acq, sea, cp, d["EnginePlacementID"],
            len(wide.get(str(cid), [])),                       # 可选宽体套件数，0 = 没有
            1 if "csc" in car_asp.get(cid, set()) else 0,      # 有引擎支持 CSC 离心机增
        ])
        full_rows.append([
            round(d[s["n"]] * RADS_TO_RPM)
            if (s["n"] in ANGVEL_FIELDS and d[s["n"]] is not None) else d[s["n"]]
            for s in full_schema])

    # ---------- 外键取值 → 中文标签（否则详情页只有数字，等于没解释） ----------
    def labels(table: str, col: str, key: str) -> dict[str, str]:
        return {str(r[0]): loc.get(table, col, r[0]) for r in cur.execute(f"SELECT {key} FROM {table}")}

    fk: dict[str, dict[str, str]] = {
        "MakeID": labels("List_CarMake", "DisplayName", "ID"),
        "ClassID": {str(r[0]): f"{(r[1] or '').replace('CLASS_', '')} 级"
                    for r in cur.execute("SELECT Id, BadgeTexturePathPrefix FROM CarClasses")},
        "CarTypeID": labels("List_CarType", "DisplayName", "Id"),
        "FamilyModelID": labels("List_FamilyModel", "DisplayName", "Id"),
        "FamilyBodyID": labels("List_FamilyBody", "DisplayName", "Id"),
        "FamilySpecialID": labels("List_FamilySpecial", "FamilySpecialID", "FamilySpecialID"),
        "RegionID": labels("List_Region", "DisplayName", "Id"),
        "CountryID": labels("List_Country", "Country", "CountryID"),
        "MaterialTypeID": {str(r[0]): r[1] for r in cur.execute(
            "SELECT MaterialTypeID, Material FROM List_MaterialType")},
        "PowertrainID": {str(r[0]): f"{r[1]}" for r in cur.execute(
            "SELECT Id, '' FROM Powertrains")},
        "DriveTypeID": labels("List_DriveType", "DisplayName", "ID"),
        "EnginePlacementID": labels("List_EnginePlacement", "DisplayName", "ID"),
        "EngineConfigID": labels("List_EngineConfig", "DisplayName", "ConfigID"),
        "CylinderID": {str(r[0]): f"{r[1]} 缸" for r in cur.execute(
            "SELECT CylinderID, Number FROM List_Cylinders")},
        "AspirationTypeId": labels("List_Aspiration", "DisplayName", "AspirationID"),
        "ContentId": {str(r[0]): (loc.get("ContentOffers", "DisplayName", r[0]) or f"内容包 {r[0]}")
                      for r in cur.execute("SELECT Id FROM ContentOffers")},
    }

    # ---------- 字段说明（4 张表 199 条） ----------
    glossary = []
    for table in ("Data_Car", "Data_Engine", "Data_CarBody", "Data_Drivetrain"):
        for f in cur.execute(
                "SELECT 字段名, 中文字段名, 数据类型, 单位, 取值范围, 说明, 注释状态 "
                "FROM _字段字典 WHERE 表名=? ORDER BY 字段序号", (table,)):
            glossary.append([table, f[0], f[1], f[3], f[5] or f[6] or ""])

    countries = [{
        "id": cid, "n": loc.get("List_Country", "Country", cid),
        "r": rid, "rn": loc.get("List_Region", "DisplayName", rid),
        "c": cnt,
    } for cid, rid, cnt in cur.execute(
        "SELECT CountryID, MIN(RegionID), COUNT(*) FROM Data_Car GROUP BY CountryID ORDER BY 3 DESC")]

    # ---------- 竞速强度分级（来自调校推荐表） ----------
    # tools/tier_map.auto.json 由 tools/build_tiers.py 生成：carId -> [{g: 组别, t: 强度, m: 原始型号}]
    # 一台车可能在多张表里出现（不同改装等级），取「强度最高、组别 PI 最大」的那条作为主标签，
    # 全部条目另外存一份给详情页展开。
    TIER_NAMES = ["Meta+", "Meta", "T0.5", "T1", "T1.5", "T2", "T3", "未知"]
    tier_map_path = Path(__file__).with_name("tools") / "tier_map.auto.json"
    tier_pairs: dict[str, list[list[Any]]] = {}
    tier_rows: dict[str, list[list[Any]]] = {}
    tier_groups: list[str] = []
    if tier_map_path.exists():
        raw_tier = json.loads(tier_map_path.read_text(encoding="utf-8"))
        for cid, entries in raw_tier.items():
            for e in entries:
                if e["g"] not in tier_groups:
                    tier_groups.append(e["g"])
        for cid, entries in raw_tier.items():
            picked = []
            for e in entries:
                ti = TIER_NAMES.index(e["t"]) if e["t"] in TIER_NAMES else 7
                gi = tier_groups.index(e["g"])
                picked.append([ti, gi])
            # 去重 + 排序：强度优先，其次组别 PI 越大越靠前
            uniq = sorted({tuple(p) for p in picked},
                          key=lambda p: (p[0], -(int(re.search(r"\d{3}", tier_groups[p[1]]).group())
                                                 if re.search(r"\d{3}", tier_groups[p[1]]) else 0)))
            tier_pairs[str(cid)] = [list(p) for p in uniq]
            # 详情/数据表用的完整行：强度、组别、驱动、难度、轮胎、定位、备注
            ordered = sorted(picked, key=lambda p: (p[0], tier_groups[p[1]]))
            seen_rows, rows_out = set(), []
            for ti, gi in ordered:
                src = next((e for e in entries
                            if (TIER_NAMES.index(e["t"]) if e["t"] in TIER_NAMES else 7) == ti
                            and tier_groups.index(e["g"]) == gi), None)
                if not src:
                    continue
                key = (ti, gi, src["d"], src["diff"], src["tire"], src["role"], src["note"])
                if key in seen_rows:
                    continue
                seen_rows.add(key)
                rows_out.append([ti, gi, src["d"], src["diff"], src["tire"],
                                 src["role"], src["note"][:220]])
            tier_rows[str(cid)] = rows_out


    uniform: list[str] = []
    _cols_all = [r[1] for r in cur.execute("PRAGMA table_info(Data_Car)")]
    for f in _cols_all:
        n = cur.execute(
            f"SELECT COUNT(DISTINCT [{f}]) FROM Data_Car WHERE [{f}] IS NOT NULL").fetchone()[0]
        if n <= 1:
            uniform.append(f)

    ci = {k: i for i, k in enumerate(COLUMNS)}
    payload = {
        "cols": COLUMNS,
        "countries": countries,
        "rows": rows,
        "groups": group_names,
        "full": full_schema,
        "fullRows": full_rows,
        "tires": tires,
        "curves": curves,
        "curveSchema": curve_schema,
        "curveName": curve_name,
        "glossary": glossary,
        "fk": fk,
        "betterMax": sorted(BETTER_MAX),
        "betterMin": sorted(BETTER_MIN),
        "brief": CMP_BRIEF,
        "buckets": buckets,
        "swaps": swaps,
        "asp": asp,        # engineId -> {ts/tt/tq/dsc/csc: [等级...]}
        "wide": wide,      # carId -> [[等级, 价格, 加宽 cm], ...]
        "wideFull": wide_full,  # carId -> {s: 原厂车身, k: [[等级, 价格, 车身...], ...]}
        "bodyFields": BODY_FIELDS,  # 车身数组的字段顺序
        "aero": aero,      # carId -> {s: 原厂尾翼, k: [[等级, 价格, 质量, 风阻缩放, 稳定性, 风阻0/1, 下压力0/1, 零攻角], ...]}
        "uniform": uniform,  # 全库取值完全一致的字段名（详情页默认折叠）
        "tier": tier_pairs,  # carId -> [[强度序号, 组别序号], ...]（首个为主标签）
        "tierRows": tier_rows,  # carId -> [[强度, 组别, 驱动, 难度, 轮胎, 定位, 备注], ...]
        "tierNames": TIER_NAMES,
        "tierGroups": tier_groups,
        "tireW": tire_w,   # carId -> {sf/sr: 原厂车身最大胎宽, wf/wr: 宽体车身最大胎宽}
        "susp": susp,      # carId -> {f/r: 悬挂结构ID, st: 转向手感ID, rs: 后轮转向ID, a: 最大转角}
        "suspType": susp_type,   # 悬挂结构ID -> {n: 粗分类, p: 物理文件路径}
        "rearSteer": rear_steer, # 后轮转向配置ID -> 参数
        "steerSet": steer_set,   # 转向手感配置ID -> 参数
        "driveMode": drive_mode, # carId -> 主动驾驶模式配置
        "meta": {
            "total": len(rows),
            "brands": len({r[3] for r in rows if r[3]}),
            "classes": {c: sum(1 for r in rows if r[4] == c) for c in CLASS_ORDER.values()},
            "drive": {d: sum(1 for r in rows if r[14] == d) for d in DRIVE.values()},
            "fields": len(full_schema),
            "compounds": len(curves),
            "npc": len(npc_ids),
            "engineTotal": engine_total,
            "stockEngines": stock_engines,
            "swapEngines": swap_engines,
            "swapCombos": swap_combos,
            "logoDark": logo_dark,
            "traffic": len(traffic_ids),
            "release": len(release),
            "guessedEngines": sum(r[ci["eg"]] for r in rows),
            "carPass": sum(r[ci["cp"]] for r in rows),
            "seriesCars": sum(1 for r in rows if r[ci["sea"]]),
            "acqMatched": sum(1 for r in rows if r[ci["acq"]]),
            "gameVersion": GAME_VERSION,
            "updated": DATA_UPDATED,
            "source": "FH6 gamedbRC 车辆主表 + 引擎 / 车身 / 轮胎 / 改装子表",
        },
    }
    con.close()
    return payload


# 简 / 繁是两个独立页面（部署包里对应 index.html / zh-hans.html 与 zh-hant.html）。
# 两边互相跳转统一用 ASCII 文件名 zh-hans.html / zh-hant.html：
# 这样无论站点是挂在根目录（EdgeOne）还是 output/ 子目录（GitHub Pages），
# 简体页都能在同级找到繁体页、繁体页也能回到同级存在的简体页，不会 404。
DOCSW_HANS = ('<span class="on" aria-current="page">简</span>'
              '<a href="zh-hant.html" title="切换到繁体版">繁</a>')
DOCSW_HANT = ('<a href="zh-hans.html" title="切換到簡體版">簡</a>'
              '<span class="on" aria-current="page">繁</span>')


def render(payload: dict[str, Any], theme: str, hant: bool = False) -> str:
    """把数据塞进模板；theme 决定首屏是浅色还是深色，hant 决定简繁开关高亮哪一侧。"""
    html = TEMPLATE.replace("__DATA__", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("__LANG__", "zh").replace("__THEME__", theme)
    html = html.replace("__DOCSW__", DOCSW_HANT if hant else DOCSW_HANS)
    if theme == "dark":
        html = html.replace('<html lang="zh-CN" data-type="software">',
                            '<html lang="zh-CN" data-type="software" data-theme="dark">')
    return html




ADMIN_HTML = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>分级后台 · FH6 车辆索引</title>
<style>
  :root{--ink:#111114;--paper:#fff;--paper-2:#f4f4f5;--steel:#65656d;--rule:#e3e3e6;--accent:#e8185f}
  *{box-sizing:border-box}
  body{margin:0;background:var(--paper-2);color:var(--ink);
    font:400 14px/1.5 "Segoe UI","Microsoft YaHei",system-ui,sans-serif}
  header{position:sticky;top:0;z-index:5;display:flex;gap:14px;align-items:center;
    padding:14px 22px;background:var(--paper);border-bottom:1px solid var(--rule)}
  header h1{font-size:15px;margin:0;font-weight:600}
  header .sp{flex:1}
  header a{color:var(--steel);text-decoration:none;font-size:13px}
  main{padding:18px 22px 60px;max-width:1180px;margin:0 auto}
  .bulk{margin-bottom:14px;background:var(--paper);border:1px solid var(--rule);border-radius:4px;padding:10px 14px}
  .bulk summary{cursor:pointer;font-weight:600;font-size:13px}
  .bulk p{margin:8px 0;color:var(--steel);font-size:12.5px}
  .bulk code{background:var(--paper-2);padding:1px 5px;border-radius:3px}
  .bulk textarea{width:100%;box-sizing:border-box;padding:9px 11px;border:1px solid var(--rule);border-radius:4px;
    font:400 12.5px/1.5 ui-monospace,Consolas,monospace;resize:vertical}
  .bulk-row{display:flex;align-items:center;gap:12px;margin-top:8px}
  .bulk-row button{padding:6px 14px;border:0;border-radius:4px;background:var(--ink);color:#fff;cursor:pointer;font-size:12.5px}
  #bulkOut{font-size:12.5px;color:var(--steel)}
  .bar{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap}
  input[type=search]{flex:1;min-width:220px;padding:9px 12px;border:1px solid var(--rule);border-radius:4px;font:inherit}
  table{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--rule);border-radius:4px;overflow:hidden}
  th,td{padding:8px 10px;border-bottom:1px solid var(--rule);text-align:left;font-size:13px;vertical-align:middle}
  th{background:#fafafa;font-weight:600}
  select{padding:5px 7px;border:1px solid var(--rule);border-radius:4px;font:inherit;background:#fff}
  button.save{padding:5px 12px;border:0;border-radius:4px;background:var(--ink);color:#fff;cursor:pointer;font-size:12.5px}
  button.save:disabled{opacity:.35;cursor:default}
  .cur{color:var(--steel);font-size:12px;white-space:nowrap}
  .ok{color:#0a7f43}
  .msg{padding:10px 2px;color:var(--steel)}
  .gate{max-width:380px;margin:12vh auto 0;padding:26px 24px;background:var(--paper);
    border:1px solid var(--rule);border-radius:6px}
  .gate h2{margin:0 0 8px;font-size:15px;font-weight:600}
  .gate p{margin:0 0 16px;color:var(--steel);font-size:12.5px;line-height:1.65}
  .gate input{width:100%;padding:9px 12px;border:1px solid var(--rule);border-radius:4px;font:inherit}
  .gate button{width:100%;margin-top:12px;padding:9px;border:0;border-radius:4px;
    background:var(--ink);color:#fff;font:inherit;cursor:pointer}
  .gate button:disabled{opacity:.4;cursor:default}
  .gate .err{min-height:18px;margin-top:10px;color:#c01048;font-size:12.5px}
  .tunemgr{margin-top:44px;border-top:1px solid var(--rule);padding-top:24px}
  .tunemgr h2{font-size:16px;font-weight:600;margin:0 0 12px}
  .tunemgr .bar{display:flex;gap:8px;margin-bottom:12px}
  .tunemgr .bar input{flex:1;padding:9px 12px;border:1px solid var(--rule);border-radius:4px;font:inherit}
  .tunemgr .bar button{padding:9px 16px;border:0;border-radius:4px;background:var(--ink);color:#fff;font:inherit;cursor:pointer}
  .titem{border:1px solid var(--rule);border-radius:6px;padding:12px;margin-bottom:10px}
  .titem .hd{display:flex;gap:10px;align-items:center;font-size:12.5px;color:var(--steel);margin-bottom:9px}
  .titem .hd b{color:var(--ink);font-size:13.5px}
  .titem .grid{display:grid;grid-template-columns:150px 1fr 200px;gap:8px;margin-bottom:8px}
  .titem input,.titem select{padding:8px 10px;border:1px solid var(--rule);border-radius:4px;font:inherit;width:100%;background:var(--paper)}
  .titem .acts{display:flex;gap:8px}
  .titem .acts button{padding:7px 14px;border-radius:4px;font:inherit;cursor:pointer}
  .titem .acts .sv{background:var(--ink);color:#fff;border:0}
  .titem .acts .dl{background:none;border:1px solid var(--rule);color:#c01048}
  .titem .acts button:disabled{opacity:.45;cursor:default}
  [hidden]{display:none !important}
</style></head>
<body>
<header><h1>分级后台</h1><span class="cur" id="who">检查登录状态…</span><span class="sp"></span>
  <a href="#" id="signout" hidden>退出</a>
  <a href="zh-hans.html">返回站点</a></header>
<div class="gate" id="gate" hidden>
  <h2>需要管理密码</h2>
  <p>这个页面只对管理员开放。密码由服务端校验，页面本身不含任何凭据；连续输错 5 次会锁定 15 分钟。</p>
  <input id="pw" type="password" autocomplete="current-password" placeholder="管理密码">
  <button id="go">进入</button>
  <div class="err" id="err"></div>
</div>
<main id="app" hidden>
  <div class="bar"><input id="q" type="search" placeholder="搜车名 / 品牌 / ID"></div>
  <details class="bulk">
    <summary>批量导入调校</summary>
    <p>每行一条，用 <b>制表符</b> 或 <b>逗号</b> 分隔：<code>车辆ID, 分享码(9位), 作者ID, 分级, 发布日期(YYYY-MM-DD), 说明</code></p>
    <textarea id="bulkText" rows="6" placeholder="4210,123456789,Noa Miyako,S1 800公路,2026-11-20,高速弯稳定"></textarea>
    <div class="bulk-row"><button id="bulkGo">开始导入</button><span id="bulkOut"></span></div>
  </details>
  <div id="msg" class="msg"></div>
  <table><thead><tr><th style="width:44%">车辆</th><th style="width:15%">竞速强度</th>
    <th style="width:19%">组别</th><th style="width:11%">漂移强度</th><th></th></tr></thead>
    <tbody id="rows"></tbody></table>

  <section class="tunemgr" id="tuneMgr">
    <h2>调校管理</h2>
    <div class="bar">
      <input id="tq" type="search" placeholder="车辆 ID（如 247），或分享码 / 作者 ID 关键词；留空列出最近 60 条">
      <button id="tqGo">查询</button>
    </div>
    <div id="tmsg" class="msg"></div>
    <div id="tlist"></div>
  </section>
</main>
<script>
const CARS = __CARS__, RACE = __RACE__, GROUPS = __GROUPS__, DRIFT = __DRIFT__;
const OVR = {};
let ROLE = "full";
const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const TODAY = (() => { const d = new Date(), p = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`; })();
const api = async (p, o = {}) => {
  const r = await fetch(p, { credentials: "include", ...o,
    headers: { "Content-Type": "application/json", "X-CSRF": "1", ...(o.headers || {}) } });
  if (!r.ok) throw Object.assign(new Error("HTTP " + r.status), { status: r.status });
  return r.json();
};
async function boot() {
  let me;
  try { me = await api("/api/me"); }
  catch { $("#who").textContent = "无法连接 API"; return; }
  if (!me.user.is_admin) { showGate(""); return; }
  try { const s = await api("/auth/admin/session"); ROLE = s.role || "full"; } catch {}
  $("#gate").hidden = true; $("#app").hidden = false; $("#signout").hidden = false;
  $("#who").textContent = (me.user.display_name || "管理员") + (ROLE === "full" ? " · 管理员" : " · 漂移管理员");
  try { const r = await api("/api/tiers"); r.overrides.forEach(o => OVR[o.car_id] = o); } catch {}
  paint();
  loadTunes();
}
function showGate(msg) {
  $("#app").hidden = true; $("#signout").hidden = true; $("#gate").hidden = false;
  $("#who").textContent = "未登录";
  $("#err").textContent = msg || "";
  setTimeout(() => $("#pw").focus(), 40);
}
$("#go").onclick = async () => {
  const pw = $("#pw").value;
  if (!pw) { $("#err").textContent = "请输入密码"; return; }
  const btn = $("#go");
  btn.disabled = true; btn.textContent = "校验中…"; $("#err").textContent = "";
  try {
    await api("/auth/admin/login", { method: "POST", body: JSON.stringify({ password: pw }) });
    $("#pw").value = ""; btn.disabled = false; btn.textContent = "进入";
    await boot();
  } catch (e) {
    btn.disabled = false; btn.textContent = "进入";
    $("#err").textContent =
      e.status === 429 ? "尝试过于频繁，请 15 分钟后再试" :
      e.status === 503 ? "服务端尚未配置 ADMIN_PASSWORD" :
      e.status === 403 ? "来源校验失败，请检查 SITE_ORIGIN 与 X-CSRF 头" :
      "密码不正确";
  }
};
$("#pw").addEventListener("keydown", e => { if (e.key === "Enter") $("#go").click(); });
$("#signout").onclick = async e => {
  e.preventDefault();
  try { await api("/auth/admin/logout", { method: "POST" }); } catch {}
  Object.keys(OVR).forEach(k => delete OVR[k]);
  showGate("已退出");
};
boot();
function paint() {
  const q = ($("#q").value || "").trim().toLowerCase();
  const list = CARS.filter(c => !q || c.n.toLowerCase().includes(q) || String(c.id).includes(q)).slice(0, 400);
  $("#rows").innerHTML = list.map(c => {
    const o = OVR[c.id] || {};
    const race = o.race_tier || c.rt || "";
    const group = o.race_group || c.rg || "";
    const drift = o.drift_tier || "";
    return `<tr data-id="${c.id}">
      <td><b>${esc(c.n)}</b><br><span class="cur">ID ${c.id} · ${c.cls} ${c.pi} · 现：${esc(c.rt || "未分级")}${c.rg ? " / " + esc(c.rg) : ""}</span></td>
      <td><select class="rt" ${ROLE === "full" ? "" : 'disabled title="漂移管理员无权限" '}>${["", ...RACE].map(t => `<option ${t === race ? "selected" : ""}>${t}</option>`).join("")}</select></td>
      <td><select class="rg" ${ROLE === "full" ? "" : 'disabled title="漂移管理员无权限" '}>${["", ...GROUPS].map(t => `<option ${t === group ? "selected" : ""}>${t}</option>`).join("")}</select></td>
      <td><select class="dt">${["", ...DRIFT].map(t => `<option ${t === drift ? "selected" : ""}>${t}</option>`).join("")}</select></td>
      <td><button class="save">保存</button></td></tr>`;
  }).join("");
  document.querySelectorAll("#rows tr").forEach(tr => {
    const btn = tr.querySelector(".save");
    btn.onclick = async () => {
      btn.disabled = true; btn.textContent = "…";
      try {
        await api("/api/tiers/" + tr.dataset.id, { method: "PUT", body: JSON.stringify({
          race_tier: tr.querySelector(".rt").value || null,
          race_group: tr.querySelector(".rg").value || null,
          drift_tier: tr.querySelector(".dt").value || null }) });
        btn.textContent = "已保存";
        setTimeout(() => { btn.textContent = "保存"; btn.disabled = false; }, 1200);
      } catch (e) { btn.textContent = "失败"; btn.disabled = false; }
    };
  });
  $("#msg").textContent = list.length ? `显示 ${list.length} 台（最多 400）` : "没有匹配的车辆";
}
$("#q").oninput = () => { clearTimeout(window.__t); window.__t = setTimeout(paint, 150); };

/* 批量导入：制表符优先，其次逗号（说明里可能有逗号，所以按前 5 段切分） */
$("#bulkGo").onclick = async () => {
  const out = $("#bulkOut");
  const lines = $("#bulkText").value.split(/\\r?\\n/).map(x => x.trim()).filter(Boolean);
  if (!lines.length) { out.textContent = "没有内容"; return; }
  const rows = lines.map(line => {
    const p = line.includes("\t") ? line.split("\t") : line.split(",");
    const f = p.map(x => x.trim());
    const note = f.length > 5 ? f.slice(5).join(",") : "";
    return { car_id: f[0], share_code: f[1], author_id: f[2], tier_group: f[3], game_date: f[4] || "", note };
  });
  out.textContent = "导入中…";
  try {
    const r = await api("/api/admin/tunes/bulk", { method: "POST", body: JSON.stringify({ rows }) });
    out.textContent = `成功 ${r.imported} 条${r.failed ? `，失败 ${r.failed} 条：` + r.errors.map(e => `第${e.line}行 ${e.why}`).join("；") : ""}`;
    if (r.imported) $("#bulkText").value = "";
  } catch (e) { out.textContent = e.status === 403 ? "需要管理员权限" : "导入失败"; }
};

/* ── 调校管理 ───────────────────────────────────────── */
const fmtCode = v => String(v).replace(/\D/g, "").slice(0, 9).replace(/(\d{3})(?=\d)/g, "$1 ");

async function loadTunes() {
  const q = ($("#tq").value || "").trim();
  $("#tmsg").textContent = "查询中…";
  try {
    const url = /^\d{1,6}$/.test(q) ? "/api/admin/tunes?carId=" + q
      : "/api/admin/tunes" + (q ? "?q=" + encodeURIComponent(q) : "");
    const r = await api(url);
    renderTunes(r.tunes || []);
    $("#tmsg").textContent = r.tunes.length ? `共 ${r.tunes.length} 条` : "没有匹配的调校";
  } catch (e) {
    $("#tmsg").textContent = e.status === 403 ? "无权限" : "查询失败，请稍后重试";
    $("#tlist").innerHTML = "";
  }
}

function renderTunes(list) {
  if (!list.length) { $("#tlist").innerHTML = ""; return; }
  $("#tlist").innerHTML = list.map(t => `<div class="titem" data-id="${esc(t.id)}">
      <div class="hd"><b>车辆 ${esc(t.car_id)}</b><span>ID ${esc(t.id)}</span></div>
      <div class="grid">
        <input class="f-code" value="${esc(fmtCode(t.share_code))}" maxlength="11" placeholder="9 位分享码">
        <input class="f-author" value="${esc(t.author_id)}" maxlength="32" placeholder="作者 ID">
        <select class="f-tier">${GROUPS.map(g => `<option ${g === t.tier_group ? "selected" : ""}>${esc(g)}</option>`).join("")}</select>
      </div>
      <div class="grid" style="grid-template-columns:150px 1fr">
        <input class="f-date" type="date" min="2026-05-18" max="${TODAY}" value="${esc(t.game_date || "")}" title="游戏内调校发布时间（2026-05-18 至今天）">
        <input class="f-note" value="${esc(t.note || "")}" maxlength="100" placeholder="说明（≤100 字）">
      </div>
      <div class="acts"><button class="sv">保存</button><button class="dl">删除</button></div>
    </div>`).join("");

  document.querySelectorAll(".titem").forEach(el => {
    const id = el.dataset.id;
    const codeEl = el.querySelector(".f-code");
    codeEl.addEventListener("input", () => {
      const d = codeEl.value.replace(/\D/g, "").slice(0, 9);
      codeEl.value = d.replace(/(\d{3})(?=\d)/g, "$1 ");
    });
    const sv = el.querySelector(".sv");
    sv.onclick = async () => {
      const code = codeEl.value.replace(/\D/g, "");
      if (!/^\d{9}$/.test(code)) { $("#tmsg").textContent = "分享码必须是 9 位数字"; return; }
      sv.disabled = true;
      try {
        await api("/api/admin/tunes/" + encodeURIComponent(id), { method: "PUT", body: JSON.stringify({
          share_code: code,
          author_id: el.querySelector(".f-author").value.trim(),
          tier_group: el.querySelector(".f-tier").value,
          game_date: el.querySelector(".f-date").value,
          note: el.querySelector(".f-note").value.trim()
        }) });
        sv.textContent = "已保存";
        setTimeout(() => { sv.textContent = "保存"; sv.disabled = false; }, 1200);
      } catch (e) {
        sv.disabled = false;
        $("#tmsg").textContent = e.status === 403 ? "无权限" : "保存失败";
      }
    };
    el.querySelector(".dl").onclick = async () => {
      if (!confirm("确定删除这条调校？")) return;
      try {
        await api("/api/admin/tunes/" + encodeURIComponent(id), { method: "DELETE" });
        el.remove();
        $("#tmsg").textContent = "已删除";
      } catch { $("#tmsg").textContent = "删除失败"; }
    };
  });
}

$("#tqGo").onclick = loadTunes;
$("#tq").addEventListener("keydown", e => { if (e.key === "Enter") loadTunes(); });
</script></body></html>"""


def write_admin(payload: dict[str, Any]) -> None:
    """分级后台：独立页面，只做「改标签」，鉴权与写库都在 API 侧。"""
    tier = payload.get("tier", {})
    names, groups = payload.get("tierNames", []), payload.get("tierGroups", [])
    cars_admin = [{
        "id": c["id"], "n": c["name"], "cls": c["cls"], "pi": c["pi"],
        "rt": names[tier[str(c["id"])][0][0]] if str(c["id"]) in tier else "",
        "rg": groups[tier[str(c["id"])][0][1]] if str(c["id"]) in tier else "",
    } for c in payload.get("_cars_brief", [])]
    html = (ADMIN_HTML
            .replace("__CARS__", json.dumps(cars_admin, ensure_ascii=False, separators=(",", ":")))
            .replace("__RACE__", json.dumps(names, ensure_ascii=False))
            .replace("__GROUPS__", json.dumps(groups, ensure_ascii=False))
            .replace("__DRIFT__", json.dumps(["S", "A", "B", "C", "D"], ensure_ascii=False)))
    (OUT.parent / "admin.html").write_text(html, encoding="utf-8")
    print(f"[OK] admin.html  {(OUT.parent / 'admin.html').stat().st_size / 1024:.0f} KB")

def main() -> int:
    if not DB.exists():
        raise SystemExit(f"找不到数据库：{DB}")
    payload = build_payload()
    payload["_cars_brief"] = [
        {"id": r[0], "name": r[2], "cls": r[4], "pi": r[5]} for r in payload["rows"]]
    # 中文名是主文件；同时写 ASCII 副本，供 GitHub Pages / 本地服务直接访问
    HANS = {"light": OUT, "dark": OUT.with_name("车辆索引_暗色.html")}
    HANS_ASCII = {"light": "zh-hans.html", "dark": "zh-hans-dark.html"}
    for theme, path in HANS.items():
        html = render(payload, theme)
        path.write_text(html, encoding="utf-8")
        (OUT.parent / HANS_ASCII[theme]).write_text(html, encoding="utf-8")
        print(f"[OK] {path.name} + {HANS_ASCII[theme]}  {path.stat().st_size / 1024:.0f} KB")

    write_admin(payload)

    # ── 繁體版：分类名换成 CHT 原文，其余文案整体转繁 ──
    hant = copy.deepcopy(payload)
    for b in hant.get("buckets", []):
        if b.get("tw"):
            b["zh"] = b["tw"]
    HANT_ASCII = {"light": "zh-hant.html", "dark": "zh-hant-dark.html"}
    for theme, name in (("light", "車輛索引.html"), ("dark", "車輛索引_暗色.html")):
        html = zhconv.convert(render(hant, theme, True), "zh-hant")
        html = html.replace('lang="zh-CN"', 'lang="zh-Hant"')
        (OUT.parent / HANT_ASCII[theme]).write_text(html, encoding="utf-8")
        path = OUT.with_name(name)
        path.write_text(html, encoding="utf-8")
        print(f"[OK] {path.name}  {path.stat().st_size / 1024:.0f} KB")
    m = payload["meta"]
    print(f"     {m['total']} 台车 · {m['brands']} 品牌 · {m['fields']} 字段/车 · "
          f"{m['compounds']} 种轮胎配方 · {len(payload['glossary'])} 条字段说明")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
