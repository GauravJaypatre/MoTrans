# Central Bank Statement Annotation Guide — MoTrans-15

This guide provides the standardized rubric, scale definitions, and benchmark examples for human annotation of central bank monetary policy statements in the MoTrans-15 research dataset.

---

## 1. Annotation Protocol

1. **Independent Blind Coding**: Annotators must evaluate statements independently without conferring or viewing model predictions.
2. **Context Restriction**: Annotations must be based solely on the text of the official monetary policy statement published on that date. Do not incorporate retrospective knowledge or subsequent press conference Q&A.
3. **Target Sample**: The 181 English-language policy statements in `data/final/hand_label_sample_with_text.csv` (and `docs/hand_label_sample.csv`), covering the Federal Reserve, European Central Bank, Bank of Japan, and Reserve Bank of India across `train`, `crisis`, and `blind_test` splits.
4. **Output Columns**: Fill only the five numeric score columns (`hawkish_dovish`, `inflation_concern`, `growth_concern`, `uncertainty`, `forward_guidance_shift`) and annotate `labelled_by` with your assigned coder ID (e.g. `annotator_A`).

---

## 2. Coding Dimensions & Scales

### 1. `hawkish_dovish` (Overall Policy Stance)
Measures the overall net bias of the central bank's communication regarding monetary conditions, balance of risks, and policy outlook.

- **Scale**: Integer from `-2` to `+2`.
  - **`-2` (Very Dovish)**: Explicit signaling of imminent easing, cuts, substantial asset purchases, or grave economic risks requiring aggressive policy support.
  - **`-1` (Dovish)**: Cautious tone highlighting downside growth risks, subdued inflation, or accommodation bias.
  - **`0` (Neutral / Balanced)**: Risks to inflation and growth are balanced; policy stance is characterized as appropriate and steady.
  - **`+1` (Hawkish)**: Heightened vigilance over persistent price pressures, robust labor markets, or tightening bias.
  - **`+2` (Very Hawkish)**: Unconditional commitment to rapid tightening, aggressive rate hikes, quantitative tightening, or prioritizing inflation reduction over output stabilization.

**Examples**:
- *Score +2*: *"The Committee is strongly committed to returning inflation to its 2 percent objective... and anticipates that ongoing increases in the target range will be appropriate."* (Fed, May 2022)
- *Score 0*: *"The Committee judges that the risks to achieving its employment and inflation goals are moving into better balance."* (Fed, Jan 2024)
- *Score -2*: *"The coronavirus outbreak has harmed communities and disrupted economic activity... The Federal Reserve is committed to using its full range of tools to support the U.S. economy."* (Fed, Mar 2020)

---

### 2. `inflation_concern` (Perceived Price Pressures)
Measures the degree of concern expressed regarding consumer price inflation, wage pressures, commodity prices, or de-anchoring of inflation expectations.

- **Scale**: Integer from `0` to `3`.
  - **`0` (Low / Absent)**: Inflation is at or below target; disinflationary forces dominate; price risks are unmentioned or benign.
  - **`1` (Moderate)**: Inflation is near target or moving toward target as expected; transitory variations acknowledged without alarm.
  - **`2` (Elevated)**: Inflation is above target; upside risks to prices are emphasized; persistent broad-based price increases observed.
  - **`3` (Severe / High Alert)**: Inflation is unacceptable, highly elevated, or accelerating; risk of de-anchored expectations; primary macroeconomic challenge.

**Examples**:
- *Score 3*: *"Inflation remains elevated, reflecting supply and demand imbalances related to the pandemic, higher energy prices, and broader price pressures."* (Fed, Jun 2022)
- *Score 1*: *"HICP inflation is expected to remain around 2% over the projection horizon, supported by wage growth."* (ECB, Dec 2017)
- *Score 0*: *"CPI inflation has continued to decline to exceptionally low levels, well below the price stability target."* (BoJ, Oct 2014)

---

### 3. `growth_concern` (Downside Output & Labor Risks)
Measures the central bank's stated concern regarding slowing GDP growth, labor market slack, unemployment, trade headwinds, or recession risks.

