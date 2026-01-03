import subprocess
from pathlib import Path
from .base import Step

class Dcm2NiixStep(Step):
    def run(self, ctx):
        out = ctx["work_dir"] / "T1w.nii.gz"
        cmd = [
            "dcm2niix",
            "-z", "y",
            "-f", "T1w",
            "-o", str(ctx["work_dir"]),
            str(ctx["dicom_dir"])
        ]
        subprocess.run(cmd, check=True)
        ctx["image"] = out
        ctx["metadata"]["source"] = "DICOM"
        return ctx
