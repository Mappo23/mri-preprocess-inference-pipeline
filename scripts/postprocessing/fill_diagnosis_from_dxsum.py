#!/usr/bin/env python3

import argparse
import pandas as pd


# ADNI standard mapping
DX_MAP = {
    1: "CN",
    2: "MCI",
    3: "AD"
}


def main():
    parser = argparse.ArgumentParser(
        description="Fill missing Diagnosis and Diagnosis_Label from DXSUM with full debug"
    )
    parser.add_argument("--images_csv", required=True)
    parser.add_argument("--dxsum_csv", required=True)
    parser.add_argument("--out_csv", required=True)
    parser.add_argument("--image_date_col", default="image_date")
    parser.add_argument("--subject_col", default="subject_id")
    parser.add_argument("--max_days", type=int, default=180)
    parser.add_argument(
        "--drop_unfilled",
        action="store_true",
        help="Drop rows where Diagnosis is still missing after matching (default: OFF)"
    )
    args = parser.parse_args()

    print("Loading imaging CSV...")
    df_img = pd.read_csv(args.images_csv)

    print("Loading DXSUM CSV...")
    df_dx = pd.read_csv(args.dxsum_csv)

    df_dx = df_dx[["PTID", "EXAMDATE", "DIAGNOSIS"]].copy()

    # -----------------------
    # DATE PARSING DEBUG
    # -----------------------
    print("\nParsing dates...")

    print("Imaging date column preview BEFORE parsing:")
    print(df_img[args.image_date_col].head(5))

    df_img[args.image_date_col] = pd.to_datetime(
        df_img[args.image_date_col],
        format="%Y-%m-%d",
        errors="coerce"
    )

    print("\nImaging date column preview AFTER parsing:")
    print(df_img[args.image_date_col].head(5))

    print("NaT count in imaging date column:",
          df_img[args.image_date_col].isna().sum())

    df_dx["EXAMDATE"] = pd.to_datetime(
        df_dx["EXAMDATE"],
        format="%Y-%m-%d",
        errors="coerce"
    )

    print("NaT count in DXSUM EXAMDATE column:",
          df_dx["EXAMDATE"].isna().sum())

    # -----------------------
    # MATCHING
    # -----------------------
    filled_counter = 0
    skipped_date_counter = 0
    subject_not_found_counter = 0

    missing_mask = df_img["Diagnosis"].isna()

    print("\nMatching missing Diagnosis entries...")

    for idx, row in df_img[missing_mask].iterrows():

        ptid = row[args.subject_col]
        img_date = row[args.image_date_col]

        if pd.isna(img_date):
            skipped_date_counter += 1
            continue

        subject_dx = df_dx[df_dx["PTID"] == ptid].copy()

        if subject_dx.empty:
            subject_not_found_counter += 1
            continue

        subject_dx["date_diff"] = (
            subject_dx["EXAMDATE"] - pd.Timestamp(img_date)
        ).abs()

        closest_row = subject_dx.sort_values("date_diff").iloc[0]

        if pd.isna(closest_row["date_diff"]):
            skipped_date_counter += 1
            continue

        if closest_row["date_diff"].days <= args.max_days:

            dx_code = closest_row["DIAGNOSIS"]

            if pd.notna(dx_code):

                dx_code = int(dx_code)

                df_img.at[idx, "Diagnosis"] = dx_code

                if "Diagnosis_Label" in df_img.columns:
                    df_img.at[idx, "Diagnosis_Label"] = DX_MAP.get(
                        dx_code, "UNKNOWN"
                    )

                filled_counter += 1
            else:
                skipped_date_counter += 1
        else:
            skipped_date_counter += 1

    # -----------------------
    # OPTIONAL DROP STEP
    # -----------------------
    if args.drop_unfilled:
        before_drop = len(df_img)
        df_img = df_img[df_img["Diagnosis"].notna()].copy()
        after_drop = len(df_img)
        print("\nDropping rows with still-missing Diagnosis...")
        print("Rows removed:", before_drop - after_drop)

    # -----------------------
    # FINAL SUMMARY
    # -----------------------
    print("\n===== SUMMARY =====")
    print("Total missing Diagnosis initially:", missing_mask.sum())
    print("Filled:", filled_counter)
    print("Skipped (date too far or invalid):", skipped_date_counter)
    print("Subjects not found in DXSUM:", subject_not_found_counter)
    print("Final dataset size:", len(df_img))
    print("===================\n")

    df_img.to_csv(args.out_csv, index=False)
    print(f"Saved updated CSV to: {args.out_csv}")
    print("Done.")


if __name__ == "__main__":
    main()