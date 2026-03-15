from pathlib import Path
import pandas as pd
import logging

# ------------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
DERIV_ROOT = Path("/scratch/midway3/riccardolispi/riccardol/data/derivatives")
COVARIATES_CSV = Path("/scratch/midway3/riccardolispi/riccardol/scripts/postprocessing/Genotype_2_2_T1w_ComBat_Ready.csv")
OUTPUT_CSV = Path("/scratch/midway3/riccardolispi/riccardol/scripts/postprocessing/ComBat_Covariates_apoe2_2_with_volumes.csv")

volume_rows = []
n_seen = 0
n_skipped = 0

logger.info(f"Scanning derivatives directory: {DERIV_ROOT}")

# ------------------------------------------------------------------
# 1) Collect all volume CSVs
# ------------------------------------------------------------------
for vol_csv in DERIV_ROOT.rglob("result-vol.csv"):
    n_seen += 1
    try:
        # Extract image_id from path: I10952545 -> 10952545
        image_dir = vol_csv.parent.parent.name
        image_id = image_dir.lstrip("I")

        df = pd.read_csv(vol_csv)

        # Sanity check: expect exactly one row
        if len(df) != 1:
            logger.error(
                f"Invalid row count ({len(df)}) in {vol_csv}, skipping"
            )
            n_skipped += 1
            continue

        df.insert(0, "image_id", image_id)
        volume_rows.append(df)

    except Exception as e:
        logger.exception(f"Failed processing {vol_csv}")
        n_skipped += 1

logger.info(
    f"Found {n_seen} result-vol.csv files "
    f"({len(volume_rows)} valid, {n_skipped} skipped)"
)

if not volume_rows:
    raise RuntimeError("No valid volume files found. Aborting.")

# ------------------------------------------------------------------
# Combine all volumes into a single dataframe
# ------------------------------------------------------------------
volumes_df = pd.concat(volume_rows, ignore_index=True)
volumes_df["image_id"] = volumes_df["image_id"].astype(str)

logger.info(f"Volumes dataframe shape: {volumes_df.shape}")

# ------------------------------------------------------------------
# 2) Load covariates
# ------------------------------------------------------------------
logger.info(f"Loading covariates from {COVARIATES_CSV}")
cov_df = pd.read_csv(COVARIATES_CSV)
cov_df["image_id"] = cov_df["image_id"].astype(str)

logger.info(f"Covariates dataframe shape: {cov_df.shape}")

# ------------------------------------------------------------------
# 3) Merge
# ------------------------------------------------------------------
merged_df = cov_df.merge(
    volumes_df,
    on="image_id",
    how="left"
)

logger.info(f"Merged dataframe shape (pre-drop): {merged_df.shape}")

# ------------------------------------------------------------------
# 4) Drop rows without volumetries
# ------------------------------------------------------------------
region_cols = volumes_df.columns.drop("image_id")

n_before = len(merged_df)
merged_df = merged_df.dropna(
    subset=region_cols,
    how="all"
)
n_after = len(merged_df)

logger.info(
    f"Dropped {n_before - n_after} rows without volumetries "
    f"({n_after} remaining)"
)

# ------------------------------------------------------------------
# 5) Final sanity checks + save
# ------------------------------------------------------------------
if merged_df["image_id"].duplicated().any():
    logger.warning("Duplicate image_id detected after merge")

merged_df.to_csv(OUTPUT_CSV, index=False)
logger.info(f"Saved merged dataset to {OUTPUT_CSV}")
