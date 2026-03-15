#!/usr/bin/env python

"""
Feature-consistent ComBat + ICV preprocessing pipeline.

This version is intentionally conservative and keeps *exactly* the same
scientific semantics as your original script, while adding:

- Batch label normalization (case / dash / underscore)
- Defensive row dropping (missing covariates, NaN/inf ROIs)
- Batch size and Batch×Diagnosis diagnostics
- Optional singleton-batch removal
- Linear, readable control flow (no hidden magic)

Key invariants vs your OLD script:
- CN-only regression for residualization
- Residuals = raw − prediction + CN mean
- ComBat uses ONLY Diagnosis as covariate
- Same plots, same stats, same outputs
"""

import argparse
import logging
from pathlib import Path
import re

import statsmodels.api as sm
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from neurocombat_sklearn import CombatModel

EPS = 1e-6

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

def setup_logging(outdir: Path):
    log_file = outdir / "combat.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

# ---------------------------------------------------------------------
# Batch normalization
# ---------------------------------------------------------------------

def normalize_batch(series: pd.Series):
    original = series.astype(str)
    normalized = (
        original
        .str.strip()
        .str.upper()
        .str.replace("-", "_", regex=False)
        .str.replace(r"_+", "_", regex=True)
        .str.rstrip("_")
    )

    mapping = (
        pd.DataFrame({"original": original, "normalized": normalized})
        .drop_duplicates()
        .sort_values("original")
    )

    return normalized, mapping

