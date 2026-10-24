# Phase B hand-check: 10 events x 4 broad indices

Gate before Phase C (spec, Phase B step 6): a person checks every row against the
official announcement and the price history, then fills `checked_by` / `ok` / `notes`
in `outputs/hand_check_10_events.csv` (regenerate with `python -m src.hand_check`).

How to check a row:
1. Open `source_url`: confirm the date, and the time where one is given.
2. Confirm `reacting_session_date` is the first session of that market that closes after `window_start_utc` (DECISION-013), and `baseline_date` the session before it.
3. Open `price_source`: confirm `baseline_close` and `react_close`; `clr_1` = ln(react_close / baseline_close).

## fed_2022-03-16: hike 25 bp, 14:00 America/New_York [exact]
Source: https://www.federalreserve.gov/newsevents/pressreleases/monetary20220316a.htm

| market | baseline | reacting | in session | ambiguous | baseline close | react close | clr_1 | clr_5 | ok |
|---|---|---|---|---|---|---|---|---|---|
| DE (de_dax) | 2022-03-16 | 2022-03-17 | 0 | 0 | 14,440.74 | 14,388.06 | -0.0037 | -0.0109 | ☐ |
| IN (in_nifty50) | 2022-03-16 | 2022-03-17 | 0 | 0 | 16,975.35 | 17,287.05 | 0.0182 | 0.0145 | ☐ |
| JP (jp_nikkei225) | 2022-03-16 | 2022-03-17 | 0 | 0 | 25,762.01 | 26,652.89 | 0.0340 | 0.0872 | ☐ |
| US (us_sp500) | 2022-03-15 | 2022-03-16 | 1 | 0 | 4,262.45 | 4,357.86 | 0.0221 | 0.0568 | ☐ |

## fed_2020-03-15: cut -100 bp, 17:00 America/New_York [exact]
Source: https://www.federalreserve.gov/newsevents/pressreleases/monetary20200315a.htm

| market | baseline | reacting | in session | ambiguous | baseline close | react close | clr_1 | clr_5 | ok |
|---|---|---|---|---|---|---|---|---|---|
| DE (de_dax) | 2020-03-13 | 2020-03-16 | 0 | 0 | 9,232.08 | 8,742.25 | -0.0545 | -0.0334 | ☐ |
| IN (in_nifty50) | 2020-03-13 | 2020-03-16 | 0 | 0 | 9,955.20 | 9,197.40 | -0.0792 | -0.1296 | ☐ |
| JP (jp_nikkei225) | 2020-03-13 | 2020-03-16 | 0 | 0 | 17,431.05 | 17,002.04 | -0.0249 | -0.0317 | ☐ |
| US (us_sp500) | 2020-03-13 | 2020-03-16 | 0 | 0 | 2,711.02 | 2,386.13 | -0.1277 | -0.1623 | ☐ |

## fed_2008-10-08: cut -50 bp, 07:00 America/New_York [exact]
Source: https://www.federalreserve.gov/newsevents/press/monetary/20081008a.htm

| market | baseline | reacting | in session | ambiguous | baseline close | react close | clr_1 | clr_5 | ok |
|---|---|---|---|---|---|---|---|---|---|
| DE (de_dax) | 2008-10-07 | 2008-10-08 | 1 | 0 | 5,326.63 | 5,013.62 | -0.0606 | -0.0242 | ☐ |
| IN (in_nifty50) | 2008-10-08 | 2008-10-10 | 0 | 0 | 3,513.65 | 3,279.95 | -0.0688 | -0.0721 | ☐ |
| JP (jp_nikkei225) | 2008-10-08 | 2008-10-09 | 0 | 0 | 9,203.32 | 9,157.49 | -0.0050 | -0.0844 | ☐ |
| US (us_sp500) | 2008-10-07 | 2008-10-08 | 0 | 0 | 996.23 | 984.94 | -0.0114 | 0.0018 | ☐ |

