import SimpleITK as sitk
from .base import Step

class ResampleStep(Step):
    def run(self, ctx):
        spacing = tuple(self.params.get("spacing", (1.0, 1.0, 1.0)))
        tolerance = self.params.get("tolerance", 0.05)

        img = sitk.ReadImage(str(ctx["image"]))
        in_spacing = img.GetSpacing()

        if all(abs(in_spacing[i] - spacing[i]) < tolerance for i in range(3)):
            return ctx

        new_size = [
            int(round(img.GetSize()[i] * in_spacing[i] / spacing[i]))
            for i in range(3)
        ]

        resampler = sitk.ResampleImageFilter()
        resampler.SetInterpolator(sitk.sitkLinear)
        resampler.SetOutputSpacing(spacing)
        resampler.SetSize(new_size)
        resampler.SetOutputDirection(img.GetDirection())
        resampler.SetOutputOrigin(img.GetOrigin())

        out = ctx["work_dir"] / "T1w_1mm.nii.gz"
        sitk.WriteImage(resampler.Execute(img), str(out))

        ctx["image"] = out
        ctx["metadata"]["final_spacing"] = spacing
        return ctx