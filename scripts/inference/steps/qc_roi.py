"""
QC step for ROI-based segmentation / parcellation.
Designed for multi-label outputs (e.g. ~100 ROIs).

QC strategy:
1) Identify ROIs by voxel count
2) Select representative ROIs across size spectrum
   - largest ROI
   - median-sized ROI
   - smallest non-empty ROI
3) For each ROI:
   - find slice with maximum ROI area
   - export overlay PNG on anatomical image

This avoids lesion-centric assumptions and gives coverage
from large cortical regions to small subcortical ROIs.

Main question to answer:
“Is this parcellation anatomically sane for this subject?”
"""

from pathlib import Path
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from .base import Step


class QCRoiStep(Step):
    def run(self, ctx):
        """
        Explicit ROI-based QC.

        Expected in ctx:
          - image: anatomical NIfTI
          - mask: ROI label map (int)
          - work_dir

        Params (YAML):
          roi_labels: list[int]      # REQUIRED
          slice_mode: axial|sagittal|coronal (default: axial)
          alpha: overlay transparency (default: 0.4)
        """
        roi_labels = self.params.get("roi_labels")
        if not roi_labels:
            raise ValueError("qc_roi requires 'roi_labels' in params")

        slice_mode = self.params.get("slice_mode", "axial")
        alpha = self.params.get("alpha", 0.4)

        out_dir = ctx["work_dir"] / "qc_roi"
        out_dir.mkdir(parents=True, exist_ok=True)

        print(">>> ROI QC STEP RUNNING")

        # --- Load + canonicalize image ---
        img_nii = nib.as_closest_canonical(nib.load(str(ctx["image"])))
        img = img_nii.get_fdata()

        # --- Load + canonicalize segmentation ---
        mask_nii = nib.as_closest_canonical(nib.load(str(ctx["mask"])))
        mask = mask_nii.get_fdata().astype(int)

        # --- Safety check ---
        if img.shape != mask.shape:
            raise RuntimeError(
                f"Image/mask shape mismatch: {img.shape} vs {mask.shape}"
            )

        # Axis mapping
        axis_map = {
            "sagittal": 0,
            "coronal": 1,
            "axial": 2,
        }
        if slice_mode not in axis_map:
            raise ValueError(f"Invalid slice_mode: {slice_mode}")

        axis = axis_map[slice_mode]

        qc_outputs = []

        for roi_label in roi_labels:
            roi_mask = mask == roi_label

            if roi_mask.sum() == 0:
                print(f"[QC] ROI {roi_label} not present, skipping")
                continue

            # --- slice with max ROI area ---
            slice_sums = roi_mask.sum(axis=tuple(i for i in range(3) if i != axis))
            idx = int(np.argmax(slice_sums))

            if axis == 0:
                img_slice = img[idx, :, :]
                roi_slice = roi_mask[idx, :, :]
            elif axis == 1:
                img_slice = img[:, idx, :]
                roi_slice = roi_mask[:, idx, :]
            else:
                img_slice = img[:, :, idx]
                roi_slice = roi_mask[:, :, idx]

            vmin, vmax = np.percentile(img_slice, (2, 98))

            plt.figure(figsize=(6, 6))
            plt.imshow(img_slice.T, cmap="gray", origin="lower",
                       vmin=vmin, vmax=vmax)
            plt.imshow(roi_slice.T, cmap="autumn", origin="lower",
                       alpha=alpha)
            plt.axis("off")
            plt.title(f"ROI {roi_label} | {slice_mode}={idx}")

            out_png = out_dir / f"qc_roi_{roi_label}_{slice_mode}.png"
            plt.savefig(out_png, bbox_inches="tight", dpi=150)
            plt.close()

            qc_outputs.append(str(out_png))

        ctx["qc_roi"] = qc_outputs
        return ctx