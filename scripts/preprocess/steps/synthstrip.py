import subprocess
from .base import Step

class SynthStripStep(Step):
    def run(self, ctx):
        brain = ctx["work_dir"] / "T1w_1mm_brain.nii.gz"
        mask = ctx["work_dir"] / "T1w_1mm_brain_mask.nii.gz"

        cmd = [
            "mri_synthstrip",
            "-i", str(ctx["image"]),
            "-o", str(brain),
            "-m", str(mask)
        ]
        subprocess.run(cmd, check=True)

        ctx["image"] = brain
        ctx["mask"] = mask
        ctx["metadata"]["skull_strip"] = "SynthStrip"
        return ctx