## fed_2013-06-19: hold 0 bp, time unknown (America/New_York day) [unknown]
Source: https://www.federalreserve.gov/newsevents/pressreleases/monetary20130619a.htm

| market | baseline | reacting | in session | ambiguous | baseline close | react close | clr_1 | clr_5 | ok |
|---|---|---|---|---|---|---|---|---|---|
| DE (de_dax) | 2013-06-18 | 2013-06-19 | 0 | 1 | 8,229.51 | 8,197.08 | -0.0040 | -0.0522 | ☐ |
| IN (in_nifty50) | 2013-06-18 | 2013-06-19 | 1 | 1 | 5,813.60 | 5,822.25 | 0.0015 | -0.0358 | ☐ |
| JP (jp_nikkei225) | 2013-06-18 | 2013-06-19 | 1 | 1 | 13,007.28 | 13,245.22 | 0.0181 | -0.0029 | ☐ |
| US (us_sp500) | 2013-06-18 | 2013-06-19 | 0 | 1 | 1,651.81 | 1,628.93 | -0.0140 | -0.0394 | ☐ |

## ecb_2022-07-21: hike 50 bp, 14:15 Europe/Berlin [exact]
Source: https://www.ecb.europa.eu/pub/pdf/annex/Dataset_EA-MPD.xlsx

| market | baseline | reacting | in session | ambiguous | baseline close | react close | clr_1 | clr_5 | ok |
|---|---|---|---|---|---|---|---|---|---|
| DE (de_dax) | 2022-07-20 | 2022-07-21 | 1 | 0 | 13,281.98 | 13,246.64 | -0.0027 | -0.0087 | ☐ |
| IN (in_nifty50) | 2022-07-21 | 2022-07-22 | 0 | 0 | 16,605.25 | 16,719.45 | 0.0069 | 0.0193 | ☐ |
| JP (jp_nikkei225) | 2022-07-21 | 2022-07-22 | 0 | 0 | 27,803.00 | 27,914.66 | 0.0040 | 0.0004 | ☐ |
| US (us_sp500) | 2022-07-20 | 2022-07-21 | 0 | 0 | 3,959.90 | 3,998.95 | 0.0098 | 0.0160 | ☐ |

## ecb_2011-04-07: hike 25 bp, 13:45 Europe/Berlin [exact]
Source: https://www.ecb.europa.eu/pub/pdf/annex/Dataset_EA-MPD.xlsx

| market | baseline | reacting | in session | ambiguous | baseline close | react close | clr_1 | clr_5 | ok |
|---|---|---|---|---|---|---|---|---|---|
| DE (de_dax) | 2011-04-06 | 2011-04-07 | 1 | 0 | 7,215.11 | 7,178.78 | -0.0050 | -0.0052 | ☐ |
| IN (in_nifty50) | 2011-04-07 | 2011-04-08 | 0 | 0 | 5,885.70 | 5,842.00 | -0.0075 | -0.0270 | ☐ |
| JP (jp_nikkei225) | 2011-04-07 | 2011-04-08 | 0 | 0 | 9,590.93 | 9,768.08 | 0.0183 | 0.0066 | ☐ |
| US (us_sp500) | 2011-04-06 | 2011-04-07 | 0 | 0 | 1,335.54 | 1,333.51 | -0.0015 | -0.0159 | ☐ |

## rbi_2022-05-04: hike 40 bp, time unknown (Asia/Kolkata day) [unknown]
Source: https://www.rbi.org.in/Scripts/Annualpolicy.aspx

