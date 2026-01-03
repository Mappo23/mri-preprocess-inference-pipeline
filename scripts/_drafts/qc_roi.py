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
        Expected in ctx:
          - image: path to anatomical MRI (NIfTI)
          - mask: ROI label map (int labels, 0 = background)
          - out_dir

        Params:
          alpha: overlay transparency (default 0.4)
          max_rois: maximum number of ROIs to QC (default 3)
        """
        alpha = self.params.get("alpha", 0.4)
        max_rois = self.params.get("max_rois", 3)

        out_dir = ctx["work_dir"] / "qc_roi"
        out_dir.mkdir(parents=True, exist_ok=True)

        # Load anatomical image
        img = nib.load(str(ctx["image"]))
        vol = img.get_fdata()

        print(">>> ROI QC STEP RUNNING")
        
        # Load ROI label map
        mask_obj = ctx.get("mask")
        if isinstance(mask_obj, (str, Path)):
            roi_map = nib.load(str(mask_obj)).get_fdata().astype(int)
        else:
            roi_map = mask_obj.astype(int)

        # Compute ROI sizes (exclude background)
        labels, counts = np.unique(roi_map, return_counts=True)
        roi_sizes = {
            int(l): int(c)
            for l, c in zip(labels, counts)
            if l != 0 and c > 0
        }

        if len(roi_sizes) == 0:
            return ctx  # nothing to QC

        # Sort ROIs by size
        sorted_rois = sorted(roi_sizes.items(), key=lambda x: x[1], reverse=True)

        selected = []
        if max_rois >= 1:
            selected.append(sorted_rois[0][0])  # largest
        if max_rois >= 2:
            selected.append(sorted_rois[len(sorted_rois) // 2][0])  # median
        if max_rois >= 3:
            selected.append(sorted_rois[-1][0])  # smallest

        selected = selected[:max_rois]

        qc_outputs = []

        for roi_label in selected:
            roi_mask = roi_map == roi_label

            # Slice with max ROI area (axial)
            slice_sums = roi_mask.sum(axis=(0, 1))
            z = int(np.argmax(slice_sums)) if slice_sums.max() > 0 else vol.shape[2] // 2

            img_slice = vol[:, :, z]
            roi_slice = roi_mask[:, :, z]

            vmin, vmax = np.percentile(img_slice, (2, 98))

            plt.figure(figsize=(6, 6))
            plt.imshow(img_slice.T, cmap="gray", origin="lower", vmin=vmin, vmax=vmax)
            plt.imshow(roi_slice.T, cmap="viridis", origin="lower", alpha=alpha)
            plt.axis("off")
            plt.title(f"ROI {roi_label} | z={z} | voxels={roi_sizes[roi_label]}")

            out_png = out_dir / f"qc_roi_{roi_label}.png"
            plt.savefig(out_png, bbox_inches="tight", dpi=150)
            plt.close()

            qc_outputs.append(str(out_png))

        ctx["qc_roi"] = qc_outputs
        return ctx