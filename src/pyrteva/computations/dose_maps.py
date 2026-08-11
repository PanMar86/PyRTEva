import logging

import numpy as np
from scipy.interpolate import RegularGridInterpolator


def generate_dose_maps(ct_series, ct_series_acquisition_parameters, dose, dose_grid_interpolation_method):
    """
    This function generates planar and volumetric dose maps aligned to the CT series. Essentially, it evaluates the
    spatial alignment between the dose grid and the CT series. If the dose grid planes and the slices of the CT series
    are planarly and z axis (fully or partially) aligned, no interpolation is performed. If they are fully or partially
    aligned along the z-axis but not planarly aligned, 2D planar interpolation is performed (slice by slice) to generate
    dose maps aligned to the CT series.

    Parameters
    ----------
    ct_series : list of dict
        List of slices sorted superior to inferior.

    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    dose : dict
        Dictionary containing the numpy array describing the dose distribution, along with parameters relevant to the
        dose grid.

    dose_grid_interpolation_method : str
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
    """

    logger = logging.getLogger(__name__)

    # Determine the alignment type (if any).
    planar_alignment = verify_planar_alignment(ct_series_acquisition_parameters, dose)
    z_axis_alignment = verify_z_axis_alignment(ct_series, ct_series_acquisition_parameters, dose)

    if planar_alignment and (not z_axis_alignment):

        logger.error("The dose grid and the CT series are planarly aligned but not z axis aligned.\n"
                     "Volume (3D) interpolation is not currently supported.")
        raise ValueError("The dose grid and the CT series are planarly aligned but not z axis aligned.\n"
                         "Volume (3D) interpolation is not currently supported.")

    elif not planar_alignment and (not z_axis_alignment):

        logger.error("The dose grid and the CT series are neither planarly nor z axis aligned.\n"
                     "Volume (3D) interpolation is not currently supported.")
        raise ValueError("The dose grid and the CT series are neither planarly nor z axis aligned.\n"
                         "Volume (3D) interpolation is not currently supported.")

    elif z_axis_alignment:

        # Match the slices of the CT series with the corresponding dose grid planes. In case of no associated dose grid
        # plane, a dose map corresponding to zero dose is applied.
        ct_slices_z_positions = np.array([ct_slice["ImagePositionPatient"][2] for ct_slice in ct_series])

        # Determine the type of the DoseGridFrameOffsetVector.
        # https://dicom.innolitics.com/ciods/rt-dose/rt-dose/3004000c
        if dose["DoseGridFrameOffsetVector"][0] == 0:

            dose_grid_planes_z_positions = (np.array(dose["DoseGridFrameOffsetVector"]) +
                                            dose["DoseGridPositionPatient"][2])

        elif dose["DoseGridFrameOffsetVector"][0] == dose["DoseGridPositionPatient"][2]:

            dose_grid_planes_z_positions = np.array(dose["DoseGridFrameOffsetVector"])

        # For each slice of the CT series, store the index of the corresponding dose grid plane. An index value of -1
        # shows the absense of a dose grid plane for this particular slice.
        dose_grid_planes_indices = -1 * np.ones(len(ct_series), dtype=np.int16)

        for ct_slice_index in range(len(ct_series)):

            if np.any(np.isclose(ct_slices_z_positions[ct_slice_index], dose_grid_planes_z_positions, rtol=0, atol=0.01)):

                dose_grid_planes_indices[ct_slice_index] = np.argmax(np.isclose(ct_slices_z_positions[ct_slice_index],
                                                                                dose_grid_planes_z_positions, rtol=0, atol=0.01))

        # Construct the planar and the volumetric dose maps.
        volumetric_dose_map = np.zeros((len(ct_series), ct_series_acquisition_parameters["ImageDimensions"][0],
                                        ct_series_acquisition_parameters["ImageDimensions"][1]), dtype=np.float64)
        planar_dose_map = np.zeros((ct_series_acquisition_parameters["ImageDimensions"][0],
                                    ct_series_acquisition_parameters["ImageDimensions"][1]), dtype=np.float64)
        planar_dose_maps = []

        if planar_alignment:

            # The dose grid planes and the slices of the CT series are planarly aligned and z axis (partially or fully)
            # aligned. Interpolation is not required.
            for ct_slice_index in range(len(ct_series)):

                if dose_grid_planes_indices[ct_slice_index] != -1:

                    planar_dose_maps.append({"DoseMap": dose["DoseDistribution"][dose_grid_planes_indices[ct_slice_index], :, :],
                                             "ReferencedSOPInstanceUID": ct_series[ct_slice_index]["SOPInstanceUID"]})
                    volumetric_dose_map[ct_slice_index, :, :] = dose["DoseDistribution"][dose_grid_planes_indices[ct_slice_index], :, :]

                else:

                    planar_dose_maps.append({"DoseMap": planar_dose_map,
                                             "ReferencedSOPInstanceUID": ct_series[ct_slice_index]["SOPInstanceUID"]})

        elif not planar_alignment:

            # The dose grid planes and the slices of the CT series are z-axis aligned (partially or fully). Planar (2D)
            # interpolation will be performed.

            # Map the upper-left pixel of the dose grid planes (origin) to the slices of the CT series.
            dose_grid_plane_origin_slice_coordinates = [np.round(np.abs((ct_series_acquisition_parameters["ImagePlanarPositionPatient"][1] -
                                                                         dose["DoseGridPositionPatient"][1]) /
                                                                        ct_series_acquisition_parameters["PixelSpacing"][0]), decimals=0).astype(np.uint16),
                                                        np.round(np.abs((ct_series_acquisition_parameters["ImagePlanarPositionPatient"][0] -
                                                                         dose["DoseGridPositionPatient"][0]) /
                                                                        ct_series_acquisition_parameters["PixelSpacing"][1]), decimals=0).astype(np.uint16)]

            for ct_slice_index in range(len(ct_series)):

                if dose_grid_planes_indices[ct_slice_index] != -1:

                    # Perform 2D (planar) interpolation, so that the spatial resolution of the dose grid planes matches
                    # the spatial resolution of the slices of the CT series.
                    resampled_dose_grid_plane = planar_interpolation(ct_series_acquisition_parameters, dose, dose_grid_planes_indices[ct_slice_index], dose_grid_interpolation_method)
                    planar_dose_map[dose_grid_plane_origin_slice_coordinates[0] : dose_grid_plane_origin_slice_coordinates[0] + resampled_dose_grid_plane.shape[0],
                                    dose_grid_plane_origin_slice_coordinates[1] : dose_grid_plane_origin_slice_coordinates[1] + resampled_dose_grid_plane.shape[1]] = resampled_dose_grid_plane

                planar_dose_maps.append({"DoseMap": planar_dose_map, "ReferencedSOPInstanceUID" : ct_series[ct_slice_index]["SOPInstanceUID"]})
                volumetric_dose_map[ct_slice_index, :, :] = planar_dose_map


        dose_maps = {"PlanarDoseMaps": planar_dose_maps,
                     "VolumetricDoseMap": volumetric_dose_map}

        logger.info("Planar and volumetric dose maps have been successfully generated.")

        return dose_maps


