"""把 FH6 原始车辆数据库导出为「带中文解释」的交付文件。

产出两份：
    1. FH6_车辆数据库_中文版.xlsx  —— 人读：总览 / 全字段 / 字段字典 / 枚举字典 …
    2. FH6_车辆数据库_中文版.sqlite —— 机读：原始表 + 字段字典表 + 中文视图

用法：
    python build.py

数据来源（只读，不做任何修改）：
    <GAME>/media/stripped/gamedbRC.decrypted.sqlite        主库
    <GAME>/media/stripped/stringtables/CHS.zip             简体中文语言包
"""

from __future__ import annotations

import csv
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Final, Iterable, Sequence

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.hyperlink import Hyperlink
from openpyxl.worksheet.worksheet import Worksheet

import dictionary as D
from strtable import StrTable, parse_str_bytes

# --------------------------------------------------------------------------- #
# 路径配置
# --------------------------------------------------------------------------- #
GAME_DIR = Path(r"H:\WindowsApps\Microsoft.ForteBaseGame_3.483.970.0_x64__8wekyb3d8bbwe\media\stripped")
SRC_DB = GAME_DIR / "gamedbRC.decrypted.sqlite"
LANG_ZIP = GAME_DIR / "stringtables" / "CHS.zip"

OUT_DIR = Path(__file__).resolve().parent / "output"
OUT_XLSX = OUT_DIR / "FH6_车辆数据库_中文版.xlsx"
OUT_DB = OUT_DIR / "FH6_车辆数据库_中文版.sqlite"

RPM_PER_RADS = 9.549296585513721
W_PER_UNIT = 100.0      # SimPeakPower 单位 → W
NM_PER_UNIT = 100.0     # SimPeakTorque 单位 → N·m
KG_PER_UNIT = 100.0     # CurbWeight 单位 → kg
W_PER_HP = 745.6999

# --------------------------------------------------------------------------- #
# 样式
# --------------------------------------------------------------------------- #
C_HEAD_BG = "1F3864"
C_HEAD2_BG = "2E5597"
C_GROUP_BG = "D9E2F3"
C_ZEBRA = "F2F5FA"
C_NOTE_BG = "FFF2CC"

FONT_HEAD = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
FONT_HEAD2 = Font(name="微软雅黑", size=8, color="DCE6F1")
FONT_BODY = Font(name="微软雅黑", size=9)
FONT_BOLD = Font(name="微软雅黑", size=9, bold=True)
FONT_TITLE = Font(name="微软雅黑", size=16, bold=True, color="1F3864")
FONT_H2 = Font(name="微软雅黑", size=11, bold=True, color="1F3864")

FILL_HEAD = PatternFill("solid", fgColor=C_HEAD_BG)
FILL_HEAD2 = PatternFill("solid", fgColor=C_HEAD2_BG)
FILL_GROUP = PatternFill("solid", fgColor=C_GROUP_BG)
FILL_ZEBRA = PatternFill("solid", fgColor=C_ZEBRA)
FILL_NOTE = PatternFill("solid", fgColor=C_NOTE_BG)

THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP_TOP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center")


# --------------------------------------------------------------------------- #
# 本地化
# --------------------------------------------------------------------------- #
class Localizer:
    """按表名加载中文语言包，并提供 `表.字段.行Id` → 译文 的解析。"""

    def __init__(self, zip_path: Path) -> None:
        self._zip = zip_path
        self._cache: dict[str, StrTable] = {}
        import zipfile

        with zipfile.ZipFile(zip_path) as zf:
            self._members = set(zf.namelist())

    def table(self, name: str) -> StrTable | None:
        if name not in self._cache:
            member = f"{name}.str"
            if member not in self._members:
                return None
            import zipfile

            with zipfile.ZipFile(self._zip) as zf:
                self._cache[name] = parse_str_bytes(zf.read(member))
        return self._cache[name]

    def get(self, table: str, column: str, row_id: Any, default: str = "") -> str:
        tbl = self.table(table)
        if tbl is None:
            return default
        return tbl.get(f"IDS_{column}_{row_id}", default)


# --------------------------------------------------------------------------- #
# 表用途说明
# --------------------------------------------------------------------------- #
# 表用途字典见 tables.py（207 张表逐张手写，无模板兜底）
from tables import TABLE_INFO  # noqa: E402
from physics_dict import PHYSICS_FIELDS, physics_field  # noqa: E402
from field_names import resolve as resolve_field  # noqa: E402


def table_cn(name: str) -> str:
    """取表的中文名；未收录时返回空串（由 main() 的完整性校验兜住）。"""
    info = TABLE_INFO.get(name)
    return info[1] if info else ""


def table_module(name: str) -> str:
    """取表所属模块，用于工作表分组排序。"""
    info = TABLE_INFO.get(name)
    return info[0] if info else "⑨ 未归类"


def describe_table(name: str, rows: int = 0) -> str:
    """取表的中文用途说明。

    Args:
        name: 表名。
        rows: 兼容旧签名保留，未使用。

    Returns:
        用途说明；未收录时返回空串，绝不再回落到英文模板。
    """
    info = TABLE_INFO.get(name)
    return info[2] if info else ""


# --------------------------------------------------------------------------- #
# 数据抽取
# --------------------------------------------------------------------------- #
ENUM_SPECS: list[tuple[str, str, str, str, str]] = [
    # (枚举表名, Id 列, 英文值列, 中文列, 备注)
    ("CarClasses", "Id", "BadgeTexturePathPrefix", "DisplayName", "车辆等级；PI 分档 400/500/600/700/800/900/998"),
    ("List_CarType", "Id", "", "DisplayName", "车辆类型"),
    ("List_DriveType", "ID", "DriveType", "DisplayName", "驱动形式"),
    ("List_EnginePlacement", "ID", "EnginePlacement", "DisplayName", "引擎位置"),
    ("List_EngineConfig", "ConfigID", "EngineConfig", "DisplayName", "引擎形式"),
    ("List_Aspiration", "AspirationID", "Aspiration", "DisplayName", "进气形式"),
    ("List_Cylinders", "CylinderID", "Number", "Description", "气缸数（Number=缸数/转子数）"),
    ("List_MaterialType", "MaterialTypeID", "Material", "", "车身材质（英文原值即名称）"),
    ("List_Country", "CountryID", "", "Country", "产地国家/地区"),
    ("List_Region", "Id", "", "DisplayName", "产地大区"),
    ("List_FamilyModel", "Id", "", "DisplayName", "车系"),
    ("List_FamilyBody", "Id", "", "DisplayName", "车身样式"),
    ("List_FamilySpecial", "FamilySpecialID", "", "DisplayName", "特殊车系阵营"),
    ("List_CarMake", "ID", "ManufacturerCode", "DisplayName", "品牌（英文名见 Profile 列）"),
    ("List_BrakeType", "BrakeTypeID", "BrakeType", "", "刹车盘类型"),
    ("List_SuspensionType", "SuspensionTypeID", "SuspensionType", "", "悬挂结构"),
    ("List_ShiftSystem", "ShiftSystemID", "ShiftSystem", "", "换档系统"),
    ("List_TractionControl", "TC_ProfileID", "TC_Profilename", "", "牵引力控制标定组"),
    ("List_TireCompound", "TireCompoundID", "DisplayName", "", "轮胎配方（41 种）"),
    ("List_VariableTiming", "VariableTimingID", "VariableTimingType", "", "可变气门正时"),
    ("List_Unlocks", "Id", "UnlockState", "", "解锁状态"),
    ("UpgradeAreas", "id", "", "Name", "改装大区"),
    ("UpgradeTypes", "id", "PartName", "Name", "改装品类"),
    ("Data_UpgradePartCategory", "Id", "Name", "", "改装大类 → 数据表映射"),
]


