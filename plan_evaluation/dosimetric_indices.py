import numpy as np


def compute_maximum_dose(dose_volume_histogram):
    """
    This function computes the structure's maximum received dose. The dose bins of the DVHs have been constructed in such
    a way that the voxel or voxels corresponding to the maximum dose, belong always to the last dose bin. Therefore, the
    center of the last dose bin is considered equal to the maximum dose.

    Parameters
    ----------
    dose_volume_histogram : dict
        Dictionary containing the generated DVH.

    Returns
    -------
    maximum_dose : float
        Maximum dose received by the structure, rounded to two decimal places.
    """

    maximum_dose = np.round((dose_volume_histogram["DoseBinEdges"][-2] +
                             dose_volume_histogram["DoseBinEdges"][-1]) / 2, 2)

    return maximum_dose


def compute_minimum_dose(dose_volume_histogram):
    """
    This function computes the structure's minimum received dose. The center of the first dose bin that contains at least
    one voxel is considered equal to the minimum dose.

    Parameters
    ----------
    dose_volume_histogram : dict
        Dictionary containing the generated DVH.

    Returns
    -------
    minimum_dose : float
        Minimum dose received by the structure, rounded to two decimal places.
    """

    first_non_empty_dose_bin_index = np.flatnonzero(dose_volume_histogram["DifferentialDoseVolumeHistogram"])[0]
    minimum_dose = np.round((dose_volume_histogram["DoseBinEdges"][first_non_empty_dose_bin_index] +
                             dose_volume_histogram["DoseBinEdges"][first_non_empty_dose_bin_index + 1]) / 2, 2)

    return minimum_dose


def compute_mean_dose(dose_volume_histogram):
    """
    This function computes the structure's mean received dose. The calculation is based on the assumption that all voxels
    in a dose bin receive dose equal to the center of the bin.

    Parameters
    ----------
    dose_volume_histogram : dict
        Dictionary containing the generated DVH.

    Returns
    -------
    mean_dose : float
        Mean dose received by the structure, rounded to two decimal places.
    """

    dose_bin_centers = dose_volume_histogram["DoseBinEdges"][1::] - (dose_volume_histogram["DoseBinWidth"]/2)
    mean_dose = np.round(np.sum(dose_bin_centers * dose_volume_histogram["DifferentialDoseVolumeHistogram"]) /
                         np.sum(dose_volume_histogram["DifferentialDoseVolumeHistogram"]), 2)

    return mean_dose


def compute_Vd(dose_volume_histogram, threshold_dose):
    """
    This function computes the percentage of the structure's volume receiving a dose greater than or equal to a given
    threshold. If the threshold dose does not coincide with a dose bin edge, the volume percentage is estimated by
    averaging the values of the normalized cumulative DVH that correspond to the (two) dose bin edges closest to the
    given threshold dose.

    Parameters
    ----------
    dose_volume_histogram : dict
        Dictionary containing the generated DVH.

    threshold_dose : float
        Threshold dose, expressed in Gy.

    Returns
    -------
    volume : float
        Percentage of the structure's volume receiving a dose greater than or equal to the given threshold, rounded to
        two decimal places.
    """

    if threshold_dose < 0:

        raise ValueError("Negative dose values are not supported.")

    elif threshold_dose > dose_volume_histogram["DoseBinEdges"][-1]:

        volume = np.round(0,2)

        return volume

    else:

        # Check if any of the dose bin edges matches the given threshold dose. The atol parameter contains an additional
        # multiplicative factor equal to 1/2, in order to test (using the test_dosimetric_indices module) the proper
        # behaviour of the function when the given threshold dose doesn't coincide with a dose bin edge.
        index = np.where(np.isclose(threshold_dose, dose_volume_histogram["DoseBinEdges"],
                                    rtol = 0, atol = dose_volume_histogram["DoseBinWidth"] / 4))[0]

        if (index.size != 0 and threshold_dose != 0) or (index.size != 0 and threshold_dose == 0):

            volume = np.round(dose_volume_histogram["NormalizedCumulativeDoseVolumeHistogram"][index[0]] , 2)

            return volume

        elif index.size == 0:

            index = np.where(threshold_dose < dose_volume_histogram["DoseBinEdges"])[0]
            volume = np.round((dose_volume_histogram["NormalizedCumulativeDoseVolumeHistogram"][index[0] - 1] +
                               dose_volume_histogram["NormalizedCumulativeDoseVolumeHistogram"][index[0]]) / 2, 2)

            return volume


