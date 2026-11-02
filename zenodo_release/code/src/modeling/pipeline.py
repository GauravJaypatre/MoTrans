"""Fold-Safe Preprocessing Pipeline for MoTrans-15.

Ensures strict zero-leakage preprocessing by fitting all scalers and transformations
solely on training partitions. Attempting to fit on validation or test observations
raises a ValueError.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd


class FoldSafeScaler:
    """Standardizes numerical features strictly on training data."""

    def __init__(self, feature_cols: Optional[List[str]] = None):
        self.feature_cols = feature_cols or ["shock_raw_bp"]
        self.means_: Dict[str, float] = {}
        self.stds_: Dict[str, float] = {}
        self.is_fitted_: bool = False

    def fit(
        self,
        df: pd.DataFrame,
        is_train_mask: Optional[pd.Series] = None,
        allow_final_fit: bool = False,
    ) -> FoldSafeScaler:
        """Fit scaler parameters on training data only.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe containing features to standardize.
        is_train_mask : Optional[pd.Series]
            Boolean mask indicating training observations. If None, checks for
            'final_split' or role columns.
        allow_final_fit : bool
            If True, permits fitting on combined train+validation (2010-2023)
            specifically for the final_fit pre-test model. Test observations
            remain strictly forbidden under all circumstances.

        Raises
        ------
        ValueError
            If validation (when allow_final_fit is False) or test rows are detected.
        """
        if is_train_mask is None:
            if "final_split" in df.columns:
                test_present = (df["final_split"] == "test").any()
                if test_present:
                    raise ValueError(
                        "Data leakage detected! Fitting sample contains locked test split observations. "
                        "Test observations can never be used to fit scalers."
                    )
                val_present = (df["final_split"] == "validation").any()
                if val_present and not allow_final_fit:
                    raise ValueError(
                        "Data leakage detected! Fitting sample contains validation split observations. "
                        "Scalers must be fit strictly on training fold observations (pass allow_final_fit=True only for final_fit)."
                    )
                fit_df = df if allow_final_fit else df[df["final_split"] == "train"]
            else:
                fit_df = df
        else:
            if "final_split" in df.columns:
                active = df[is_train_mask]
                if (active["final_split"] == "test").any():
                    raise ValueError(
                        "Data leakage detected! is_train_mask includes locked test split observations."
                    )
                if (active["final_split"] == "validation").any() and not allow_final_fit:
                    raise ValueError(
                        "Data leakage detected! is_train_mask includes validation observations."
                    )
            fit_df = df[is_train_mask]

        if fit_df.empty:
            raise ValueError("Cannot fit scaler on empty training dataframe.")

        for col in self.feature_cols:
            if col not in fit_df.columns:
                raise KeyError(f"Feature column '{col}' not present in dataframe.")
            vals = fit_df[col].dropna()
            if len(vals) == 0:
                raise ValueError(f"Feature column '{col}' has zero non-null values in training set.")
            m = float(vals.mean())
            s = float(vals.std(ddof=1))
            if s == 0.0 or np.isnan(s):
                s = 1.0  # Avoid division by zero
            self.means_[col] = m
            self.stds_[col] = s

        self.is_fitted_ = True
        return self

    def transform(self, df: pd.DataFrame, suffix: str = "_fold_std") -> pd.DataFrame:
        """Transform dataframe using previously fitted parameters."""
        if not self.is_fitted_:
            raise RuntimeError("FoldSafeScaler must be fit before transforming data.")

        out = df.copy()
        for col in self.feature_cols:
            if col in out.columns:
                m = self.means_[col]
                s = self.stds_[col]
                out[f"{col}{suffix}"] = (out[col] - m) / s
        return out

    def fit_transform(
        self,
        df: pd.DataFrame,
        is_train_mask: Optional[pd.Series] = None,
        suffix: str = "_fold_std",
    ) -> pd.DataFrame:
        """Fit on training data and transform the input dataframe."""
        return self.fit(df, is_train_mask=is_train_mask).transform(df, suffix=suffix)


def standardize_by_fold(
    df_train: pd.DataFrame,
    df_eval: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
) -> tuple[pd.DataFrame, pd.DataFrame, FoldSafeScaler]:
    """Fit scaler on df_train and transform both df_train and df_eval."""
    cols = feature_cols or ["shock_raw_bp"]
    scaler = FoldSafeScaler(feature_cols=cols)
    scaler.fit(df_train)
    scaled_train = scaler.transform(df_train)
    scaled_eval = scaler.transform(df_eval)
    return scaled_train, scaled_eval, scaler

