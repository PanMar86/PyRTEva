import numpy as np
from scipy.interpolate import RegularGridInterpolator


def generate_dose_maps(ct_series, ct_series_acquisition_parameters, computed_dose, interpolation_method):
    """
    This function generates planar and volumetric dose maps aligned to the CT series. Essentially, it evaluates the
    spatial coincidence between the dose grid and the CT series. If the dose grid planes and the slices of the CT series
    are perfectly coincident, no interpolation is performed. If they are coincident along the z-axis but not planar
    aligned, 2D planar interpolation is performed (slice by slice) to generate dose maps aligned to the CT series.

    Parameters
    ----------
    ct_series : list of dict
        List of slices sorted superior to inferior.

    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    computed_dose : dict
        Dictionary containing the numpy array describing the dose distribution, along with parameters relevant to the
        dose grid.

    interpolation_method : str
        String representing the interpolation method used by the planar_interpolation function.

    Returns
    -------
    dose_maps : dict
        Dictionary containing the generated dose maps. The dictionary contains:
        - "PlanarDoseMaps" : list of dict
            List of 2D dose maps corresponding to the slices of the CT series. Each dictionary contains:
            - "DoseMap" : numpy.ndarray
                2D dose map aligned to a CT slice.
            - "ReferencedSOPInstanceUID" : str
                Unique identifier of the corresponding slice.
        - "VolumetricDoseMap" : numpy.ndarray
            3D dose map, aligned to the CT series.

    Limitations
    -----------
    - Only 2D planar interpolation is supported (when z-axis coincidence exists).
    """

    planar_alignment = verify_planar_alignment(ct_series_acquisition_parameters, computed_dose)
    z_axis_coincidence = verify_z_axis_coincidence(ct_series, ct_series_acquisition_parameters, computed_dose)
    perfect_coincidence= planar_alignment and z_axis_coincidence

    if perfect_coincidence:

        print("The dose grid planes and the slices of the CT series are perfectly coincident.\n"
              "Interpolation is not required.")

        volumetric_dose_map = np.zeros((len(ct_series), ct_series_acquisition_parameters["ImageDimensions"][0],
                                        ct_series_acquisition_parameters["ImageDimensions"][1]), dtype = np.float64)

        planar_dose_maps = []

        for grid_frame_index in range(computed_dose["DoseGridFrames"]):

            if computed_dose["DoseGridPositionPatient"][2] == ct_series[-1]["ImagePositionPatient"][2]:

                planar_dose_maps.append({"DoseMap": computed_dose["ScaledDoseArray"][grid_frame_index, :, :],
                                         "ReferencedSOPInstanceUID": ct_series[-1 - grid_frame_index]["SOPInstanceUID"]})
                volumetric_dose_map[-1 - grid_frame_index, :, :] = computed_dose["ScaledDoseArray"][grid_frame_index, :, :]

            elif computed_dose["DoseGridPositionPatient"][2] == ct_series[0]["ImagePositionPatient"][2]:

                planar_dose_maps.append({"DoseMap": computed_dose["ScaledDoseArray"][grid_frame_index, :, :],
                                         "ReferencedSOPInstanceUID": ct_series[grid_frame_index]["SOPInstanceUID"]})
                volumetric_dose_map[grid_frame_index, :, :] = computed_dose["ScaledDoseArray"][grid_frame_index, :, :]

        dose_maps = {"PlanarDoseMaps": planar_dose_maps,
                     "VolumetricDoseMap": volumetric_dose_map}

    elif z_axis_coincidence:

        print("The dose grid planes and the slices of the CT series are z-axis coincident.\n"
              "Planar (2D) interpolation is being performed. Please wait...")

        volumetric_dose_map = np.zeros((len(ct_series), ct_series_acquisition_parameters["ImageDimensions"][0],
                                        ct_series_acquisition_parameters["ImageDimensions"][1]), dtype = np.float64)
        planar_dose_maps = []

        # Map the upper-left pixel of the dose grid planes (origin) to the slices of the CT series.
        dose_grid_plane_origin_slice_coordinates = [np.round(np.abs((ct_series_acquisition_parameters["ImagePlanarPositionPatient"][1] -
                                                                     computed_dose["DoseGridPositionPatient"][1]) /
                                                                    ct_series_acquisition_parameters["PixelSpacing"][0]), decimals = 0).astype(np.uint16),
                                                    np.round(np.abs((ct_series_acquisition_parameters["ImagePlanarPositionPatient"][0] -
                                                                     computed_dose["DoseGridPositionPatient"][0]) /
                                                                    ct_series_acquisition_parameters["PixelSpacing"][1]), decimals = 0).astype(np.uint16)]

        for grid_frame_index in range(computed_dose["DoseGridFrames"]):

            planar_dose_map = np.zeros((ct_series_acquisition_parameters["ImageDimensions"][0],
                                        ct_series_acquisition_parameters["ImageDimensions"][1]), dtype = np.float64)

            # Perform 2D (planar) interpolation, so that the spatial resolution of the dose grid planes matches the spatial
            # resolution of the slices of the CT series.
            resampled_dose_grid_plane = planar_interpolation(ct_series_acquisition_parameters, computed_dose, grid_frame_index, interpolation_method)
            planar_dose_map[dose_grid_plane_origin_slice_coordinates[0] :
                            dose_grid_plane_origin_slice_coordinates[0] +
                            resampled_dose_grid_plane.shape[0],
                            dose_grid_plane_origin_slice_coordinates[1] :
                            dose_grid_plane_origin_slice_coordinates[1] +
                            resampled_dose_grid_plane.shape[1]] = resampled_dose_grid_plane

            if computed_dose["DoseGridPositionPatient"][2] == ct_series[-1]["ImagePositionPatient"][2]:

                planar_dose_maps.append({"DoseMap": planar_dose_map,
                                         "ReferencedSOPInstanceUID" : ct_series[-1 - grid_frame_index]["SOPInstanceUID"]})
                volumetric_dose_map[-1 - grid_frame_index, :, :] = planar_dose_map

            elif computed_dose["DoseGridPositionPatient"][2] == ct_series[0]["ImagePositionPatient"][2]:

                planar_dose_maps.append({"DoseMap": planar_dose_map,
                                         "ReferencedSOPInstanceUID" : ct_series[grid_frame_index]["SOPInstanceUID"]})
                volumetric_dose_map[grid_frame_index, :, :] = planar_dose_map

        dose_maps = {"PlanarDoseMaps": planar_dose_maps,
                     "VolumetricDoseMap": volumetric_dose_map}

    elif planar_alignment:
        raise ValueError("The dose grid planes and the slices of the CT series are planar aligned but not z-axis coincident.\n"
                         "Volume (3D) interpolation is not supported.")

    else:
        raise ValueError("The dose grid planes and the slices of the CT series are neither planar aligned nor z-axis coincident.\n"
                         "Volume (3D) interpolation is not supported.")

    return dose_maps


