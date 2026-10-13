# Source Registry — MoTrans-15

Every variable used in the dataset is listed here with its source, access
method, coverage, known gaps, and licence. All entries start as **unverified
candidates** and are marked `✅ Verified` only after the source is opened and
the series confirmed in Phase B onward.

> **Rule:** No data is downloaded until the source is verified and this table
> is updated. If a source fails or is paywalled, log it in
> [`docs/issues.md`](issues.md) and ask.

---

## 1. Equity Indices (~45 series)

3 indices per country: broad market, banks/financials, small-cap or growth.

| Country | Class | Candidate Index | Candidate Source | API / URL | Access Method | Coverage (est.) | Known Gaps | Licence / Terms | Verified? |
|---|---|---|---|---|---|---|---|---|---|
| US | broad | S&P 500 | yfinance | `^GSPC` | Python API | 2000-01-03– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| US | banks | KBW Nasdaq Bank Index | yfinance | `^BKX` (replaces XLF ETF) | Python API | 2000-01-03– | 26 zero-return days | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| US | smallcap | Russell 2000 | yfinance | `^RUT` | Python API | 2000-01-03– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| China | broad | CSI 300 | csindex.com.cn (official) | `000300` | HTTP API | 2002-01-04– | CSIndex history starts 2002 | CSI terms (no redistribution) | ✅ 2026-10-13 |
| China | banks | CSI 300 Banks | csindex.com.cn (official) | `000951` | HTTP API | 2004-12-31– | 2000-2004 missing | CSI terms | ✅ 2026-10-13 |
| China | smallcap | CSI 500 (CSI Smallcap 500) | csindex.com.cn (official) | `000905` | HTTP API | 2004-12-31– | 2000-2004 missing | CSI terms | ✅ 2026-10-13 |
| Japan | broad | Nikkei 225 | yfinance | `^N225` | Python API | 2000-01-04– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| Japan | banks | NEXT FUNDS TOPIX Banks ETF | yfinance | `1615.T` | Python API | 2008-01-04– | ETF; 267 zero-volume days; 2000-2007 missing | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| Japan | smallcap | TSE Mothers ETF | yfinance | `1563.T` | Python API | 2011-11-25– | ETF; trades away from index (e.g. Aug 2014); 2000-2011 missing | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| Germany | broad | DAX | yfinance | `^GDAXI` | Python API | 2000-01-03– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| Germany | banks | iShares EURO STOXX Banks 30-15 ETF (euro-area, not DE-specific); robustness: DAXsector Banks `^CXPBX` (2013+) | yfinance | `EXX1.DE` | Python API | 2008-01-02– | ETF; 2000-2007 missing; ex-div & stale flags | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| Germany | smallcap | MDAX (mid-cap) | yfinance | `^MDAXI` | Python API | 2000-01-03– | mid- not small-cap | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| France | broad | CAC 40 | yfinance | `^FCHI` | Python API | 2000-01-03– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| France | banks | euro-area banks ETF (shared) | yfinance | `EXX1.DE` (row de_stoxx_banks_etf) | — | 2008– | not country-specific (DECISION-015) | — | ⇄ shared |
| France | smallcap | MSCI EMU Small Cap ETF (shared, EA) | yfinance | `SXRJ.DE` (row ea_emu_smallcap_etf) | — | 2009– | not country-specific | — | ⇄ shared |
| Italy | broad | FTSE MIB | yfinance | `FTSEMIB.MI` | Python API | 2000-01-03– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| Italy | banks | euro-area banks ETF (shared) | yfinance | `EXX1.DE` | — | 2008– | not country-specific | — | ⇄ shared |
| Italy | smallcap | MSCI EMU Small Cap ETF (shared, EA) | yfinance | `SXRJ.DE` | — | 2009– | not country-specific | — | ⇄ shared |
| Spain | broad | IBEX 35 | yfinance | `^IBEX` | Python API | 2000-01-03– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| Spain | banks | euro-area banks ETF (shared) | yfinance | `EXX1.DE` | — | 2008– | not country-specific | — | ⇄ shared |
| Spain | smallcap | MSCI EMU Small Cap ETF (shared, EA) | yfinance | `SXRJ.DE` | — | 2009– | not country-specific | — | ⇄ shared |
| UK | broad | FTSE 100 | yfinance | `^FTSE` | Python API | 2000-01-04– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| UK | banks | FTSE 350 Banks | — | not available free (Yahoo/Stooq/FTSE) | — | — | **dropped** (ISS-017) | — | ✗ |
| UK | smallcap | FTSE SmallCap | yfinance | `^FTSC` | Python API | 2000-01-04– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| India | broad | NIFTY 50 | niftyindices.com (official) | POST getHistoricaldatatabletoString | HTTP API | 2000-01-03– | special Saturday/Muhurat sessions kept | NSE Indices website terms (no redistribution) | ✅ 2026-10-13 |
| India | banks | NIFTY BANK | niftyindices.com (official) | POST getHistoricaldatatabletoString | HTTP API | 2000-01-01– | early years back-calculated by index provider (base date) | NSE Indices website terms (no redistribution) | ✅ 2026-10-13 |
| India | smallcap | NIFTY Smallcap 100 | niftyindices.com (official) | POST getHistoricaldatatabletoString | HTTP API | 2004-01-01– | 2000-2003 missing (base date 2004) | NSE Indices website terms (no redistribution) | ✅ 2026-10-13 |
| Russia | broad | MOEX Russia | Moscow Exchange ISS (official) | `IMOEX` | HTTP API | 2000-01-05– | 2022 halt rows | MOEX ISS terms | ✅ 2026-10-13 |
| Russia | banks | MOEX Financials | Moscow Exchange ISS | `MOEXFN` | HTTP API | 2004-12-30– | 2000-2004 missing | MOEX ISS terms | ✅ 2026-10-13 |
| Russia | smallcap | MOEX SMID | Moscow Exchange ISS | `MCXSM` | HTTP API | 2012-12-17– | 2000-2012 missing | MOEX ISS terms | ✅ 2026-10-13 |
| Canada | broad | S&P/TSX Composite | yfinance | `^GSPTSE` | Python API | 2000-01-04– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| Canada | banks | S&P/TSX Capped Financials | yfinance | `^SPTTFS` | Python API | 2000-10-02– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| Canada | smallcap | S&P/TSX Venture Composite (growth proxy) | yfinance | `^SPCDNX` | Python API | 2001-12-10– | venture, not TSX SmallCap | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| Brazil | broad | Ibovespa | yfinance | `^BVSP` | Python API | 2000-01-03– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| Brazil | banks | IFNC (financials) | B3 index statistics (official) | `IFNC` | HTTP API | 2004-12-30– | 2000-2004 missing | B3 terms | ✅ 2026-10-13 |
| Brazil | smallcap | SMLL | B3 index statistics (official) | `SMLL` | HTTP API | 2005-08-31– | 2000-2005 missing | B3 terms | ✅ 2026-10-13 |
| Mexico | broad | S&P/BMV IPC | yfinance | `^MXX` | Python API | 2000-01-03– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| Mexico | banks | Mexican financials | — | not available free | — | — | **dropped** (ISS-017) | — | ✗ |
| Mexico | smallcap | small/mid-cap | — | not available free | — | — | **dropped** (ISS-017) | — | ✗ |
| Australia | broad | S&P/ASX 200 | yfinance | `^AXJO` | Python API | 2000-01-04– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| Australia | banks | S&P/ASX 200 Financials | yfinance | `^AXFJ` | Python API | 2013-03-06– | 2000-2012 missing | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| Australia | smallcap | S&P/ASX Small Ordinaries | yfinance | `^AXSO` | Python API | 2004-05-03– | 2000-2004 missing | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| South Korea | broad | KOSPI | yfinance | `^KS11` | Python API | 2000-01-04– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| South Korea | banks | KODEX Banks ETF | yfinance | `091170.KS` | Python API | 2007-01-29– | ETF; 2000-2006 missing | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |
| South Korea | smallcap | KOSDAQ Composite | yfinance | `^KQ11` | Python API | 2000-10-16– | none | Yahoo Finance ToS (no redistribution) | ✅ 2026-10-13 |

