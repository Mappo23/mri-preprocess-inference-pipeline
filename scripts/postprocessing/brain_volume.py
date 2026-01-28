#!/usr/bin/env python3

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import nibabel as nib
from tqdm import tqdm


def compute_brain_volume(mask_path: Path) -> float:
    """
    Compute full brain volume from a binary brain mask.
    Returns volume in mm^3.
    """
    img = nib.load(mask_path)
    data = img.get_fdata()

    voxel_volume = np.prod(img.header.get_zooms())  # mm^3
    brain_voxels = np.count_nonzero(data > 0)

    return brain_voxels * voxel_volume


def main(args):
    csv_path = Path(args.csv)
    derivatives_root = Path(args.derivatives_root)
    output_csv = Path(args.output)

    print(f"Reading CSV: {csv_path}")
    df = pd.read_csv(csv_path)

    required_cols = {"SUBJECT", "image_id"}
    if not required_cols.issubset(df.columns):
        raise ValueError(
            f"CSV must contain columns {required_cols}, "
            f"found: {set(df.columns)}"
        )

    volumes = []

    print("Computing full brain volumes...")
    for _, row in tqdm(df.iterrows(), total=len(df)):

        image_id = f"I{int(row['image_id'])}"

        mask_path = (
            derivatives_root
            / str(row["subject_id"])
            / image_id
            / "preproc"
            / "T1w_1mm_brain_mask.nii.gz"
        )

        if mask_path.exists():
            try:
                vol = compute_brain_volume(mask_path)
            except Exception as e:
                print(f"[WARNING] Failed to read {mask_path}: {e}")
                vol = np.nan
        else:
            print(f"[WARNING] Missing mask: {mask_path}")
            vol = np.nan

        volumes.append(vol)

    df["brain_volume_mm3"] = volumes

    print(f"Writing output CSV: {output_csv}")
    df.to_csv(output_csv, index=False)

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add full brain volume from brain mask to ADNI covariates CSV"
    )
    parser.add_argument(
        "--csv",
        required=True,
        help="Input covariates CSV"
    )
    parser.add_argument(
        "--derivatives-root",
        required=True,
        help="Derivatives root directory (e.g. data/derivatives)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output CSV with brain volume added"
    )

    args = parser.parse_args()
    main(args)