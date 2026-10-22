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
    path = RAW_DIR / "ecb_ea_mpd_dataset.xlsx"
    if not path.exists():
        import requests
        url = "https://www.ecb.europa.eu/pub/pdf/annex/Dataset_EA-MPD.xlsx"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (MoTrans-15 research)"}, timeout=120)
        resp.raise_for_status()
        save_raw_file(resp.content, "ecb_ea_mpd_dataset.xlsx",
                      source="European Central Bank", url_or_api=url,
                      series_id="EA-MPD (Altavilla et al. 2019)",
                      licence="ECB terms of use (free reuse with attribution)",
                      notes="Euro Area Monetary Policy Event-Study Database")
    raw = path.read_bytes()
    df = pd.read_excel(io.BytesIO(raw), sheet_name="Monetary Event Window")

    def _parse_eampd_date(x):
        if pd.isna(x):
            return None
        if isinstance(x, (dt.datetime, dt.date)):
            return x.date() if isinstance(x, dt.datetime) else x
        return dt.datetime.strptime(str(x).strip(), "%d/%m/%Y").date()

    df["date"] = df["date"].apply(_parse_eampd_date)
    df = df[df["date"].notna()].copy()
    return df[df["date"] >= dt.date(1999, 1, 1)][["date", "OIS_1Y"]]


PROXY_TENOR = {
    "Fed": "1Y", "ECB": "1Y", "BoJ": "1Y", "BoE": "1Y", "BoC": "2Y",
    "CBR": "1Y", "BCB": "1Y", "RBA": "2Y", "PBoC": "2Y",
}