> **Note on Germany banks (Phase B1):** the only country-specific free series,
> DAXsector Banks, starts 2013-03-05. The euro-area bank ETF (2008+) is primary so
> the training period includes the 2008 and 2011 ECB hikes; see DECISION-009.

---

## 2. Policy Rates and Decision Dates (12 regimes)

| Regime | Central Bank | Candidate Source | API / URL | Access Method | Coverage (est.) | Known Gaps | Licence | Verified? |
|---|---|---|---|---|---|---|---|---|
| Fed | Federal Reserve | FOMC historical pages + calendars (statement links); BIS WS_CBPOL US (rate); openmarket.htm (cross-check) | `federalreserve.gov/monetarypolicy/fomchistorical{YYYY}.htm`, `fomccalendars.htm`, `stats.bis.org/api/v1/data/WS_CBPOL/D.US` | HTML + CSV API | 2000–2026 | times unknown 2011-2015 (ISS-006) | Public domain / BIS terms | ✅ 2026-10-13 |
| ECB | European Central Bank | EA-MPD (meeting dates to Oct 2023) + ECB monetary-policy-statement lists; ECB Data Portal MRR_FR, MRR_MBR, DFR, MLFR | `ecb.europa.eu/pub/pdf/annex/Dataset_EA-MPD.xlsx`, `data-api.ecb.europa.eu` | XLSX + HTML + CSV API | 2000–2026 | scheduled flag not in source (ISS-011) | ECB reuse policy | ✅ 2026-10-13 |
| PBoC | — | BIS WS_CBPOL CN (lending rate; LPR from Aug 2019; no meetings) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| BoJ | Bank of Japan | BoJ statement lists + MPM minutes (dates, meeting end times); BIS WS_CBPOL JP (rate) | `boj.or.jp/en/mopo/mpmdeci/state_{YYYY}`, `.../mpmsche_minu/minu_{YYYY}` | HTML + PDF + CSV API | 2000–2026 | no rate in QE periods (ISS-010) | BoJ terms (credit source) / BIS terms | ✅ 2026-10-13 |
| BoE | — | BIS WS_CBPOL GB (rate changes only; no meeting list) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| CBR | — | BIS WS_CBPOL RU (refinancing rate; key rate from Sep 2013) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| BoC | — | BIS WS_CBPOL CA (rate changes only) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| BCB | — | BCB Copom communiqué API (meetings) + BIS WS_CBPOL BR | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| Banxico | — | Banxico announcement list (meetings) + BIS WS_CBPOL MX (target from Jan 2008) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| RBA | — | BIS WS_CBPOL AU (rate changes only; rba.gov.au blocks automated access) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| BoK | — | BIS WS_CBPOL KR (rate changes only) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| RBI | Reserve Bank of India | RBI monetary policy archive (one page per FY); BIS WS_CBPOL IN (rate) | `rbi.org.in/Scripts/Annualpolicy.aspx` (form post), `stats.bis.org/.../D.IN` | HTML + CSV API | 2000–2026 | no release times; intermeeting dates (ISS-007/008) | RBI terms / BIS terms | ✅ 2026-10-13 |

