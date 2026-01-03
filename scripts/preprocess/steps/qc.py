import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from .base import Step

class QCStep(Step):
    def run(self, ctx):
        if not ctx.get("qc", False):
            return ctx

        print(">>> QC STEP ENTERED")

        img = nib.as_closest_canonical(nib.load(str(ctx["image"])))
        data = img.get_fdata()

        mask = None
        if ctx.get("mask") is not None:
            mask_img = nib.as_closest_canonical(nib.load(str(ctx["mask"])))
            mask = mask_img.get_fdata()
            z_indices = np.where(mask > 0)[2]
            z = int(z_indices.mean())
        else:
            z = data.shape[2] // 2

        slice_img = data[:, :, z]

        plt.figure(figsize=(5, 5))
        plt.imshow(slice_img, cmap="gray")

        if mask is not None:
            plt.contour(mask[:, :, z], colors="r", linewidths=0.25)

        plt.axis("off")
        out = ctx["work_dir"] / "qc_mid_brain_slice.png"
        plt.savefig(out, bbox_inches="tight", dpi=150)
        plt.close()

        ctx["metadata"]["qc"] = str(out)

        print(f">>> QC PNG SAVED TO {out}")

        return ctx