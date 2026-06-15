#!/usr/bin/env python3
"""Regenerate data.js from cllisites.xlsx.

Reads the spreadsheet and writes the site list into data.js as plain JS
constants (COLUMNS + SITES) so the static webapp can load it with a simple
<script> tag — no fetch/CORS, so it works both on GitHub Pages and when the
page is opened directly from disk (file://).

Usage:
    python build_data.py
"""
import json
import sys

try:
    import openpyxl
except ImportError:
    sys.exit("openpyxl is required: pip install openpyxl")

SRC = "cllisites.xlsx"
OUT = "data.js"


def main():
    wb = openpyxl.load_workbook(SRC, data_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        sys.exit(f"{SRC} is empty")

    headers = [str(h).strip() if h is not None else "" for h in rows[0]]

    sites = []
    for r in rows[1:]:
        if all(c is None for c in r):
            continue
        sites.append({
            h: ("" if v is None else str(v).strip())
            for h, v in zip(headers, r)
        })

    with open(OUT, "w", newline="\n") as f:
        f.write("// Auto-generated from cllisites.xlsx by build_data.py — do not edit by hand.\n")
        f.write("// Columns: " + ", ".join(headers) + "\n")
        f.write("const COLUMNS = " + json.dumps(headers) + ";\n")
        f.write("const SITES = " + json.dumps(sites, indent=2) + ";\n")

    print(f"Wrote {OUT} with {len(sites)} sites and {len(headers)} columns.")


if __name__ == "__main__":
    main()
