import numpy as np


def generate_dose_volume_histogram(ct_series_acquisition_parameters, structures_masks, volumetric_dose_map, dose_bin_width, additional_structures_inclusion):
    """
    This function generates the differential and cumulative dose volume histogram (DVH) for each structure. Cumulative
    DVHs are reported both as normalized percentages and absolute volumes (in cc). The cumulative DVHs follow the common
    radiotherapy convention of representing the percentage (or the absolute volume) of a structure receiving at least a
    given dose.

    Parameters
    ----------
    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    structures_masks : list of dict
        List of generated structures masks.

    volumetric_dose_map : dict
        3D dose map, aligned to the CT series.

    dose_bin_width : float
        Width of the dose bins, expressed in Gy.

    additional_structures_inclusion : bool
        Whether to include the optimization structures and structures of type Other or not.

    Returns
    -------
    dose_volume_histograms : list of dict
        List of generated DVHs. Each dictionary contains:
        - "StructureName" : str
            Name of the structure to which the DVHs correspond.
        - "StructureType" : str
            Type of the structure.
        - "VolumetricMask" : numpy.ndarray
            Volumetric mask of the structure.
        - "DifferentialDoseVolumeHistogram" : numpy.ndarray
            Differential DVH, representing the number of voxels per dose bin.
        - "NormalizedCumulativeDoseVolumeHistogram" : numpy.ndarray
            Cumulative DVH, expressed as percentage of the structure's volume.
        - "AbsoluteVolumeCumulativeDoseVolumeHistogram" : numpy.ndarray
            Cumulative DVH, expressed as structure's absolute volume in cubic centimeters (cc).
        - "StructureVolumeInCubicCentimeters" : float
            Total structure's volume in cubic centimeters.
        - "StructureVoxels" : int
            Number of voxels belonging to the structure.
        - "VoxelVolumeInCubicCentimeters" : float
            Volume of a single voxel in cubic centimeters.
        - "DoseBinEdges" : numpy.ndarray
            Dose bin edges, expressed in Gy.
        - "DoseBinWidth" : float
            Dose bin width, expressed in Gy.
    """

    # Determine the structures that will be included in the generated dose volume histograms.
    if additional_structures_inclusion:

        included_structure_types = ["Tumorous Structure", "Tumorous Structure (Optimization)", "Organ At Risk", "Organ At Risk (Optimization)", "Other"]

    elif not additional_structures_inclusion:

        included_structure_types = ["Tumorous Structure", "Organ At Risk"]

    dose_volume_histograms = []

    for structure_mask in structures_masks:

        if structure_mask["StructureType"] in included_structure_types:

            structure_volumetric_mask = structure_mask["VolumetricMask"]
            structure_voxels_dose = volumetric_dose_map[structure_volumetric_mask != 0]

            # Pixel spacing and slice thickness are expressed in mm. Divide by 1000 to convert into cubic centimeters (cc).
            num_structure_voxels = structure_voxels_dose.shape[0]
            voxel_volume_cc = (ct_series_acquisition_parameters["PixelSpacing"][0] * ct_series_acquisition_parameters["PixelSpacing"][1] *
                               ct_series_acquisition_parameters["SliceThickness"]) / 1000
            structure_volume_cc = num_structure_voxels * voxel_volume_cc

            # The dose bins are constructed in such a way, that the voxel/voxels corresponding to the maximum dose
            # will always be placed in the last dose bin.
            dose_bin_edges = [x * dose_bin_width for x in range(np.floor((np.max(structure_voxels_dose)/dose_bin_width) + 1).astype(np.uint32) + 1)]
            differential_dvh, bin_edges = np.histogram(structure_voxels_dose, bins = dose_bin_edges)
            normalized_cumulative_dvh = 100 * (1 - (np.cumsum(differential_dvh)/num_structure_voxels))

            # Slightly modify the cumulative dose volume histogram so that its first element corresponds to the leftmost
            # dose bin edge (0). In other words, the first element is equal to the percentage of the structure's volume
            # that receives zero (or more) Gy (100%).
            normalized_cumulative_dvh = np.concat([np.array([100]), normalized_cumulative_dvh])

            absolute_volume_cumulative_dvh = structure_volume_cc * (normalized_cumulative_dvh / 100)

            dose_volume_histograms.append({"StructureName" : structure_mask["StructureName"],
                                           "StructureType" : structure_mask["StructureType"],
                                           "VolumetricMask" : structure_volumetric_mask,
                                           "DifferentialDoseVolumeHistogram" : differential_dvh,
                                           "NormalizedCumulativeDoseVolumeHistogram" : normalized_cumulative_dvh,
                                           "AbsoluteVolumeCumulativeDoseVolumeHistogram" : absolute_volume_cumulative_dvh,
                                           "StructureVolumeInCubicCentimeters" : structure_volume_cc,
                                           "StructureVoxels" : num_structure_voxels,
                                           "VoxelVolumeInCubicCentimeters" : voxel_volume_cc,
                                           "DoseBinEdges" : bin_edges,
                                           "DoseBinWidth" : dose_bin_width})

    return dose_volume_histograms