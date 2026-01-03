import SimpleITK as sitk

def resample_if_needed(in_nii, out_nii, target_spacing=(1.0,1.0,1.0)):
    img = sitk.ReadImage(in_nii)
    spacing = img.GetSpacing()

    if all(abs(spacing[i] - target_spacing[i]) < 0.05 for i in range(3)):
        sitk.WriteImage(img, out_nii)
        return

    new_size = [
        int(round(img.GetSize()[i] * spacing[i] / target_spacing[i]))
        for i in range(3)
    ]

    resampler = sitk.ResampleImageFilter()
    resampler.SetOutputSpacing(target_spacing)
    resampler.SetSize(new_size)
    resampler.SetInterpolator(sitk.sitkLinear)
    resampler.SetOutputDirection(img.GetDirection())
    resampler.SetOutputOrigin(img.GetOrigin())

    resampled = resampler.Execute(img)
    sitk.WriteImage(resampled, out_nii)