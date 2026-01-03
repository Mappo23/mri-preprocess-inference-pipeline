import nibabel as nib
import numpy as np
from pathlib import Path
from .base import Step

class ReorientStep(Step):
    def run(self, ctx):
        orientation = self.params.get("orientation", "LIA")
        out = ctx["work_dir"] / f"T1w_{orientation}.nii.gz"

        img = nib.load(str(ctx["image"]))
        img = nib.as_closest_canonical(img)

        target_ornt = nib.orientations.axcodes2ornt(tuple(orientation))
        current_ornt = nib.orientations.io_orientation(img.affine)
        transform = nib.orientations.ornt_transform(current_ornt, target_ornt)

        data = nib.orientations.apply_orientation(img.get_fdata(), transform)
        new_affine = img.affine @ nib.orientations.inv_ornt_aff(transform, img.shape)

        nib.save(nib.Nifti1Image(data.astype(np.float32), new_affine), str(out))

        ctx["image"] = out
        ctx["metadata"]["orientation"] = orientation
        return ctx