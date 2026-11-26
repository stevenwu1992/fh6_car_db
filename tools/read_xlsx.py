"""把 xlsx 的每个工作表读成二维文本数组（openpyxl 打不开这个文件，直接解析 XML）。"""
import json
import re
import zipfile
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def col_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref).group()
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_xlsx(path: str) -> dict[str, list[list[str]]]:
    z = zipfile.ZipFile(path)
    shared: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter(
                "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")))

    rels = {}
    rel_root = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    for rel in rel_root:
        rels[rel.get("Id")] = rel.get("Target").lstrip("/")
    wb = ET.fromstring(z.read("xl/workbook.xml"))

    out: dict[str, list[list[str]]] = {}
    for s in wb.find("m:sheets", NS):
        name, rid = s.get("name"), s.get(RNS + "id")
        target = rels[rid]
        if not target.startswith("xl/"):
            target = "xl/" + target
        rows: list[list[str]] = []
        root = ET.fromstring(z.read(target))
        for row in root.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
            cells: dict[int, str] = {}
            for c in row.findall("m:c", NS):
                ref = c.get("r")
                if not ref:
                    continue
                t = c.get("t")
                v = c.find("m:v", NS)
                isv = c.find("m:is", NS)
                if t == "s" and v is not None:
                    txt = shared[int(v.text)]
                elif t == "inlineStr" and isv is not None:
                    txt = "".join(x.text or "" for x in isv.iter(
                        "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"))
                else:
                    txt = v.text if v is not None else ""
                cells[col_index(ref)] = (txt or "").strip()
            if cells:
                width = max(cells) + 1
                rows.append([cells.get(i, "") for i in range(width)])
        out[name] = rows
    return out


if __name__ == "__main__":
    data = read_xlsx("地平线6线上车辆调校推荐.xlsx")
    for name, rows in data.items():
        print(f"=== {name} | {len(rows)} 行")
        for r in rows[:3]:
            print("   ", [c[:24] for c in r][:11])
