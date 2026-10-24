# Pre-Registered Analysis Plan Lock — MoTrans-15 v1.0

**Document**: MoTrans-15 Pre-Registration & Confirmatory Analysis Plan  
**Lock Hash (SHA-256 of docs/preregistration.md)**: `384c0d71a1debb054798272965f42f0d36f2e7c6f96461770a6291004739c040`  
**Parent Release**: `v1.0-data-freeze` (Git Commit: `1774400c972fef4105b04f2747521be4bb6805fd`)  
**Recorded Date**: 2026-10-24  

---

## 1. Confirmatory Lock Protocol

This document permanently records the hash of the pre-registered confirmatory analysis plan for MoTrans-15 v1.0 prior to unblinding or executing any exploratory time-series modeling in v2.0.

1. **Pre-Registration Integrity**: The pre-registered confirmatory test is locked under tag `v1.0-data-freeze`. Any confirmatory evaluation of hypotheses H1 (Domestic Transmission) and H2 (Cross-Border Spillovers) must strictly follow `docs/preregistration.md` (hash above).
2. **Separation of v2.0 Exploratory Forecasting**: MoTrans-15 v2.0 (`v2-2010plus` branch) is an exploratory dataset for out-of-sample time-series forecasting. Results from v2.0 cannot be reported as confirmatory evidence for the v1 blind test.
3. **Guardrail Enforcement**: In `src/model_guard.py`, access to rows tagged `split_tag == "blind_test"` in v1 tables triggers a hard `PermissionError` unless explicitly unlocked (`UNLOCK_BLIND=1`). In v2 tables, `split_tag` cannot contain `'blind_test'`, preserving complete methodological isolation.
