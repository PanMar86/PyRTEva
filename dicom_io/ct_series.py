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
        - "HUArray" : numpy.ndarray
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
            X and Y coordinates of the slice's upper-left pixel, with respect to the patient's coordinate system,
            expressed in mm.
        - "PixelSpacing" : list of float
            In-plane pixel spacing, expressed in mm.
        - "SliceThickness" : float
            Nominal slice thickness, expressed in mm.
        - "ImageOrientationPatient" : list of float
            CT series spatial orientation, with respect to the patient's coordinate system.
        - "FrameOfReferenceUID" : str
            Unique identifier of the CT series' frame of reference
        - "SpacingBetweenSlices" : float
            Spacing between adjacent slices, expressed in mm.

    Limitations
    -----------
    - Slice spatial orientations that do not correspond to HFS patient positioning with zero gantry tilt, are not
      supported.
    - Slices that are not adjacent to each other are not supported.
    - Multiple CT series within the same directory are not supported.
    """

    ct_series_dir = os.path.join(patient_dir_path, "CT")

    filenames = os.listdir(ct_series_dir)

    # Load CT series
    ct_series = []

    for filename in filenames:

        if not filename.lower().endswith(".dcm"):

            continue

        slice_path = os.path.join(ct_series_dir, filename)
        ct_slice = pydicom.dcmread(slice_path)
        hu_array = np.array((ct_slice.pixel_array * ct_slice.RescaleSlope) + ct_slice.RescaleIntercept, dtype = np.int16)
        ct_series.append({"HUArray" : hu_array,
                          "ImagePositionPatient" : ct_slice.ImagePositionPatient,
                          "SOPInstanceUID" : ct_slice.SOPInstanceUID})

    # Sort the slices superior to inferior.
    ct_series = sorted(ct_series, key=lambda x: x["ImagePositionPatient"][2], reverse=True)

    # Extract the acquisition parameters from the last slice of the series (since all slices belong to the series,
    # they share the same parameters).
    ct_series_acquisition_parameters = {"ImageDimensions" : [ct_slice.Rows, ct_slice.Columns],
                                        "ImagePlanarPositionPatient": ct_slice.ImagePositionPatient[:2],
                                        "PixelSpacing" : ct_slice.PixelSpacing,
                                        "SliceThickness" : ct_slice.SliceThickness,
                                        "ImageOrientationPatient" : ct_slice.ImageOrientationPatient,
                                        "FrameOfReferenceUID" : ct_slice.FrameOfReferenceUID}

    # Check if SpacingBetweenSlices attribute is present.
    if "SpacingBetweenSlices" in ct_slice.dir():

        ct_series_acquisition_parameters["SpacingBetweenSlices"] = ct_slice.SpacingBetweenSlices

    else:

        # Calculate the spacing between adjacent slices.
        spacing_between_slices = np.diff([x["ImagePositionPatient"][2] for x in ct_series])

        # Check if spacing between adjacent slices is constant
        constant_spacing = np.allclose(spacing_between_slices, spacing_between_slices[0], rtol = 0, atol = 0.01)

        if constant_spacing:

            ct_series_acquisition_parameters["SpacingBetweenSlices"] = np.abs(spacing_between_slices[0])

        else:

            raise ValueError("Slice spacing is not constant. Non constant slice spacing is not supported.")

    # Check if the CT series consists of adjacent slices.
    if not np.allclose(ct_series_acquisition_parameters["SliceThickness"],
                       ct_series_acquisition_parameters["SpacingBetweenSlices"], rtol = 0, atol = 0.01):

        raise ValueError("Non adjacent slices are not supported")

    # Check if the CT series spatial orientation corresponds to HFS patient positioning with zero gantry tilt.
    hfs_slice_orientation = [1, 0, 0, 0, 1, 0]

    if not np.allclose(ct_series_acquisition_parameters["ImageOrientationPatient"], hfs_slice_orientation,
                       rtol = 0, atol = 0.01):

        raise ValueError(f"ImageOrientationPatient = {ct_series_acquisition_parameters["ImageOrientationPatient"]} != {hfs_slice_orientation}\n"
                          "Only the slice orientation that corresponds to HFS patient positioning with zero gantry tilt "
                          "is supported.")

    return ct_series, ct_series_acquisition_parameters