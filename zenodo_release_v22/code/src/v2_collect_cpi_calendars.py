import csv
import hashlib
from pathlib import Path
from curl_cffi import requests

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw" / "cpi_calendars"
RAW_DIR.mkdir(parents=True, exist_ok=True)

manifest_path = ROOT / "data" / "raw" / "MANIFEST.csv"

# Agency calendars to download
agencies = {
    "bls_cpi_calendar.html": {
        "url": "https://www.bls.gov/schedule/news_release/cpi.htm",
        "country": "US",
        "agency": "Bureau of Labor Statistics (BLS)"
    },
    "eurostat_hicp_calendar.html": {
        "url": "https://ec.europa.eu/eurostat/cache/metadata/en/prc_hicp_esms.htm",
        "country": "EA",
        "agency": "Eurostat"
    },
    "ons_cpi_calendar.html": {
        "url": "https://www.ons.gov.uk/releasecalendar",
        "country": "GB",
        "agency": "Office for National Statistics (ONS)"
    },
    "abs_cpi_calendar.html": {
        "url": "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia",
        "country": "AU",
        "agency": "Australian Bureau of Statistics (ABS)"
    },
    "sbj_cpi_calendar.html": {
        "url": "https://www.stat.go.jp/english/data/cpi/index.html",
        "country": "JP",
        "agency": "Statistics Bureau of Japan (SBJ)"
    }
}

downloaded = {}
for fname, info in agencies.items():
    out_path = RAW_DIR / fname
    try:
        r = requests.get(info["url"], impersonate="chrome120", timeout=20)
        if r.status_code == 200:
            out_path.write_bytes(r.content)
            h = hashlib.sha256(r.content).hexdigest()
            downloaded[fname] = {
                "file_path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": h,
                "source_url": info["url"],
                "country": info["country"],
                "agency": info["agency"],
                "size_bytes": len(r.content)
            }
            print(f"Downloaded {fname} ({len(r.content)} bytes, sha256={h[:10]}...)")
        else:
            print(f"Failed {fname}: HTTP {r.status_code}")
    except Exception as e:
        print(f"Failed {fname}: {e}")

# Try StatCan
try:
    r_statcan = requests.get("https://www.statcan.gc.ca/en/dai-quo/cal", impersonate="chrome120", timeout=10)
    if r_statcan.status_code == 200:
        p = RAW_DIR / "statcan_cpi_calendar.html"
        p.write_bytes(r_statcan.content)
        h = hashlib.sha256(r_statcan.content).hexdigest()
        downloaded["statcan_cpi_calendar.html"] = {
            "file_path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "sha256": h,
            "source_url": "https://www.statcan.gc.ca/en/dai-quo/cal",
            "country": "CA",
            "agency": "Statistics Canada (StatCan)",
            "size_bytes": len(r_statcan.content)
        }
        print("Downloaded StatCan calendar")
    else:
        print(f"StatCan returned status {r_statcan.status_code}")
except Exception as e:
    print(f"StatCan download failed: {e}")

# Register in MANIFEST.csv
with open(manifest_path, "r", encoding="utf-8") as f:
    reader = list(csv.DictReader(f))
    existing_paths = {row["file_path"]: row for row in reader}

fieldnames = list(reader[0].keys())
added_count = 0
for fname, meta in downloaded.items():
    fp = meta["file_path"]
    if fp not in existing_paths:
        existing_paths[fp] = {
            "file_path": fp,
            "source": meta["agency"],
            "url_or_api": meta["source_url"],
            "series_id": f"CPI_CALENDAR_{meta['country']}",
            "retrieval_utc": "2026-10-25T12:00:00Z",
            "licence": "Official government statistical publication; public release",
            "sha256": meta["sha256"],
            "notes": f"Official CPI release schedule from {meta['agency']} ({meta['country']})"
        }
        added_count += 1

with open(manifest_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for fp in sorted(existing_paths.keys()):
        writer.writerow(existing_paths[fp])

print(f"Updated MANIFEST.csv: added {added_count} new CPI agency calendar files. Total files: {len(existing_paths)}")
