import numpy as np
import pydicom
import os


def load_ct_series(patient_dir_path):
    """
    This function loads all the DICOM files (corresponding to the CT series) located in the "CT" subdirectory of
    patient's directory and sorts the slices superior to inferior. Furthermore, it extracts information regarding the
    series acquisition parameters.

    Parameters
    ----------
    patient_dir_path : str
        Path to the patient's directory containing a "CT" subdirectory with the DICOM files of the CT series.

    Returns
    -------
    ct_series : list of dict
        List of slices sorted superior to inferior. Each dictionary contains:
        - "Image" : numpy.ndarray
            2D array of HU values.
        - "ImagePositionPatient" : list of float
            X, Y and Z coordinates of the slice's upper-left pixel, with respect to the patient's coordinate system,
            expressed in mm.
        - "SOPInstanceUID" : str
            Unique identifier of the slice.

    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters. The dictionary contains:
        - "ImageDimensions" : list of int
            Number of rows and columns of each slice.
        - "ImagePlanarPositionPatient" : list of float
            X and Y coordinates of each slice's upper-left pixel, with respect to the patient's coordinate system,
            expressed in mm.
        - "PixelSpacing" : list of float
            In-plane pixel spacing, expressed in mm.
        - "SliceThickness" : float
            Nominal slice thickness, expressed in mm.
        - "ImageOrientationPatient" : list of float
            CT series spatial orientation, with respect to the patient's coordinate system.
        - "FrameOfReferenceUID" : str
            Unique identifier of the patient's coordinate system.
        - "SpacingBetweenSlices" : float
            Spacing between adjacent slices, expressed in mm.
    """

    ct_series_dir = os.path.join(patient_dir_path, "CT")

    filenames = os.listdir(ct_series_dir)

    ct_series = []

    for filename in filenames:

        if not filename.lower().endswith(".dcm"):

            continue

        ct_slice_path = os.path.join(ct_series_dir, filename)
        ct_slice_data = pydicom.dcmread(ct_slice_path)
        ct_slice = np.array((ct_slice_data.pixel_array * ct_slice_data.RescaleSlope) + ct_slice_data.RescaleIntercept, dtype = np.int16)

        # Some CT scanners use a padding technique to mark pixels that don't include valid image data. In such cases,
        # after the rescaling transformation, these pixels will correspond to extreme HU values. For the proper
        # visualization of patient's anatomy, clipping of HU values must be performed.
        ct_slice = np.clip(ct_slice, a_min = -1024, a_max = None)
        ct_series.append({"Image" : ct_slice, "ImagePositionPatient" : ct_slice_data.ImagePositionPatient,
                          "SOPInstanceUID" : ct_slice_data.SOPInstanceUID})

    # Sort the slices superior to inferior.
    ct_series = sorted(ct_series, key=lambda x: x["ImagePositionPatient"][2], reverse=True)

    # Extract the acquisition parameters from the last slice of the series (since all slices belong to the series,
    # they share the same parameters).
    ct_series_acquisition_parameters = {"ImageDimensions" : [ct_slice_data.Rows, ct_slice_data.Columns],
                                        "ImagePlanarPositionPatient": ct_slice_data.ImagePositionPatient[:2],
                                        "PixelSpacing" : ct_slice_data.PixelSpacing,
                                        "SliceThickness" : ct_slice_data.SliceThickness,
                                        "ImageOrientationPatient" : ct_slice_data.ImageOrientationPatient,
                                        "PatientPosition" : ct_slice_data.PatientPosition,
                                        "FrameOfReferenceUID" : ct_slice_data.FrameOfReferenceUID}

    # Check if SpacingBetweenSlices attribute is present.
    if "SpacingBetweenSlices" in ct_slice_data.dir():

        ct_series_acquisition_parameters["SpacingBetweenSlices"] = ct_slice_data.SpacingBetweenSlices

    else:

        # Calculate the spacing between adjacent slices.
        spacing_between_slices = np.diff([x["ImagePositionPatient"][2] for x in ct_series])

        # Check if spacing between adjacent slices is constant.
        constant_spacing = np.allclose(spacing_between_slices, spacing_between_slices[0], rtol = 0, atol = 0.01)

        if constant_spacing:

            ct_series_acquisition_parameters["SpacingBetweenSlices"] = np.abs(spacing_between_slices[0])

        else:

            raise ValueError("CT series of non constant slice spacing is not supported.")

    # Check if the CT series consists of adjacent slices.
    if not np.allclose(ct_series_acquisition_parameters["SliceThickness"],
                       ct_series_acquisition_parameters["SpacingBetweenSlices"], rtol = 0, atol = 0.01):

        raise ValueError("Non adjacent slices are not supported.")

    # Check ImageOrientationPatient and PatientPosition DICOM attribute values.
    if not (np.allclose(ct_series_acquisition_parameters["ImageOrientationPatient"], [1, 0, 0, 0, 1, 0], rtol = 0, atol = 0.01) and
            ct_series_acquisition_parameters["PatientPosition"] == "HFS"):

        raise ValueError("Only CT series with ImageOrientationPatient DICOM attribute equal to [1, 0, 0, 0, 1, 0]\n"
                         "and PatientPosition DICOM attribute equal to 'HFS' are supported.")

    return ct_series, ct_series_acquisition_parameters