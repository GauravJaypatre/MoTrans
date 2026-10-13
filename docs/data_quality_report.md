# Data quality report (Phase C)

Panel: 222,646 rows, 38 series, 16 markets, 2000-01-01 to 2026-10-12.

## Series coverage vs exchange calendars

| series | country | class | source | first | last | obs | missing sessions | outliers >10% | stale | halt rows |
|---|---|---|---|---|---|---|---|---|---|---|
| au_asx200 | AU | broad | yfinance | 2000-01-04 | 2026-10-12 | 6,763 | 14 | 1 | 0 | 0 |
| au_asx200_fin | AU | banks | yfinance | 2013-03-06 | 2026-10-12 | 3,369 | 75 | 2 | 0 | 0 |
| au_small_ords | AU | smallcap | yfinance | 2004-05-03 | 2026-10-12 | 5,679 | 4 | 0 | 0 | 0 |
| br_ibov | BR | broad | yfinance | 2000-01-03 | 2026-10-09 | 6,634 | 4 | 9 | 0 | 0 |
| br_ifnc | BR | banks | b3.com.br | 2004-12-30 | 2026-10-09 | 5,397 | 0 | 13 | 0 | 0 |
| br_smll | BR | smallcap | b3.com.br | 2005-08-31 | 2026-10-09 | 5,230 | 0 | 10 | 0 | 0 |
| ca_tsx | CA | broad | yfinance | 2000-01-04 | 2026-10-09 | 6,725 | 0 | 4 | 0 | 0 |
| ca_tsx_fin | CA | banks | yfinance | 2000-10-02 | 2026-10-09 | 6,534 | 1 | 9 | 0 | 0 |
| ca_tsx_venture | CA | smallcap | yfinance | 2001-12-10 | 2026-10-09 | 6,212 | 25 | 3 | 0 | 0 |
| cn_csi300 | CN | broad | csindex.com.cn | 2002-01-04 | 2026-10-12 | 6,006 | 0 | 0 | 0 | 0 |
| cn_csi300_banks | CN | banks | csindex.com.cn | 2004-12-31 | 2026-10-12 | 5,287 | 0 | 3 | 0 | 0 |
| cn_csi500 | CN | smallcap | csindex.com.cn | 2004-12-31 | 2026-10-12 | 5,287 | 0 | 1 | 0 | 0 |
| de_dax | DE | broad | yfinance | 2000-01-03 | 2026-10-12 | 6,800 | 4 | 4 | 0 | 0 |
| de_dax_banks | DE | banks_robustness | yfinance | 2013-03-05 | 2026-10-12 | 3,446 | 4 | 8 | 0 | 0 |
| de_mdax | DE | smallcap | yfinance | 2000-01-03 | 2026-10-12 | 6,800 | 4 | 2 | 0 | 0 |
| de_stoxx_banks_etf | DE | banks | yfinance | 2008-01-02 | 2026-10-12 | 4,765 | 4 | 13 | 257 | 0 |
| ea_emu_smallcap_etf | EA | smallcap | yfinance | 2009-11-27 | 2026-10-09 | 4,196 | 86 | 1 | 740 | 0 |
| es_ibex35 | ES | broad | yfinance | 2000-01-03 | 2026-10-12 | 6,811 | 3 | 4 | 0 | 0 |
| fr_cac40 | FR | broad | yfinance | 2000-01-03 | 2026-10-12 | 6,844 | 6 | 2 | 0 | 0 |
| gb_ftse100 | GB | broad | yfinance | 2000-01-04 | 2026-10-12 | 6,764 | 2 | 1 | 0 | 0 |
| gb_ftse_smallcap | GB | smallcap | yfinance | 2000-01-04 | 2026-10-12 | 6,684 | 82 | 1 | 0 | 0 |
| in_nifty50 | IN | broad | niftyindices.com | 2000-01-03 | 2026-10-12 | 6,658 | 1 | 4 | 0 | 0 |
| in_nifty_bank | IN | banks | niftyindices.com | 2000-01-01 | 2026-10-12 | 6,659 | 1 | 7 | 0 | 0 |
| in_nifty_smallcap100 | IN | smallcap | niftyindices.com | 2004-01-01 | 2026-10-12 | 5,655 | 1 | 5 | 0 | 0 |
| it_ftsemib | IT | broad | yfinance | 2000-01-03 | 2026-10-12 | 6,797 | 1 | 5 | 0 | 0 |
| jp_mothers_etf | JP | smallcap | yfinance | 2011-11-25 | 2026-10-09 | 3,635 | 1 | 17 | 3 | 0 |
| jp_nikkei225 | JP | broad | yfinance | 2000-01-04 | 2026-10-09 | 6,555 | 3 | 6 | 0 | 0 |
| jp_topix_banks_etf | JP | banks | yfinance | 2008-01-04 | 2026-10-09 | 4,585 | 4 | 10 | 246 | 0 |
| kr_banks_etf | KR | banks | yfinance | 2007-01-29 | 2026-10-12 | 4,278 | 579 | 3 | 1 | 0 |
| kr_kosdaq | KR | smallcap | yfinance | 2000-10-16 | 2026-10-12 | 6,402 | 7 | 10 | 0 | 0 |
| kr_kospi | KR | broad | yfinance | 2000-01-04 | 2026-10-12 | 6,591 | 8 | 8 | 0 | 0 |
| mx_ipc | MX | broad | yfinance | 2000-01-03 | 2026-10-12 | 6,722 | 24 | 1 | 0 | 0 |
| ru_imoex | RU | broad | iss.moex.com | 2000-01-05 | 2026-10-12 | 6,703 | 30 | 19 | 0 | 16 |
| ru_moex_fin | RU | banks | iss.moex.com | 2004-12-30 | 2026-10-12 | 5,453 | 18 | 20 | 0 | 18 |
| ru_moex_smid | RU | smallcap | iss.moex.com | 2012-12-17 | 2026-10-12 | 3,468 | 18 | 4 | 0 | 18 |
| us_bkx | US | banks | yfinance | 2000-01-03 | 2026-10-12 | 6,732 | 2 | 42 | 0 | 0 |
| us_rut | US | smallcap | yfinance | 2000-01-03 | 2026-10-12 | 6,734 | 0 | 4 | 0 | 0 |
| us_sp500 | US | broad | yfinance | 2000-01-03 | 2026-10-12 | 6,734 | 0 | 3 | 0 | 0 |