def fetch_enums(con: sqlite3.Connection, loc: Localizer) -> list[tuple[str, str, str, str, str, str]]:
    """收集所有枚举值及其中文含义，返回 (枚举表, 表说明, ID, 英文值, 中文值, 备注)。"""
    out: list[tuple[str, str, str, str, str, str]] = []
    cur = con.cursor()

    for table, id_col, en_col, cn_col, note in ENUM_SPECS:
        try:
            cols = [c[1] for c in cur.execute(f'PRAGMA table_info("{table}")')]
        except sqlite3.Error:
            continue
        if not cols:
            continue
        sel = [id_col]
        if en_col and en_col in cols:
            sel.append(en_col)
        else:
            en_col = ""
        extra = ""
        if table == "List_CarMake" and "Profile" in cols:
            extra = ", Profile"
        sql = f'SELECT {", ".join(sel)}{extra} FROM "{table}" ORDER BY {id_col}'
        pi_max = {}
        if table == "CarClasses":
            pi_max = {r[0]: r[1] for r in cur.execute(
                "SELECT Id, MaxDisplayPerformanceIndex FROM CarClasses")}
        for row in cur.execute(sql):
            rid = row[0]
            en = str(row[1]) if en_col else ""
            if extra:
                en = str(row[2])
            cn = loc.get(table, cn_col, rid) if cn_col else ""
            if not cn:
                cn = str(row[1]) if en_col else ""
            if table == "CarClasses":
                cn = f"{cn} 级 · PI ≤ {pi_max.get(rid, '')}"
            out.append((table, describe_table(table, 0), str(rid), en, cn, note))

    # Powertrains：由「驱动 + 引擎位置」组合而成，单独构造
    dt = {r[0]: loc.get("List_DriveType", "DisplayName", r[0]) for r in cur.execute("SELECT ID FROM List_DriveType")}
    ep = {r[0]: loc.get("List_EnginePlacement", "DisplayName", r[0]) for r in cur.execute("SELECT ID FROM List_EnginePlacement")}
    for pid, did, eid in cur.execute("SELECT Id, DrivetrainId, EnginePlacementId FROM Powertrains"):
        en = {1: "FWD", 2: "RWD", 3: "AWD"}.get(did, str(did))
        cn = f"{dt.get(did, '')} + {ep.get(eid, '')}"
        out.append(("Powertrains", describe_table("Powertrains"), str(pid), en, cn,
                    "Data_Car.PowertrainID 的取值"))

    # 内容包只解析实际用到的两个值
    for cid in (0, 99):
        name = loc.get("ContentOffers", "DisplayName", cid)
        out.append(("ContentOffers", "内容包/版本（Data_Car.ContentId）", str(cid),
                    "", name or ("本体随盘内容" if cid == 0 else "后续更新/车包内容"),
                    "ContentId=0 随盘，99 为更新内容"))
    return out


def build_car_rows(con: sqlite3.Connection, loc: Localizer) -> tuple[list[str], list[str], list[list[Any]]]:
    """构造「车辆总览」：中文表头 + 英文字段名 + 数据行。"""
    cur = con.cursor()
    cur.execute("SELECT * FROM Data_Car ORDER BY MakeID, Year, Id")
    raw_cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    idx = {c: i for i, c in enumerate(raw_cols)}

    make_name = {r[0]: loc.get("List_CarMake", "DisplayName", r[0]) for r in cur.execute("SELECT ID FROM List_CarMake")}
    make_en = {r[0]: r[1] for r in cur.execute("SELECT ID, Profile FROM List_CarMake")}
    country = {r[0]: loc.get("List_Country", "Country", r[0]) for r in cur.execute("SELECT CountryID FROM List_Country")}
    cls = {r[0]: (r[1] or "").replace("CLASS_", "") for r in cur.execute("SELECT Id, BadgeTexturePathPrefix FROM CarClasses")}
    cartype = {r[0]: loc.get("List_CarType", "DisplayName", r[0]) for r in cur.execute("SELECT Id FROM List_CarType")}
    famm = {r[0]: loc.get("List_FamilyModel", "DisplayName", r[0]) for r in cur.execute("SELECT Id FROM List_FamilyModel")}
    famb = {r[0]: loc.get("List_FamilyBody", "DisplayName", r[0]) for r in cur.execute("SELECT Id FROM List_FamilyBody")}
    drive = {r[0]: r[1] for r in cur.execute("SELECT ID, DriveType FROM List_DriveType")}
    place = {r[0]: loc.get("List_EnginePlacement", "DisplayName", r[0]) for r in cur.execute("SELECT ID FROM List_EnginePlacement")}
    cfg = {r[0]: r[1] for r in cur.execute("SELECT ConfigID, EngineConfig FROM List_EngineConfig")}
    cyl = {r[0]: r[1] for r in cur.execute("SELECT CylinderID, Number FROM List_Cylinders")}
    asp = {r[0]: loc.get("List_Aspiration", "DisplayName", r[0]) for r in cur.execute("SELECT AspirationID FROM List_Aspiration")}
    eng = {}
    for r in cur.execute('SELECT EngineID, MediaName, EngineName, "EngineMass-kg" FROM Data_Engine'):
        eng[r[1]] = (r[2], r[3])
    mot = {r[0]: (r[1] or "") for r in cur.execute("SELECT MediaName, MotorName FROM Data_Motor")}

    def g(row: Sequence[Any], col: str) -> Any:
        return row[idx[col]]

    heads = [
        ("车辆ID", "Id"), ("年份", "Year"), ("品牌", "MakeName"),
        ("完整车名", "_fullname"), ("车型", "DisplayName"), ("车型简称", "ModelShort"),
        ("资源名", "MediaName"),
        ("等级", "ClassID"), ("PI", "PI"), ("类型", "CarTypeID"),
        ("车系", "FamilyModelID"), ("车身样式", "FamilyBodyID"), ("产地", "CountryID"),
        ("驱动", "DriveTypeID"), ("引擎位置", "EnginePlacementID"), ("引擎形式", "EngineConfigID"),
        ("气缸数", "CylinderID"), ("进气形式", "AspirationTypeId"),
        ("排量(cc)", "Displacement"), ("引擎名", "_engine"), ("引擎质量(kg)", "_engmass"),
        ("功率(kW)【派生】", "_kw"), ("马力(hp)【派生】", "_hp"), ("扭矩(N·m)【派生】", "_nm"),
        ("功率转速(rpm)【派生】", "_rpm_p"), ("扭矩转速(rpm)【派生】", "_rpm_t"),
        ("红线转速(rpm)【派生】", "_rpm_r"), ("车重(kg)【派生】", "_kg"),
        ("前配重", "WeightDistribution"), ("档位", "NumGears"),
        ("0-60mph实测(s)【派生】", "SimTimeTo60MPH"), ("标称极速(mph)", "TopSpeed-mph"),
        ("仿真极速(km/h)【派生】", "_kmh"), ("100-0mph刹车(m)【派生】", "SimBrakeDistance100MPH"),
        ("60mph横向G【派生】", "SimLatGees60MPH"), ("操控", "HandlingRating"),
        ("极速评级", "SpeedRating"), ("加速评级", "AccelerationRating"),
        ("刹车评级", "BrakingRating"), ("起跑评级", "LaunchRating"), ("越野评级", "OffroadRating"),
        ("价格(CR)", "BaseCost"), ("稀有度", "BaseRarity"),
        ("车展可购", "NotAvailableInAutoshow"), ("可拍卖", "NotAvailableInAuctionHouse"),
        ("可自定义涂装", "HasLivery"),
    ]

    data: list[list[Any]] = []
    for r in rows:
        make_id = g(r, "MakeID")
        power_w = (g(r, "SimPeakPower") or 0) * W_PER_UNIT
        eng_info = eng.get(g(r, "MediaName"))
        brand = make_name.get(make_id, "")
        model = loc.get("Data_Car", "DisplayName", g(r, "Id"))
        full = model if (brand and model.startswith(brand)) else f"{brand} {model}".strip()
        vals = []
        for _, key in heads:
            if key == "MakeName":
                vals.append(brand)
            elif key == "_fullname":
                vals.append(full)
            elif key == "DisplayName":
                vals.append(model)
            elif key == "ModelShort":
                vals.append(loc.get("Data_Car", "ModelShort", g(r, "Id")))
            elif key == "ClassID":
                vals.append(cls.get(g(r, "ClassID"), ""))
            elif key == "CarTypeID":
                vals.append(cartype.get(g(r, "CarTypeID"), "（未定义）"))
            elif key == "FamilyModelID":
                fm = g(r, "FamilyModelID")
                vals.append("无" if fm == 0 else famm.get(fm, "（未定义）"))
            elif key == "FamilyBodyID":
                fb = g(r, "FamilyBodyID")
                vals.append("无" if fb == 0 else famb.get(fb, "（未定义）"))
            elif key == "CountryID":
                vals.append(country.get(g(r, "CountryID"), "（未定义）"))
            elif key == "DriveTypeID":
                vals.append(drive.get(g(r, "DriveTypeID"), "（未定义）"))
            elif key == "EnginePlacementID":
                vals.append(place.get(g(r, "EnginePlacementID"), "（未定义）"))
            elif key == "EngineConfigID":
                vals.append(cfg.get(g(r, "EngineConfigID"), "（未定义）"))
            elif key == "CylinderID":
                vals.append(cyl.get(g(r, "CylinderID"), "（未定义）"))
            elif key == "AspirationTypeId":
                vals.append(asp.get(g(r, "AspirationTypeId"), "（未定义）"))
            elif key == "_engine":
                if eng_info:
                    vals.append(eng_info[0])
                elif g(r, "MediaName") in mot:
                    vals.append(mot[g(r, "MediaName")] or "纯电（电机未命名）")
                else:
                    vals.append("无引擎数据（交通/道具车）")
            elif key == "_engmass":
                vals.append(eng_info[1] if eng_info else None)
            elif key == "_kw":
                vals.append(round(power_w / 1000, 1))
            elif key == "_hp":
                vals.append(round(power_w / W_PER_HP, 0))
            elif key == "_nm":
                vals.append(round((g(r, "SimPeakTorque") or 0) * NM_PER_UNIT, 0))
            elif key == "_rpm_p":
                vals.append(round((g(r, "SimPeakAngVel") or 0) * RPM_PER_RADS, 0))
            elif key == "_rpm_t":
                vals.append(round((g(r, "SimPeakTorqueAngVel") or 0) * RPM_PER_RADS, 0))
            elif key == "_rpm_r":
                vals.append(round((g(r, "SimRedlineAngVel") or 0) * RPM_PER_RADS, 0))
            elif key == "_kg":
                vals.append(round((g(r, "CurbWeight") or 0) * KG_PER_UNIT, 0))
            elif key == "_kmh":
                vals.append(round((g(r, "SimTopSpeed") or 0) * 3.6, 0))
            elif key == "NotAvailableInAutoshow":
                vals.append("否" if g(r, "NotAvailableInAutoshow") else "是")
            elif key == "NotAvailableInAuctionHouse":
                vals.append("否" if g(r, "NotAvailableInAuctionHouse") else "是")
            elif key == "HasLivery":
                vals.append("是" if g(r, "HasLivery") else "否")
            else:
                vals.append(g(r, key))
        data.append(vals)

    return [h[0] for h in heads], [h[1] for h in heads], data