---

## 3. Monetary Policy Shocks (12 regimes)

| Regime | Shock Type | Grade | Candidate Source | API / URL | Notes | Verified? |
|---|---|---|---|---|---|---|
| Fed | Public HF surprise series | A (if found) | TBD — must find a maintained, citable series | TBD | Extend to latest FOMC if possible | ☐ |
| ECB | EA-MPD or equivalent | A (if found) | Euro Area Monetary Policy Event-Study Database | TBD | Verify public access | ☐ |
| PBoC | — | BIS WS_CBPOL CN (lending rate; LPR from Aug 2019; no meetings) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| BoJ | 1Y gov yield change (proxy) | B | FRED (Japan 1Y yield) | TBD | — | ☐ |
| BoE | — | BIS WS_CBPOL GB (rate changes only; no meeting list) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| CBR | — | BIS WS_CBPOL RU (refinancing rate; key rate from Sep 2013) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| BoC | — | BIS WS_CBPOL CA (rate changes only) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| BCB | — | BCB Copom communiqué API (meetings) + BIS WS_CBPOL BR | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| Banxico | — | Banxico announcement list (meetings) + BIS WS_CBPOL MX (target from Jan 2008) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| RBA | — | BIS WS_CBPOL AU (rate changes only; rba.gov.au blocks automated access) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| BoK | — | BIS WS_CBPOL KR (rate changes only) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| RBI | 1Y gov yield change (proxy) | B | RBI / FRED | TBD | — | ☐ |

