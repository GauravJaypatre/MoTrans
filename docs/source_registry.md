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
| US | broad | S&P 500 | yfinance | `yfinance: ^GSPC` | Python API | 2000–present | — | Yahoo Finance ToS | ☐ |
| US | banks | S&P 500 Financials or KBW Bank | yfinance | `yfinance: XLF` or `^BKX` | Python API | ~2000–present | — | Yahoo Finance ToS | ☐ |
| US | smallcap | Russell 2000 | yfinance | `yfinance: ^RUT` | Python API | 2000–present | — | Yahoo Finance ToS | ☐ |
| China | broad | CSI 300 | yfinance | `yfinance: 000300.SS` | Python API | ~2005–present | pre-2005 | Yahoo Finance ToS | ☐ |
| China | banks | CSI 300 Financials / SSE Financials | yfinance / Stooq | TBD | Python API / CSV | ~2005–present | pre-2005 | TBD | ☐ |
| China | smallcap | CSI 500 or ChiNext | yfinance | `yfinance: 000905.SS` or `399006.SZ` | Python API | ~2007–present | pre-2007 | Yahoo Finance ToS | ☐ |
| Japan | broad | TOPIX or Nikkei 225 | yfinance | `yfinance: ^N225` or `^TPX` | Python API | 2000–present | — | Yahoo Finance ToS | ☐ |
| Japan | banks | TOPIX Banks | yfinance / Stooq | TBD | Python API / CSV | 2000–present | TBD | TBD | ☐ |
| Japan | smallcap | TSE Growth / Mothers | yfinance / Stooq | TBD | Python API / CSV | ~2003–present | TBD | TBD | ☐ |
| Germany | broad | DAX | yfinance | `yfinance: ^GDAXI` | Python API | 2000–present | — | Yahoo Finance ToS | ☐ |
| Germany | banks | Euro-area bank index (NOT country-specific — see note) | yfinance / Stooq | TBD | TBD | TBD | TBD | TBD | ☐ |
| Germany | smallcap | SDAX or MDAX | yfinance | `yfinance: ^SDAXI` or `^MDAXI` | Python API | 2000–present | TBD | Yahoo Finance ToS | ☐ |
| France | broad | CAC 40 | yfinance | `yfinance: ^FCHI` | Python API | 2000–present | — | Yahoo Finance ToS | ☐ |
| France | banks | French financials/banks | yfinance / Stooq | TBD | TBD | TBD | TBD | TBD | ☐ |
| France | smallcap | CAC Mid & Small | yfinance / Stooq | TBD | TBD | TBD | TBD | TBD | ☐ |
| Italy | broad | FTSE MIB | yfinance | `yfinance: FTSEMIB.MI` | Python API | 2000–present | — | Yahoo Finance ToS | ☐ |
| Italy | banks | FTSE Italia Banks | yfinance / Stooq | TBD | TBD | TBD | TBD | TBD | ☐ |
| Italy | smallcap | FTSE Italia Small Cap / STAR | yfinance / Stooq | TBD | TBD | TBD | TBD | TBD | ☐ |
| Spain | broad | IBEX 35 | yfinance | `yfinance: ^IBEX` | Python API | 2000–present | — | Yahoo Finance ToS | ☐ |
| Spain | banks | Spanish banks index | yfinance / Stooq | TBD | TBD | TBD | TBD | TBD | ☐ |
| Spain | smallcap | IBEX Small Cap | yfinance / Stooq | TBD | TBD | TBD | TBD | TBD | ☐ |
| UK | broad | FTSE 100 | yfinance | `yfinance: ^FTSE` | Python API | 2000–present | — | Yahoo Finance ToS | ☐ |
| UK | banks | FTSE 350 Banks | yfinance / Stooq | TBD | TBD | TBD | TBD | TBD | ☐ |
| UK | smallcap | FTSE 250 or FTSE SmallCap | yfinance | `yfinance: ^FTMC` | Python API | 2000–present | TBD | Yahoo Finance ToS | ☐ |
| India | broad | Nifty 50 | yfinance | `yfinance: ^NSEI` | Python API | ~2000–present | — | Yahoo Finance ToS | ☐ |
| India | banks | Nifty Bank | yfinance | `yfinance: ^NSEBANK` | Python API | ~2000–present | TBD | Yahoo Finance ToS | ☐ |
| India | smallcap | Nifty Smallcap 100 | yfinance / Stooq | TBD | TBD | ~2005–present | TBD | TBD | ☐ |
| Russia | broad | MOEX Russia | yfinance | `yfinance: IMOEX.ME` | Python API | ~2003–present | post-Feb 2022 halts | Yahoo Finance ToS | ☐ |
| Russia | banks | MOEX Financials | yfinance / Stooq | TBD | TBD | TBD | post-Feb 2022 halts | TBD | ☐ |
| Russia | smallcap | MOEX SMID | yfinance / Stooq | TBD | TBD | TBD | post-Feb 2022 halts | TBD | ☐ |
| Canada | broad | S&P/TSX Composite | yfinance | `yfinance: ^GSPTSE` | Python API | 2000–present | — | Yahoo Finance ToS | ☐ |
| Canada | banks | TSX Financials | yfinance / Stooq | TBD | TBD | TBD | TBD | TBD | ☐ |
| Canada | smallcap | TSX SmallCap | yfinance / Stooq | TBD | TBD | TBD | TBD | TBD | ☐ |
| Brazil | broad | Ibovespa | yfinance | `yfinance: ^BVSP` | Python API | 2000–present | — | Yahoo Finance ToS | ☐ |
| Brazil | banks | IFNC | yfinance / Stooq | TBD | TBD | TBD | TBD | TBD | ☐ |
| Brazil | smallcap | SMLL | yfinance / Stooq | TBD | TBD | TBD | TBD | TBD | ☐ |
| Mexico | broad | S&P/BMV IPC | yfinance | `yfinance: ^MXX` | Python API | 2000–present | — | Yahoo Finance ToS | ☐ |
| Mexico | banks | Mexican financials | TBD | TBD | TBD | TBD | TBD | TBD | ☐ |
| Mexico | smallcap | Small/mid-cap | TBD | TBD | TBD | TBD | TBD | TBD | ☐ |
| Australia | broad | S&P/ASX 200 | yfinance | `yfinance: ^AXJO` | Python API | 2000–present | — | Yahoo Finance ToS | ☐ |
| Australia | banks | ASX 200 Financials | yfinance / Stooq | TBD | TBD | TBD | TBD | TBD | ☐ |
| Australia | smallcap | Small Ordinaries | yfinance / Stooq | TBD | TBD | TBD | TBD | TBD | ☐ |
| South Korea | broad | KOSPI | yfinance | `yfinance: ^KS11` | Python API | 2000–present | — | Yahoo Finance ToS | ☐ |
| South Korea | banks | KRX Banks | yfinance / Stooq | TBD | TBD | TBD | TBD | TBD | ☐ |
| South Korea | smallcap | KOSDAQ | yfinance | `yfinance: ^KQ11` | Python API | 2000–present | — | Yahoo Finance ToS | ☐ |