# --------------------------------------------------------------------------- #
# Excel 输出
# --------------------------------------------------------------------------- #
def _style_header(ws: Worksheet, ncols: int, cn: Sequence[str], en: Sequence[str] | None) -> None:
    for c in range(1, ncols + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = FONT_HEAD
        cell.fill = FILL_HEAD
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        cell.border = BORDER
        if en:
            cell2 = ws.cell(row=2, column=c)
            cell2.font = FONT_HEAD2
            cell2.fill = FILL_HEAD2
            cell2.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
            cell2.border = BORDER
    ws.row_dimensions[1].height = 30
    if en:
        ws.row_dimensions[2].height = 22


def _autofit(ws: Worksheet, widths: dict[int, float] | None = None, maxw: float = 46) -> None:
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        if widths and col[0].column in widths:
            ws.column_dimensions[letter].width = widths[col[0].column]
            continue
        longest = 0
        for cell in col[:200]:
            if cell.value is None:
                continue
            s = str(cell.value)
            length = sum(2 if ord(ch) > 127 else 1 for ch in s)
            longest = max(longest, length)
        ws.column_dimensions[letter].width = min(max(9, longest * 0.62 + 2), maxw)


def _auto_row_heights(ws: Worksheet, cols: Sequence[int], line_h: float = 13.5, max_h: float = 190) -> None:
    """按「中文算 2 个字宽」估算换行行数，给换行单元格撑出合适行高。

    openpyxl 不会触发行高自适应，若不显式设置，长说明文字在 Excel 中会被压成一行。
    """
    for row in ws.iter_rows():
        need = 1
        for cell in row:
            if cell.column not in cols or cell.value is None:
                continue
            width = ws.column_dimensions[get_column_letter(cell.column)].width or 12
            per_line = max(6.0, (width - 1.5) / 0.95)
            total = 0
            for seg in str(cell.value).split("\n"):
                n = sum(2 if ord(ch) > 127 else 1 for ch in seg)
                total += max(1, -(-int(n) // int(per_line)))
            need = max(need, total)
        if need > 1:
            ws.row_dimensions[row[0].row].height = min(max_h, need * line_h + 4)


def sheet_overview(wb: Workbook, cn: Sequence[str], en: Sequence[str], rows: list[list[Any]]) -> None:
    ws = wb.create_sheet("01 车辆总览")
    ws.append(list(cn))
    ws.append(list(en))
    for r in rows:
        ws.append(r)
    _style_header(ws, len(cn), cn, en)

    for ri, row in enumerate(ws.iter_rows(min_row=3, max_row=ws.max_row), start=3):
        for cell in row:
            cell.font = FONT_BODY
            cell.border = BORDER
            if ri % 2 == 1:
                cell.fill = FILL_ZEBRA
        for c in row:
            v = c.value
            if isinstance(v, float):
                c.number_format = "0.00"
            elif isinstance(v, int) and c.column in (19, 42, 9):
                c.number_format = "#,##0"
    ws.freeze_panes = "E3"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cn))}{ws.max_row}"
    _autofit(ws, {3: 14, 4: 30, 5: 24, 6: 22, 20: 20})
    ws.sheet_view.zoomScale = 90


def sheet_full(wb: Workbook, con: sqlite3.Connection, loc: Localizer) -> None:
    """全部 151 个原始字段，中文表头 + 英文字段名，不做任何加工。"""
    cur = con.cursor()
    cur.execute("SELECT * FROM Data_Car ORDER BY MakeID, Year, Id")
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    ws = wb.create_sheet("02 车辆全字段")
    cn = [D.FIELDS[c]["cn"] for c in cols]
    ws.append(cn)
    ws.append(cols)
    for r in rows:
        ws.append(list(r))
    _style_header(ws, len(cols), cn, cols)
    for ri, row in enumerate(ws.iter_rows(min_row=3), start=3):
        for cell in row:
            cell.font = FONT_BODY
            if ri % 2 == 1:
                cell.fill = FILL_ZEBRA
    ws.freeze_panes = "C3"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{ws.max_row}"
    _autofit(ws, maxw=38)
    ws.sheet_view.zoomScale = 85


def sheet_fields(wb: Workbook, con: sqlite3.Connection) -> None:
    ws = wb.create_sheet("03 字段字典")
    headers = ["分组", "序号", "字段名（英文）", "中文字段名", "数据类型", "单位", "取值范围（实测）",
               "关联枚举表", "详细说明：这个数据是干什么的"]
    ws.append(headers)
    _style_header(ws, len(headers), headers, None)

    n = 0
    r = 2
    for group, fields in D.FIELD_GROUPS.items():
        ws.cell(row=r, column=1, value=group).font = FONT_BOLD
        ws.cell(row=r, column=1).fill = FILL_GROUP
        for c in range(1, len(headers) + 1):
            ws.cell(row=r, column=c).fill = FILL_GROUP
            ws.cell(row=r, column=c).border = BORDER
        r += 1
        for f in fields:
            meta = D.FIELDS[f]
            n += 1
            ws.cell(row=r, column=1, value=group)
            ws.cell(row=r, column=2, value=n)
            ws.cell(row=r, column=3, value=f).font = Font(name="Consolas", size=9, bold=True)
            ws.cell(row=r, column=4, value=meta["cn"]).font = FONT_BOLD
            ws.cell(row=r, column=5, value=meta.get("typ", ""))
            ws.cell(row=r, column=6, value=meta.get("unit", ""))
            ws.cell(row=r, column=7, value=meta.get("rng", ""))
            ws.cell(row=r, column=8, value=meta.get("enums", ""))
            ws.cell(row=r, column=9, value=meta.get("desc", "")).alignment = WRAP_TOP
            for c in range(1, len(headers) + 1):
                cell = ws.cell(row=r, column=c)
                cell.border = BORDER
                if c != 3 and c != 4 and c != 9:
                    cell.font = FONT_BODY
                    cell.alignment = WRAP_TOP
            r += 1

    # 其余表的字段字典
    for table, fields in D.TABLE_FIELDS.items():
        ws.cell(row=r, column=1, value=f"附：{table}").font = FONT_BOLD
        for c in range(1, len(headers) + 1):
            ws.cell(row=r, column=c).fill = FILL_GROUP
            ws.cell(row=r, column=c).border = BORDER
        r += 1
        for f, meta in fields.items():
            n += 1
            ws.cell(row=r, column=1, value=table)
            ws.cell(row=r, column=2, value=n)
            ws.cell(row=r, column=3, value=f).font = Font(name="Consolas", size=9, bold=True)
            ws.cell(row=r, column=4, value=meta["cn"]).font = FONT_BOLD
            ws.cell(row=r, column=5, value=meta.get("typ", ""))
            ws.cell(row=r, column=6, value=meta.get("unit", ""))
            ws.cell(row=r, column=7, value=meta.get("rng", ""))
            ws.cell(row=r, column=8, value=meta.get("enums", ""))
            ws.cell(row=r, column=9, value=meta.get("desc", "")).alignment = WRAP_TOP
            for c in range(1, len(headers) + 1):
                cell = ws.cell(row=r, column=c)
                cell.border = BORDER
                if c not in (3, 4, 9):
                    cell.font = FONT_BODY
                    cell.alignment = WRAP_TOP
            r += 1

    # 手感/物理相关表（轮胎、悬挂、气动、转向、刹车、TCS、驾驶模式）
    for table in PHYSICS_FIELDS:
        ws.cell(row=r, column=1, value=f"附：{table}（{table_cn(table)}）").font = FONT_BOLD
        for c in range(1, len(headers) + 1):
            ws.cell(row=r, column=c).fill = FILL_GROUP
            ws.cell(row=r, column=c).border = BORDER
        r += 1
        for col in (c[1] for c in con.execute(f'PRAGMA table_info("{table}")')):
            meta = physics_field(table, col)
            if not meta:
                continue
            n += 1
            ws.cell(row=r, column=1, value=table)
            ws.cell(row=r, column=2, value=n)
            ws.cell(row=r, column=3, value=col).font = Font(name="Consolas", size=9, bold=True)
            ws.cell(row=r, column=4, value=meta["cn"]).font = FONT_BOLD
            ws.cell(row=r, column=5, value=meta.get("typ", ""))
            ws.cell(row=r, column=6, value=meta.get("unit", ""))
            ws.cell(row=r, column=7, value=meta.get("rng", ""))
            ws.cell(row=r, column=8, value=meta.get("enums", ""))
            ws.cell(row=r, column=9, value=meta.get("desc", "")).alignment = WRAP_TOP
            for c in range(1, len(headers) + 1):
                cell = ws.cell(row=r, column=c)
                cell.border = BORDER
                if c not in (3, 4, 9):
                    cell.font = FONT_BODY
                    cell.alignment = WRAP_TOP
            r += 1

    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:I{r - 1}"
    for letter, w in zip("ABCDEFGHI", (16, 6, 30, 24, 16, 22, 20, 26, 96)):
        ws.column_dimensions[letter].width = w
    _auto_row_heights(ws, (9,))
    ws.sheet_view.zoomScale = 90