> **Grade definitions:** A = clean public surprise series, B = reasonable
> proxy, C = weak (descriptive use only). Written justification required for
> each grade in Phase D.

---

## 4. Controls

| Variable | Frequency | Candidate Sources | Notes | Verified? |
|---|---|---|---|---|
| 1-year government yield | Daily | FRED, national central banks, Stooq | If 1Y not available, use 2Y or short-tenor OIS/interbank rate; log and ask | ☐ |
| FX vs USD | Daily | FRED, ECB Data Portal | — | ☐ |
| Volatility (implied) | Daily | VIX (US), VSTOXX (EA), national equivalents where available | Fall back to realized vol from broad index if implied not freely available | ☐ |
| CPI | Monthly | FRED, OECD, national statistics offices | Release-date-aware lag required (no look-ahead) | ☐ |
| Growth indicator | Monthly/Quarterly | FRED, OECD (industrial production or GDP) | Release-date-aware lag required | ☐ |
| Valuation proxy (P/E or earnings yield) | Varies | yfinance, Stooq, national sources | Log gaps where not freely available | ☐ |

---

## 5. Russia Trading Halt Dates

| Variable | Source | Notes | Verified? |
|---|---|---|---|
| `halt_flag` — MOEX trading halt periods | **Must come from cited, verifiable sources** (e.g. MOEX official announcements, CBR press releases, Reuters/Bloomberg news reports with URLs) | Do NOT enter dates from memory. Each halt period must have a source URL recorded here. | ☐ |

> **Per DECISION-007:** Halt dates will be populated in Phase B/C only after
> verifying official sources. No dates are entered from memory.

---

## 6. Central-Bank Statements (Phase E)

| Regime | Statement Type | Candidate Source | API / URL | Language | Coverage (est.) | Verified? |
|---|---|---|---|---|---|---|
| Fed | FOMC statements | Federal Reserve website | `federalreserve.gov` | English | 2000–present | ☐ |
| ECB | Monetary policy decisions / press conferences | ECB website | `ecb.europa.eu` | English | 2000–present | ☐ |
| BoE | — | BIS WS_CBPOL GB (rate changes only; no meeting list) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| BoJ | Monetary policy statements | BoJ website | `boj.or.jp` | English | 2000–present | ☐ |
| RBI | Policy statements | RBI website | `rbi.org.in` | English | ~2005–present | ☐ |
| BoC | — | BIS WS_CBPOL CA (rate changes only) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| RBA | — | BIS WS_CBPOL AU (rate changes only; rba.gov.au blocks automated access) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| BoK | — | BIS WS_CBPOL KR (rate changes only) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| BCB | — | BCB Copom communiqué API (meetings) + BIS WS_CBPOL BR | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| Banxico | — | Banxico announcement list (meetings) + BIS WS_CBPOL MX (target from Jan 2008) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| CBR | — | BIS WS_CBPOL RU (refinancing rate; key rate from Sep 2013) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| PBoC | — | BIS WS_CBPOL CN (lending rate; LPR from Aug 2019; no meetings) | stats.bis.org | CSV API | 2000–2026 | holds missing unless meetings listed (ISS-019) | BIS terms | ✅ 2026-10-13 |
| BIS | Central bankers' speeches | BIS website | `bis.org/speeches` | English | Broad coverage | ☐ |
