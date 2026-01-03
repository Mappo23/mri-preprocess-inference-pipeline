#!/bin/bash
#SBATCH --job-name=mri_preprocess
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --array=0-999
#SBATCH --output=logs/preprocess_%A_%a.out

CONFIG=configs/preprocess_T1.yaml

CASE=$(sed -n "$((SLURM_ARRAY_TASK_ID+1))p" cases.txt)
DICOM_DIR=$(echo $CASE | cut -d',' -f1)
OUT_DIR=$(echo $CASE | cut -d',' -f2)

python preprocess/run_preprocess.py \
  --dicom "$DICOM_DIR" \
  --out "$OUT_DIR" \
  --config "$CONFIG" \
  --qc