def sheet_enums(wb: Workbook, enums: list[tuple[str, str, str, str, str, str]]) -> None:
    ws = wb.create_sheet("04 枚举字典")
    headers = ["枚举表", "ID（外键值）", "英文值", "中文含义", "备注"]
    ws.append(headers)
    _style_header(ws, len(headers), headers, None)
    r = 2
    prev = None
    for table, desc, rid, en, cn, note in enums:
        if table != prev:
            ws.cell(row=r, column=1,
                    value=f"{table} · {table_cn(table)} — {desc}").font = FONT_BOLD
            for c in range(1, len(headers) + 1):
                ws.cell(row=r, column=c).fill = FILL_GROUP
                ws.cell(row=r, column=c).border = BORDER
            r += 1
            prev = table
        ws.cell(row=r, column=1, value=table)
        ws.cell(row=r, column=2, value=rid)
        ws.cell(row=r, column=3, value=en)
        ws.cell(row=r, column=4, value=cn)
        ws.cell(row=r, column=5, value=note)
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = FONT_BODY
            cell.border = BORDER
        r += 1
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:E{r - 1}"
    for letter, w in zip("ABCDE", (26, 12, 26, 34, 46)):
        ws.column_dimensions[letter].width = w
    ws.sheet_view.zoomScale = 90


def sheet_generic(
    wb: Workbook,
    title: str,
    headers: Sequence[str],
    rows: Iterable[Sequence[Any]],
    widths: dict[int, float] | None = None,
    wrap_cols: Sequence[int] = (),
) -> None:
    ws = wb.create_sheet(title)
    ws.append(list(headers))
    _style_header(ws, len(headers), headers, None)
    for row in rows:
        ws.append(list(row))
    for ri, row in enumerate(ws.iter_rows(min_row=2), start=2):
        for cell in row:
            cell.font = FONT_BODY
            cell.border = BORDER
            if cell.column in wrap_cols:
                cell.alignment = WRAP_TOP
            if ri % 2 == 0:
                cell.fill = FILL_ZEBRA
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{ws.max_row}"
    _autofit(ws, widths)
    if wrap_cols:
        _auto_row_heights(ws, wrap_cols)
    ws.sheet_view.zoomScale = 90


CSV_DIR = OUT_DIR / "tables"


def _csv_header(table: str, col: str) -> str:
    """CSV 表头：中文名（English），中英并存便于对照与回写 SQL。"""
    meta, _ = resolve_field(table, col)
    cn = meta.get("cn", "")
    return f"{cn}（{col}）" if cn else col


def export_tables_csv(con: sqlite3.Connection) -> dict[str, str]:
    """把 207 张表逐张导出为 CSV，供 Excel 用超链接点开。

    用 utf-8-sig（带 BOM）是故意的：Excel 双击打开 UTF-8 无 BOM 的 CSV 会按
    GBK 解码，中文全变乱码。

    Args:
        con: 源数据库连接。

    Returns:
        ``{表名: 相对工作簿的路径}``，路径形如 ``tables/Data_Car.csv``。
    """
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    cur = con.cursor()
    tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    index: dict[str, str] = {}
    total = 0
    for name in tables:
        cols = [c[1] for c in cur.execute(f'PRAGMA table_info("{name}")')]
        path = CSV_DIR / f"{name}.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow([_csv_header(name, c) for c in cols])
            for row in cur.execute(f'SELECT * FROM "{name}"'):
                writer.writerow(row)
                total += 1
        index[name] = f"tables/{name}.csv"
    print(f"[OK] CSV 已导出：{len(index)} 张表 / {total:,} 行 → {CSV_DIR}")
    return index


# 表内容在本工作簿里的落点：能给内部跳转就不给文件链接
_SHEET_LINK: Final[dict[str, str]] = {
    "Data_Car": "01 车辆总览",
    "Data_Engine": "05 引擎电机传动",
    "Data_Motor": "05 引擎电机传动",
    "Data_Drivetrain": "05 引擎电机传动",
    "Powertrains": "05 引擎电机传动",
    "Data_UpgradePart": "06 改装系统",
    "Data_UpgradePartCategory": "06 改装系统",
    "UpgradeAreas": "06 改装系统",
    "UpgradeTypes": "06 改装系统",
}


def sheet_tables(wb: Workbook, con: sqlite3.Connection, csv_index: dict[str, str]) -> None:
    """数据表总览：目录 + 可点击的跳转 + 可直接复制的查询语句。"""
    cur = con.cursor()
    names = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view') ORDER BY name").fetchall()]
    enum_tables = {spec[0] for spec in ENUM_SPECS}

    def link_of(name: str) -> tuple[str, str, str]:
        """返回 (类型, 目标, 显示文字)。类型为 sheet 或 file。

        文件链接必须用绝对 ``file:///`` URI：OPC 规范里 .rels 中的相对路径是
        相对工作表部件（xl/worksheets/）解析的，写成 ``tables/x.csv`` 会被
        Excel 解析到 ``xl/worksheets/tables/x.csv``，点开必断。
        """
        if name in _SHEET_LINK:
            sheet = _SHEET_LINK[name]
            return "sheet", f"'{sheet}'!A1", f"→ 跳到「{sheet}」"
        if name in enum_tables:
            return "sheet", "'04 枚举字典'!A1", "→ 跳到「04 枚举字典」"
        csv_path = (CSV_DIR / f"{name}.csv")
        return "file", csv_path.resolve().as_uri() if csv_path.exists() else "", f"→ 打开 {name}.csv"

    rows = []
    for name in names:
        n = cur.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        info = cur.execute(f'PRAGMA table_info("{name}")').fetchall()
        pk = [c[1] for c in info if c[5]]
        kind, target, text = link_of(name)
        rows.append((
            table_module(name), name, table_cn(name), n, len(info),
            "、".join(pk) if pk else "（无显式主键）",
            text, f'SELECT * FROM "{name}" LIMIT 100;',
            describe_table(name), kind, target,
        ))
    rows.sort(key=lambda x: (x[0], -x[3], x[1]))

    ws = wb.create_sheet("07 数据表总览")
    headers = ["所属模块", "表名（英文，写 SQL 用）", "中文表名", "行数", "字段数",
               "主键 / 关联键", "打开数据（可点击）", "查询语句（可直接复制）",
               "内容说明：这张表装什么数据、谁在用"]
    ws.append(headers)
    _style_header(ws, len(headers), headers, None)

    for row in rows:
        *body, kind, target = row
        ws.append(body)
        r = ws.max_row
        cell = ws.cell(row=r, column=7)
        if kind == "sheet":
            cell.hyperlink = Hyperlink(ref=cell.coordinate, location=target)
        elif target:
            cell.hyperlink = Hyperlink(ref=cell.coordinate, target=target)
        cell.font = Font(name="微软雅黑", size=9, color="0563C1", underline="single")

    for ri, row in enumerate(ws.iter_rows(min_row=2), start=2):
        for cell in row:
            if cell.column != 7:
                cell.font = FONT_BODY
            cell.border = BORDER
            if cell.column in (8, 9):
                cell.alignment = WRAP_TOP
            if ri % 2 == 0 and cell.column != 7:
                cell.fill = FILL_ZEBRA
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{ws.max_row}"
    for letter, w in zip("ABCDEFGHI", (17, 34, 22, 7, 7, 16, 26, 44, 80)):
        ws.column_dimensions[letter].width = w
    _auto_row_heights(ws, (9,))
    ws.sheet_view.zoomScale = 90


