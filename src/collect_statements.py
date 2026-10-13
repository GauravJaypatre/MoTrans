"""Phase E: English central-bank policy statements, aligned to decisions (collection only).

Coverage (DECISION-019): the four regimes whose official decision lists link each decision
to its English statement - Fed, ECB, BoJ, RBI. Other regimes are listed as gaps in
docs/statements_coverage.md (no complete meeting list, or no English list read).

  Fed  FOMC statement pages saved in Phase B (data/raw/fed_statements/)
  ECB  monetary policy statement / press conference page linked from the ECB year lists
  BoJ  statement linked from the BoJ year lists (HTML or PDF)
  RBI  policy statement / MPC resolution linked from the RBI policy archive for that date

Outputs
  data/final/statements.parquet   one row per statement: event_id, regime, decision_date,
                                  pub_ts_utc, source_url, language, retrieval_utc, text, word_count
  docs/statements_coverage.md     regime x year coverage and gaps
  docs/hand_label_sample.csv      stratified random sample (seed 2026), links only, with EMPTY label
                                  columns for the Text lead - never filled by code; the copy with
                                  full texts is data/final/hand_label_sample_with_text.csv (local)
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import logging
import re
from pathlib import Path

import bs4
import pandas as pd

from src.collect_policy import fetch
from src.download import MANIFEST_PATH, RAW_DIR

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "data" / "final"
LABELS = ["hawkish_dovish", "inflation_concern", "growth_concern", "uncertainty", "forward_guidance_shift"]
SAMPLE_SIZE = 180
SEED = 2026
ECB = "https://www.ecb.europa.eu"
BOJ = "https://www.boj.or.jp"
RBI = "https://www.rbi.org.in"
LICENCE = {"ECB": "ECB reuse policy", "BoJ": "BoJ website terms (credit the source)", "RBI": "RBI website terms"}


# --- text extraction -------------------------------------------------------------------

# Website furniture that is not part of a statement (government banners, cookie notices, menus).
BOILERPLATE = re.compile(
    r"official website of the United States Government|Official websites use \.gov|Secure \.gov websites|"
    r"cookies?|privacy (statement|policy)|Skip to main content|Search the Website|"
    r"Please enable JavaScript|Official Website of Reserve Bank of India", re.IGNORECASE)


def clean(text: str) -> str:
    lines = [ln.strip() for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln and not BOILERPLATE.search(ln))


def html_to_text(raw: bytes) -> str:
    soup = bs4.BeautifulSoup(raw.decode("utf-8", errors="replace"), "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):  # not "form": RBI wraps its body in one
        tag.decompose()
    paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    text = "\n".join(p for p in paras if len(p.split()) >= 5)
    if len(text.split()) < 80:  # pages without <p> structure (older Fed/RBI pages)
        text = soup.get_text("\n", strip=True)
    return clean(re.sub(r"[ \t]+", " ", text)).strip()


def pdf_to_text(raw: bytes) -> str:
    from pypdf import PdfReader
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    return clean("\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(raw)).pages)).strip()


def to_text(raw: bytes, url: str) -> str:
    return pdf_to_text(raw) if url.lower().endswith(".pdf") else html_to_text(raw)


def saved_by_url() -> dict[str, Path]:
    """Raw files keyed by the exact URL they were downloaded from (MANIFEST.csv)."""
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return {r["url_or_api"]: ROOT / r["file_path"] for r in csv.DictReader(f)}


SAVED: dict[str, Path] = {}


def get(url: str, regime: str, stem: str) -> tuple[bytes | None, Path]:
    """Return (content, raw path) for a statement URL, downloading it once.

    A file is reused only if it was saved from exactly this URL, so a changed link can never
    pick up another document's text. New files carry a URL fingerprint in their name.
    """
    if not SAVED:
        SAVED.update(saved_by_url())
    if url in SAVED and SAVED[url].exists():
        return SAVED[url].read_bytes(), SAVED[url]
    ext = "pdf" if url.lower().endswith(".pdf") else "html"
    name = f"statements/{regime.lower()}/{stem}_{hashlib.sha1(url.encode()).hexdigest()[:8]}.{ext}"
    raw = fetch(url, name, source={"ECB": "European Central Bank", "BoJ": "Bank of Japan",
                                   "RBI": "Reserve Bank of India"}[regime],
                series_id=f"{regime} policy statement", licence=LICENCE[regime],
                notes="Policy statement text (Phase E)", missing_ok=True)
    return raw, RAW_DIR / name


# --- statement links per regime ---------------------------------------------------------

def fed_statements(policy: pd.DataFrame) -> list[dict]:
    out = []
    for r in policy[policy.regime == "Fed"].itertuples():
        path = RAW_DIR / f"fed_statements/fed_stmt_{r.decision_date.replace('-', '')}.html"
        if path.exists():
            out.append({"regime": "Fed", "decision_date": r.decision_date, "source_url": r.source_url,
                        "raw_path": path, "text": html_to_text(path.read_bytes())})
    return out


def collect(regime: str, policy: pd.DataFrame, links: dict[str, str]) -> list[dict]:
    out = []
    for d in policy.loc[policy.regime == regime, "decision_date"]:
        if d in links:
            raw, path = get(links[d], regime, f"{regime.lower()}_{d}")
            if raw:
                out.append({"regime": regime, "decision_date": d, "source_url": links[d], "raw_path": path,
                            "text": to_text(raw, links[d])})
    return out


def ecb_statements(policy: pd.DataFrame) -> list[dict]:
    links = {}
    for page in sorted((RAW_DIR / "ecb_mps").glob("ecb_mps_*.html")):
        for dt_txt, dd in re.findall(r"<dt[^>]*>(.*?)</dt>\s*<dd>(.*?)</dd>", page.read_text("utf-8", "replace"),
                                     re.DOTALL):
            href = re.search(r'href="(/press/press_conference/[^"]+\.en\.html)"', dd)
            day = re.search(r"(\d{1,2}) (\w+) (\d{4})", re.sub(r"<[^>]+>", " ", dt_txt))
            if href and day:
                d = dt.datetime.strptime(" ".join(day.groups()), "%d %B %Y").date().isoformat()
                links.setdefault(d, ECB + href.group(1))
    return collect("ECB", policy, links)


def boj_statements(policy: pd.DataFrame) -> list[dict]:
    """One document per meeting day: the policy statement, which the BoJ files as k<yymmdd>a."""
    preferred = re.compile(r"Statement on Monetary Policy|Announcement of the Monetary Policy Meeting|"
                           r"Guideline for Money Market Operations", re.IGNORECASE)
    scored: dict[str, tuple[int, str]] = {}
    for page in sorted(RAW_DIR.glob("boj_state_*.html")):
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page.read_text("utf-8", "replace"), re.DOTALL):
            tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)
            href = re.search(r'href="([^"]+\.(?:htm|pdf))"', tr)
            if len(tds) < 2 or not href:
                continue
            day = re.search(r"([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2}),\s+(\d{4})", re.sub(r"<[^>]+>|&nbsp;", " ", tds[0]))
            if not day:
                continue
            d = dt.datetime.strptime(" ".join(day.groups()), "%b %d %Y").date().isoformat()
            url = BOJ + href.group(1) if href.group(1).startswith("/") else href.group(1)
            title = re.sub(r"<[^>]+>", " ", tds[1])
            score = 2 * bool(re.search(r"/k\d{6}a?\.(?:htm|pdf)$", url)) + bool(preferred.search(title))
            if d not in scored or score > scored[d][0]:
                scored[d] = (score, url)
    return collect("BoJ", policy, {d: url for d, (_, url) in scored.items()})


def rbi_statements(policy: pd.DataFrame) -> list[dict]:
    want = re.compile(r"Resolution of the Monetary Policy Committee|Monetary Policy Statement|Governor.s Statement|"
                      r"Policy Statement|Monetary and Credit Policy|Review of Monetary Policy|Press Release",
                      re.IGNORECASE)
    skip = re.compile(r"Transcript|Audio|Webcast|Minutes|teleconference|Macroeconomic|Recording", re.IGNORECASE)
    date_re = re.compile(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, \d{4}$")
    links: dict[str, str] = {}
    for page in sorted((RAW_DIR / "rbi_policy").glob("rbi_policy_fy*.html")):
        soup = bs4.BeautifulSoup(page.read_text("utf-8", "replace"), "html.parser")
        current = None
        for tr in soup.find_all("tr"):
            if tr.find("tr"):
                continue
            text = tr.get_text(" ", strip=True)
            if date_re.match(text):
                current = dt.datetime.strptime(re.sub(r"^(\w{3})\w*", r"\1", text), "%b %d, %Y").date().isoformat()
                continue
            # The row text carries the document title; its link may just read "Full Document".
            if current and current not in links and want.search(text) and not skip.search(text):
                for a in tr.find_all("a", href=True):
                    href = a["href"]
                    if not re.search(r"\.mp3$|youtu", href, re.IGNORECASE):
                        links[current] = href if href.startswith("http") else f"{RBI}/Scripts/{href.lstrip('/')}"
                        break
    return collect("RBI", policy, links)


# --- outputs ---------------------------------------------------------------------------------

def retrieval_times() -> dict[str, str]:
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return {r["file_path"]: r["retrieval_utc"] for r in csv.DictReader(f)}


def coverage_md(statements: pd.DataFrame, policy: pd.DataFrame) -> str:
    years = range(2000, dt.date.today().year + 1)
    lines = ["# Statement corpus coverage (Phase E)", "",
             ("Statements per regime and year (English). A blank regime row means no statements were "
             "collected; reasons in docs/issues.md (ISS-026)."), "",
             "| regime | decisions | statements | " + " | ".join(str(y)[2:] for y in years) + " |",
             "|---|---|---|" + "---|" * len(years)]
    for reg in sorted(policy.regime.unique()):
        s = statements[statements.regime == reg]
        per = s.groupby(pd.to_datetime(s.decision_date).dt.year).size() if len(s) else pd.Series(dtype=int)
        cells = " | ".join(str(per.get(y, "")) for y in years)
        lines.append(f"| {reg} | {(policy.regime == reg).sum()} | {len(s)} | {cells} |")
    lines += ["", f"Total: {len(statements)} statements, median {int(statements.word_count.median())} words.", ""]
    return "\n".join(lines)


def hand_label_sample(statements: pd.DataFrame) -> pd.DataFrame:
    """Stratified by regime x decision; proportional with a floor of 2 per non-empty cell."""
    groups = statements.groupby(["regime", "decision"])
    share = SAMPLE_SIZE / len(statements)
    picks = []
    for _, g in groups:
        n = min(len(g), max(2, round(len(g) * share)))
        picks.append(g.sample(n, random_state=SEED))
    sample = pd.concat(picks).sort_values(["regime", "decision_date"])
    cols = ["event_id", "regime", "decision_date", "decision", "source_url", "word_count", "text"]
    out = sample[cols].copy()
    for c in LABELS:
        out[c] = ""  # filled by the Text lead, never by code
    out["labelled_by"], out["notes"] = "", ""
    return out


def main() -> pd.DataFrame:
    policy = pd.read_csv(FINAL / "policy_decisions.csv", dtype={"decision_date": str})
    rows = fed_statements(policy) + ecb_statements(policy) + boj_statements(policy) + rbi_statements(policy)
    df = pd.DataFrame(rows)
    df = df[df.text.str.split().str.len() >= 40]  # drop empty or failed extractions
    retrieved = retrieval_times()
    df["retrieval_utc"] = [retrieved.get(Path(p).relative_to(ROOT).as_posix(), "") for p in df.raw_path]
    df["event_id"] = df.regime.str.lower() + "_" + df.decision_date
    meta = policy.assign(event_id=policy.regime.str.lower() + "_" + policy.decision_date)
    df = df.merge(meta[["event_id", "announce_ts_utc", "decision"]], on="event_id", how="left")
    df["pub_ts_utc"] = df.announce_ts_utc
    df["language"] = "en"
    df["word_count"] = df.text.str.split().str.len().astype("int32")
    cols = ["event_id", "regime", "decision_date", "decision", "pub_ts_utc", "source_url", "language",
            "retrieval_utc", "text", "word_count"]
    df = df[cols].drop_duplicates("event_id").sort_values(["regime", "decision_date"]).reset_index(drop=True)
    df.to_parquet(FINAL / "statements.parquet", index=False)
    (ROOT / "docs" / "statements_coverage.md").write_text(coverage_md(df, policy), encoding="utf-8")
    sample = hand_label_sample(df)
    # Texts stay out of the public repo (ECB/BoJ/RBI terms): the tracked file has links only,
    # the labelling copy with full texts lives in the git-ignored data/final/.
    sample.to_csv(FINAL / "hand_label_sample_with_text.csv", index=False)
    sample.drop(columns=["text"]).to_csv(ROOT / "docs" / "hand_label_sample.csv", index=False)
    print(df.groupby("regime").size().to_string())
    print(f"statements: {len(df)}; hand-label sample: {len(sample)} rows -> docs/hand_label_sample.csv")
    return df


if __name__ == "__main__":
    main()
