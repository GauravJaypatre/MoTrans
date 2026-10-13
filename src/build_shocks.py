"""Phase D: monetary policy shocks for every decision of the 12 regimes.

For each event the shock is taken from the best available source:
  Fed  A  FRBSF Bauer-Swanson (2023) update: MPS, 30-min futures surprise (to Dec 2023)
  ECB  A  EA-MPD (Altavilla et al. 2019): 1-year OIS change, monetary event window (to Oct 2023)
  all  B  proxy: change in the home 1-year government yield from the baseline close to the
          reacting-session close (DECISION-013 timing), in basis points
  C       no usable shock (no 1-year yield for the regime/date) -> descriptive use only

Standardisation (DECISION-018): shock_std = shock_raw / SD(shock_raw over train-period
events of the same source). The training-period SD is used so the blind test (2022+)
does not leak into the scaling; values are not de-meaned, so 0 still means "no surprise".
Both the high-frequency and the proxy shock are kept for every event (robustness), and
`shock_std` uses the high-frequency one where it exists.

Outputs: data/final/shocks.parquet, data/final/events.parquet (shock columns filled),
docs/shock_validation.md and outputs/shocks_<regime>.png.
"""

from __future__ import annotations

import datetime as dt
import io
from pathlib import Path

import numpy as np
import pandas as pd

from src import split_tag
from src.alignment import align
from src.download import RAW_DIR, save_raw_file

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "data" / "final"
INTERIM = ROOT / "data" / "interim"
FRBSF_URL = "https://www.frbsf.org/wp-content/uploads/monetary-policy-surprises-data.xlsx"
TRAIN_END = dt.date(2019, 12, 31)
# Home market whose 1-year yield proxies the regime's shock (first market for the ECB).
YIELD_MARKET = {"Fed": "US", "ECB": "EA", "RBI": "IN", "BoJ": "JP", "BoE": "GB", "PBoC": "CN", "CBR": "RU",
                "BoC": "CA", "BCB": "BR", "Banxico": "MX", "RBA": "AU", "BoK": "KR"}
CAL_MARKET = {"EA": "DE"}  # sessions for the euro-area yield: Xetra


def frbsf() -> pd.DataFrame:
    path = RAW_DIR / "shocks/frbsf_monetary_policy_surprises.xlsx"
    if not path.exists():
        import requests
        resp = requests.get(FRBSF_URL, headers={"User-Agent": "Mozilla/5.0 (MoTrans-15 research)"}, timeout=120)
        resp.raise_for_status()
        save_raw_file(resp.content, "shocks/frbsf_monetary_policy_surprises.xlsx",
                      source="Federal Reserve Bank of San Francisco", url_or_api=FRBSF_URL,
                      series_id="Bauer-Swanson MPS (FOMC update 2023 sheet)",
                      licence="FRBSF public data; cite Bauer and Swanson (2023)",
                      notes="High-frequency FOMC announcement surprises with announcement times")
    df = pd.read_excel(path, sheet_name="FOMC (update 2023)")
    df["date"] = pd.to_datetime(df["Date"]).dt.date
    return df[["date", "Time", "Unscheduled", "MPS", "MPS_ORTH"]]


def eampd() -> pd.DataFrame:
    """EA-MPD 'Monetary Event Window' (sheet 4): 1-year OIS change in bp."""
    raw = (RAW_DIR / "ecb_ea_mpd_dataset.xlsx").read_bytes()
    df = pd.read_excel(io.BytesIO(raw), sheet_name="Monetary Event Window")
    df = df[pd.to_datetime(df["date"], errors="coerce").notna()].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df[df["date"] >= dt.date(1999, 1, 1)][["date", "OIS_1Y"]]


def yield_series(controls: pd.DataFrame) -> dict[str, pd.Series]:
    y = controls[controls["variable"] == "yield_1y"]
    return {c: g.set_index("date")["value"].sort_index() for c, g in y.groupby("country")}


