import nibabel as nib

def reorient_to_LIA(in_nii, out_nii):
    img = nib.load(in_nii)

    # Canonical first (RAS)
    img = nib.as_closest_canonical(img)

    # Target orientation: LIA
    # L = Left (-X), I = Inferior (-Z), A = Anterior (+Y)
    target_ornt = nib.orientations.axcodes2ornt(("L", "I", "A"))
    current_ornt = nib.orientations.io_orientation(img.affine)

    transform = nib.orientations.ornt_transform(current_ornt, target_ornt)
    data = nib.orientations.apply_orientation(img.get_fdata(), transform)

    new_affine = img.affine @ nib.orientations.inv_ornt_aff(transform, img.shape)
    out = nib.Nifti1Image(data, new_affine)

    nib.save(out, out_nii)