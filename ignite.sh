#!/bin/bash
#SBATCH --account pi-cchen3
#SBATCH --partition gpu
#SBATCH --job-name=mripipeline
#SBATCH --output=logs/job_%A_%a.out
#SBATCH --error=logs/job_%A_%a.err
#SBATCH --time=04:00:00
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G

set -euo pipefail

# -------------------------
# Environment
# -------------------------
module load python
module load freesurfer/7.4
export FREESURFER_HOME=/software/freesurfer-7.4-el8-x86_64
source activate /project2/cchen3/riccardol/envs/dpscan3

# -------------------------
# Arguments
# -------------------------
CSV=${1:?CSV file required}
START=${2:?START row required}
END=${3:?END row required}

echo "Running pipeline on rows ${START} → ${END}"
echo "CSV: ${CSV}"

# -------------------------
# Run orchestrator
# -------------------------
python orchestrator_v2.py \
  "$CSV" \
  --start "$START" \
  --end "$END"