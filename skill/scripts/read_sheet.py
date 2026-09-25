#!/usr/bin/env python3
"""Stage 1 helper — turn the "Data Infra What's New" sheet into products_raw.json.

The sheet is fetched with the Google Drive connector, exported as xlsx
(exportMimeType = application/vnd.openxmlformats-officedocument.spreadsheetml.sheet).
That tool result is saved as JSON; pass it here together with the tab name.

Usage:
    python read_sheet.py <tool_result.json|file.xlsx> <tab_name> <run_dir>

Writes <run_dir>/products_raw.json with one entry per product row group and a
list of review notes (skipped products, empty rows, truncated cells, missing
mascots). Merged cells are forward-filled so multi-feature products come out as one
product with several features.
"""
import base64
import json
import os
import re
import sys

from openpyxl import load_workbook

HEADERS = {
    "no": ["No."],
    "product": ["Product"],
    "feature": ["更新功能名称", "功能名称"],
    "problem": ["解决的用户问题 / 场景", "解决的用户问题/实现的场景"],
    "audience": ["目标用户"],
    "status": ["上线范围和状态"],
    "entry": ["产品入口"],
    "guide": ["Guide / Demo", "Guide 或 Demo"],
    "screenshot": ["可提供的截图"],
    "existing_copy": ["現有可提供文案"],
}

# product name in the sheet -> canonical id + mascot key (see references/mascots.md)
PRODUCT_MAP = {
    "diana": ("diana", "diana_dgc_girl"),
    "studio agent": ("data_studio", "datastudio"),
    "data studio": ("data_studio", "datastudio"),
    "scheduler agent": ("scheduler_agent", None),
    "langfuse": ("langfuse", "langfuse_octopus"),
    "cli": ("cli", "cli_boy"),
    "dgc agent": ("dgc_agent", "diana_dgc_girl"),
    "data hub agent": ("datahub_agent", "datahub_robot"),
    "datahub": ("datahub_agent", "datahub_robot"),
    "onebi - spreadsheet": ("onebi_spreadsheet", None),
    "ram": ("ram", None),
}

LIVE_PAT = re.compile(r"(released|已上线|已上線|全量|live|✅)", re.I)
COMING_PAT = re.compile(r"(expected|即将|即將|coming|🔜|下旬|上旬|中旬)", re.I)
SKIP_PAT = re.compile(r"(下個月|下个月|next month|再宣傳|再宣传)", re.I)


RUN_DIR = None


def load_xlsx(path):
    if path.endswith(".xlsx"):
        return path
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    inner = json.loads(d[0]["text"]) if isinstance(d, list) else d
    out = os.path.join(os.path.abspath(RUN_DIR), "sheet_export.xlsx") if RUN_DIR else "sheet_export.xlsx"
    with open(out, "wb") as f:
        f.write(base64.b64decode(inner["content"]))
    return out


def col_index(ws):
    idx = {}
    for cell in ws[1]:
        for key, names in HEADERS.items():
            if cell.value and str(cell.value).strip() in names:
                idx[key] = cell.column - 1
    return idx


def status_of(s):
    if not s:
        return "unknown"
    if SKIP_PAT.search(s):
        return "skip"
    if COMING_PAT.search(s):
        return "coming"
    if LIVE_PAT.search(s):
        return "live"
    return "unknown"


def main(src, tab, run_dir):
    global RUN_DIR
    RUN_DIR = run_dir
    os.makedirs(run_dir, exist_ok=True)
    xlsx = load_xlsx(src)
    wb = load_workbook(xlsx)
    if tab not in wb.sheetnames:
        sys.exit(f"tab {tab!r} not found; available: {wb.sheetnames}")
    ws = wb[tab]
    idx = col_index(ws)
    notes = []
    products, current = [], None

    def get(row, key):
        i = idx.get(key)
        v = row[i] if i is not None and i < len(row) else None
        return str(v).strip() if v is not None else ""

    for r, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not any(c is not None for c in row):
            continue
        name = get(row, "product")
        if name:  # new product group (merged cells only carry value in first row)
            key = name.lower().strip()
            pid, mascot = PRODUCT_MAP.get(key, (re.sub(r"\W+", "_", key), None))
            current = {
                "id": pid, "name": name, "mascot": mascot, "source_rows": [], "features": [],
                "audience_raw": "", "status_raw": "", "entry": "", "guide": "", "existing_copy": "",
            }
            products.append(current)
            if mascot is None:
                notes.append(f"{name}: no mascot mapped in PRODUCT_MAP — ask for a reference image")
        if current is None:
            continue
        current["source_rows"].append(r)
        feat = get(row, "feature")
        problem = get(row, "problem")
        if feat and feat not in ("/", "-", "—"):
            current["features"].append({"name_raw": feat, "problem_raw": problem, "row": r})
            if problem and re.search(r"[A-Za-z]\s*$", problem) and not problem.rstrip().endswith((".", "。", ")", "）")):
                notes.append(f"{current['name']} row {r}: problem text may be truncated in the sheet — confirm with PIC")
        elif feat in ("/", "-", "—"):
            notes.append(f"{name}: marked '/' — no update this month, skipped")
        for k in ("audience_raw", "status_raw", "entry", "guide", "existing_copy"):
            v = get(row, k.replace("_raw", ""))
            if v and not current[k]:
                current[k] = v
            elif v and current[k] and v != current[k] and k == "audience_raw":
                current[k] += " | " + v

    for p in products:
        p["status"] = status_of(p["status_raw"])
        p["skip"] = not p["features"] or p["status"] == "skip"
        if p["features"] and not any(f["problem_raw"] for f in p["features"]):
            notes.append(f"{p['name']}: feature names only, no problem/scenario text — copy will be thin; ask PIC or use existing docs")
        if p["features"] and not p["entry"]:
            notes.append(f"{p['name']}: no product entry URL — required for the card button")

    os.makedirs(run_dir, exist_ok=True)
    out = os.path.join(run_dir, "products_raw.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"tab": tab, "products": products, "notes": notes}, f, ensure_ascii=False, indent=2)
    print(out)
    print("\n".join("NOTE: " + n for n in notes))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
