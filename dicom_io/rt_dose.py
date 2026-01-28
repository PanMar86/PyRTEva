import numpy as np
import pydicom
import os


def load_computed_dose(patient_dir_path, ct_series_frame_of_reference_uid, ct_series_orientation):
    """
    This function loads the DICOM RTDOSE file located in the "RTDOSE" subdirectory of patient's directory and applies the
    DoseGridScaling factor in order to obtain the actual dose distribution. Furthermore, it extracts information
    regarding the dose grid parameters.

    Parameters
    ----------
    patient_dir_path : str
        Path to the patient's directory containing an "RTDOSE" subdirectory with the DICOM RTDOSE file.

    ct_series_frame_of_reference_uid : str
        Unique identifier of the CT series' frame of reference. Used to verify that the dose grid origin is expressed
        with regards to the same coordinate system.

    ct_series_orientation : list of float
        Spatial orientation of the CT series. Used to verify that the dose grid has the same spatial orientation as the
        CT series.

    Returns
    -------
    computed_dose : dict
        Dictionary containing the numpy array describing the dose distribution, along with parameters relevant to the
        dose grid. The dictionary contains:
        - "ScaledDoseArray" : numpy.ndarray
            3D array of dose values.
        - "MaximumDose" : float
            Maximum dose value.
        - "DoseType" : str
            Type of dose (e.g., PHYSICAL).
        - "DoseUnits" : str
            Units of dose (e.g., Gy, cGy).
        - "DoseGridPlanarDimensions" : list of int
            Number of rows and columns of each dose grid slice.
        - "DoseGridFrames" : int
            Number of frames (slices) of the dose grid.
        - "DoseGridPlanarSpacing" : list of float
            In-plane pixel spacing, expressed in mm.
        - "DoseGridFrameOffsetVector" : list of float
            Offsets along the z-axis for each dose grid slice.
        - "DoseGridOrientationPatient" : list of float
            Spatial Orientation of the dose grid, with respect to the patient's coordinate system.
        - "DoseGridPositionPatient" : list of float
            X, Y and Z coordinates of the upper-left pixel of the first dose grid slice, with respect to the patient's
            coordinate system, expressed in mm.

    Assumptions
    -----------
    - The dicom_data attribute DoseGridScaling is present.
    - Dose is expressed in Gy units.
    - Dose refers to absorbed physical dose.
    - The dose distribution corresponds to a completed treatment plan
      (DICOM attribute DoseSummationType is equal to "PLAN")

    Limitations
    -----------
    - Dose expressed in units other than Gy is not supported.
    - Dose types other than absorbed physical dose are not supported.
    - Dose summation not based on a completed plan is not supported.
    - Dose grids that don't have the same spatial orientation as the CT series are not supported.
    - Multiple RTDOSE files within the same directory are not supported.
    """

    computed_dose_dir = os.path.join(patient_dir_path, "RTDOSE")

    filenames = os.listdir(computed_dose_dir)

    for filename in filenames:

        if not filename.lower().endswith(".dcm"):

            continue

        else:

            compute_dose_filename = filename

    computed_dose_path = os.path.join(computed_dose_dir, compute_dose_filename)
    computed_dose = pydicom.dcmread(computed_dose_path)

    if computed_dose.FrameOfReferenceUID != ct_series_frame_of_reference_uid:

        raise ValueError("There was a frame of reference mismatch. Different frames of reference are not supported.")

    if not np.allclose(computed_dose.ImageOrientationPatient, ct_series_orientation, rtol = 0, atol = 0.01):

        raise ValueError("There was an orientation mismatch. Dose grids that have different orientation than the CT series"
                         " are not supported.")

    computed_dose_distribution = np.array(computed_dose.pixel_array * computed_dose.DoseGridScaling, dtype = np.float64)

    computed_dose = {"ScaledDoseArray" : computed_dose_distribution,
                     "MaximumDose" : np.max(computed_dose_distribution),
                     "DoseType" : computed_dose.DoseType,
                     "DoseUnits" : computed_dose.DoseUnits,
                     "DoseGridPlanarDimensions" : [computed_dose.Rows, computed_dose.Columns],
                     "DoseGridFrames" : computed_dose.NumberOfFrames,
                     "DoseGridPlanarSpacing" : computed_dose.PixelSpacing,
                     "DoseGridFrameOffsetVector" : computed_dose.GridFrameOffsetVector,
                     "DoseGridOrientationPatient" : computed_dose.ImageOrientationPatient,
                     "DoseGridPositionPatient" : computed_dose.ImagePositionPatient}

    return computed_dose