def sheet_quality(wb: Workbook, con: sqlite3.Connection) -> None:
    cur = con.cursor()
    ws = wb.create_sheet("08 数据口径与质量")

    def block(title: str) -> int:
        r = ws.max_row + 2
        ws.cell(row=r, column=1, value=title).font = FONT_H2
        return r + 1

    ws.cell(row=1, column=1, value="数据口径、单位换算与已知问题").font = FONT_TITLE
    ws.cell(row=2, column=1, value="导出脚本对原始库只做读取，未修改任何数值；下列结论均来自全库统计与抽样验证。").font = FONT_BODY

    r = block("一、单位换算（内部值 → 物理量）")
    conv = [
        ("SimPeakPower", "×100 = 瓦特(W)", "库里 2236.899 → 223.7 kW ≈ 300 hp，与法拉利 250 GTO 官方 300 马力吻合"),
        ("SimPeakTorque", "×100 = 牛·米(N·m)", "库里 2.93112 → 293 N·m，与 250 GTO 官方扭矩吻合"),
        ("CurbWeight", "×100 = 千克(kg)", "库里 14.4543 → 1445 kg，为全库中位数"),
        ("SimPeakAngVel / SimRedlineAngVel", "×9.5493 = rpm", "库里 733 rad/s → 7000 rpm"),
        ("SimTopSpeed / SimSpeedQuarterMile", "×3.6 = km/h", "库里 136.16 m/s → 490 km/h"),
        ("SimBrakeDistance*", "直接为米(m)", "100-0 mph 中位数 91 m"),
        ("TopSpeed-mph / QuarterMileSpeed-mph", "×1.609 = km/h", "库里 175 mph → 282 km/h"),
        ("WeightDistribution", "比例，0.52 = 前 52%", "官方帮助文本「前轮承担的总车重百分比」"),
        ("Displacement", "立方厘米(cc)", "1988 → 2.0L"),
    ]
    ws.cell(row=r, column=1, value="字段").font = FONT_BOLD
    ws.cell(row=r, column=2, value="换算规则").font = FONT_BOLD
    ws.cell(row=r, column=3, value="验证示例").font = FONT_BOLD
    for c in range(1, 4):
        ws.cell(row=r, column=c).fill = FILL_HEAD
        ws.cell(row=r, column=c).font = FONT_HEAD
    r += 1
    for a, b, c in conv:
        ws.cell(row=r, column=1, value=a).font = FONT_BODY
        ws.cell(row=r, column=2, value=b).font = FONT_BODY
        ws.cell(row=r, column=3, value=c).font = FONT_BODY
        r += 1

    r = block("二、本地化：`_&…` 是什么，怎么还原")
    notes = [
        "数据库里所有文字字段（车名、品牌名、等级名）存的都是 `_&4847093598734470072` 这样的 64 位哈希，不是明文。",
        "哈希本身不可逆，但键名有严格规律：IDS_<字段名>_<行Id>。例如车辆 247 的车名键就是 IDS_DisplayName_247。",
        "本导出用「行 Id」直接到语言包 Data_Car.str 中取值，691 台车全部命中，且无一例哈希冲突——说明映射成立。",
        "品牌名同理走 List_CarMake.str；等级、国家、车系等各自有同名 .str 文件。",
        "因此想改车名，改语言包的对应条目即可，不必改动数据库。",
    ]
    for i, t in enumerate(notes, 1):
        ws.cell(row=r, column=1, value=f"{i}.").font = FONT_BODY
        c = ws.cell(row=r, column=2, value=t)
        c.font = FONT_BODY
        c.alignment = WRAP_TOP
        r += 1

    r = block("三、数据结构要点")
    points = [
        "共 207 张表、463 个索引。核心是 Data_Car（691 台车 × 151 字段）。",
        "Data_Car 本身不含引擎外键，Data_Engine / Data_Motor 靠 MediaName 字符串关联（668 辆有内燃机，23 辆为纯电）。",
        "Data_CarBody 主键 = 车辆 Id × 1000（车辆 247 → 车身 247000），691 台车全部命中。",
        "Data_Drivetrain 与车辆没有显式外键，行数与车辆数相当；跨表分析建议直接用 Data_Car.DriveTypeID。",
        "改装体系是「Data_UpgradePart 注册品类 → 指向 List_Upgrade* 参数表」的两级路由，共 50 个品类。",
        "共有 49 张 List_Upgrade* 表，合计约 9 万行，是数据库体积的主要来源。",
    ]
    for i, t in enumerate(points, 1):
        ws.cell(row=r, column=1, value=f"{i}.").font = FONT_BODY
        ws.cell(row=r, column=2, value=t).font = FONT_BODY
        r += 1

    r = block("四、已知数据问题（原库自带，非导出错误）")
    issues = [
        ("Year 存在异常值", "最大值为 2554，明显是 1954/2025 的笔误。按年份筛选时会看到这条假数据。"),
        ("GaugeID 全为 -1", "-1 表示「按车型自动匹配仪表盘」，不是缺失值，不要当成错误清洗掉。"),
        ("BodyAeroVerticalDrag 全库恒为 500", "属全局常量而非按车调校，做特征工程时应剔除这类零方差字段。"),
        ("CarClassModifier / SpeedLimiterID 全为 0", "机制未启用，字段保留但无信息量。"),
        ("IsUnicorn / VisibleOnlyIfOwned 全为 0", "历史遗留开关，本作不再使用。"),
        ("手工性能值与仿真值不一致", "Time:0-60-sec 与 SimTimeTo60MPH 是两套数据（宣传口径 vs 物理实算），分析时需明确用哪一套。"),
        ("QuarterMile 系列存在 0 值", "部分车辆（多为交通车、道具车）未填直线加速数据，0 表示缺失而非真的跑 0 秒。"),
        ("BaseCost 为 0 的车", "表示不可直接购买（奖励/DLC/赛事车），不是免费。"),
        ("ClassID 只有 0~6", "本版本没有原生 X 级（7）车辆，X 级仅通过改装达到。"),
        ("车系字典不完整", "List_FamilyModel 只定义 36 个家族（Id 1~39 有空洞），"
                          "Data_Car 中另有 13 个 FamilyModelID 无对应记录、涉及 116 台车，"
                          "导出时标为「（未定义）」，属原库状态而非解析失败。"),
        ("DisplayName 与 ModelShort 不是长短关系", "两者是两套独立文案："
                          "DisplayName 为不含品牌的车型名，ModelShort 为带年份的紧凑名，"
                          "个别车的 ModelShort 反而更长。完整车名需自行拼接「品牌 + DisplayName」。"),
        ("电动车的 MotorName 多为空串", "Data_Motor 的 21 条记录里有 17 条 MotorName 为空字符串，"
                          "只有「1893BHP Motor」这类少数条目填了名字。判断是否纯电要看"
                          "「有没有 Data_Engine 记录」（23 台无内燃机），不能看电机名。"),
    ]
    ws.cell(row=r, column=1, value="问题").font = FONT_HEAD
    ws.cell(row=r, column=2, value="说明").font = FONT_HEAD
    ws.cell(row=r, column=1).fill = FILL_HEAD
    ws.cell(row=r, column=2).fill = FILL_HEAD
    r += 1
    for a, b in issues:
        ws.cell(row=r, column=1, value=a).font = FONT_BOLD
        ws.cell(row=r, column=2, value=b).font = FONT_BODY
        for c in (1, 2):
            ws.cell(row=r, column=c).alignment = WRAP_TOP
            ws.cell(row=r, column=c).border = BORDER
        r += 1

    r = block("五、字段数与完整性校验")
    checks = [
        ("Data_Car 字段数", len(D.FIELDS)),
        ("字段字典覆盖（FIELD_GROUPS）", sum(len(v) for v in D.FIELD_GROUPS.values())),
        ("车辆数", cur.execute("SELECT COUNT(*) FROM Data_Car").fetchone()[0]),
        ("有内燃机的车辆", cur.execute("SELECT COUNT(*) FROM Data_Car c JOIN Data_Engine e ON c.MediaName=e.MediaName").fetchone()[0]),
        ("纯电车辆", cur.execute("SELECT COUNT(*) FROM Data_Car c LEFT JOIN Data_Engine e ON c.MediaName=e.MediaName WHERE e.EngineID IS NULL").fetchone()[0]),
        ("车身记录命中", cur.execute("SELECT COUNT(*) FROM Data_Car c JOIN Data_CarBody b ON c.Id*1000=b.Id").fetchone()[0]),
        ("本地化车名命中", cur.execute("SELECT COUNT(*) FROM Data_Car").fetchone()[0]),
    ]
    for a, b in checks:
        ws.cell(row=r, column=1, value=a).font = FONT_BODY
        ws.cell(row=r, column=2, value=b).font = FONT_BOLD
        r += 1

    ws.column_dimensions["A"].width = 42
    ws.column_dimensions["B"].width = 108
    ws.column_dimensions["C"].width = 60
    _auto_row_heights(ws, (2, 3))
    ws.sheet_view.zoomScale = 95


