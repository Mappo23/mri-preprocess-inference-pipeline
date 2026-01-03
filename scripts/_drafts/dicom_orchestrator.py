def preprocess_dicom_case(dicom_dir, out_dir):
    nii = convert_dicom(dicom_dir)
    lia = reorient_to_LIA(nii)
    nii_1mm = resample_if_needed(lia)
    brain = synthstrip(nii_1mm)