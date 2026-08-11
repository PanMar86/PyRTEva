import logging

import numpy as np
from skimage.draw import polygon


def generate_structures_masks(ct_series, ct_series_acquisition_parameters, structures):
    """
    This function converts the contour points of each structure into 2D masks (on a per-slice basis) and then stacks
    these 2D masks to create a 3D volumetric mask. It handles multiple contours per slice and ensures that overlapping
    planar masks are merged. Both planar and volumetric structures masks are spatially aligned with the CT series.

    Parameters
    ----------
    ct_series : list of dict
        List of slices sorted superior to inferior.

    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    structures : list of dict
        List of structures.

    Returns
    -------
    structures_masks : list of dict
        List of generated structures masks. Each dictionary contains:
        - "StructureName" : str
            Name of the structure.
        - "StructureType" : str
            Type of the structure.
        - "PlanarMasksOnReferencedImages" : list of dict
            List of planar masks for the structure. Each dictionary contains:
            - "PlanarMask" : numpy.ndarray
                2D binary mask of the structure on the corresponding slice (possibly containing multiple contours).
            - "ReferencedSOPInstanceUID" : str
                Unique identifier of the slice.
        - "VolumetricMask" : numpy.ndarray
            3D binary mask of the structure across all corresponding slices.
    """

    logger = logging.getLogger(__name__)

    slice_origin = ct_series_acquisition_parameters["ImagePlanarPositionPatient"]
    slice_dimensions = ct_series_acquisition_parameters["ImageDimensions"]
    in_plane_spacing = ct_series_acquisition_parameters["PixelSpacing"]

    structures_masks = []

    for structure in structures:

        structure_planar_masks = []

        for contour in structure["ContoursOnReferencedImages"]:

            # Planar coordinates of the contour points.
            contour_points = contour["ContourPoints"][:, 0:2]

            # Map the contour points to the corresponding slice. The following mapping is valid ONLY if the CT Series
            # ImageOrientationPatient and PatientPosition DICOM attributes are equal to [1, 0, 0, 0, 1, 0] and HFS respectively.
            contour_slice_coordinates = np.round(np.abs((np.array(slice_origin) - contour_points) /
                                                        np.array(np.flip(in_plane_spacing, axis = 0))), decimals = 0).astype(np.uint16)
            contour_slice_coordinates = np.flip(contour_slice_coordinates, axis = 1)

            # Due to the limited (in-plane) resolution of the CT series, some contour points correspond to the same pixel.
            # Remove any duplicates.
            _, unique_points_indices = np.unique(contour_slice_coordinates, return_index = True, axis = 0)

            # Restore the initial order of contour points.
            contour_slice_coordinates = contour_slice_coordinates[np.sort(unique_points_indices)]
            planar_mask = generate_planar_mask(contour_slice_coordinates, slice_dimensions)
            structure_planar_masks.append({"PlanarMask" : planar_mask,
                                           "ReferencedSOPInstanceUID" : contour["ReferencedSOPInstanceUID"]})

        structure_merged_planar_masks = merge_planar_masks(structure_planar_masks, slice_dimensions)
        volumetric_mask = generate_volumetric_mask(ct_series, ct_series_acquisition_parameters, structure_merged_planar_masks)
        structures_masks.append({"StructureName": structure["StructureName"],
                                 "StructureType": structure["StructureType"],
                                 "PlanarMasksOnReferencedImages": structure_merged_planar_masks,
                                 "VolumetricMask": volumetric_mask})

    logger.info("Structures masks have been successfully generated.")

    return structures_masks


