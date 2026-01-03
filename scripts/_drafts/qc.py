import nibabel as nib
import matplotlib.pyplot as plt
from .base import Step


class QCStep(Step):
    def run(self, ctx):
        # Hard, explicit signal in logs
        print(">>> QC STEP ENTERED")

        # QC gate
        if not ctx.get("qc", False):
            print(">>> QC DISABLED, SKIPPING")
            return ctx

        # Sanity checks
        if "image" not in ctx:
            raise RuntimeError("QCStep: ctx['image'] missing")

        img_path = ctx["image"]
        work_dir = ctx["work_dir"]

        # Load image
        img = nib.load(str(img_path))
        data = img.get_fdata()

        # Mid-slice
        z = data.shape[2] // 2
        slice_img = data[:, :, z]

        # Plot
        plt.figure(figsize=(5, 5))
        plt.imshow(slice_img.T, cmap="gray", origin="lower")

        # Optional mask overlay
        if ctx.get("mask") is not None:
            mask = nib.load(str(ctx["mask"])).get_fdata()
            plt.contour(mask[:, :, z].T, colors="r", linewidths=0.5)

        plt.axis("off")

        # Output
        out = work_dir / "qc_mid_slice.png"
        plt.savefig(out, bbox_inches="tight", dpi=150)
        plt.close()

        print(f">>> QC PNG SAVED TO {out}")

        return ctx

