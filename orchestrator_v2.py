#!/usr/bin/env python3
import csv
from pathlib import Path
import subprocess
import sys
import logging
import argparse


# -------------------------
# Arguments
# -------------------------
parser = argparse.ArgumentParser()
parser.add_argument("csv_file", help="Input CSV file")
parser.add_argument("--start", type=int, required=True, help="Start row (1-based, excluding header)")
parser.add_argument("--end", type=int, required=True, help="End row (1-based, inclusive)")
parser.add_argument("--dry-run", action="store_true", help="Do not run subprocesses, just print what would be processed")
args = parser.parse_args()

csv_file = args.csv_file
start = args.start
end = args.end

if start < 1 or end < start:
    raise ValueError(f"Invalid range: start={start}, end={end}")


# -------------------------
# Logging
# -------------------------
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "pipeline.log"

handlers = []

# File handler (always)
file_handler = logging.FileHandler(log_file, mode="a")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
)
handlers.append(file_handler)

# Console handler (dry-run only)
if args.dry_run:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter("[%(levelname)s] %(message)s")
    )
    handlers.append(console_handler)

logging.basicConfig(
    level=logging.INFO,
    handlers=handlers
)

logging.info(
    f"Mode: {'DRY-RUN' if args.dry_run else 'EXECUTION'} | "
    f"Rows {start} → {end}"
)

# -------------------------
# Read CSV and process
# -------------------------

with open(csv_file) as f:
    reader = csv.DictReader(f)

    for row_idx, row in enumerate(reader, start=1):
        # row_idx is 1-based and excludes header

        if row_idx < start:
            continue

        if row_idx > end:
            break

        subject = row["subject_id"]
        series  = row["series_id"]

        logging.info(f"CSV row {row_idx}: {subject}/{series}")

        dicom_dir = Path(row["dicom_dir"])
        out_dir = Path("data/derivatives") / subject / series
        preproc_dir = out_dir / "preproc"
        preproc_img = preproc_dir / "T1w_1mm_brain.nii.gz"
        seg_dir = out_dir / "seg"
        preproc_dir.mkdir(parents=True, exist_ok=True)
        seg_dir.mkdir(parents=True, exist_ok=True)

        done_flag = seg_dir / "PIPELINE_DONE.ok"

        if args.dry_run:
            logging.info(f"[DRY-RUN] CSV row {row_idx}: {subject}/{series}")
            continue

        if done_flag.exists():
            logging.info(f"[{subject}/{series}] Pipeline already completed. Skipping.")
            continue   # skip this subject
            
        try:
            # -------------------------
            # Preprocessing step (/project2/cchen3/riccardol/scripts/preprocess)
            # -------------------------
            if preproc_img.exists():
                logging.info(
                    f"[{subject}/{series}] Preprocessing already done "
                    f"({preproc_img.name} exists). Skipping."
                )
            else:
                logging.info(f"[{subject}/{series}] Starting preprocessing...")

                subprocess.run([
                    sys.executable,
                    "-m",
                    "scripts.preprocess.run_preprocess",
                    "--dicom", str(dicom_dir),
                    "--out", str(preproc_dir),
                    "--config", "/project2/cchen3/riccardol/configs/pre_ADNI_T1.yaml",
                    "--qc"
                ], check=True)

                logging.info(f"[{subject}/{series}] Preprocessing done.")

            # -------------------------
            # Inference step (/project2/cchen3/riccardol/scripts/inference)
            # -------------------------
            logging.info(f"[{subject}/{series}] Starting inference...")

            subprocess.run([
                sys.executable, 
                "-m",
                "scripts.inference.run_inference",
                "--image", str(preproc_dir / "T1w_1mm_brain.nii.gz"),
                "--out", str(seg_dir),
                "--config", "/project2/cchen3/riccardol/configs/infer_and_qc.yaml"
            ], check=True)

            logging.info(f"[{subject}/{series}] Inference done.")

        

        except subprocess.CalledProcessError as e:
            logging.error(f"[{subject}/{series}] ERROR: {e}")


# -------------------------
#  DONE - Exit loop
# -------------------------
logging.info("All subjects processed successfully. Exiting.")
sys.exit(0)