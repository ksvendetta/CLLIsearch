# CLLIsearch

A lightweight, zero-dependency web app for searching CLLI sites and sorting them
by distance from you. Type anything into the search box and matching sites
appear instantly right below it.

**Search behavior**

- **Case-insensitive** — `milw`, `MILW`, and `Milw` all match.
- **Any column** — matches across CLLI, Address, City, State, ZIP, Site Name, and GeoLoc.
- **Partial matches** — `wauk` matches `MILWAUKEE`.
- **Multi-term** — space-separated terms are AND'd together (e.g. `madison main`).
- Matching text is highlighted in the results.

**Distance / location**

- Click **Use my location** (or enter a ZIP / address) and every result shows
  its distance from you, sorted **nearest-first**.
- Distance is the primary sort once a location is set; otherwise results are
  ranked by best-match column (CLLI → Address → GeoLoc → ZIP → City → State →
  Site Name).
- ⚠️ The browser's location button only works over **https** (or `localhost`) —
  that's a browser security rule, not an app limitation. On the GitHub Pages
  URL it works; on a plain `http://<lan-ip>` address it won't, so use the
  **ZIP / address** box there instead.

## Run it

It's a static site — no build step, no server required.

- **Locally:** open `index.html` in any browser (double-click works).
- **GitHub Pages:** enable Pages on the `main` branch (root) and visit the published URL.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | The web app (UI + search + distance logic, no dependencies). |
| `data.js` | Site data **with lat/lon coordinates**, loaded by `index.html`. |
| `cllisites.xlsx` | Source spreadsheet (the data of record). |
| `geocode.py` | Regenerates `data.js` from the spreadsheet and geocodes addresses. |
| `coords_cache.json` | Cached geocoding results, so re-runs are instant. |

## Updating the data

Edit `cllisites.xlsx`, then regenerate `data.js` (this also geocodes any new or
changed addresses):

```bash
pip install openpyxl
python geocode.py
```

The first worksheet row is treated as column headers; every non-empty row below
becomes a searchable site. Coordinates come from the **US Census** batch
geocoder, with an **OpenStreetMap (Nominatim)** fallback for rural-style
addresses it can't parse (those are flagged `geoApprox` and shown with a `≈`).

> Note: the **GeoLoc** column (e.g. `PB0105`) is an internal telco grid code,
> *not* latitude/longitude — distances are computed from the geocoded street
> addresses, not from GeoLoc.