def yield_series(controls: pd.DataFrame) -> dict[str, pd.Series]:
    y = controls[controls["variable"].isin(["yield_1y", "yield_2y"])]
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
        a = align(ev.window_start_utc, ev.window_end_utc, CAL_MARKET.get(market, market), time_quality=getattr(ev, "time_quality", None))
        proxy = proxy_change(ys.get(market), a.baseline_date, a.reacting_date)
        tenor = PROXY_TENOR.get(ev.regime, "1Y")
        hf, hf_source = np.nan, ""
        if ev.regime == "Fed" and d in fs.index and pd.notna(fs.loc[d, "MPS"]):
            hf, hf_source = float(fs.loc[d, "MPS"]) * 100, "FRBSF Bauer-Swanson MPS (bp)"
        if ev.regime == "ECB" and d in ea.index and pd.notna(ea.loc[d]):
            hf, hf_source = float(ea.loc[d]), "EA-MPD OIS 1Y, monetary event window (bp)"
        rows.append({"event_id": f"{ev.regime.lower()}_{ev.decision_date}", "regime": ev.regime,
                     "decision_date": d, "announce_ts_utc": ev.announce_ts_utc, "decision": ev.decision,
                     "size_bp": ev.size_bp, "event_type": ev.event_type, "shock_hf_raw": hf,
                     "shock_hf_source": hf_source, "shock_proxy_raw": proxy,
                     "shock_proxy_source": f"{tenor} yield change, {market} (bp)" if not np.isnan(proxy) else "",
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

    # Consistent definition: within-regime training SD scale for all regimes and events (BoJ = 1.1357 bp)
    df["shock_std"] = np.where(use_hf, df["shock_hf_std"], df["shock_proxy_std"])
    df["shock_std_legacy_sd"] = df["shock_std"]
    df["shock_std_w"] = df["shock_std"].clip(lower=-4.0, upper=4.0)

    # Peer DM benchmark scale for BoJ sensitivity analysis (ECB Bund 1Y proxy training SD = 4.4806 bp)
    train_mask = df["decision_date"] <= TRAIN_END
    peer_dm_scale = float(df[train_mask & (df["regime"] == "ECB")]["shock_proxy_raw"].std())

    # Peer-scale version in shock_std_peer_scale: rescaled for BoJ, matches shock_std for other regimes
    df["shock_std_peer_scale"] = np.where(
        df["regime"] == "BoJ",
        df["shock_proxy_raw"] / peer_dm_scale,
        df["shock_std"]
    )
    df["shock_source"] = np.where(use_hf, df["shock_hf_source"], df["shock_proxy_source"])
    df["shock_grade"] = np.select([use_hf, df["shock_proxy_std"].notna()], ["A", "B"], "C")
    df["shock_measure_type"] = np.select([use_hf, df["shock_proxy_std"].notna()], ["hf_ois", "yield_proxy"], "")
    df["shock_tier"] = pd.Series(
        np.where(
            (df["shock_grade"] == "A") & (df["shock_measure_type"] == "hf_ois"),
            1,
            np.where(
                (df["shock_grade"] == "B") & (df["shock_measure_type"] == "yield_proxy"),
                2,
                np.nan
            )
        ),
        dtype="Int64"
    )
    df["shock_usable"] = (df["shock_grade"].isin(["A", "B"]) & df["shock_std"].notna()).astype(int)
    df["shock_proxy_tenor"] = np.where(df["shock_proxy_std"].notna(), df["regime"].map(PROXY_TENOR).fillna(""), "")

    is_boj_zirp = (df["regime"] == "BoJ") & (pd.to_datetime(df["decision_date"]).dt.date <= dt.date(2024, 3, 18))
    is_boj_all = (df["regime"] == "BoJ")
    is_cbr_break = (df["regime"] == "CBR") & (pd.to_datetime(df["decision_date"]).dt.date >= dt.date(2022, 2, 24))
    is_china = (df["regime"] == "PBoC")

    # Baseline pre-registered default: shock_primary = 0 for all BoJ
    is_primary_excluded = is_boj_all | is_cbr_break | is_china
    df["shock_primary"] = ((df["shock_usable"] == 1) & (~is_primary_excluded)).astype(int)

    # Labeled sensitivity analysis: shock_primary_rescaled includes 21 post-exit BoJ events
    df["shock_primary_rescaled"] = ((df["shock_usable"] == 1) & (~(is_boj_zirp | is_cbr_break | is_china))).astype(int)

    df["shock_quality_flag"] = np.where(
        is_boj_zirp,
        "low_sensitivity_zero_lower_bound",
        np.where(
            is_cbr_break,
            "structural_break_ukraine_sanctions",
            np.where(
                is_china,
                "tenor_2y_proxy_policy_transmission",
                np.where(df["shock_grade"] == "A", "high_frequency",
                         np.where(df["shock_grade"] == "B", "sovereign_yield_proxy", "no_shock"))
            )
        )
    )

    # Overlap counting for window lengths 1, 3, 5, 20, 60 trading days
    bdate_range = pd.bdate_range("1999-12-01", "2026-12-31")
    event_dates = pd.to_datetime(df["decision_date"]).to_numpy()
    event_ids = df["event_id"].to_numpy()

    for W in (1, 3, 5, 20, 60):
        cnts = []
        for d, eid in zip(event_dates, event_ids):
            b_idx = int(np.searchsorted(bdate_range, d))
            end_b = bdate_range[min(b_idx + W - 1, len(bdate_range) - 1)]
            mask = (event_dates >= d) & (event_dates <= end_b) & (event_ids != eid)
            cnts.append(int(mask.sum()))
        df[f"overlap_count_{W}d"] = cnts
        df[f"overlap_{W}d"] = (df[f"overlap_count_{W}d"] > 0).astype(int)

    return df


def validation_md(df: pd.DataFrame) -> str:
    lines = ["# Shock validation (Phase D & Priority Group 2)", "",
             ("Grades: A = public high-frequency surprise; B = 1-year (or 2-year benchmark) yield change proxy; "
              "C = no usable shock (descriptive only). `shock_std` is in units of the training-period (to 2019) SD "
              "of its source."), "",
             "## Coverage by regime", "",
             "| regime | events | A | B | C | first shock | last shock |", "|---|---|---|---|---|---|---|"]
    for reg, g in df.groupby("regime"):
        s = g[g["shock_std"].notna()]
        lines.append(f"| {reg} | {len(g)} | {(g.shock_grade == 'A').sum()} | {(g.shock_grade == 'B').sum()} | "
                     f"{(g.shock_grade == 'C').sum()} | {s.decision_date.min() if len(s) else '-'} | "
                     f"{s.decision_date.max() if len(s) else '-'} |")

    lines += ["", "## Usable and Primary shocks by regime and split (Priority Group 2)", "",
              ("`shock_usable = 1` requires a valid non-missing standardized shock (`shock_grade` in {'A', 'B'}). "
               "`shock_primary = 1` restricts to clean shocks (excluding BoJ ZIRP/YCC, CBR post-Feb 2022, and PBoC). "
               "Regimes with fewer than 20 primary blind-test events are flagged below."), "",
              "| regime | usable train | primary train | usable crisis | primary crisis | usable blind | primary blind | total usable | total primary | primary blind status |",
              "|---|---|---|---|---|---|---|---|---|---|"]

    for reg, g in df.groupby("regime"):
        u = g[g["shock_usable"] == 1]
        p = g[g["shock_primary"] == 1]
        u_train = len(u[u["split_tag"] == "train"])
        p_train = len(p[p["split_tag"] == "train"])
        u_crisis = len(u[u["split_tag"] == "crisis"])
        p_crisis = len(p[p["split_tag"] == "crisis"])
        u_blind = len(u[u["split_tag"] == "blind_test"])
        p_blind = len(p[p["split_tag"] == "blind_test"])
        u_total = len(u)
        p_total = len(p)
        status = "**FLAGGED (< 20)**" if p_blind < 20 else "Sufficient (>= 20)"
        lines.append(f"| {reg} | {u_train} | {p_train} | {u_crisis} | {p_crisis} | {u_blind} | {p_blind} | {u_total} | {p_total} | {status} |")

    lines += ["", "## Japan zero-rate proxy review", "",
              "During 2000-2019 (ZIRP/QQE), the 1-year JGB yield was compressed near zero with minimal variance "
              "(train SD = 1.13 bp). As an artifact of standardization by the training SD, post-2022 rate movements "
              "scale to extreme values (e.g. +8.02 SD on 2024-07-31). In addition, during quantitative easing and "
              "Yield Curve Control, short yields were pinned, reducing sensitivity to policy surprises. "
              "Events during the zero-rate era carry `shock_quality_flag = 'low_sensitivity_zero_lower_bound'`.", ""]

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
    overlap_cols = [f"overlap_{w}d" for w in (1, 3, 5, 20, 60)] + [f"overlap_count_{w}d" for w in (1, 3, 5, 20, 60)]
    cols = ["event_id", "regime", "decision_date", "announce_ts_utc", "decision", "size_bp", "event_type",
            "shock_raw", "shock_std", "shock_std_peer_scale", "shock_std_legacy_sd", "shock_std_w", "shock_source",
            "shock_grade", "shock_measure_type", "shock_tier", "shock_usable", "shock_primary", "shock_primary_rescaled",
            "shock_proxy_tenor", "shock_quality_flag", "shock_hf_raw", "shock_hf_std", "shock_proxy_raw",
            "shock_proxy_std", "split_tag"] + overlap_cols
    shocks[cols].to_parquet(FINAL / "shocks.parquet", index=False)

    drop_ev_cols = ["shock_std", "shock_std_peer_scale", "shock_std_legacy_sd", "shock_std_w", "shock_source",
                    "shock_grade", "shock_measure_type", "shock_tier", "shock_usable", "shock_primary", "shock_primary_rescaled",
                    "shock_proxy_tenor", "shock_quality_flag"] + overlap_cols
    events = pd.read_parquet(FINAL / "events.parquet").drop(
        columns=drop_ev_cols,
        errors="ignore"
    )
    merge_ev_cols = ["event_id", "shock_std", "shock_std_peer_scale", "shock_std_legacy_sd", "shock_std_w",
                     "shock_source", "shock_grade", "shock_measure_type", "shock_tier", "shock_usable", "shock_primary",
                     "shock_primary_rescaled", "shock_proxy_tenor", "shock_quality_flag"] + overlap_cols
    events = events.merge(
        shocks[merge_ev_cols],
        on="event_id", how="left"
    )
    events.to_parquet(FINAL / "events.parquet", index=False)

    drop_pol_cols = ["shock_tier", "shock_usable", "shock_primary", "shock_primary_rescaled", "shock_grade",
                     "shock_measure_type", "shock_quality_flag", "analysis_ready_timing"] + overlap_cols
    policy = policy.drop(columns=drop_pol_cols, errors="ignore")
    shocks_subset = shocks[["event_id", "shock_tier", "shock_usable", "shock_primary", "shock_primary_rescaled",
                            "shock_grade", "shock_measure_type", "shock_quality_flag"] + overlap_cols].drop_duplicates()
    if "event_id" not in policy.columns:
        policy["event_id"] = policy["regime"].str.lower() + "_" + policy["decision_date"].astype(str)
    policy = policy.merge(shocks_subset, on="event_id", how="left")
    
    # Attach analysis_ready_timing to policy_decisions (1 iff exact or approximate time with resolved session)
    ev_timing = events.groupby("event_id")["analysis_ready_timing"].max().reset_index()
    policy = policy.merge(ev_timing, on="event_id", how="left")
    policy["analysis_ready_timing"] = policy["analysis_ready_timing"].fillna(0).astype(int)
    policy.to_csv(FINAL / "policy_decisions.csv", index=False)

    (ROOT / "docs" / "shock_validation.md").write_text(validation_md(shocks), encoding="utf-8")
    plots(shocks)

    # Regenerate docs/validation_report.md
    try:
        from scratch.generate_validation_report import generate_report
        generate_report()
    except Exception as e:
        print(f"Warning: validation report generation failed: {e}")

    print(shocks.groupby("regime").shock_grade.value_counts().unstack(fill_value=0).to_string())
    return shocks


if __name__ == "__main__":
    main()
