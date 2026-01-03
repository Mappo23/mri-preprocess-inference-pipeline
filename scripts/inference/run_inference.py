import yaml
import json
from pathlib import Path
from .pipeline import Pipeline


def main(image, out_dir, config_path):
    with open(config_path) as f:
        config = yaml.safe_load(f)

    ctx = {
        "image": Path(image),
        "work_dir": Path(out_dir),
        "roi": None,
        "qc": False,
        "metadata": {}
    }

    ctx["work_dir"].mkdir(parents=True, exist_ok=True)

    pipeline = Pipeline(config)
    ctx = pipeline.run(ctx)

    with open(ctx["work_dir"] / "metadata.json", "w") as f:
        json.dump(ctx["metadata"], f, indent=2)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--config", required=True)
    args = p.parse_args()

    main(args.image, args.out, args.config)