> **Note on Germany banks:** The euro-area bank index is shared across DE, FR,
> IT, ES (one shock source = ECB). This is documented as a deliberate design
> choice — there is no freely available country-specific German bank index
> with sufficient history. Verify in Phase B.

---

## 2. Policy Rates and Decision Dates (12 regimes)

| Regime | Central Bank | Candidate Source | API / URL | Access Method | Coverage (est.) | Known Gaps | Licence | Verified? |
|---|---|---|---|---|---|---|---|---|
| Fed | Federal Reserve | FRED (DFEDTARU) + FOMC calendar | `FRED API` | fredapi | 2000–present | — | Public domain | ☐ |
| ECB | European Central Bank | ECB Data Portal | `ECB SDW` | REST API / CSV | 2000–present | — | ECB reuse policy | ☐ |
| PBoC | People's Bank of China | PBoC website / FRED | TBD | Web / API | ~2000–present | Pre-2005 limited | TBD | ☐ |
| BoJ | Bank of Japan | BoJ website | `boj.or.jp` | Web scrape / CSV | 2000–present | — | BoJ terms | ☐ |
| BoE | Bank of England | BoE website / FRED | `bankofengland.co.uk` | CSV download | 2000–present | — | OGL v3.0 | ☐ |
| CBR | Bank of Russia | CBR website | `cbr.ru` | Web / CSV | ~2003–present | Post-2022 disruptions | CBR terms | ☐ |
| BoC | Bank of Canada | BoC website | `bankofcanada.ca` | CSV download | 2000–present | — | BoC terms | ☐ |
| BCB | Banco Central do Brasil | BCB website / FRED | `bcb.gov.br` | API / CSV | 2000–present | — | BCB terms | ☐ |
| Banxico | Banco de México | Banxico website | `banxico.org.mx` | API / CSV | 2000–present | — | Banxico terms | ☐ |
| RBA | Reserve Bank of Australia | RBA website | `rba.gov.au` | CSV download | 2000–present | — | CC BY 4.0 | ☐ |
| BoK | Bank of Korea | BoK ECOS | `ecos.bok.or.kr` | API / CSV | 2000–present | — | BoK terms | ☐ |
| RBI | Reserve Bank of India | RBI website | `rbi.org.in` | Web / CSV | 2000–present | — | RBI terms | ☐ |