def proxy_change(series: pd.Series | None, baseline: dt.date | None, reacting: dt.date | None) -> float:
    """Yield change (bp) from the last value on/before baseline to the first on/after reacting."""
    if series is None or baseline is None or reacting is None:
        return np.nan
    before = series[series.index <= baseline]
    after = series[series.index >= reacting]
    if before.empty or after.empty or (after.index[0] - reacting).days > 5 or (baseline - before.index[-1]).days > 5:
        return np.nan  # stale yield data: no proxy rather than a wrong one
    return float((after.iloc[0] - before.iloc[-1]) * 100)


def build(policy: pd.DataFrame, controls: pd.DataFrame) -> pd.DataFrame:
    fs = frbsf().set_index("date")
    ea = eampd().set_index("date")["OIS_1Y"]
    ys = yield_series(controls)
    rows = []
    for ev in policy.itertuples(index=False):
        d = dt.date.fromisoformat(ev.decision_date)
        market = YIELD_MARKET[ev.regime]
        a = align(ev.window_start_utc, ev.window_end_utc, CAL_MARKET.get(market, market))
        proxy = proxy_change(ys.get(market), a.baseline_date, a.reacting_date)
        hf, hf_source = np.nan, ""
        if ev.regime == "Fed" and d in fs.index and pd.notna(fs.loc[d, "MPS"]):
            hf, hf_source = float(fs.loc[d, "MPS"]) * 100, "FRBSF Bauer-Swanson MPS (bp)"
        if ev.regime == "ECB" and d in ea.index and pd.notna(ea.loc[d]):
            hf, hf_source = float(ea.loc[d]), "EA-MPD OIS 1Y, monetary event window (bp)"
        rows.append({"event_id": f"{ev.regime.lower()}_{ev.decision_date}", "regime": ev.regime,
                     "decision_date": d, "announce_ts_utc": ev.announce_ts_utc, "decision": ev.decision,
                     "size_bp": ev.size_bp, "event_type": ev.event_type, "shock_hf_raw": hf,
                     "shock_hf_source": hf_source, "shock_proxy_raw": proxy,
                     "shock_proxy_source": f"1-year yield change, {market} (bp)" if not np.isnan(proxy) else "",
                     "split_tag": split_tag(d)})
    df = pd.DataFrame(rows)

    def scale(col: str, group: pd.Series) -> pd.Series:
        train = df["decision_date"] <= TRAIN_END
        sd = df[train].groupby(group[train])[col].std()
        return df[col] / group.map(sd)

    df["shock_hf_std"] = scale("shock_hf_raw", df["regime"])
    df["shock_proxy_std"] = scale("shock_proxy_raw", df["regime"])
    use_hf = df["shock_hf_std"].notna()
    df["shock_raw"] = np.where(use_hf, df["shock_hf_raw"], df["shock_proxy_raw"])
    df["shock_std"] = np.where(use_hf, df["shock_hf_std"], df["shock_proxy_std"])
    df["shock_source"] = np.where(use_hf, df["shock_hf_source"], df["shock_proxy_source"])
    df["shock_grade"] = np.select([use_hf, df["shock_proxy_std"].notna()], ["A", "B"], "C")
    return df


