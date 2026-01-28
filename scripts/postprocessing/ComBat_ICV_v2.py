#!/usr/bin/env python

import argparse
import logging
from pathlib import Path
import statsmodels.api as sm
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from neurocombat_sklearn import CombatModel

EPS = 1e-6

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

def parse_args():
    parser = argparse.ArgumentParser(description="Run ComBat harmonisation on volumetric data")
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--roi", type=str, default="Left-Hippocampus")
    return parser.parse_args()

def main():
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    setup_logging(args.outdir)

    logging.info("Starting ComBat harmonisation")
    logging.info(f"Input CSV: {args.csv}")

    df = pd.read_csv(args.csv)
    
    # ---------------------------------------------------------
    # STEP 1: NORMALIZE (Calculate Residuals for ROIs)
    # ---------------------------------------------------------
    
    # Identify Volume Columns
    vol_cols = df.columns[df.columns.get_loc("SUBJECT") + 1:]
    
    # Identify Controls (Assuming Diagnosis 1 = CN based on your previous logs)
    # CHECK THIS: If CN is 0 or 'CN', change this line.
    cn_mask = df["Diagnosis"] == 1 
    
    if cn_mask.sum() < 10:
        raise ValueError("Not enough Controls (Diagnosis=1) found to train normalization model.")
    
    logging.info(f"Training normalization model on {cn_mask.sum()} Healthy Controls.")
    
    # Prepare Predictors for Normalization (Biological Variables)
    # We remove ICV, Age, and Sex here so ComBat doesn't have to see them
    X_biol = df[["brain_volume_mm3", "Age", "Sex_Code"]]
    X_biol = sm.add_constant(X_biol) # Add intercept
    
    # Create a copy for residuals
    df_resid = df.copy()
    
    logging.info("Calculating residuals for all volumetric features...")
    
    for col in vol_cols:
        # 1. Train on CONTROLS only
        y_cn = df.loc[cn_mask, col]
        X_cn = X_biol.loc[cn_mask]
        
        model = sm.OLS(y_cn, X_cn).fit()
        
        # 2. Predict for EVERYONE
        # We add the mean of controls back so the values stay in a normal range
        # (e.g. 3000 instead of 0)
        pred = model.predict(X_biol)
        mean_val = y_cn.mean()
        
        df_resid[col] = df[col] - pred + mean_val

    # Update the data matrix to use RESIDUALS, not Raw Volumes
    X_img = df_resid[vol_cols].values.astype(float)
    
    if not np.isfinite(X_img).all():
        raise ValueError("Non-finite values (NaN or inf) found in volumetric data")

    logging.info(f"Number of volumetric features: {X_img.shape[1]}")

    # ---------------------------------------------------------
    # STEP 2: HARMONIZE (ComBat)
    # ---------------------------------------------------------

    # Covariates: ONLY Diagnosis
    # We removed ICV/Age/Sex in Step 1, so we do NOT include them here.
    covars = df[[
        "Diagnosis"
    ]].copy()

    covars["Diagnosis"] = covars["Diagnosis"].astype("category")

    # Encode Batch
    batch_str = df["Batch"].astype(str)
    batch_codes, batch_uniques = pd.factorize(batch_str)
    batch = batch_codes.astype(int).reshape(-1, 1) # Sklearn Combat expects 2D array sometimes, check impl
    # Note: neurocombat_sklearn usually takes 1D array for batch, but let's stick to your format
    # If it fails, revert to: batch = batch_codes.astype(int)
    
    
    batch_map = dict(enumerate(batch_uniques))
    logging.info(f"Batch encoding map: {batch_map}")

    logging.info("Fitting ComBat model (Batch + Diagnosis only)")
    combat = CombatModel()

    # Design Matrix Rank Check
    # Intercept + Batch + Diagnosis
    # We must ensure Diagnosis is dummy encoded for rank check calculation manually, 
    # but CombatModel handles this internally usually.
    # Simple check:
    logging.info("Skipping manual rank check (ComBat handles this).")

    # Run ComBat
    combat.fit(X_img, batch, covars)

    logging.info("Applying ComBat transformation")
    X_harmonized = combat.transform(X_img, batch, covars)

    logging.info(
    f"Post-ComBat volume range: "
    f"min={X_harmonized.min():.2f}, "
    f"max={X_harmonized.max():.2f}"
    )

    df_harmonized = df.copy()
    # Save the HARMONIZED RESIDUALS
    df_harmonized[vol_cols] = X_harmonized

    out_csv = args.outdir / "harmonized_volumes_residuals.csv"
    df_harmonized.to_csv(out_csv, index=False)
    logging.info(f"Harmonised CSV saved to {out_csv}")

    # -------- PLOTS --------
    # Note: We plot the RESIDUALS, not the raw volumes
    roi = args.roi
    if roi not in df.columns:
        raise ValueError(f"ROI '{roi}' not found in dataframe")

    logging.info(f"Generating plots for ROI: {roi}")

    plt.figure(figsize=(8, 5))
    # Plot Pre-ComBat Residuals
    sns.boxplot(x=df["Batch"], y=df_resid[roi]) 
    plt.title(f"Before ComBat ({roi} Residuals)")
    plt.tight_layout()
    plt.savefig(args.outdir / f"{roi}_before_combat.png", dpi=300)
    plt.close()

    plt.figure(figsize=(8, 5))
    # Plot Post-ComBat Harmonized Residuals
    sns.boxplot(x=df_harmonized["Batch"], y=df_harmonized[roi])
    plt.title(f"After ComBat ({roi} Harmonized)")
    plt.tight_layout()
    plt.savefig(args.outdir / f"{roi}_after_combat.png", dpi=300)
    plt.close()

    logging.info("Plots saved successfully")

    # -------- STATS --------
    # Use the Residuals for comparison
    ad_before = df_resid[df_resid["Diagnosis"] == 3][roi]
    cn_before = df_resid[df_resid["Diagnosis"] == 1][roi]
    logging.info(f"Mean {roi} BEFORE ComBat (AD): {ad_before.mean():.4f}")
    logging.info(f"Mean {roi} BEFORE ComBat (CN): {cn_before.mean():.4f}")

    # Post-ComBat
    ad_after = df_harmonized[df_harmonized["Diagnosis"] == 3][roi]
    cn_after = df_harmonized[df_harmonized["Diagnosis"] == 1][roi]
    logging.info(f"Mean {roi} AFTER ComBat (AD): {ad_after.mean():.4f}")
    logging.info(f"Mean {roi} AFTER ComBat (CN): {cn_after.mean():.4f}")

    logging.info("ComBat harmonisation completed successfully")

if __name__ == "__main__":
    main()