def verify_planar_alignment(ct_series_acquisition_parameters, dose):
    """
    This function checks whether the dose grid planes are planarly aligned with the slices of the CT series. It explicitly
    checks properties such as plane origin, in-plane spacing and plane dimensions.

    Parameters
    ----------
    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    dose : dict
        Dictionary containing the numpy array describing the dose distribution, along with parameters relevant to the
        dose grid.

    Returns
    -------
    planar_alignment : bool
        True if the dose grid planes and the slices of the CT series are planarly aligned, False otherwise.
    """

    origin_equality = np.allclose(ct_series_acquisition_parameters["ImagePlanarPositionPatient"],
                                  dose["DoseGridPositionPatient"][0:2], rtol = 0, atol = 0.01)

    in_plane_spacing_equality = np.allclose(ct_series_acquisition_parameters["PixelSpacing"],
                                            dose["DoseGridPlanarSpacing"], rtol = 0, atol = 0.01)

    dimensions_equality = ct_series_acquisition_parameters["ImageDimensions"] == dose["DoseGridPlanarDimensions"]

    planar_alignment = origin_equality and in_plane_spacing_equality and dimensions_equality

    return planar_alignment


def verify_z_axis_alignment(ct_series, ct_series_acquisition_parameters, dose):
    """
    This function checks whether the dose grid planes are z-axis aligned with the slices of the CT series (planar
    alignment is assessed via verify_planar_alignment function). It performs multiple consistency checks including dose
    grid and CT series z spacing equality check, number of dose grid planes and number of CT series slices equality check, etc.

    Parameters
    ----------
    ct_series : list of dict
        List of slices sorted superior to inferior.

    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    dose : dict
        Dictionary containing the numpy array describing the dose distribution, along with parameters relevant to the
        dose grid.

    Returns
    -------
    z_axis_alignment : bool
        True in case of alignment, False otherwise.
    """

    z_axis_alignment = False

    # Check if the z-spacing between the dose grid planes is constant and equal to the spacing between the slices of the CT series.
    z_axis_spacing_equality = verify_z_axis_spacing_equality(dose["DoseGridFrameOffsetVector"], ct_series_acquisition_parameters)

    if not z_axis_spacing_equality:

        return z_axis_alignment

    else:

        ct_slices_z_positions = np.array([ct_slice["ImagePositionPatient"][2] for ct_slice in ct_series])

        # Determine the type of the DoseGridFrameOffsetVector
        # https://dicom.innolitics.com/ciods/rt-dose/rt-dose/3004000c
        if dose["DoseGridFrameOffsetVector"][0] == 0:

            dose_grid_planes_z_positions = np.array(dose["DoseGridFrameOffsetVector"]) + dose["DoseGridPositionPatient"][2]

        elif dose["DoseGridFrameOffsetVector"][0] == dose["DoseGridPositionPatient"][2]:

            dose_grid_planes_z_positions = np.array(dose["DoseGridFrameOffsetVector"])

        # Check if at least one dose grid plane coincides with a slice of the CT series.
        for dose_grid_plane_z_position in dose_grid_planes_z_positions:

            if np.any(np.isclose(dose_grid_plane_z_position, ct_slices_z_positions, rtol=0, atol=0.01)):

                z_axis_alignment = True

                break

        return z_axis_alignment