---

## 3. Monetary Policy Shocks (12 regimes)

| Regime | Shock Type | Grade | Candidate Source | API / URL | Notes | Verified? |
|---|---|---|---|---|---|---|
| Fed | Public HF surprise series | A (if found) | TBD — must find a maintained, citable series | TBD | Extend to latest FOMC if possible | ☐ |
| ECB | EA-MPD or equivalent | A (if found) | Euro Area Monetary Policy Event-Study Database | TBD | Verify public access | ☐ |
| PBoC | 1Y gov yield change (proxy) | B/C | FRED / national source | TBD | — | ☐ |
| BoJ | 1Y gov yield change (proxy) | B | FRED (Japan 1Y yield) | TBD | — | ☐ |
| BoE | 1Y gov yield change (proxy) | B | FRED / BoE | TBD | — | ☐ |
| CBR | 1Y gov yield change (proxy) | B/C | CBR / national source | TBD | Post-2022 disruptions | ☐ |
| BoC | 1Y gov yield change (proxy) | B | FRED / BoC | TBD | — | ☐ |
| BCB | 1Y gov yield change (proxy) | B | BCB / FRED | TBD | — | ☐ |
| Banxico | 1Y gov yield change (proxy) | B | Banxico / FRED | TBD | — | ☐ |
| RBA | 1Y gov yield change (proxy) | B | RBA / FRED | TBD | — | ☐ |
| BoK | 1Y gov yield change (proxy) | B | BoK / FRED | TBD | — | ☐ |
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
| BoE | MPC minutes / statements | BoE website | `bankofengland.co.uk` | English | 2000–present | ☐ |
| BoJ | Monetary policy statements | BoJ website | `boj.or.jp` | English | 2000–present | ☐ |
| RBI | Policy statements | RBI website | `rbi.org.in` | English | ~2005–present | ☐ |
| BoC | Press releases | BoC website | `bankofcanada.ca` | English | 2000–present | ☐ |
| RBA | Media releases | RBA website | `rba.gov.au` | English | 2000–present | ☐ |
| BoK | Press releases | BoK website | `bok.or.kr` | English (if available) | TBD | ☐ |
| BCB | Copom statements | BCB website | `bcb.gov.br` | English (if available) | TBD | ☐ |
| Banxico | Press releases | Banxico website | `banxico.org.mx` | English (if available) | TBD | ☐ |
| CBR | Press releases | CBR website | `cbr.ru` | English (if available) | TBD | ☐ |
| PBoC | Statements | PBoC website | `pbc.gov.cn` | English (if available) | TBD | ☐ |
| BIS | Central bankers' speeches | BIS website | `bis.org/speeches` | English | Broad coverage | ☐ |
