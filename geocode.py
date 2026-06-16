#!/usr/bin/env python3
"""Geocode CLLI site addresses to lat/lon and (re)write data.js with coordinates.

Source: US Census batch geocoder (no API key, US addresses). Addresses that
don't match exactly are retried at city level and flagged approximate. Results
are cached in coords_cache.json so re-runs don't re-hit the network.

This supersedes build_data.py: it writes the same COLUMNS/SITES plus lat, lon,
and geoApprox on each site.

Usage:
    python geocode.py
"""
import csv
import io
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request

try:
    import openpyxl
except ImportError:
    sys.exit("openpyxl required: pip install openpyxl")

SRC = "cllisites.xlsx"
OUT = "data.js"
CACHE = "coords_cache.json"
BENCHMARK = "Public_AR_Current"
BATCH_URL = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
ONELINE_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"


def load_sites():
    wb = openpyxl.load_workbook(SRC, data_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    sites = []
    for r in rows[1:]:
        if all(c is None for c in r):
            continue
        sites.append({h: ("" if v is None else str(v).strip())
                      for h, v in zip(headers, r)})
    return headers, sites


def addr_key(s):
    return ", ".join([s.get("Address", ""), s.get("City", ""),
                      s.get("State", ""), s.get("ZIP", "")])


def batch_geocode(subset):
    """subset: list of site dicts. Returns {index_in_subset: {lat, lon}}."""
    buf = io.StringIO()
    w = csv.writer(buf)
    for i, s in enumerate(subset):
        w.writerow([i, s.get("Address", ""), s.get("City", ""),
                    s.get("State", ""), s.get("ZIP", "")])
    with open("_batch.csv", "w", newline="") as f:
        f.write(buf.getvalue())

    res = subprocess.run(
        ["curl", "-s", "--form", "addressFile=@_batch.csv",
         "--form", "benchmark=" + BENCHMARK, BATCH_URL],
        capture_output=True, text=True, timeout=180,
    )
    coords = {}
    for row in csv.reader(io.StringIO(res.stdout)):
        if len(row) < 6:
            continue
        rid, status, lonlat = row[0], row[2], row[5]
        if status == "Match" and "," in lonlat:
            try:
                lon, lat = (float(x) for x in lonlat.split(","))
                coords[int(rid)] = {"lat": lat, "lon": lon, "approx": False}
            except ValueError:
                pass
    return coords


def geocode_nominatim(q):
    """OpenStreetMap fallback. Handles town/ZIP queries the Census street
    geocoder rejects. Be polite: one request/second, descriptive User-Agent."""
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 1, "countrycodes": "us"})
    req = urllib.request.Request(
        url, headers={"User-Agent": "CLLIsearch-geocoder/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            arr = json.load(r)
        if arr:
            return {"lat": float(arr[0]["lat"]),
                    "lon": float(arr[0]["lon"]), "approx": True}
    except Exception:
        return None
    return None


def main():
    headers, sites = load_sites()
    try:
        cache = json.load(open(CACHE))
    except Exception:
        cache = {}

    coords = {}
    need = []
    for i, s in enumerate(sites):
        k = addr_key(s)
        if k in cache:
            coords[i] = cache[k]
        else:
            need.append(i)

    if need:
        print(f"Batch geocoding {len(need)} addresses...")
        batch = batch_geocode([sites[i] for i in need])
        for sub, i in enumerate(need):
            if sub in batch:
                coords[i] = batch[sub]
                cache[addr_key(sites[i])] = batch[sub]

    # OpenStreetMap fallback for anything still unmatched (rural-style
    # addresses). Try the full address, then town, then ZIP — first hit wins.
    for i, s in enumerate(sites):
        if i in coords:
            continue
        queries = (
            f"{s.get('Address','')}, {s.get('City','')}, {s.get('State','')} {s.get('ZIP','')}, USA",
            f"{s.get('City','')}, {s.get('State','')}, USA",
            f"{s.get('ZIP','')}, USA",
        )
        for q in queries:
            r = geocode_nominatim(q)
            time.sleep(1)
            if r:
                coords[i] = r
                cache[addr_key(sites[i])] = r
                break

    json.dump(cache, open(CACHE, "w"), indent=2)

    matched = approx = missing = 0
    for i, s in enumerate(sites):
        c = coords.get(i)
        if c:
            s["lat"] = round(c["lat"], 6)
            s["lon"] = round(c["lon"], 6)
            s["geoApprox"] = bool(c.get("approx"))
            matched += 1
            approx += 1 if c.get("approx") else 0
        else:
            s["lat"] = s["lon"] = None
            s["geoApprox"] = False
            missing += 1

    with open(OUT, "w", newline="\n") as f:
        f.write("// Auto-generated from cllisites.xlsx by geocode.py — do not edit by hand.\n")
        f.write("// Columns: " + ", ".join(headers) + "\n")
        f.write("// Each site also has lat/lon (WGS84) and geoApprox (true = city-level fallback).\n")
        f.write("const COLUMNS = " + json.dumps(headers) + ";\n")
        f.write("const SITES = " + json.dumps(sites, indent=2) + ";\n")

    print(f"Geocoded {matched}/{len(sites)} sites "
          f"({approx} approximate, {missing} missing). Wrote {OUT}.")


if __name__ == "__main__":
    main()
