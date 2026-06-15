# CLLIsearch

A lightweight, zero-dependency web app for searching CLLI sites. Type anything
into the search box and matching sites appear instantly right below it.

**Search behavior**

- **Case-insensitive** — `milw`, `MILW`, and `Milw` all match.
- **Any column** — matches across CLLI, Address, City, State, ZIP, Site Name, and GeoLoc.
- **Partial matches** — `wauk` matches `MILWAUKEE`.
- **Multi-term** — space-separated terms are AND'd together (e.g. `madison main`).
- Matching text is highlighted in the results.

## Run it

It's a static site — no build step, no server required.

- **Locally:** open `index.html` in any browser (double-click works).
- **GitHub Pages:** enable Pages on the `main` branch (root) and visit the published URL.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | The web app (UI + search logic, no dependencies). |
| `data.js` | The site data as JS constants, loaded by `index.html`. |
| `cllisites.xlsx` | Source spreadsheet (the data of record). |
| `build_data.py` | Regenerates `data.js` from the spreadsheet. |

## Updating the data

Edit `cllisites.xlsx`, then regenerate the embedded data:

```bash
pip install openpyxl
python build_data.py
```

This rewrites `data.js` from the first worksheet. The first row is treated as
column headers; every non-empty row below becomes a searchable site.