## Control coverage (share of observed rows with a value)

| country | fx | policy rate | 1y yield | realized vol | CPI | ind. prod. |
|---|---|---|---|---|---|---|
| AU | 100% | 100% | 0% | 100% | 100% | 0% |
| BR | 100% | 100% | 70% | 100% | 100% | 90% |
| CA | 100% | 100% | 98% | 100% | 100% | 91% |
| CN | 100% | 100% | 0% | 100% | 100% | 0% |
| DE | 100% | 100% | 100% | 100% | 100% | 89% |
| EA | 100% | 100% | 100% | 100% | 100% | 86% |
| ES | 100% | 100% | 83% | 100% | 100% | 91% |
| FR | 100% | 100% | 83% | 100% | 100% | 91% |
| GB | 100% | 100% | 100% | 100% | 100% | 91% |
| IN | 100% | 99% | 0% | 100% | 100% | 86% |
| IT | 100% | 100% | 83% | 100% | 100% | 92% |
| JP | 100% | 74% | 100% | 100% | 100% | 89% |
| KR | 100% | 100% | 0% | 100% | 100% | 90% |
| MX | 100% | 100% | 0% | 100% | 100% | 69% |
| RU | 100% | 100% | 95% | 100% | 97% | 78% |
| US | 100% | 100% | 100% | 100% | 100% | 92% |

Valuation is empty for every market (no free historical source; ISS-021).
Coverage gaps, substitutions and open questions: docs/issues.md.
