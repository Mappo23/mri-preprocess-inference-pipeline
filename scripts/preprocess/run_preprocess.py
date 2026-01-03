import yaml
import json
from pathlib import Path
from .pipeline import Pipeline


def main(dicom_dir, out_dir, config_path, qc):
    with open(config_path) as f:
        config = yaml.safe_load(f)

    ctx = {
        "dicom_dir": Path(dicom_dir),
        "work_dir": Path(out_dir),
        "image": None,
        "mask": None,
        "qc": qc,
        "metadata": {}
    }

    ctx["work_dir"].mkdir(parents=True, exist_ok=True)

    pipeline = Pipeline(config)
    if qc and "qc" not in [type(s).__name__.lower() for s in pipeline.steps]:
        from .steps.qc import QCStep
        pipeline.steps.append(QCStep())
        
    ctx = pipeline.run(ctx)

    with open(ctx["work_dir"] / "metadata.json", "w") as f:
        json.dump(ctx["metadata"], f, indent=2)


if __name__ == "__main__":
    import argparse
    
    p = argparse.ArgumentParser()
    p.add_argument("--dicom", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--qc", action="store_true")
    p.add_argument("--config", required=True)
    args = p.parse_args()

    main(args.dicom, args.out, args.config, args.qc)