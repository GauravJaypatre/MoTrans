# Issues Log — MoTrans-15

Track failed sources, substitutions, and open questions here.
Every issue gets an ID, date, status (open / resolved), and resolution.

The full machine-generated list for the policy table is rebuilt on every run in
`data/interim/pilot_policy_issues.txt`; the entries below summarise it.

---

## Phase B1 (2026-10-13)

### ISS-001 — First B1 collector fabricated data · resolved
The Antigravity/Gemini version of `src/collect_policy.py` hard-coded ~140 RBI decisions,
the ECB 2024-2026 meeting dates, all emergency meetings and BoJ "exact" times citing
minutes it never downloaded. Its ECB parser also missed the variable-rate-tender period
(MRO stored as minimum bid rate 2000-2008), dropping ~10 hikes. Rewritten to parse only
saved official files (DECISION-010). Old interim outputs were regenerated.

### ISS-002 — Coverage lost to substitutions · open (accepted)
| Series | Starts | Lost | Why |
|---|---|---|---|
| DE banks `EXX1.DE` (ETF) | 2008-01-02 | 2000-2007 | EURO STOXX Banks index not free (stoxx.com gated) |
| DE banks robustness `^CXPBX` | 2013-03-05 | 2000-2012 | only free country-specific bank index |
| JP banks `1615.T` (ETF) | 2008-01-04 | 2000-2007 | TOPIX Banks index gated (JPX/J-Quants) |
| JP small-cap `1563.T` (ETF) | 2011-11-25 | 2000-2011 | TSE Mothers index gated |
| IN small-cap NIFTY Smallcap 100 | 2004-01-01 | 2000-2003 | index base date |

Fix if the university provides Datastream/Bloomberg/FactSet (official indices from 2000).

### ISS-003 — ETF price quality · open (flagged in data)
- `1615.T`: 267 zero-volume days (`stale_flag`), 615 zero-return days of 4,606.
- `1563.T`: trades away from its index at times, e.g. +18%/+15%/-15% on 11-13 Aug 2014
  with consistent OHLC and heavy volume (real trades at a premium, not a data error).
- Ex-dividend days carry `exdiv_flag` (price drop is a payout).

### ISS-004 — Yahoo placeholder rows · resolved
Zero-volume rows on exchange holidays dropped: EXX1.DE 3, ^N225 1, 1615.T 21, 1563.T 21.

### ISS-005 — India special sessions · resolved (kept)
NIFTY series include ~40 observations on non-session days (Saturday special sessions
2003-2006, Diwali Muhurat trading). Official index values, so kept.

### ISS-006 — Fed release times 2011-2015 unknown · mitigated (DECISION-013), times still wanted from Phase D
Statement pages for 2011-2015 say "For immediate release" with no time. 45 Fed events
have `time_quality = unknown` (8/yr 2011-2015 plus 7 unscheduled actions in 2001,
2007, 2008). Scheduled meetings 2000-Apr 2011 use the assumed 14:15 ET (approximate).
Resolve with the announcement timestamps in the Phase D US surprise dataset.

### ISS-007 — RBI release times unknown · resolved by DECISION-013
RBI archive pages give no time. All 163 RBI events are `unknown` and get a whole-day
announcement window (IST). B2 measures from the last close before the window and flags
`timing_ambiguous` where the window straddles a session boundary.

### ISS-008 — RBI intermeeting changes dated by effective date · open (needs a person)
23 repo/bank-rate changes (mostly 2000-2010) are not on an archive policy date and are
kept as `unscheduled_rate_change` with the BIS effective date. Announcement dates must be
checked against RBI press releases. Pre-3 Apr 2001 rows use the bank rate (BIS note).

### ISS-009 — RBI off-cycle flags incomplete · open
MPC meeting schedules were found only for FY2020-21 to FY2024-25. Decisions in other
MPC-era years default to `scheduled = True` (e.g. 27 Mar 2020 is off-cycle). Verify by hand.

### ISS-010 — BoJ quantity-target periods · open → Phase D
BIS has no BoJ policy rate 12 Feb 1999 - 11 Aug 2000, 19 Mar 2001 - 9 Mar 2006 and
4 Apr 2013 - 21 Sep 2016. 137 BoJ meetings in those spans are `decision = unclassified`
(includes QE, QQE and the 29 Jan 2016 negative-rate decision). Classify from statements.

### ISS-011 — BoJ / ECB scheduled flag · open
Neither the BoJ lists nor EA-MPD mark unscheduled meetings. Known emergency meetings
currently marked scheduled: BoJ 18 Sep 2008, 29 Sep 2008, 14 Oct 2008, 30 Nov 2011,
22 May 2020 (evening or short meetings per the minutes); ECB 17 Sep 2001, 8 Oct 2008.
BoJ times are meeting end times from the minutes (`approximate`, window = end + 60 min per
DECISION-013); 3 meetings lack minutes (whole-day window).

### ISS-012 — ECB conventions · resolved
Primary rate MRO until 17 Sep 2024, DFR from 18 Sep 2024 (BIS note). Decisions that moved
only the DFR before then (e.g. 3 Dec 2015, -10 bp) are `hold` by MRO; all three rates are
stored. Six EA-MPD meetings have no press conference (August meetings 2002-2007 and
8 Oct 2008) - expected, not an error.

### ISS-013 — FRED unreachable · resolved
FRED CSV downloads timed out from this machine. Fed targets come from BIS WS_CBPOL US
(mid-point + 0.125 for the range era), cross-checked against openmarket.htm (2003+): no
disagreements.

## Phase B2 (2026-10-13)

### ISS-014 — Historical trading hours not modelled · open (low impact)
`exchange_calendars` applies today's session hours to the whole history (except changes
it tracks, e.g. Tokyo's close moving to 15:30 on 5 Nov 2024). Earlier changes in Xetra and
NSE hours are not modelled, so events within the changed hours in early years may be
mapped to the wrong session. ECB (13:45/14:15 CET) and Fed (US afternoon) releases are far
from those boundaries. The Data lead should confirm the historical hours and list affected
events.

### ISS-015 — Overlapping event windows · open → Phase C/D
Windows of up to 60 sessions overlap other events (BoJ met ~14 times a year before 2006,
the ECB twice a month in 2000-2001). `clr_20` and `clr_60` therefore mix several
decisions; Phase D/E models must control for this (clustering by date, or dropping
overlaps as robustness).

### ISS-016 — Hand-check · resolved 2026-10-13 (Phase B gate passed)
`docs/phase_b_hand_check.md` / `outputs/hand_check_10_events.csv` list 10 events × 4
broad indices. A person must verify every row against the official release and the price
history before Phase C starts (spec, Phase B gate).
Resolved: Prachi checked all 40 rows (160/160 checks Yes, no notes) in
`docs/phase_b_hand_check.xlsx`.
