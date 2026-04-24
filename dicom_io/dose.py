import numpy as np
import pydicom
import os


def load_dose(patient_dir_path, ct_series_frame_of_reference_uid, ct_series_orientation):
    """
    This function loads the DICOM RTDOSE file located in the "RTDOSE" subdirectory of patient's directory and applies
    the DoseGridScaling factor in order to obtain the actual dose distribution. Furthermore, it extracts information
    regarding the dose grid parameters.

    Parameters
    ----------
    patient_dir_path : str
        Path to the patient's directory containing an "RTDOSE" subdirectory with the DICOM RTDOSE file.

    ct_series_frame_of_reference_uid : str
        Unique identifier of the patient's coordinate system, associated with the CT series. Used to verify that the
        dose grid origin is expressed with regards to the same coordinate system.

    ct_series_orientation : list of float
        CT series spatial orientation, with respect to the patient's coordinate system. Used to verify that the dose
        grid has the same spatial orientation as the CT series.

    Returns
    -------
    dose : dict
        Dictionary containing the numpy array describing the dose distribution, along with parameters relevant to the
        dose grid. The dictionary contains:
        - "DoseDistribution" : numpy.ndarray
            3D array of dose values.
        - "DoseType" : str
            Type of dose (e.g., PHYSICAL).
        - "DoseUnits" : str
            Units of dose (e.g., Gy, cGy).
        - "DoseGridPlanarDimensions" : list of int
            Number of rows and columns of each dose grid plane.
        - "DoseGridFrames" : int
            Number of frames (planes) of the dose grid.
        - "DoseGridPlanarSpacing" : list of float
            In-plane pixel spacing, expressed in mm.
        - "DoseGridFrameOffsetVector" : list of float
            Offsets along the z-axis for each dose grid plane.
        - "DoseGridOrientationPatient" : list of float
            Spatial orientation of the dose grid, with respect to the patient's coordinate system.
        - "DoseGridPositionPatient" : list of float
            X, Y and Z coordinates of the upper-left pixel of the first dose grid plane, with respect to the patient's
            coordinate system, expressed in mm.
    """

    dose_dir = os.path.join(patient_dir_path, "RTDOSE")

    filenames = os.listdir(dose_dir)

    for filename in filenames:

        if not filename.lower().endswith(".dcm"):

            continue

        else:

            dose_filename = filename

    dose_path = os.path.join(dose_dir, dose_filename)
    dose_data = pydicom.dcmread(dose_path)

    if dose_data.FrameOfReferenceUID != ct_series_frame_of_reference_uid:

        raise ValueError("There was a frame of reference mismatch. Different frames of reference are not supported.")

    if not np.allclose(dose_data.ImageOrientationPatient, ct_series_orientation, rtol = 0, atol = 0.01):

        raise ValueError("There was an orientation mismatch. Dose grids that have different spatial orientation than\n"
                         "the CT series (with respect to the patient's coordinate system) are not supported.")

    dose_distribution = np.array(dose_data.pixel_array * dose_data.DoseGridScaling, dtype = np.float64)

    dose = {"DoseDistribution" : dose_distribution,
            "DoseType" : dose_data.DoseType,
            "DoseUnits" : dose_data.DoseUnits,
            "DoseGridPlanarDimensions" : [dose_data.Rows, dose_data.Columns],
            "DoseGridFrames" : dose_data.NumberOfFrames,
            "DoseGridPlanarSpacing" : dose_data.PixelSpacing,
            "DoseGridFrameOffsetVector" : dose_data.GridFrameOffsetVector,
            "DoseGridOrientationPatient" : dose_data.ImageOrientationPatient,
            "DoseGridPositionPatient" : dose_data.ImagePositionPatient}

    return dose