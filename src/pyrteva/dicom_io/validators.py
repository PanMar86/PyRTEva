import os


def validate_directory_structure(patient_dir_path):
    """
    This function checks whether the patient directory contains the required subdirectories "CT", "RTSTRUCT", "RTDOSE"
    and "RTPLAN". For each subdirectory, it checks that:
    - The subdirectory exists.
    - The subdirectory is not empty.
    - At least one DICOM file is present.
    - Only one DICOM file exists for non-CT subdirectories.

    Parameters
    ----------
    patient_dir_path : str
        Path to the patient's root directory containing the required subdirectories.

    Returns
    -------
    patient_dir_path :str
        The validated patient directory path.
    """

    # Verify that certain subdirectories exist.
    sub_dirs = os.listdir(patient_dir_path)

    for sub_dir in ["CT", "RTSTRUCT", "RTDOSE", "RTPLAN"]:

        if sub_dir not in sub_dirs:

            raise FileNotFoundError(f"{sub_dir} subdirectory was not found in patient's directory.")

        # Verify that subdirectories are not empty.
        sub_dir_path = os.path.join(patient_dir_path, sub_dir)
        sub_dir_filenames = os.listdir(sub_dir_path)

        if not sub_dir_filenames:

            raise FileNotFoundError(f"{sub_dir} subdirectory is empty.")

        # Verify that there are unique DICOM RTSTRUCT, RTDOSE and RTPLAN files inside the corresponding subdirectories.
        num_dcm_files = 0

        for filename in sub_dir_filenames:

            if filename.lower().endswith(".dcm"):

                num_dcm_files += 1

        if num_dcm_files == 0:

            raise FileNotFoundError(f"No {sub_dir.lower()} files were found in the {sub_dir} subdirectory.")

        elif (num_dcm_files) > 1 and (sub_dir != "CT"):

            raise ValueError(f"Multiple {sub_dir.lower()} files within the same directory are not supported.")

    return patient_dir_path