def verify_planar_alignment(ct_series_acquisition_parameters, computed_dose):
    """
    This function checks whether the dose grid planes are planar aligned with the slices of the CT series. It explicitly
    checks properties such as plane origin, in-plane spacing and plane dimensions.

    Parameters
    ----------
    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    computed_dose : dict
        Dictionary containing the numpy array describing the dose distribution, along with parameters relevant to the
        dose grid.

    Returns
    -------
    planar_alignment : bool
        True if the dose grid planes and the slices of the CT series are planar aligned, False otherwise.
    """

    origin_check = np.allclose(ct_series_acquisition_parameters["ImagePlanarPositionPatient"],
                               computed_dose["DoseGridPositionPatient"][0:2], rtol = 0, atol = 0.01)

    in_plane_spacing_check = np.allclose(ct_series_acquisition_parameters["PixelSpacing"],
                                         computed_dose["DoseGridPlanarSpacing"], rtol = 0, atol = 0.01)

    dimensions_check = ct_series_acquisition_parameters["ImageDimensions"] == computed_dose["DoseGridPlanarDimensions"]

    planar_alignment = origin_check and in_plane_spacing_check and dimensions_check

    return planar_alignment


def verify_z_axis_coincidence(ct_series, ct_series_acquisition_parameters, computed_dose):
    """
    This function checks whether the dose grid planes are z-axis coincident with the slices of the CT series (planar
    alignment is assessed via verify_planar_alignment function). It performs multiple consistency checks including
    boundary coincidence check, dose grid plane spacing and CT series slice spacing comparison, and equality check
    between the number of dose grid planes and the number of the slices of the CT series.

    Parameters
    ----------
    ct_series : list of dict
        List of slices sorted superior to inferior.

    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    computed_dose : dict
        Dictionary containing the numpy array describing the dose distribution, along with parameters relevant to the
        dose grid.

    Returns
    -------
    z_axis_coincidence : bool
        True if the dose grid planes are coincident with the slices of the CT series along the z-axis, False otherwise.
    """

    # Determine the type of the DoseGridFrameOffsetVector
    # https://dicom.innolitics.com/ciods/rt-dose/rt-dose/3004000c

    if computed_dose["DoseGridFrameOffsetVector"][0] == 0:

        # Check if the first plane of the dose grid is z-axis coincident with the first or the last slice of the CT series.
        boundary_coincidence_check = np.allclose(computed_dose["DoseGridPositionPatient"][2],
                                                 ct_series[-1]["ImagePositionPatient"][2], rtol = 0, atol = 0.01) or \
                                     np.allclose(computed_dose["DoseGridPositionPatient"][2],
                                                 ct_series[0]["ImagePositionPatient"][2], rtol = 0, atol = 0.01)

        # Check if the z-spacing between the dose planes is constant and equal to the spacing between the slices of the
        # CT series.
        z_axis_spacing_coincidence_check = verify_z_axis_spacing_coincidence(computed_dose["DoseGridFrameOffsetVector"],
                                                                             ct_series_acquisition_parameters)

        # Check if the number of the slices of the CT series is equal to the number of dose grid planes.
        slices_frames_check = len(ct_series) == computed_dose["DoseGridFrames"]

        z_axis_coincidence = boundary_coincidence_check and z_axis_spacing_coincidence_check and slices_frames_check

    elif computed_dose["DoseGridFrameOffsetVector"][0] == computed_dose["DoseGridPositionPatient"][2]:

        slices_z_axis_position = sorted([x["ImagePositionPatient"][2] for x in ct_series])
        dose_planes_z_axis_position = sorted(computed_dose["DoseGridFrameOffsetVector"])

        z_axis_coincidence = slices_z_axis_position == dose_planes_z_axis_position

    return z_axis_coincidence


