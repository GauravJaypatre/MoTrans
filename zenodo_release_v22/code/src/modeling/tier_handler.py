"""Tier Separation and Hierarchy Protocol for MoTrans-15.

Enforces analytical discipline across shock tiers:
1. Tier 1 (high-frequency intraday OIS/MPS) and Tier 2 (daily sovereign yield proxy)
   must NEVER be pooled without an explicit shock_tier indicator and stratified reporting.
2. Secondary holds (scheduled hold decisions with yield proxies) are strictly restricted
   to labeled sensitivity analyses.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
import pandas as pd

from src.modeling.data_loader import load_modeling_data


def validate_tier_spec(
    tier: str,
    feature_cols: Optional[List[str]] = None,
    is_sensitivity: bool = False,
) -> None:
    """Validate that a model specification adheres to tier separation protocols.

    Parameters
    ----------
    tier : str
        'tier1', 'tier2', 'tier2_primary', 'pooled', or 'secondary_holds'.
    feature_cols : Optional[List[str]]
        List of explanatory variables in model.
    is_sensitivity : bool
        Flag indicating if model is an explicit sensitivity analysis.

    Raises
    ------
    ValueError
        If rules are violated.
    """
    valid_tiers = ["tier1", "tier2", "tier2_primary", "pooled", "secondary_holds"]
    if tier not in valid_tiers:
        raise ValueError(f"Unknown tier: '{tier}'. Must be one of {valid_tiers}.")

    if tier == "secondary_holds" and not is_sensitivity:
        raise ValueError(
            "Secondary holds cannot be modeled as primary evidence! "
            "They must be strictly designated with is_sensitivity=True."
        )

    if tier == "pooled":
        if feature_cols is not None:
            tier_indicators = ["shock_tier", "is_tier2", "tier_indicator", "shock_tier_2"]
            has_tier_indicator = any(ti in feature_cols for ti in tier_indicators)
            if not has_tier_indicator:
                raise ValueError(
                    "Methodological violation: Tier 1 (hf_ois) and Tier 2 (yield_proxy) "
                    "cannot be pooled into a common sample without an explicit 'shock_tier' "
                    "indicator variable in feature_cols."
                )


def prepare_tier_sample(
    tier: str = "tier1",
    split: str = "train_val",
    drop_embargo: bool = True,
    is_sensitivity: bool = False,
    pristine_only: bool = False,
    version: str = "v2_2",
) -> pd.DataFrame:
    """Load and prepare an analysis dataset enforcing tier separation.

    Parameters
    ----------
    tier : str
        'tier1', 'tier2', 'tier2_primary', 'pooled', or 'secondary_holds'.
    split : str
        Split partition.
    drop_embargo : bool
        Whether to exclude embargo-dropped rows.
    is_sensitivity : bool
        Whether this is a sensitivity run (required for secondary holds).
    pristine_only : bool
        If True, restricts to pristine decisions (read_by_prior_analysis == 0).
    version : str
        'v2_2' (default) or 'v2_1'.

    Returns
    -------
    pd.DataFrame
    """
    validate_tier_spec(tier, is_sensitivity=is_sensitivity)

    if tier in ["tier1", "tier2", "tier2_primary", "secondary_holds"]:
        table_key = "tier2_primary" if tier == "tier2" else tier
        df = load_modeling_data(
            table=table_key,
            split=split,
            drop_embargo=drop_embargo,
            pristine_only=pristine_only,
            version=version,
        )
        df["is_sensitivity"] = 1 if is_sensitivity else 0
        return df

    elif tier == "pooled":
        # Load Tier 1 and Tier 2 Primary
        df_t1 = load_modeling_data(
            table="tier1",
            split=split,
            drop_embargo=drop_embargo,
            pristine_only=pristine_only,
            version=version,
        )
        df_t2 = load_modeling_data(
            table="tier2_primary",
            split=split,
            drop_embargo=drop_embargo,
            pristine_only=pristine_only,
            version=version,
        )

        df_t1["shock_tier"] = 1
        df_t2["shock_tier"] = 2

        pooled = pd.concat([df_t1, df_t2], ignore_index=True)
        pooled["is_sensitivity"] = 1 if is_sensitivity else 0
        return pooled

    raise ValueError(f"Unsupported tier configuration: {tier}")