def compute_Dv(dose_volume_histogram, volume_percentage):
    """
    This function computes the minimum dose being received by a given percentage of the structure's volume. If the volume
    percentage does not coincide with a value of the normalized cumulative DVH, the dose is estimated by averaging the
    dose bin edges that correspond to the (two) values of the normalized cumulative DVH, closest to the given percentage.

    Parameters
    ----------
    dose_volume_histogram : dict
        Dictionary containing the generated DVH.

    volume_percentage : float
        Volume percentage.

    Returns
    -------
    dose : float
        Minimum dose received by the given percentage of the structure's volume, rounded to two decimal places.
    """

    if volume_percentage < 0 or volume_percentage > 100:

        raise ValueError("Negative volume fractions or volume fractions that exceed 100 are not supported.")

    else:

        # Check if any of the normalized cumulative DVH values matches the given volume percentage. The atol parameter
        # has been set, taking into consideration that the minimum difference between two values in a normalized cumulative
        # DVH is equal to 100 / total number of voxels. An additional multiplicative factor equal to 1/2 has been added in
        # order to test (using the test_dosimetric_indices module) the proper behaviour of the function when the given
        # volume percentage doesn't coincide with a normalized cumulative DVH value.
        index = np.where(np.isclose(volume_percentage, dose_volume_histogram["NormalizedCumulativeDoseVolumeHistogram"],
                                    rtol = 0, atol = 100 / (4 * dose_volume_histogram["StructureVoxels"])))[0]

        if (index.size != 0 and volume_percentage != 0) or (index.size != 0 and volume_percentage == 0):

            dose = np.round(dose_volume_histogram["DoseBinEdges"][index[index.size - 1]], 2)

            return dose

        elif index.size == 0:

            index = np.where(volume_percentage > dose_volume_histogram["NormalizedCumulativeDoseVolumeHistogram"])[0]
            dose = np.round((dose_volume_histogram["DoseBinEdges"][index[0] - 1] + dose_volume_histogram["DoseBinEdges"][index[0]]) / 2, 2)

            return dose


def compute_Dabsv(dose_volume_histogram, volume):
    """
    This function computes the minimum dose being received by a given (absolute) volume of the structure. If the volume
    does not coincide with a value of the absolute volume cumulative DVH, the dose is estimated by averaging the dose
    bin edges that correspond to the (two) values of the absolute volume cumulative DVH, closest to the given (absolute)
    volume.

    Parameters
    ----------
    dose_volume_histogram : dict
        Dictionary containing the generated DVH.

    volume : float
        Absolute volume, expressed in cc.

    Returns
    -------
    dose : float
        Minimum dose received by the given (absolute) volume of the structure, rounded to two decimal places.
    """

    structure_volume = dose_volume_histogram["StructureVolumeInCubicCentimeters"]

    if volume < 0 or volume > structure_volume:

        raise ValueError("Negative volume values or volume values that exceed the structure's volume are not supported.")

    else:

        # Check if any of the absolute volume cumulative DVH values matches the given volume. The atol parameter has been
        # set, taking into consideration that the minimum difference between two values in an absolute volume cumulative
        # DVH is equal to the voxel volume. An additional multiplicative factor equal to 1/2 has been added in order to
        # test (using the test_dosimetric_indices module) the proper behaviour of the function when the given volume
        # doesn't coincide with an absolute volume cumulative DVH value.
        index = np.where(np.isclose(volume, dose_volume_histogram["AbsoluteVolumeCumulativeDoseVolumeHistogram"],
                                    rtol = 0, atol = dose_volume_histogram["VoxelVolumeInCubicCentimeters"] / 4))[0]

        if (index.size != 0 and volume != 0) or (index.size != 0 and volume == 0):

            dose = np.round(dose_volume_histogram["DoseBinEdges"][index[index.size - 1]], 2)

            return dose

        elif index.size == 0:

            index = np.where(volume > dose_volume_histogram["AbsoluteVolumeCumulativeDoseVolumeHistogram"])[0]

            dose = np.round((dose_volume_histogram["DoseBinEdges"][index[0] - 1] + dose_volume_histogram["DoseBinEdges"][index[0]]) / 2, 2)

            return dose