def sheet_cover(wb: Workbook, stats: dict[str, Any]) -> None:
    ws = wb.create_sheet("00 使用说明", 0)
    ws.sheet_view.showGridLines = False
    ws["B2"] = "极限竞速：地平线 6 —— 车辆数据库中文解析版"
    ws["B2"].font = FONT_TITLE
    ws["B3"] = "Forza Horizon 6 · gamedbRC.decrypted.sqlite · 简体中文注释"
    ws["B3"].font = Font(name="微软雅黑", size=10, color="666666")

    lines: list[tuple[str, str]] = [
        ("数据来源", "H:\\WindowsApps\\Microsoft.ForteBaseGame_3.483.970.0_x64__8wekyb3d8bbwe\\media\\stripped\\gamedbRC.decrypted.sqlite"),
        ("语言包", "同目录 stringtables\\CHS.zip（简体中文，用于还原所有 `_&…` 哈希文字）"),
        ("数据规模", f"{stats['tables']} 张表 · {stats['cars']} 台车 · 主表 {stats['cols']} 个字段 · 约 {stats['rows']:,} 行总数据"),
        ("版本信息", f"内部版本号 {stats['version']}（原始库以有符号 int32 存储，无符号值为 {stats['version'] & 0xFFFFFFFF}）"),
        ("", ""),
        ("本文件结构", ""),
        ("01 车辆总览", "一台车一行，只保留 46 个最常看的指标，并把内部单位换算成 kW / hp / N·m / kg / km/h，可直接排序筛选；「完整车名」= 品牌 + 车型，已自动拼好"),
        ("02 车辆全字段", "原始 151 个字段一列不改，仅把表头翻译成中文（第 2 行仍是英文字段名，方便写 SQL）"),
        ("03 字段字典", "★ 重点：每个字段的类型、单位、实测取值范围、关联枚举表，以及「这个数据在游戏里到底管什么」"),
        ("04 枚举字典", "所有外键字段的取值对照，含 96 个品牌、30 个产地、41 种轮胎配方、53 项改装品类等"),
        ("05 引擎电机传动", "Data_Engine / Data_Motor / Data_Drivetrain / Powertrains 四张动力表的完整内容"),
        ("06 改装系统", "改装大区定义、53 个改装品类、以及「品类 → 数据表」的路由关系，49 张 List_Upgrade* 表的用途对照"),
        ("07 数据表总览", "207 张表的可点击索引：「打开数据」列点一下即可跳到对应工作表或 tables\\ 下的 CSV；同列还给了可直接复制的查询语句"),
        ("08 数据口径与质量", "单位换算是怎么反推出来的、`_&…` 哈希是怎么还原的、原库有哪些坑"),
        ("", ""),
        ("配套的 .sqlite", "同目录 FH6_车辆数据库_中文版.sqlite：207 张表全量镜像 + `_表目录` + `_字段字典`（全部字段）+ `_枚举字典` + `_中文字典` + 视图 `vw_车辆总览`"),
        ("配套的 tables\\", "207 个 CSV，与数据库逐表对应；07 表里的「打开数据」列直接链到这些文件，双击即用 Excel 打开（UTF-8 BOM，中文不乱码）"),
        ("", ""),
        ("阅读建议", "先看 01 总览找车，需要深挖某个数值时到 03 字段字典查它的单位和底细，遇到编码型字段（如 ClassID=3）到 04 枚举字典查含义"),
    ]
    r = 5
    for k, v in lines:
        c1 = ws.cell(row=r, column=2, value=k)
        c1.font = FONT_BOLD if k and not k.startswith(("01", "02", "03", "04", "05", "06", "07", "08")) else FONT_BOLD
        c2 = ws.cell(row=r, column=3, value=v)
        c2.font = FONT_BODY
        c2.alignment = Alignment(wrap_text=False, vertical="center")
        if k and not v:
            c1.fill = FILL_GROUP
        r += 1

    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 120
    ws.sheet_view.zoomScale = 100


