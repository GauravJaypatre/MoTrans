"""CBR Date Verification Audit against Bank of Russia Official Board Calendar.

Compares ALL CBR decision dates (2010 to 2022-02-24) with the Bank of Russia's official
Board meeting calendar saved in data/raw/timing_sources/cbr_cal_mp.html.

Outputs:
- outputs/v2/cbr_date_verification_audit.csv
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import re
from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

def run_cbr_verification():
    out_dir = ROOT / "outputs" / "v2"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    html_path = ROOT / "data" / "raw" / "timing_sources" / "cbr_cal_mp.html"
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")

    year_tabs = {
        "t9": 2022, "t1": 2021, "t2": 2020, "t3": 2019, "t4": 2018,
        "t5": 2017, "t6": 2016, "t7": 2015, "t8": 2014
    }
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
    }

    official_meetings = []
    # 2013-09-13: Key rate established at Friday Board meeting
    official_meetings.append({
        "official_date": "2013-09-13",
        "official_day": "Friday",
        "meeting_type": "Introduction of Key Rate (5.50%)"
    })

    for tab_id, year in year_tabs.items():
        container = soup.find("div", id=f"tab_content_{tab_id}")
        if not container:
            continue
        # Table rows (2014-2018 format)
        for tr in container.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) >= 2:
                m = re.search(r"(\d{1,2})\s+([A-Za-z]+)|([A-Za-z]+)\s+(\d{1,2})", tds[0].text.replace("\xa0", " "))
                if m:
                    d_str = m.group(1) or m.group(4)
                    m_str = (m.group(2) or m.group(3)).lower()
                    if m_str in months:
                        dt = pd.Timestamp(year, months[m_str], int(d_str))
                        official_meetings.append({
                            "official_date": dt.strftime("%Y-%m-%d"),
                            "official_day": dt.day_name(),
                            "meeting_type": tds[1].text.strip().replace("\xa0", " ")[:60]
                        })
        # Text strings (2019-2022 format)
        lines = [x.strip().replace("\xa0", " ") for x in container.stripped_strings]
        for i, line in enumerate(lines):
            m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)(?:\s+(\d{4}))?$", line)
            if m:
                d_str, m_str, y_str = m.group(1), m.group(2).lower(), m.group(3)
                if m_str in months:
                    y = int(y_str) if y_str else year
                    next_txt = " ".join(lines[i+1:i+3]) if i+1 < len(lines) else ""
                    if "meeting" in next_txt.lower() or "board" in next_txt.lower():
                        dt = pd.Timestamp(y, months[m_str], int(d_str))
                        official_meetings.append({
                            "official_date": dt.strftime("%Y-%m-%d"),
                            "official_day": dt.day_name(),
                            "meeting_type": next_txt[:60]
                        })

    df_off = pd.DataFrame(official_meetings).drop_duplicates(subset=["official_date"])
    df_off["dt"] = pd.to_datetime(df_off["official_date"])

    policy = pd.read_csv(ROOT / "data" / "final" / "policy_decisions.csv")
    cbr = policy[(policy["regime"] == "CBR") & (policy["decision_date"] >= "2010-01-01") & (policy["decision_date"] <= "2022-02-24")].copy()
    cbr["dt"] = pd.to_datetime(cbr["decision_date"])
    cbr["dataset_day"] = cbr["dt"].dt.day_name()
    cbr["effective"] = (cbr["shock_primary"] == 1) & (cbr["time_quality"].isin(["exact", "approximate"]))

    records = []
    for _, row in cbr.iterrows():
        cand = df_off[(df_off["dt"] <= row["dt"]) & (df_off["dt"] >= row["dt"] - pd.Timedelta(days=5))]
        if len(cand) > 0:
            c = cand.iloc[-1]
            records.append({
                "dataset_date": row["decision_date"],
                "dataset_day": row["dataset_day"],
                "decision": row["decision"],
                "size_bp": row["size_bp"],
                "new_rate_pct": row["new_rate_pct"],
                "official_meeting_date": c["official_date"],
                "official_meeting_day": c["official_day"],
                "date_changed": 1 if row["decision_date"] != c["official_date"] else 0,
                "days_lag": (row["dt"] - c["dt"]).days,
                "is_effective": 1 if row["effective"] else 0,
                "meeting_type": c["meeting_type"]
            })
        else:
            # Pre-2014 or emergency/unscheduled
            records.append({
                "dataset_date": row["decision_date"],
                "dataset_day": row["dataset_day"],
                "decision": row["decision"],
                "size_bp": row["size_bp"],
                "new_rate_pct": row["new_rate_pct"],
                "official_meeting_date": row["decision_date"],
                "official_meeting_day": row["dataset_day"],
                "date_changed": 0,
                "days_lag": 0,
                "is_effective": 1 if row["effective"] else 0,
                "meeting_type": "Refinancing Rate Era (Pre-2014) or Unscheduled"
            })

    df_cbr_audit = pd.DataFrame(records)
    out_file = out_dir / "cbr_date_verification_audit.csv"
    df_cbr_audit.to_csv(out_file, index=False)
    
    total = len(df_cbr_audit)
    mondays = (df_cbr_audit["dataset_day"] == "Monday").sum()
    fridays = (df_cbr_audit["dataset_day"] == "Friday").sum()
    changed = df_cbr_audit["date_changed"].sum()
    eff_changed = df_cbr_audit[df_cbr_audit["is_effective"] == 1]["date_changed"].sum()
    print(f"Wrote {out_file} ({total} rows).")
    print(f"Dataset days: Monday={mondays}, Friday={fridays}. Dates changing to Friday={changed} (Effective changing={eff_changed}/41).")
    return df_cbr_audit

if __name__ == "__main__":
    run_cbr_verification()
