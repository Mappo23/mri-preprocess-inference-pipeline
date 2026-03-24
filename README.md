# MRI Preprocess Inference Pipeline

This repository contains an **MRI preprocessing, inference, and post-processing pipeline** used for the study:

**Radiomic Characterization of Neuroanatomical Changes in Alzheimer’s Disease Using DL-based tools and ADNI Data**

within the research scope of:

**APOE ε4 Status and Regional Brain Atrophy Trajectories in MCI and AD**

The pipeline processes raw MRI data through multiple stages, producing **segmentation outputs and volumetric measurements** that are later standardized and harmonized for downstream statistical analysis.

---

# Project Purpose

Large neuroimaging datasets often combine scans acquired across **different scanners, sites, and acquisition protocols**, introducing systematic variability.

This pipeline aims to:

- preprocess MRI scans  
- run inference and segmentation  
- extract volumetric brain features  
- standardize results across acquisition sites  

The final outputs are **analysis-ready datasets of regional brain volumes**, suitable for statistical modeling and neurodegeneration studies.

---

# Pipeline Architecture

The project follows a **modular pipeline architecture** composed of several independent processing stages coordinated by an **orchestrator**.

Each stage follows:

```
input data → processing step → output dataset
```

Advantages:

- modular and reusable scripts  
- easier debugging  
- reproducibility  
- ability to rerun individual pipeline stages  

---

# Pipeline Entry Point

## `ignite.sh`

Start the pipeline with:

```bash
./ignite.sh
```

This script:

- prepares the runtime environment  
- activates the correct Python environment  
- loads configuration  
- submits the pipeline job to the RCC (UC HPC environment), which manages execution of the full workflow.
- launches the orchestrator (i.e. orchestrator_v2.py)
- sends push Telegram notifications when jobs start and finish  

---

# Pipeline Orchestration

## `orchestrator_v2.py`

The orchestrator manages the **execution flow of preprocessing and inference stages**.

It:

- reads configuration files  
- discovers datasets  
- launches preprocessing jobs  
- triggers inference and segmentation  
- organizes outputs  

This ensures a **structured and reproducible pipeline execution**.

---

# Pipeline Stages

## Pre-processing

The preprocessing stage prepares raw MRI scans for inference.

Typical operations include:

- data format standardization  
- spatial normalization / registration  
- intensity normalization  
- quality control checks  

Outputs are **clean and standardized MRI images** (on compressed NIfTI format) ready for model inference.

---

## Inference

The inference stage applies trained models to extract **brain segmentations and volumetric information**.

Typical operations include:

- running DL-based segmentation models (e.g. DL+DiReCT)  
- generating region-wise brain masks  
- computing regional volumetric measures  

Outputs are:

- segmentation maps  
- regional brain volumes  

These outputs are the **input for the post-processing stage**.

---

# Repository Structure

```
mri-preprocess-inference-pipeline/
│
├── README.md
├── ignite.sh
├── orchestrator_v2.py
│
├── scripts/
│   ├── preprocessing/
│   ├── inference/
│   └── postprocessing/
│
├── configs/
└── requirements.txt
```

---

# Post-processing Pipeline

The `scripts/postprocessing` directory transforms segmentation outputs into **analysis-ready datasets**.

Key steps:

1. merge volumes with metadata  
2. compute intracranial volume (ICV)  
3. harmonize data using ComBat  
4. generate residualized volumes  

---

# Post-processing Scripts

| Script | Purpose |
|------|------|
| `cvs_merge_v2.py` | Merge segmentation volumes with ADNI metadata |
| `brain_volume.py` | Compute intracranial volume (ICV) |
| `ComBat_pre.py` | Apply ComBat harmonization |
| `debug_diagnosis_nan.py` | Detect missing diagnosis values |
| `fill_diagnosis_from_dxsum.py` | Recover missing diagnosis labels |

---

# ⚠️ Important: Post-processing Execution

**Post-processing is NOT handled by the orchestrator and must be executed manually.**

This stage involves **data validation, inspection, and correction steps** that cannot be fully automated.

Before proceeding between steps, users should:

- inspect intermediate outputs  
- verify metadata consistency  
- fix missing or incorrect values if needed  

Failure to do so may lead to **incorrect harmonization results or pipeline failures**.

---

# Running Post-processing Scripts

## 1. Merge volumes with metadata

```bash
python scripts/postprocessing/cvs_merge_v2.py \
  --volumes_csv data/volumes.csv \
  --metadata_csv data/adni_metadata.csv \
  --output merged_volumes.csv
```

---

## 2. Compute intracranial volume (ICV)

```bash
python scripts/postprocessing/brain_volume.py \
  --input merged_volumes.csv \
  --output merged_volumes_icv.csv
```

---

## 3. Check missing diagnosis values

```bash
python scripts/postprocessing/debug_diagnosis_nan.py \
  --input merged_volumes_icv.csv
```

---

## 4. Fix diagnosis values (if needed)

```bash
python scripts/postprocessing/fill_diagnosis_from_dxsum.py \
  --input merged_volumes_icv.csv \
  --dxsum dxsum.csv \
  --output merged_volumes_icv_fixed.csv
```

---

## 5. Run ComBat harmonization

```bash
python scripts/postprocessing/ComBat_pre.py \
  --input merged_volumes_icv.csv \
  --batch site \
  --covariates age sex diagnosis \
  --output combat_residuals.csv
```

---

# Recommended Execution Order

```
1. cvs_merge_v2.py
2. brain_volume.py
3. debug_diagnosis_nan.py
4. fill_diagnosis_from_dxsum.py (only if needed)
5. ComBat_pre.py
```

Final output:

```
combat_residuals.csv
```

---

# Setup

```bash
git clone https://github.com/Mappo23/mri-preprocess-inference-pipeline.git
cd mri-preprocess-inference-pipeline
pip install -r requirements.txt
```

Python **3.10+** is recommended.

---

# Notes

- assumes **ADNI-style datasets**  
- missing metadata is the most common failure cause  
- keep intermediate CSVs for reproducibility  