def verify_z_axis_spacing_coincidence(grid_frame_offset_vector, ct_series_acquisition_parameters):
    """
    This function checks whether the spacing between dose grid planes (as defined by the GridFrameOffsetVector parameter)
    is constant and matches the spacing between the slices of the CT series.

    Parameters
    ----------
    grid_frame_offset_vector : list of float
        List-like object, containing the z-offsets of the dose grid planes relative to the first one, expressed in mm.

    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    Returns
    -------
    z_axis_spacing_coincidence : bool
        True if the spacing between all consecutive dose grid planes is constant and equal to the spacing between the
        slices of the CT series, False otherwise.
    """

    # Calculate the differences between the offsets.
    offsets_differences = np.diff(grid_frame_offset_vector)

    # Check if the spacing between the dose grid planes is constant.
    constant_spacing = np.allclose(offsets_differences, offsets_differences[0], rtol = 0, atol = 0.01)

    # Provided that the spacing between the dose grid planes is constant,
    # check if it is equal to the spacing between the slices of the CT series.
    if constant_spacing:

        if np.allclose(np.abs(offsets_differences[0]), ct_series_acquisition_parameters["SpacingBetweenSlices"],
                       rtol = 0, atol = 0.01):

            z_axis_spacing_coincidence = True

        else:

            z_axis_spacing_coincidence = False

    else:

        raise ValueError("Dose grid plane spacing is not constant. Non constant plane spacing is not supported.")

    return z_axis_spacing_coincidence


