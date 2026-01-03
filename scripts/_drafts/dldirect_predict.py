from pathlib import Path
import subprocess
from .base import Step

class DLDirectPredict(Step):
    def run(self, ctx):
        """
        Expected params in YAML:
          model_dir: path to DL-DiReCT model folder
          config: path to DL-DiReCT config (if needed)
        """
        model_dir = Path(self.params["model_dir"])
        out_dir = ctx["out_dir"]
        image = ctx["image"]

        out_dir.mkdir(parents=True, exist_ok=True)

        # DL-DiReCT inference is CLI-based
        cmd = [
            "python",
            str(model_dir / "infer.py"),
            "--input", str(image),
            "--output", str(out_dir),
        ]

        if "config" in self.params:
            cmd += ["--config", self.params["config"]]

        subprocess.run(cmd, check=True)

        # Expected DL-DiReCT outputs (adapt if naming differs)
        ctx["prob_map"] = out_dir / "prob_map.nii.gz"
        ctx["mask"] = out_dir / "lesion_mask.nii.gz"

        ctx["metadata"] = ctx.get("metadata", {})
        ctx["metadata"]["model"] = "DL-DiReCT"
        return ctx