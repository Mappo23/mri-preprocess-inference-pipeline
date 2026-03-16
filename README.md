# MRI Preprocess Inference Pipeline

This repository contains an **MRI preprocessing and inference pipeline** used for the study:

**Radiomic Characterization of Neuroanatomical Changes in Alzheimer’s Disease Using DL+DiReCT and ADNI Data**

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

Each stage typically follows the pattern:

```
input data → processing step → output dataset
```

Advantages of this approach:

- modular and reusable scripts
- easier debugging
- reproducibility
- ability to rerun individual pipeline stages

---

# Pipeline Entry Point

## `ignite.sh`

The pipeline is typically started using the shell script:

```bash
./ignite.sh
```

This script acts as the **entry point of the pipeline** and performs the initial setup required to launch the processing workflow.

Typical responsibilities include:

- loading the required environment
- activating the correct Python environment
- preparing configuration variables
- launching the main pipeline orchestrator

The script ensures that the pipeline is executed in a **consistent runtime environment**.

---

# Pipeline Orchestration

## `orchestrator_v2.py`

The core coordination of the pipeline is handled by:

```
orchestrator_v2.py
```

The orchestrator manages the **execution order of the different pipeline modules**, ensuring that each stage runs only when the required inputs are available.

Typical tasks performed by the orchestrator include:

- reading pipeline configuration files
- discovering available datasets
- launching preprocessing jobs
- triggering inference and segmentation stages
- organizing intermediate outputs
- coordinating downstream processing steps

The orchestrator allows the pipeline to run in a **structured and reproducible way**, avoiding manual execution of each step.

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

The `scripts/postprocessing` directory contains the stage responsible for transforming segmentation outputs into **analysis-ready volumetric datasets**.

Key steps include:

1. merging segmentation volumes with metadata
2. computing intracranial volume (ICV)
3. applying ComBat harmonization
4. producing residualized regional brain volumes

---

# Post-processing Scripts

| Script | Purpose |
|------|------|
| `cvs_merge_v2.py` | Merge segmentation volumes with ADNI metadata |
| `brain_volume.py` | Compute intracranial volume (ICV) |
| `ComBat_pre.py` | Apply ComBat harmonization |
| `debug_diagnosis_nan.py` | Detect missing diagnosis values |
| `fill_diagnosis_from_dxsum.py` | Recover missing diagnosis labels from ADNI DXSUM |

---

# Post-processing Workflow

Typical manual execution sequence:

```
1. cvs_merge_v2.py
2. brain_volume.py
3. debug_diagnosis_nan.py
4. fill_diagnosis_from_dxsum.py (if needed)
5. ComBat_pre.py
```

---

# Setup

Clone the repository:

```bash
git clone https://github.com/Mappo23/mri-preprocess-inference-pipeline.git
cd mri-preprocess-inference-pipeline
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Python **3.8+** is recommended.

---

# Notes

- The pipeline assumes **ADNI-style datasets**
- Missing metadata values are the most common cause of pipeline failures
- Intermediate outputs should be preserved for **reproducibility and debugging**