def verify_z_axis_spacing_equality(grid_frame_offset_vector, ct_series_acquisition_parameters):
    """
    This function checks whether the spacing between dose grid planes (as defined by the GridFrameOffsetVector parameter)
    is constant and matches the spacing between the slices of the CT series.

    Parameters
    ----------
    grid_frame_offset_vector : list of float
        List containing either the z-offsets of the dose grid planes relative to the first one, or the absolute z-positions
        of the dose grid planes with respect to the patient's coordinate system, expressed in mm.

    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    Returns
    -------
    z_axis_spacing_equality : bool
        True if the spacing between all consecutive dose grid planes is constant and equal to the spacing between the
        slices of the CT series, False otherwise.
    """

    logger = logging.getLogger(__name__)

    # Calculate the differences between the offsets.
    offsets_differences = np.diff(grid_frame_offset_vector)

    # Check if the spacing between the dose grid planes is constant.
    constant_spacing = np.allclose(offsets_differences, offsets_differences[0], rtol = 0, atol = 0.01)

    # Provided that the spacing between the dose grid planes is constant, check if it is equal to the spacing between
    # the slices of the CT series.
    if constant_spacing:

        if np.allclose(np.abs(offsets_differences[0]), ct_series_acquisition_parameters["SpacingBetweenSlices"], rtol = 0, atol = 0.01):

            z_axis_spacing_equality = True

        else:

            z_axis_spacing_equality = False

    else:

        logger.error("Dose grid plane spacing is not constant. Non constant plane spacing is not supported.")
        raise ValueError("Dose grid plane spacing is not constant. Non constant plane spacing is not supported.")

    return z_axis_spacing_equality


def planar_interpolation(ct_series_acquisition_parameters, dose, grid_frame_index, interpolation_method):
    """
    This function resamples a dose grid plane so that its spatial resolution matches that of the slices of the CT series.

    Parameters
    ----------
    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    dose : dict
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
    dose_plane_points_x_coordinate = np.array([x * dose["DoseGridPlanarSpacing"][1]
                                               for x in range(dose["DoseGridPlanarDimensions"][1])], dtype = np.float32)
    dose_plane_points_y_coordinate = np.array([x * dose["DoseGridPlanarSpacing"][0]
                                               for x in range(dose["DoseGridPlanarDimensions"][0])], dtype = np.float32)
    interpolator = RegularGridInterpolator((dose_plane_points_y_coordinate, dose_plane_points_x_coordinate),
                                           dose["DoseDistribution"][grid_frame_index, :, :], method = interpolation_method)

    # Define the points of the resampled dose grid plane. The resampled plane covers approximately (due to the rounding
    # operation) the same physical space as the original dose plane.
    dose_plane_x_axis_length = (dose["DoseGridPlanarDimensions"][1] - 1) * dose["DoseGridPlanarSpacing"][1]
    dose_plane_y_axis_length = (dose["DoseGridPlanarDimensions"][0] - 1) * dose["DoseGridPlanarSpacing"][0]
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