- **Scale**: Integer from `0` to `3`.
  - **`0` (Low / Benign)**: Growth is robust, output is expanding at or above potential, labor markets are tight.
  - **`1` (Moderate)**: Growth is moderating to trend pace; minor sectoral softness noted without systemic worry.
  - **`2` (Elevated)**: Clear slowdown in economic activity; weakening domestic demand, rising unemployment, or significant external headwinds.
  - **`3` (Severe / Crisis)**: Severe economic contraction, acute distress in financial/labor markets, or impending recession.

**Examples**:
- *Score 3*: *"Economic activity collapsed in the second quarter... with widespread closures and sharp reductions in employment and consumer spending."* (ECB, Jun 2020)
- *Score 1*: *"Growth in economic activity has moderated from the strong pace seen earlier in the year."* (Fed, Sep 2023)
- *Score 0*: *"The economy expanded at a vigorous pace, driven by strong gains in employment, personal consumption, and business fixed investment."* (Fed, Jun 2018)

---

### 4. `uncertainty` (Perception of Economic Environment)
Measures the degree of uncertainty, opacity, and difficulty in assessing the economic outlook, geopolitical tensions, or policy impact.

- **Scale**: Integer from `0` to `3`.
  - **`0` (Low / Predictable)**: Clear outlook, high visibility, policy proceeding according to long-term projections.
  - **`1` (Moderate)**: Standard references to data dependence, balanced uncertainties, and monitoring incoming information.
  - **`2` (Elevated)**: Heightened uncertainty explicitly highlighted; conflicting economic indicators or geopolitical tensions noted.
  - **`3` (Extreme / Radical Uncertainty)**: Extraordinary uncertainty; conventional forecasting frameworks impaired; war, pandemic shocks, or financial instability.

**Examples**:
- *Score 3*: *"The invasion of Ukraine by Russia is causing enormous human and economic hardship. The implications for the U.S. economy are highly uncertain."* (Fed, Mar 2022)
- *Score 1*: *"The Committee will continue to monitor the implications of incoming information for the economic outlook."* (Fed, Dec 2015)
- *Score 0*: *"The expansion remains solid and broadly based across sectors, proceeding in line with staff baseline projections."* (ECB, Mar 2006)

---

### 5. `forward_guidance_shift` (Change in Policy Path Communication)
Measures the net directional shift in explicit or implicit forward guidance regarding future interest rate adjustments or balance sheet policy.

- **Scale**: Integer from `-2` to `+2`.
  - **`-2` (Strong Dovish Shift)**: Announcing rate cuts ahead, introducing forward guidance pegging rates low, or extending asset purchases.
  - **`-1` (Dovish Tilt)**: Softening previous tightening commitments; introducing language that policy will pause or be calibrated conservatively.
  - **`0` (Unchanged / No Shift)**: Standard forward guidance repeated verbatim or without directional change.
  - **`+1` (Hawkish Tilt)**: Removing easing bias; hinting at upcoming rate increases or balance sheet runoff.
  - **`+2` (Strong Hawkish Shift)**: Introducing explicit guidance for rapid/supersized hikes or expedited quantitative tightening.

**Examples**:
- *Score +2*: *"The Governing Council decided to increase the key ECB interest rates by 75 basis points... and expects to raise interest rates further to dampen demand."* (ECB, Sep 2022)
- *Score -1*: *"The Committee will assess the cumulative tightening of monetary policy, the lags with which policy affects economic activity, and economic developments."* (Fed, Nov 2022)
- *Score 0*: *"The Committee will maintain the target range for the federal funds rate at 5-1/4 to 5-1/2 percent and continue reducing its holdings of Treasury securities."* (Fed, May 2024)

---

## 3. Quality Control & Agreement Assessment

Inter-annotator reliability is evaluated using `src/label_agreement.py`:
- **Cohen's Kappa ($\kappa$)**: Target unweighted $\kappa \ge 0.60$; linear/quadratic weighted $\kappa \ge 0.75$.
- **Spearman Rank Correlation ($\rho$)**: Target $\rho \ge 0.70$.
- **Discrepancy Resolution**: Differences $> 1$ point must be discussed and resolved in a joint consensus review session.