def planar_interpolation(ct_series_acquisition_parameters, computed_dose, grid_frame_index, interpolation_method):
    """
    This function resamples a dose grid plane so that its spatial resolution matches that of the slices of the CT series.

    Parameters
    ----------
    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    computed_dose : dict
        Dictionary containing the numpy array describing the dose distribution, along with parameters relevant to the
        dose grid.

    grid_frame_index : int
        Index of the dose grid plane to resample.

    interpolation_method : str
        String representing the interpolation method used by the RegularGridInterpolator object. Supported methods are:
        - "linear"
        - "nearest"
        - "slinear"
        - "cubic"
        - "quintic"
        - "pchip"

    Returns
    -------
    resampled_dose_plane : np.ndarray
        2D array representing the resampled dose grid plane.
    """

    # First, construct the RegularGridInterpolator object based on the X and Y coordinates of the points of the dose
    # grid plane. The origin is defined as the center of the upper-left pixel of the dose grid plane. X-axis is parallel
    # to the rows whereas Y-axis is parallel to the columns of the dose grid plane.
    dose_plane_points_x_coordinate = np.array([x * computed_dose["DoseGridPlanarSpacing"][1]
                                               for x in range(computed_dose["DoseGridPlanarDimensions"][1])], dtype = np.float32)
    dose_plane_points_y_coordinate = np.array([x * computed_dose["DoseGridPlanarSpacing"][0]
                                               for x in range(computed_dose["DoseGridPlanarDimensions"][0])], dtype = np.float32)
    interpolator = RegularGridInterpolator((dose_plane_points_y_coordinate, dose_plane_points_x_coordinate),
                                           computed_dose["ScaledDoseArray"][grid_frame_index, :, :], method = interpolation_method)

    # Define the points of the resampled dose grid plane. The resampled plane covers approximately (due to the rounding
    # operation) the same physical space as the original dose plane.
    dose_plane_x_axis_length = (computed_dose["DoseGridPlanarDimensions"][1] - 1) * computed_dose["DoseGridPlanarSpacing"][1]
    dose_plane_y_axis_length = (computed_dose["DoseGridPlanarDimensions"][0] - 1) * computed_dose["DoseGridPlanarSpacing"][0]
    resampled_dose_plane_points_x_coordinate = np.array([x * ct_series_acquisition_parameters["PixelSpacing"][1]
                                                         for x in range(np.round((dose_plane_x_axis_length /
                                                                                  ct_series_acquisition_parameters["PixelSpacing"][1]),
                                                                                 decimals = 0).astype(np.uint16))], dtype = np.float32)
    resampled_dose_plane_points_y_coordinate = np.array([x * ct_series_acquisition_parameters["PixelSpacing"][0]
                                                         for x in range(np.round((dose_plane_y_axis_length /
                                                                                  ct_series_acquisition_parameters["PixelSpacing"][0]),
                                                                                 decimals = 0).astype(np.uint16))], dtype = np.float32)

    resampled_dose_plane_points_y_coordinates, resampled_dose_plane_points_x_coordinates = np.meshgrid(resampled_dose_plane_points_y_coordinate,
                                                                                                       resampled_dose_plane_points_x_coordinate, indexing="ij")
    resampled_dose_plane_points_x_coordinates = resampled_dose_plane_points_x_coordinates.ravel()
    resampled_dose_plane_points_y_coordinates = resampled_dose_plane_points_y_coordinates.ravel()
    resampled_dose_plane_points_coordinates = np.array([resampled_dose_plane_points_y_coordinates,
                                                        resampled_dose_plane_points_x_coordinates]).T

    # Resample the dose grid plane.
    resampled_dose_plane_values = interpolator(resampled_dose_plane_points_coordinates)

    # Reconstruct the dose grid plane.
    resampled_dose_plane = np.reshape(resampled_dose_plane_values,(resampled_dose_plane_points_y_coordinate.shape[0],
                                                                   resampled_dose_plane_points_x_coordinate.shape[0]))

    # Some interpolation methods might produce slightly negative values (with no physical interpretation) in the very
    # low dose region.
    resampled_dose_plane[resampled_dose_plane < 0] = 0

    return resampled_dose_plane