| market | baseline | reacting | in session | ambiguous | baseline close | react close | clr_1 | clr_5 | ok |
|---|---|---|---|---|---|---|---|---|---|
| DE (de_dax) | 2022-05-03 | 2022-05-04 | 0 | 1 | 14,039.47 | 13,970.82 | -0.0049 | -0.0366 | ☐ |
| IN (in_nifty50) | 2022-05-02 | 2022-05-04 | 0 | 1 | 17,069.10 | 16,677.60 | -0.0232 | -0.0498 | ☐ |
| JP (jp_nikkei225) | 2022-05-02 | 2022-05-06 | 0 | 0 | 26,818.53 | 27,003.56 | 0.0069 | -0.0407 | ☐ |
| US (us_sp500) | 2022-05-02 | 2022-05-03 | 1 | 1 | 4,155.38 | 4,175.48 | 0.0048 | -0.0403 | ☐ |

## rbi_2019-02-07: cut -25 bp, time unknown (Asia/Kolkata day) [unknown]
Source: https://www.rbi.org.in/Scripts/Annualpolicy.aspx

| market | baseline | reacting | in session | ambiguous | baseline close | react close | clr_1 | clr_5 | ok |
|---|---|---|---|---|---|---|---|---|---|
| DE (de_dax) | 2019-02-06 | 2019-02-07 | 0 | 1 | 11,324.72 | 11,022.02 | -0.0271 | -0.0140 | ☐ |
| IN (in_nifty50) | 2019-02-06 | 2019-02-07 | 0 | 1 | 11,062.45 | 11,069.40 | 0.0006 | -0.0246 | ☐ |
| JP (jp_nikkei225) | 2019-02-06 | 2019-02-07 | 0 | 1 | 20,874.06 | 20,751.28 | -0.0059 | 0.0126 | ☐ |
| US (us_sp500) | 2019-02-05 | 2019-02-06 | 1 | 1 | 2,737.70 | 2,731.61 | -0.0022 | 0.0026 | ☐ |

## boj_2016-01-29: unclassified nan bp, 12:31 Asia/Tokyo [approximate]
Source: https://www.boj.or.jp/en/mopo/mpmdeci/mpr_2016/k160129b.pdf

| market | baseline | reacting | in session | ambiguous | baseline close | react close | clr_1 | clr_5 | ok |
|---|---|---|---|---|---|---|---|---|---|
| DE (de_dax) | 2016-01-28 | 2016-01-29 | 0 | 0 | 9,639.59 | 9,798.11 | 0.0163 | -0.0259 | ☐ |
| IN (in_nifty50) | 2016-01-28 | 2016-01-29 | 0 | 0 | 7,424.65 | 7,563.55 | 0.0185 | -0.0028 | ☐ |
| JP (jp_nikkei225) | 2016-01-28 | 2016-01-29 | 1 | 0 | 17,041.45 | 17,518.30 | 0.0276 | 0.0002 | ☐ |
| US (us_sp500) | 2016-01-28 | 2016-01-29 | 0 | 0 | 1,893.36 | 1,940.24 | 0.0245 | 0.0116 | ☐ |

## boj_2024-03-19: hike 15 bp, 12:28 Asia/Tokyo [approximate]
Source: https://www.boj.or.jp/en/mopo/mpmdeci/state_2024/k240319a.htm

| market | baseline | reacting | in session | ambiguous | baseline close | react close | clr_1 | clr_5 | ok |
|---|---|---|---|---|---|---|---|---|---|
| DE (de_dax) | 2024-03-18 | 2024-03-19 | 0 | 0 | 17,932.68 | 17,987.49 | 0.0031 | 0.0182 | ☐ |
| IN (in_nifty50) | 2024-03-18 | 2024-03-19 | 0 | 0 | 22,055.70 | 21,817.45 | -0.0109 | -0.0023 | ☐ |
| JP (jp_nikkei225) | 2024-03-18 | 2024-03-19 | 1 | 0 | 39,740.44 | 40,003.60 | 0.0066 | 0.0164 | ☐ |
| US (us_sp500) | 2024-03-18 | 2024-03-19 | 0 | 0 | 5,149.42 | 5,178.51 | 0.0056 | 0.0133 | ☐ |
