#!/usr/bin/env python3
import csv
from pathlib import Path
import subprocess
import sys
import logging

# -------------------------
# Arguments
# -------------------------
if len(sys.argv) < 2:
    print("Usage: python orchestrator_v2.py <csv_file>")
    sys.exit(1)

csv_file = sys.argv[1]

# -------------------------
# Logging
# -------------------------
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "pipeline.log"

logging.basicConfig(
    filename=log_file,
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)

# -------------------------
# Read CSV and process
# -------------------------
with open(csv_file) as f:
    reader = csv.DictReader(f)
    for row in reader:
        subject = row["subject_id"]
        series  = row["series_id"]
        dicom_dir = Path(row["dicom_dir"])
        out_dir = Path("data/derivatives") / subject / series
        preproc_dir = out_dir / "preproc"
        preproc_img = preproc_dir / "T1w_1mm_brain.nii.gz"
        seg_dir = out_dir / "seg"
        preproc_dir.mkdir(parents=True, exist_ok=True)
        seg_dir.mkdir(parents=True, exist_ok=True)

        done_flag = seg_dir / "PIPELINE_DONE.ok"

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