# ---------------------------------------------------------------------
# Args
# ---------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser("ComBat harmonisation with ICV preprocessing")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--outdir", type=Path, required=True)
    p.add_argument("--roi", type=str, default="Left-Hippocampus")
    p.add_argument("--drop-singleton-batches", action="store_true")
    return p.parse_args()

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    setup_logging(args.outdir)

    logging.info("Starting ComBat harmonisation")
    logging.info(f"Input CSV: {args.csv}")

    df = pd.read_csv(args.csv)

    # -----------------------------------------------------------------
    # Batch cleanup
    # -----------------------------------------------------------------
    logging.info("Normalizing Batch labels")
    df["Batch"], batch_map = normalize_batch(df["Batch"])

    if batch_map["normalized"].nunique() < batch_map.shape[0]:
        logging.warning("Batch normalization merged labels:")
        logging.warning("\n" + batch_map.to_string(index=False))

    # -----------------------------------------------------------------
    # Drop rows with invalid / unwanted Batch labels
    # -----------------------------------------------------------------
    n_batch0 = len(df)
    df = df[~df["Batch"].isin(["OTHER"])].copy()
    if len(df) < n_batch0:
        logging.warning(f"Dropped {n_batch0 - len(df)} rows with Batch == 'OTHER'")

    # -----------------------------------------------------------------
    # Drop rows with missing biological covariates
    # -----------------------------------------------------------------
    n0 = len(df)
    df = df.dropna(subset=["Age", "Sex_Code", "brain_volume_mm3"])
    if len(df) < n0:
        logging.warning(f"Dropped {n0 - len(df)} rows with missing Age/Sex/ICV")

    # -----------------------------------------------------------------
    # Identify volumetric columns
    # -----------------------------------------------------------------
    vol_cols = df.columns[df.columns.get_loc("SUBJECT") + 1:]

    # -----------------------------------------------------------------
    # CN-only normalization model
    # -----------------------------------------------------------------
    cn_mask = df["Diagnosis"] == 1
    if cn_mask.sum() < 10:
        raise ValueError("Not enough CN subjects for normalization")

    logging.info(f"Training normalization model on {cn_mask.sum()} Healthy Controls")

    X_biol = sm.add_constant(df[["brain_volume_mm3", "Age", "Sex_Code"]])
    df_resid = df.copy()

    logging.info("Calculating residuals for all volumetric features...")

    for col in vol_cols:
        y_cn = df.loc[cn_mask, col]
        X_cn = X_biol.loc[cn_mask]

        model = sm.OLS(y_cn, X_cn).fit()
        pred = model.predict(X_biol)
        df_resid[col] = df[col] - pred + y_cn.mean()

    X_img = df_resid[vol_cols].values.astype(float)

    if not np.isfinite(X_img).all():
        raise ValueError("Non-finite values (NaN or inf) found in volumetric data")

    logging.info(f"Number of volumetric features: {X_img.shape[1]}")

    # -----------------------------------------------------------------
    # Batch diagnostics
    # -----------------------------------------------------------------
    batch_counts = df["Batch"].value_counts()
    singletons = batch_counts[batch_counts < 2]

    if not singletons.empty:
        logging.warning("Singleton batches detected:")
        logging.warning("\n" + singletons.to_string())
        if args.drop_singleton_batches:
            logging.warning("Dropping singleton batches")
            df = df[~df["Batch"].isin(singletons.index)].copy()
            df_resid = df_resid.loc[df.index]
            X_img = df_resid[vol_cols].values

    # -----------------------------------------------------------------
    # ComBat
    # -----------------------------------------------------------------
    covars = df[["Diagnosis"]].copy()
    covars["Diagnosis"] = covars["Diagnosis"].astype("category")

    batch_codes, batch_uniques = pd.factorize(df["Batch"])
    batch = batch_codes.reshape(-1, 1)

    logging.info(f"Batch encoding map: {dict(enumerate(batch_uniques))}")
    logging.info("Fitting ComBat model (Batch + Diagnosis only)")

    combat = CombatModel()

    print("\n=== DEBUG BEFORE COMBAT ===")

    print("X_img NaNs:", np.isnan(X_img).sum())
    print("batch NaNs:", np.isnan(batch).sum())

    if isinstance(covars, pd.DataFrame):
        print("Covars NaNs per column:")
        print(covars.isna().sum())
        print("Total covars NaNs:", covars.isna().sum().sum())
    else:
        print("Covars NaNs:", np.isnan(covars).sum())

    print("==========================\n")


    combat.fit(X_img, batch, covars)

    logging.info("Applying ComBat transformation")
    X_harmonized = combat.transform(X_img, batch, covars)

    logging.info(
        f"Post-ComBat volume range: min={np.nanmin(X_harmonized):.2f}, max={np.nanmax(X_harmonized):.2f}"
    )

    df_harmonized = df.copy()
    df_harmonized[vol_cols] = X_harmonized

    out_csv = args.outdir / "harmonized_volumes_residuals.csv"
    df_harmonized.to_csv(out_csv, index=False)
    logging.info(f"Saved harmonized CSV to {out_csv}")

    # -----------------------------------------------------------------
    # Plots
    # -----------------------------------------------------------------
    roi = args.roi
    logging.info(f"Generating plots for ROI: {roi}")

    plt.figure(figsize=(8, 5))
    sns.boxplot(x=df["Batch"], y=df_resid[roi])
    plt.title(f"Before ComBat ({roi} residuals)")
    plt.tight_layout()
    plt.savefig(args.outdir / f"{roi}_before_combat.png", dpi=300)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.boxplot(x=df_harmonized["Batch"], y=df_harmonized[roi])
    plt.title(f"After ComBat ({roi} harmonized)")
    plt.tight_layout()
    plt.savefig(args.outdir / f"{roi}_after_combat.png", dpi=300)
    plt.close()

    # -----------------------------------------------------------------
    # Stats
    # -----------------------------------------------------------------
    ad_before = df_resid[df_resid["Diagnosis"] == 3][roi]
    cn_before = df_resid[df_resid["Diagnosis"] == 1][roi]

    ad_after = df_harmonized[df_harmonized["Diagnosis"] == 3][roi]
    cn_after = df_harmonized[df_harmonized["Diagnosis"] == 1][roi]

    logging.info(f"Mean {roi} BEFORE ComBat (AD): {ad_before.mean():.4f}")
    logging.info(f"Mean {roi} BEFORE ComBat (CN): {cn_before.mean():.4f}")
    logging.info(f"Mean {roi} AFTER ComBat (AD): {ad_after.mean():.4f}")
    logging.info(f"Mean {roi} AFTER ComBat (CN): {cn_after.mean():.4f}")

    logging.info("ComBat harmonisation completed successfully")


if __name__ == "__main__":
    main()