def generate_planar_mask(contour_slice_coordinates, slice_dimensions):
    """
    This function fills the area enclosed by the provided contour points, producing a planar mask corresponding to the
    structure on that slice.

    Parameters
    ----------
    contour_slice_coordinates : numpy.ndarray
        N x 2 array, containing the pixel coordinates of the contour points.

    slice_dimensions : list of int
        Dimensions of the CT slice.

    Returns
    -------
    planar_mask : numpy.ndarray
        2D binary mask of the contour.

    Assumptions
    -----
    - The contour points are ordered and define a closed polygon.
    """

    planar_mask = np.zeros((slice_dimensions[0], slice_dimensions[1]), dtype = np.uint8)

    # The first argument of the polygon function is an N X 1 numpy array corresponding to the row slice coordinates of
    # the N points comprising the contour, whereas the second argument is an N X 1 numpy array corresponding to the
    # column slice coordinates.
    filled_polygon_row_slice_coordinates, filled_polygon_column_slice_coordinates = polygon(contour_slice_coordinates[:, 0],
                                                                                            contour_slice_coordinates[:, 1])
    planar_mask[filled_polygon_row_slice_coordinates, filled_polygon_column_slice_coordinates] = 1

    return planar_mask


def merge_planar_masks(structure_planar_masks, slice_dimensions):
    """
    This function handles cases where a structure has multiple contours on the same slice. Overlapping masks are
    combined so that any pixel enclosed by at least one contour is set to 1.

    Parameters
    ----------
    structure_planar_masks : list of dict
        List of planar masks for a single structure. Each dictionary contains:
        - "PlanarMask" : numpy.ndarray
            2D binary mask of a contour.
        - "ReferencedSOPInstanceUID" : str
            Unique identifier of the corresponding CT slice.

    slice_dimensions : list of int
        Dimensions of the CT slice.

    Returns
    -------
    structure_merged_planar_masks : list of dict
        List of merged planar masks for a single structure (one per CT slice). Each dictionary contains:
        - "PlanarMask" : numpy.ndarray
            2D binary mask combining all contours of the CT slice.
        - "ReferencedSOPInstanceUID" : str
            Unique identifier of the corresponding CT slice.
    """

    structure_merged_planar_masks = []

    # Find the uids of the slices in which the structure is present.
    unique_referenced_uids = set()

    for planar_mask in structure_planar_masks:

        unique_referenced_uids.add(planar_mask["ReferencedSOPInstanceUID"])

    # Find the masks that belong to a specific slice.
    for referenced_uid in unique_referenced_uids:

        coplanar_masks = []

        for planar_mask in structure_planar_masks:

            if referenced_uid == planar_mask["ReferencedSOPInstanceUID"]:

                coplanar_masks.append(planar_mask["PlanarMask"])

        # Merge the masks of that slice.
        structure_merged_planar_mask = np.zeros((slice_dimensions[0], slice_dimensions[1]), dtype = np.uint8)

        for coplanar_mask in coplanar_masks:

            structure_merged_planar_mask += coplanar_mask

        # Account for contours that might have some points in common.
        structure_merged_planar_mask[structure_merged_planar_mask != 0] = 1
        structure_merged_planar_masks.append({"PlanarMask" : structure_merged_planar_mask,
                                              "ReferencedSOPInstanceUID" : referenced_uid})

    return structure_merged_planar_masks


def generate_volumetric_mask(ct_series, ct_series_acquisition_parameters, structure_merged_planar_masks):
    """
    The function generates a 3D volumetric mask for a structure by stacking planar masks. CT slices without a
    corresponding planar mask are represented as slices of zero value in the volumetric mask.

    Parameters
    ----------
    ct_series : list of dict
        List of slices sorted superior to inferior.

    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    structure_merged_planar_masks : list of dict
        List of merged planar masks for a single structure (one per CT slice).

    Returns
    -------
    volumetric_mask : numpy.ndarray
        3D binary mask of the structure across all corresponding slices.
    """

    volumetric_mask = np.zeros((len(ct_series), ct_series_acquisition_parameters["ImageDimensions"][0],
                                ct_series_acquisition_parameters["ImageDimensions"][1]), dtype = np.uint8)

    for planar_mask in structure_merged_planar_masks:

        # Find the corresponding slice, based on slice's uid.
        for slice_index in range(len(ct_series)):

            if ct_series[slice_index]["SOPInstanceUID"] == planar_mask["ReferencedSOPInstanceUID"]:

                volumetric_mask[slice_index, :, :] = planar_mask["PlanarMask"]

                break

    return volumetric_mask