def validation_md(df: pd.DataFrame) -> str:
    lines = ["# Shock validation (Phase D)", "",
             ("Grades: A = public high-frequency surprise; B = 1-year yield change proxy; C = no usable shock "
             "(descriptive only). `shock_std` is in units of the training-period (to 2019) SD of its source."), "",
             "## Coverage by regime", "",
             "| regime | events | A | B | C | first shock | last shock |", "|---|---|---|---|---|---|---|"]
    for reg, g in df.groupby("regime"):
        s = g[g["shock_std"].notna()]
        lines.append(f"| {reg} | {len(g)} | {(g.shock_grade == 'A').sum()} | {(g.shock_grade == 'B').sum()} | "
                     f"{(g.shock_grade == 'C').sum()} | {s.decision_date.min() if len(s) else '-'} | "
                     f"{s.decision_date.max() if len(s) else '-'} |")
    lines += ["", "## High-frequency vs proxy (overlap, standardised)", "",
              "| regime | events with both | correlation |", "|---|---|---|"]
    for reg in ("Fed", "ECB"):
        g = df[(df.regime == reg) & df.shock_hf_std.notna() & df.shock_proxy_std.notna()]
        corr = g.shock_hf_std.corr(g.shock_proxy_std) if len(g) > 2 else np.nan
        lines.append(f"| {reg} | {len(g)} | {corr:.2f} |")
    lines += ["", "## Known episodes", "",
              ("Expected sign: tightening surprises positive, easing surprises negative. A hike that markets "
              "fully expected can have a near-zero shock; that is not an error."), "",
              "| event | decision | size (bp) | grade | shock_std |", "|---|---|---|---|---|"]
    episodes = ["fed_2013-06-19", "fed_2020-03-03", "fed_2020-03-15", "fed_2022-03-16", "fed_2022-06-15",
                "fed_2022-09-21", "ecb_2011-04-07", "ecb_2011-07-07", "ecb_2022-07-21", "ecb_2022-09-08",
                "boj_2024-03-19", "boe_2022-02-03", "bcb_2022-03-16", "rbi_2022-05-04"]
    for e in episodes:
        r = df[df.event_id == e]
        if len(r):
            r = r.iloc[0]
            val = f"{r.shock_std:+.2f}" if pd.notna(r.shock_std) else "-"
            lines.append(f"| {e} | {r.decision} | {r.size_bp:g} | {r.shock_grade} | {val} |")
        else:
            lines.append(f"| {e} | not in decision table | | | |")
    lines += ["", "## Largest absolute shocks (review these first)", "",
              "| event | decision | size (bp) | grade | source | shock_std |", "|---|---|---|---|---|---|"]
    top = df[df.shock_std.notna()].assign(a=df.shock_std.abs()).nlargest(15, "a")
    for r in top.itertuples():
        lines.append(f"| {r.event_id} | {r.decision} | {r.size_bp:g} | {r.shock_grade} | {r.shock_source} | "
                     f"{r.shock_std:+.2f} |")
    lines += ["", "Plots per regime: outputs/shocks_<regime>.png (regenerate with `python -m src.build_shocks`).", ""]
    return "\n".join(lines)


def plots(df: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)
    for reg, g in df[df.shock_std.notna()].groupby("regime"):
        fig, ax = plt.subplots(figsize=(10, 3))
        colors = g.shock_grade.map({"A": "#1f3864", "B": "#c55a11"})
        ax.bar(pd.to_datetime(g.decision_date), g.shock_std, width=20, color=colors)
        ax.axhline(0, color="black", lw=0.5)
        ax.set_title(f"{reg}: standardised policy shocks (blue = high-frequency, orange = 1y-yield proxy)")
        fig.tight_layout()
        fig.savefig(out / f"shocks_{reg}.png", dpi=110)
        plt.close(fig)


def main() -> pd.DataFrame:
    policy = pd.read_csv(FINAL / "policy_decisions.csv", dtype={"decision_date": str})
    controls = pd.read_parquet(INTERIM / "controls_long.parquet")
    shocks = build(policy, controls)
    cols = ["event_id", "regime", "decision_date", "announce_ts_utc", "decision", "size_bp", "event_type",
            "shock_raw", "shock_std", "shock_source", "shock_grade", "shock_hf_raw", "shock_hf_std",
            "shock_proxy_raw", "shock_proxy_std", "split_tag"]
    shocks[cols].to_parquet(FINAL / "shocks.parquet", index=False)

    events = pd.read_parquet(FINAL / "events.parquet").drop(columns=["shock_std", "shock_grade"], errors="ignore")
    events = events.merge(shocks[["event_id", "shock_std", "shock_grade"]], on="event_id", how="left")
    events.to_parquet(FINAL / "events.parquet", index=False)

    (ROOT / "docs" / "shock_validation.md").write_text(validation_md(shocks), encoding="utf-8")
    plots(shocks)
    print(shocks.groupby("regime").shock_grade.value_counts().unstack(fill_value=0).to_string())
    return shocks


if __name__ == "__main__":
    main()
