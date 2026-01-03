from pathlib import Path
import subprocess
from .base import Step


class DLDirectPredict(Step):
    def run(self, ctx):
        """
        YAML params:
          model: model name or version (e.g. v7)
        """

        image = ctx["image"]
        out_dir = ctx["work_dir"]
        model = self.params.get("model", "v7")

        out_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            "dl+direct",
            "-n",
            "-k",
            "--model", model,
            str(image),
            str(out_dir),
        ]

        subprocess.run(cmd, check=True)

        # Expected outputs (adjust ONLY if dl+direct differs)
        prob = out_dir / "softmax_seg.nii.gz"
        mask = out_dir / "T1w_norm_seg.nii.gz"

        if not prob.exists() or not mask.exists():
            raise RuntimeError(
                f"DLDirect outputs not found in {out_dir}"
            )

        ctx["prob_map"] = prob
        ctx["mask"] = mask

        ctx.setdefault("metadata", {})
        ctx["metadata"]["model"] = f"DLDirect:{model}"

        return ctx