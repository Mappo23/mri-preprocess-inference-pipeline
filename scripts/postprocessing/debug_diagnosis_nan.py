#!/usr/bin/env python3

import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="Debug Diagnosis NaNs with Label fallback")
    parser.add_argument("--csv", required=True, help="Input CSV file")
    parser.add_argument("--outdir", required=True, help="Output directory")
    args = parser.parse_args()

    print("Loading CSV...")
    df = pd.read_csv(args.csv)

    # Columns of interest
    cols = ["image_id", "subject_id", "Batch", "Diagnosis"]
    # Also check fallback
    if "Diagnosis_Label" in df.columns:
        cols.append("Diagnosis_Label")

    df_small = df[cols].copy()

    print("\n===== BASIC INFO =====")
    print("Total rows:", len(df_small))
    print("Missing Diagnosis:", df_small["Diagnosis"].isna().sum())
    if "Diagnosis_Label" in df_small.columns:
        print("Missing Diagnosis_Label:", df_small["Diagnosis_Label"].isna().sum())

    print("\nUnique values for Diagnosis (including NaN):")
    print(df_small["Diagnosis"].value_counts(dropna=False))

    if "Diagnosis_Label" in df_small.columns:
        print("\nUnique values for Diagnosis_Label (including NaN):")
        print(df_small["Diagnosis_Label"].value_counts(dropna=False))

    # Extract rows where Diagnosis is missing
    df_nan = df_small[df_small["Diagnosis"].isna()].copy()
    print("\n===== Rows with missing Diagnosis =====")
    print("Rows:", len(df_nan))

    if len(df_nan) > 0:
        print("\nBatch distribution for missing Diagnosis:")
        print(df_nan["Batch"].value_counts(dropna=False))

        # See how many have fallback Diagnosis_Label available
        if "Diagnosis_Label" in df_nan.columns:
            fallback_count = df_nan["Diagnosis_Label"].notna().sum()
            print(
                "\nRows missing Diagnosis but having Diagnosis_Label:",
                fallback_count,
            )

        out_missing = f"{args.outdir}/missing_diagnosis.csv"
        df_nan.to_csv(out_missing, index=False)
        print(f"\nSaved missing Diagnosis rows to: {out_missing}")

    # Also extract rows where Diagnosis is missing but Diagnosis_Label exists
    if "Diagnosis_Label" in df_small.columns:
        df_fallback = df_small[
            df_small["Diagnosis"].isna() & df_small["Diagnosis_Label"].notna()
        ].copy()
        print("\n===== Potential Fallback Rows =====")
        print("Count:", len(df_fallback))
        out_fallback = f"{args.outdir}/fallback_diagnosis_label.csv"
        df_fallback.to_csv(out_fallback, index=False)
        print(f"Saved fallback candidates to: {out_fallback}")

    print("\nDone.")

if __name__ == "__main__":
    main()