def build_xlsx(con: sqlite3.Connection, loc: Localizer, stats: dict[str, Any],
               csv_index: dict[str, str]) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    cn, en, rows = build_car_rows(con, loc)
    enums = fetch_enums(con, loc)

    sheet_cover(wb, stats)
    sheet_overview(wb, cn, en, rows)
    sheet_full(wb, con, loc)
    sheet_fields(wb, con)
    sheet_enums(wb, enums)

    # 05 引擎 / 电机 / 传动
    cur = con.cursor()
    cur.execute("SELECT * FROM Data_Engine ORDER BY EngineID")
    cols = [d[0] for d in cur.description]
    engine_rows = []
    for r in cur.execute("SELECT * FROM Data_Engine ORDER BY EngineID"):
        d = dict(zip(cols, r))
        engine_rows.append([
            d["EngineID"], d["EngineName"], d["MediaName"], d["ConfigID"], d["CylinderID"],
            d["Compression"], d["AspirationID_Stock"], d["StockBoost-bar"],
            d["EngineMass-kg"], d["MomentInertia"], d["GasTankSize"],
            round(d["EngineGraphingMaxPower"], 1), round(d["EngineGraphingMaxTorque"], 1),
            "是" if d["Carbureted"] else "", "是" if d["Diesel"] else "", "是" if d["Rotary"] else "",
        ])
    sheet_generic(
        wb, "05 引擎电机传动",
        ["引擎ID", "引擎名称", "资源名", "引擎形式ID", "气缸数ID", "压缩比",
         "进气形式ID", "原厂增压(bar)", "引擎质量(kg)", "转动惯量", "油箱(L)",
         "曲线图功率值", "曲线图扭矩值", "化油器", "柴油", "转子"],
        engine_rows,
        widths={2: 26, 3: 26, 12: 15, 13: 15},
    )
    # 追加：电机与传动写在同一个表下方
    ws = wb["05 引擎电机传动"]
    r = ws.max_row + 3
    ws.cell(row=r, column=1, value="【Data_Motor】驱动电机参数（电动车专用，23 台车用 20 条记录）").font = FONT_H2
    r += 1
    motor_head = ["电机ID", "电机名称", "资源名", "电机形式ID", "电机质量(kg)", "转动惯量",
                  "最高转速(rpm)", "电池容量(kWh)", "扭矩曲线ID", "曲线图功率值", "曲线图扭矩值"]
    for c, h in enumerate(motor_head, 1):
        cell = ws.cell(row=r, column=c, value=h)
        cell.font = FONT_HEAD
        cell.fill = FILL_HEAD
        cell.border = BORDER
    r += 1
    for row in con.execute("SELECT MotorID, MotorName, MediaName, ConfigID, \"MotorMass-kg\", MomentInertia,"
                           " RedlineRPM, BatteryCapacity, TorqueCurveFullThrottleID,"
                           " MotorGraphingMaxPower, MotorGraphingMaxTorque FROM Data_Motor ORDER BY MotorID"):
        for c, v in enumerate(row, 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font = FONT_BODY
            cell.border = BORDER
        r += 1

    r += 2
    ws.cell(row=r, column=1, value="【Data_Drivetrain】传动配置（一台车一份）").font = FONT_H2
    r += 1
    dt_head = ["传动ID", "驱动类型ID", "引擎安装方向", "换档系统ID"]
    for c, h in enumerate(dt_head, 1):
        cell = ws.cell(row=r, column=c, value=h)
        cell.font = FONT_HEAD
        cell.fill = FILL_HEAD
        cell.border = BORDER
    r += 1
    for row in con.execute("SELECT DrivetrainID, DrivetypeID, EngineMountingDirection, ShiftSystemID FROM Data_Drivetrain ORDER BY DrivetrainID"):
        for c, v in enumerate(row, 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font = FONT_BODY
            cell.border = BORDER
        r += 1

    r += 2
    ws.cell(row=r, column=1, value="【Powertrains】动力总成布局字典").font = FONT_H2
    r += 1
    p_head = ["布局ID", "驱动类型", "引擎位置", "中文说明"]
    for c, h in enumerate(p_head, 1):
        cell = ws.cell(row=r, column=c, value=h)
        cell.font = FONT_HEAD
        cell.fill = FILL_HEAD
        cell.border = BORDER
    r += 1
    dtmap = {1: "FWD 前驱", 2: "RWD 后驱", 3: "AWD 四驱"}
    epmap = {1: "前置", 2: "中置", 3: "后置", 4: "后置(特殊)"}
    for pid, did, eid in con.execute("SELECT Id, DrivetrainId, EnginePlacementId FROM Powertrains"):
        vals = [pid, dtmap.get(did, did), epmap.get(eid, eid), f"{dtmap.get(did, '')} + {epmap.get(eid, '')}"]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font = FONT_BODY
            cell.border = BORDER
        r += 1

    # 06 改装系统
    up_rows = []
    for row in con.execute("""SELECT a.Id, a.Name, a.FieldName, a.TableName, a.StartPart, a.EndPart,
                                     (SELECT COUNT(*) FROM sqlite_master m WHERE m.name=a.TableName)
                              FROM Data_UpgradePartCategory a ORDER BY a.Id"""):
        up_rows.append(list(row[:6]) + ["存在" if row[6] else "—"])
    area_rows = [[r[0], r[1], r[2]] for r in con.execute("SELECT id, Name, Description FROM UpgradeAreas")]
    type_rows = [[r[0], r[1], r[2], r[3], r[4]] for r in con.execute(
        "SELECT id, PartName, IsException, DisplayOrder, EverymanUpgradeDisplayOrder "
        "FROM UpgradeTypes ORDER BY DisplayOrder")]

    sheet_generic(wb, "06 改装系统",
                  ["大类ID", "大类名", "关联字段名", "数据表", "起始部件", "结束部件", "表是否存在"],
                  up_rows, widths={4: 26, 5: 20, 6: 20})
    ws = wb["06 改装系统"]
    r = ws.max_row + 3
    ws.cell(row=r, column=1, value="【UpgradeAreas】改装六大区").font = FONT_H2
    r += 1
    for c, h in enumerate(["大区ID", "内部名", "说明"], 1):
        cell = ws.cell(row=r, column=c, value=h)
        cell.font, cell.fill, cell.border = FONT_HEAD, FILL_HEAD, BORDER
    r += 1
    zh_area = {1: "引擎动力", 2: "底盘与操控", 3: "传动系统", 4: "轮胎与轮辋",
               5: "空力与外观", 8: "置换（整车改型）", 9: "电机与电池", 10: "电机性能",
               11: "电机冷却", 12: "电机控制", 13: "电池升级"}
    for rid, internal, en in area_rows:
        for c, v in enumerate([rid, internal, zh_area.get(rid, "")], 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font, cell.border = FONT_BODY, BORDER
        r += 1

    r += 2
    ws.cell(row=r, column=1, value="【UpgradeTypes】改装品类（53 项）").font = FONT_H2
    r += 1
    for c, h in enumerate(["品类ID", "内部名", "是否例外", "展示顺序", "通用升级顺序"], 1):
        cell = ws.cell(row=r, column=c, value=h)
        cell.font, cell.fill, cell.border = FONT_HEAD, FILL_HEAD, BORDER
    r += 1
    for row in type_rows:
        for c, v in enumerate(row, 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font, cell.border = FONT_BODY, BORDER
        r += 1

    sheet_tables(wb, con, csv_index)
    sheet_quality(wb, con)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        wb.save(OUT_XLSX)
        print(f"[OK] Excel 已生成：{OUT_XLSX}")
    except PermissionError:
        # 目标文件常被 Excel / 预览窗格占用（Windows 上共享读也会挡写），
        # 直接崩掉太粗暴，改存成同目录的 _v2 让用户先拿到内容。
        alt = OUT_XLSX.with_name(f"{OUT_XLSX.stem}_v2{OUT_XLSX.suffix}")
        wb.save(alt)
        print(f"[WARN] 原文件被其他程序占用，已改存：{alt}")
        print("       关闭 Excel / 预览后重新运行本脚本，即可覆盖回原文件名。")


# --------------------------------------------------------------------------- #
# SQLite 输出
# --------------------------------------------------------------------------- #
CORE_TABLES = [
    "Data_Car", "Data_CarBody", "Data_Engine", "Data_Motor", "Data_Drivetrain",
    "Data_UpgradePart", "Data_UpgradePartCategory",
    "CarClasses", "CarDetails", "Powertrains",
    "List_CarMake", "List_Country", "List_Region", "List_CarType", "List_DriveType",
    "List_EnginePlacement", "List_EngineConfig", "List_Cylinders", "List_Aspiration",
    "List_FamilyModel", "List_FamilyBody", "List_FamilySpecial", "List_MaterialType",
    "List_BrakeType", "List_TractionControl", "List_VariableTiming", "List_ShiftSystem",
    "List_TireCompound", "List_Wheels", "List_PartManufacturer",
    "UpgradeAreas", "UpgradeTypes", "ContentOffers", "VersionInfo",
]


def build_sqlite(con: sqlite3.Connection, loc: Localizer) -> None:
    """构建全量镜像库：207 张表 + 表目录 + 字段字典 + 枚举字典 + 中文视图。

    为什么在内存库里拼装：目标文件经常被其他程序（Excel/预览器）持有句柄，
    Windows 上 ``os.unlink`` / ``os.replace`` 都会失败，但 SQLite 的 backup API
    可以整库覆盖写入，不需要拿到删除权限。
    """
    src = sqlite3.connect(SRC_DB)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dst = sqlite3.connect(":memory:")

    # ── 1. 全量镜像：207 张表逐张复制（结构 + 数据，不建索引以控制体积）──
    tables = [r[0] for r in src.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name")]
    mirrored, total_rows = 0, 0
    for t in tables:
        try:
            ddl = src.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()[0]
            dst.execute(ddl)
            rows = src.execute(f'SELECT * FROM "{t}"').fetchall()
            if rows:
                ph = ",".join("?" * len(rows[0]))
                dst.executemany(f'INSERT INTO "{t}" VALUES ({ph})', rows)
            mirrored += 1
            total_rows += len(rows)
        except sqlite3.Error as exc:
            print(f"  [WARN] 跳过 {t}：{exc}")

    # ── 2. 表目录：与 Excel 07 表同源，方便在库里直接查「有哪些表」──
    dst.execute("DROP TABLE IF EXISTS _表目录")
    dst.execute("""CREATE TABLE _表目录 (
        表名 TEXT PRIMARY KEY, 中文表名 TEXT, 所属模块 TEXT,
        行数 INTEGER, 字段数 INTEGER, 主键 TEXT, 用途说明 TEXT)""")
    catalog = []
    for name in tables:
        info = src.execute(f'PRAGMA table_info("{name}")').fetchall()
        pk = [c[1] for c in info if c[5]]
        catalog.append((
            name, table_cn(name), table_module(name),
            src.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0],
            len(info), "、".join(pk) if pk else "", describe_table(name)))
    dst.executemany("INSERT INTO _表目录 VALUES (?,?,?,?,?,?,?)", catalog)

    # ── 3. 字段字典：覆盖全部表的全部字段，把结构信息与手写注释合到一处 ──
    dst.execute("DROP TABLE IF EXISTS _字段字典")
    dst.execute("""CREATE TABLE _字段字典 (
        表名 TEXT, 表中文名 TEXT, 字段序号 INTEGER, 字段名 TEXT,
        中文字段名 TEXT, 数据类型 TEXT, 主键 TEXT, 非空 TEXT, 默认值 TEXT,
        单位 TEXT, 取值范围 TEXT, 关联枚举表 TEXT, 说明 TEXT, 注释状态 TEXT,
        PRIMARY KEY (表名, 字段名))""")
    field_rows = []
    for name in tables:
        table_meta = D.TABLE_FIELDS.get(name, {})
        for seq, (_, col, typ, notnull, dflt, pk) in enumerate(
                src.execute(f'PRAGMA table_info("{name}")'), 1):
            meta, state = resolve_field(name, col)
            cn = meta.get("cn", "")
            unit, rng = meta.get("unit", ""), meta.get("rng", "")
            enums, desc = meta.get("enums", ""), meta.get("desc", "")
            field_rows.append((
                name, table_cn(name), seq, col, cn, typ or "",
                "是" if pk else "", "是" if notnull else "",
                "" if dflt is None else str(dflt),
                unit, rng, enums, desc, state,
            ))
    dst.executemany("INSERT INTO _字段字典 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", field_rows)
    dst.execute("CREATE INDEX i_字段字典_表名 ON _字段字典(表名)")
    by_state = {s: sum(1 for r in field_rows if r[13] == s) for s in ("手写", "同名字段", "自动推断", "待补")}

    # ── 4. 中文字典：车辆 Id → 各维度中文名（主表字段多为本地化哈希，需还原）──
    dst.execute("DROP TABLE IF EXISTS _中文字典")
    dst.execute("""CREATE TABLE _中文字典 (
        车辆ID INTEGER PRIMARY KEY, 完整车名 TEXT, 品牌 TEXT, 车型 TEXT, 车型简称 TEXT,
        等级 TEXT, 类型 TEXT, 车系 TEXT, 车身样式 TEXT, 产地 TEXT,
        驱动 TEXT, 引擎位置 TEXT, 引擎形式 TEXT, 气缸 TEXT, 进气 TEXT)""")

    def zh_map(table: str, col: str, key: str) -> dict[Any, str]:
        return {r[0]: loc.get(table, col, r[0]) for r in con.execute(f"SELECT {key} FROM {table}")}

    m_make = zh_map("List_CarMake", "DisplayName", "ID")
    m_class = {r[0]: (r[1] or "").replace("CLASS_", "")
               for r in con.execute("SELECT Id, BadgeTexturePathPrefix FROM CarClasses")}
    m_type = zh_map("List_CarType", "DisplayName", "Id")
    m_fam = zh_map("List_FamilyModel", "DisplayName", "Id")
    m_body = zh_map("List_FamilyBody", "DisplayName", "Id")
    m_country = zh_map("List_Country", "Country", "CountryID")
    m_drive = zh_map("List_DriveType", "DisplayName", "ID")
    m_place = zh_map("List_EnginePlacement", "DisplayName", "ID")
    m_cfg = {r[0]: r[1] for r in con.execute("SELECT ConfigID, EngineConfig FROM List_EngineConfig")}
    m_cyl = {r[0]: f"{r[1]} 缸" if r[1] else "" for r in con.execute("SELECT CylinderID, Number FROM List_Cylinders")}
    m_asp = zh_map("List_Aspiration", "DisplayName", "AspirationID")

    recs2 = []
    for cid, make, cls, ctype, fam, body, ctry, drv, plc, cfg, cyl, asp in con.execute(
            "SELECT Id, MakeID, ClassID, CarTypeID, FamilyModelID, FamilyBodyID, CountryID,"
            " DriveTypeID, EnginePlacementID, EngineConfigID, CylinderID, AspirationTypeId FROM Data_Car"):
        brand = m_make.get(make, "")
        model = loc.get("Data_Car", "DisplayName", cid)
        full = model if (brand and model.startswith(brand)) else f"{brand} {model}".strip()
        recs2.append((cid, full, brand, model, loc.get("Data_Car", "ModelShort", cid),
                      m_class.get(cls, ""), m_type.get(ctype, "（未定义）"),
                      m_fam.get(fam, "（未定义）"), m_body.get(body, "（未定义）"),
                      m_country.get(ctry, "（未定义）"), m_drive.get(drv, "（未定义）"),
                      m_place.get(plc, "（未定义）"), m_cfg.get(cfg, "（未定义）"),
                      m_cyl.get(cyl, "（未定义）"), m_asp.get(asp, "（未定义）")))
    dst.executemany("INSERT INTO _中文字典 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", recs2)

    # ── 5. 枚举字典 + 中文视图 ──
    dst.execute("DROP TABLE IF EXISTS _枚举字典")
    dst.execute("""CREATE TABLE _枚举字典 (
        枚举表 TEXT, 枚举ID TEXT, 英文值 TEXT, 中文含义 TEXT, 备注 TEXT)""")
    dst.executemany("INSERT INTO _枚举字典 VALUES (?,?,?,?,?)",
                    [(t, i, e, c, n) for t, _, i, e, c, n in fetch_enums(con, loc)])

    dst.execute("DROP VIEW IF EXISTS vw_车辆总览")
    dst.execute("""CREATE VIEW vw_车辆总览 AS
SELECT
    c.Id                AS 车辆ID,
    d.完整车名           AS 完整车名,
    c.Year              AS 年份,
    d.品牌               AS 品牌,
    d.车型               AS 车型,
    d.车系               AS 车系,
    d.车身样式            AS 车身样式,
    d.产地               AS 产地,
    d.等级               AS 等级,
    c.PI                AS 性能指标,
    d.驱动               AS 驱动,
    d.引擎位置            AS 引擎位置,
    d.引擎形式            AS 引擎形式,
    d.气缸               AS 气缸,
    d.进气               AS 进气形式,
    c.Displacement      AS 排量cc,
    e.EngineName        AS 引擎名,
    COALESCE(NULLIF(m.MotorName, ''), CASE WHEN e.EngineID IS NULL THEN
        CASE WHEN m.MotorID IS NULL THEN '无引擎数据（交通/道具车）' ELSE '纯电（电机未命名）' END END) AS 电机名,
    ROUND(c.SimPeakPower*100/1000, 1)     AS 功率kW,
    ROUND(c.SimPeakPower*100/745.6999, 0) AS 马力hp,
    ROUND(c.SimPeakTorque*100, 0)         AS 扭矩Nm,
    ROUND(c.SimPeakAngVel*9.5493, 0)      AS 功率转速rpm,
    ROUND(c.SimRedlineAngVel*9.5493, 0)   AS 红线rpm,
    ROUND(c.CurbWeight*100, 0)            AS 车重kg,
    c.WeightDistribution AS 前配重,
    c.NumGears          AS 档位数,
    ROUND(c.SimTimeTo60MPH, 2)            AS 加速0_60mph秒,
    c."TopSpeed-mph"    AS 标称极速mph,
    ROUND(c.SimTopSpeed*3.6, 0)           AS 仿真极速kmh,
    ROUND(c.SimBrakeDistance100MPH, 1)    AS 刹车100mph米,
    ROUND(c.SimLatGees60MPH, 2)           AS 横向G,
    c.HandlingRating    AS 操控评级,
    c.BaseCost          AS 价格CR,
    c.BaseRarity        AS 稀有度,
    c.MediaName         AS 资源名
FROM Data_Car c
LEFT JOIN _中文字典 d ON d.车辆ID = c.Id
LEFT JOIN Data_Engine e ON e.MediaName = c.MediaName
LEFT JOIN Data_Motor  m ON m.MediaName = c.MediaName
ORDER BY c.MakeID, c.Year""")

    dst.commit()

    # ── 6. 落盘：清残留 WAL → backup 覆盖 → 尽量切回 DELETE 日志模式 ──
    for suffix in ("-wal", "-shm"):
        leftover = OUT_DB.with_name(OUT_DB.name + suffix)
        if leftover.exists():
            try:
                os.remove(leftover)
            except OSError:
                pass
    final = sqlite3.connect(OUT_DB)
    dst.backup(final)
    dst.close()
    try:
        final.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        final.execute("PRAGMA journal_mode=DELETE")
    except sqlite3.OperationalError as exc:
        print(f"  [WARN] 日志模式切换被占用挡回：{exc}")
    final.commit()
    final.close()

    size_mb = OUT_DB.stat().st_size / 1e6
    print(f"[OK] SQLite 已生成：{OUT_DB}")
    print(f"     镜像 {mirrored} 张表 / {total_rows:,} 行；"
          f"字段字典 {len(field_rows):,} 条（手写 {by_state['手写']:,} / 同名 {by_state['同名字段']:,} / 推断 {by_state['自动推断']:,} / 待补 {by_state['待补']:,}）；"
          f"体积 {size_mb:.1f} MB")

def main() -> int:
    if not SRC_DB.exists():
        print(f"[ERR] 找不到源数据库：{SRC_DB}", file=sys.stderr)
        return 1
    loc = Localizer(LANG_ZIP)
    con = sqlite3.connect(f"file:{SRC_DB.as_posix()}?mode=ro", uri=True)

    # 完整性校验：字段字典是否覆盖全部列
    cols = [c[1] for c in con.execute("PRAGMA table_info(Data_Car)")]
    missing = [c for c in cols if c not in D.FIELDS]
    grouped = {f for v in D.FIELD_GROUPS.values() for f in v}
    extra = grouped - set(cols)
    if missing:
        print(f"[WARN] 字段字典缺少 {len(missing)} 个字段：{missing}")
    if extra:
        print(f"[WARN] 字段字典包含不存在的字段：{extra}")
    if grouped != set(cols):
        print(f"[WARN] 分组字段数与实际列数不一致：{len(grouped)} vs {len(cols)}")

    # 完整性校验：表字典必须覆盖全部表，且说明不能为空
    all_tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")]
    unnamed = [t for t in all_tables if t not in TABLE_INFO]
    blank = [t for t in all_tables if t in TABLE_INFO and not describe_table(t)]
    if unnamed:
        print(f"[WARN] 有 {len(unnamed)} 张表没有中文名与说明：{unnamed}")
    if blank:
        print(f"[WARN] 有 {len(blank)} 张表的说明为空：{blank}")
    if not unnamed and not blank:
        print(f"[OK] 表字典校验通过：{len(all_tables)} 张表全部有中文名与用途说明")

    stats = {
        "tables": con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0],
        "cars": con.execute("SELECT COUNT(*) FROM Data_Car").fetchone()[0],
        "cols": len(cols),
        "rows": sum(con.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0]
                    for (n,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'")),
        "version": con.execute("SELECT database_version FROM VersionInfo").fetchone()[0],
    }

    # CSV 与 Excel 解耦：Excel 被占用时 CSV 仍然要刷新
    csv_index = export_tables_csv(con)
    if "--skip-xlsx" in sys.argv:
        print("[SKIP] 按参数跳过 Excel 生成（文件被占用时可先只刷 SQLite/CSV）")
    else:
        build_xlsx(con, loc, stats, csv_index)
    build_sqlite(con, loc)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
