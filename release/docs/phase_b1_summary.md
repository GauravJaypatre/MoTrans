# Phase B1 pilot summary

## Equity series vs exchange calendars

`missing_days`: exchange sessions with no observation; `extra_days`: observations on non-session days; `stale_days`: ETF days with zero volume.

| series | country | class | ticker | source | first_date | last_date | obs | missing_days | extra_days | zero_return_days | stale_days | exdiv_days | outliers_gt_10pct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| de_stoxx_banks_etf | DE | banks | EXX1.DE | yfinance | 2008-01-02 | 2026-10-12 | 4765 | 4 | 0 | 47 | 257 | 39 | 13 |
| de_dax_banks | DE | banks_robustness | ^CXPBX | yfinance | 2013-03-05 | 2026-10-12 | 3446 | 4 | 0 | 7 | 0 | 0 | 8 |
| de_dax | DE | broad | ^GDAXI | yfinance | 2000-01-03 | 2026-10-12 | 6800 | 4 | 0 | 0 | 0 | 0 | 4 |
| de_mdax | DE | smallcap | ^MDAXI | yfinance | 2000-01-03 | 2026-10-12 | 6800 | 4 | 0 | 0 | 0 | 0 | 2 |
| in_nifty_bank | IN | banks | NIFTY BANK | niftyindices.com | 2000-01-01 | 2026-10-12 | 6659 | 1 | 40 | 0 | 0 | 0 | 7 |
| in_nifty50 | IN | broad | NIFTY 50 | niftyindices.com | 2000-01-03 | 2026-10-12 | 6658 | 1 | 39 | 7 | 0 | 0 | 4 |
| in_nifty_smallcap100 | IN | smallcap | NIFTY SMALLCAP 100 | niftyindices.com | 2004-01-01 | 2026-10-12 | 5655 | 1 | 35 | 1 | 0 | 0 | 5 |
| jp_topix_banks_etf | JP | banks | 1615.T | yfinance | 2008-01-04 | 2026-10-09 | 4585 | 4 | 0 | 594 | 246 | 14 | 10 |
| jp_nikkei225 | JP | broad | ^N225 | yfinance | 2000-01-04 | 2026-10-09 | 6555 | 3 | 0 | 0 | 0 | 0 | 6 |
| jp_mothers_etf | JP | smallcap | 1563.T | yfinance | 2011-11-25 | 2026-10-09 | 3635 | 1 | 0 | 92 | 3 | 8 | 17 |
| us_bkx | US | banks | ^BKX | yfinance | 2000-01-03 | 2026-10-12 | 6732 | 2 | 0 | 26 | 0 | 0 | 42 |
| us_sp500 | US | broad | ^GSPC | yfinance | 2000-01-03 | 2026-10-12 | 6734 | 0 | 0 | 3 | 0 | 0 | 3 |
| us_rut | US | smallcap | ^RUT | yfinance | 2000-01-03 | 2026-10-12 | 6734 | 0 | 0 | 5 | 0 | 0 | 4 |

## Policy decisions by regime and event type

| regime | event_type | cut | hike | hold | unclassified |
|---|---|---|---|---|---|
| BoJ | scheduled_meeting | 4 | 8 | 184 | 137 |
| ECB | scheduled_meeting | 30 | 29 | 240 | 0 |
| Fed | scheduled_meeting | 27 | 41 | 146 | 0 |
| Fed | unscheduled_meeting | 7 | 0 | 6 | 0 |
| RBI | scheduled_meeting | 22 | 26 | 85 | 0 |
| RBI | unscheduled_meeting | 1 | 2 | 4 | 0 |
| RBI | unscheduled_rate_change | 15 | 8 | 0 | 0 |

## Announcement-time quality

| regime | approximate | exact | unknown |
|---|---|---|---|
| BoJ | 330 | 0 | 3 |
| ECB | 0 | 299 | 0 |
| Fed | 90 | 92 | 45 |
| RBI | 0 | 0 | 163 |
