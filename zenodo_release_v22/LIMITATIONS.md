# MoTrans-15: Scientific Limitations & Scope Boundaries

1. **Held-Out Test Split Regime Asymmetry**:
   The held-out test split (2024-2025) coincides exclusively with a global easing and hold regime (0 policy rate hikes). Out-of-sample validity for contractionary tightening cycles is unverified.
2. **High-Frequency Identification Boundaries**:
   Official high-frequency intraday surprises for the Federal Reserve terminate on December 13, 2023. Subsequent Fed surprises rely on daily Treasury yield changes.
3. **Daily Yield Proxy Noise**:
   Daily sovereign bond yield proxies contain ~67% non-monetary background market noise ($R^2 = 0.3305$ vs intraday HFI on common decisions).
4. **Market Session Alignment**:
   Approximately 21% of decision-index pairs announce during local equity trading hours (`announce_in_session == 1`), introducing pre-announcement trading hours into standard 1-day cumulative returns. Researchers must use `clr_1_clean` for clean out-of-session reactions.
5. **Statistical Power**:
   Robust headline Minimum Detectable Effect (MDE) for the pooled specification is 119.10 bp. Clean Tier 1 MDE is 101.27 bp.
6. **Outlier Leverage Sensitivity**:
   The emergency rate hike by the Bank of Russia (`cbr_2014-12-16`, +499 bp) exerts substantial econometric leverage. All headline models must report pre-declared sensitivity checks excluding this event.
7. **Qualitative Text Labels**:
   Human qualitative statement coding requires formal double annotation and adjudication. Qualitative features are quarantined until human annotation is completed.
