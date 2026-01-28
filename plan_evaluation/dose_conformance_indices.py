import numpy as np
from plan_evaluation.dosimetric_indices import compute_Dv


def compute_homogeneity_index(prescribed_dose, tumorous_structure_dose_volume_histogram):
    """
    This function computes the homogeneity index, which is defined as:

        HI = 1 - (D2 - D98) / prescribed_dose (a slightly modified version of what has been proposed in ICRU-83 report),

    where D2 and D98 represent the minimum dose received by 2% and 98% of the tumorous structure, respectively.

    Parameters
    ----------
    prescribed_dose : float
        Prescribed dose, expressed in Gy.

    tumorous_structure_dose_volume_histogram : dict
        Dictionary containing the generated DVH.

    Returns
    -------
    homogeneity_index : float
        Homogeneity index, rounded to three decimal places.
    """

    D2 = compute_Dv(tumorous_structure_dose_volume_histogram, 2)
    D98 = compute_Dv(tumorous_structure_dose_volume_histogram, 98)

    homogeneity_index = np.round(1 - ((D2 - D98) / prescribed_dose), 3)

    return homogeneity_index


def compute_conformity_index(volumetric_dose_map, prescribed_dose, reference_isodose, tumorous_structure_volumetric_mask):
    """
    This function computes the conformity index, which is defined as the fraction of the tumorous_structure's volume enclosed
    by the reference isodose (Lomax, N. J., & Scheib, S. G. (2003). Quantifying the degree of conformity in radiosurgery
    treatment planning. International Journal of Radiation Oncology* Biology* Physics, 55(5), 1409-1419).

    Parameters
    ----------
    volumetric_dose_map : numpy.ndarray
        3D dose map, aligned to the CT series.

    prescribed_dose : float
        Prescribed dose, expressed in Gy.

    reference_isodose : float
        Reference isodose level expressed as a fraction of the prescribed dose.

    tumorous_structure_volumetric_mask : numpy.ndarray
        3D binary mask of the structure across all corresponding slices.

    Returns
    -------
    conformity_index : float
        Conformity index, rounded to three decimal places.
    """

    # Volume is expressed in voxels.
    reference_isodose_volumetric_mask = np.where(volumetric_dose_map >= reference_isodose * prescribed_dose, 1, 0)
    tumorous_structure_volume = np.sum(tumorous_structure_volumetric_mask)
    tumorous_structure_volume_enclosed_by_reference_isodose = np.sum((tumorous_structure_volumetric_mask &
                                                                      reference_isodose_volumetric_mask))

    conformity_index = np.round(tumorous_structure_volume_enclosed_by_reference_isodose /
                                tumorous_structure_volume, 3)

    return conformity_index


def compute_healthy_tissue_conformity_index(volumetric_dose_map, prescribed_dose, reference_isodose,
                                            tumorous_structure_volumetric_mask):
    """
    This function computes the healthy tissue conformity index, which is defined as the ratio between the tumorous structure's
    volume enclosed by the reference isodose and the total volume enclosed by the reference isodose (Lomax, N. J., & Scheib,
    S. G. (2003). Quantifying the degree of conformity in radiosurgery treatment planning. International Journal of
    Radiation Oncology* Biology* Physics, 55(5), 1409-1419).

    Parameters
    ----------
    volumetric_dose_map : numpy.ndarray
        3D dose map, aligned to the CT series.

    prescribed_dose : float
        Prescribed dose, expressed in Gy.

    reference_isodose : float
        Reference isodose level expressed as a fraction of the prescribed dose.

    tumorous_structure_volumetric_mask : numpy.ndarray
        3D binary mask of the structure across all corresponding slices.

    Returns
    -------
    ht_conformity_index : float
        Healthy tissue conformity index, rounded to three decimal places.
    """

    # Volume is expressed in voxels.
    reference_isodose_volumetric_mask = np.where(volumetric_dose_map >= reference_isodose * prescribed_dose, 1, 0)
    volume_enclosed_by_reference_isodose = np.sum(reference_isodose_volumetric_mask)
    tumorous_structure_volume_enclosed_by_reference_isodose = np.sum((tumorous_structure_volumetric_mask &
                                                                      reference_isodose_volumetric_mask))

    ht_conformity_index = np.round(tumorous_structure_volume_enclosed_by_reference_isodose /
                                   volume_enclosed_by_reference_isodose, 3)

    return ht_conformity_index


def compute_conformation_number(volumetric_dose_map, prescribed_dose, reference_isodose, tumorous_structure_volumetric_mask):
    """
    This function computes the conformation number, which is defined as the product of the conformity index and the healthy
    tissue conformity index (Van't Riet, A., Mak, A. C., Moerland, M. A., Elders, L. H., & Van Der Zee, W. (1997). A
    conformation number to quantify the degree of conformality in brachytherapy and external beam irradiation:
    application to the prostate. International Journal of Radiation Oncology* Biology* Physics, 37(3), 731-736).

    Parameters
    ----------
    volumetric_dose_map : numpy.ndarray
        3D dose map, aligned to the CT series.

    prescribed_dose : float
        Prescribed dose, expressed in Gy.

    reference_isodose : float
        Reference isodose level expressed as a fraction of the prescribed dose.

    tumorous_structure_volumetric_mask : numpy.ndarray
        3D binary mask of the structure across all corresponding slices.

    Returns
    -------
    conformation_number : float
        Conformation number, rounded to three decimal places.
    """

    # Volume is expressed in voxels.
    reference_isodose_volumetric_mask = np.where(volumetric_dose_map >= reference_isodose * prescribed_dose, 1, 0)
    volume_enclosed_by_reference_isodose = np.sum(reference_isodose_volumetric_mask)
    tumorous_structure_volume = np.sum(tumorous_structure_volumetric_mask)
    tumorous_structure_volume_enclosed_by_reference_isodose = np.sum((tumorous_structure_volumetric_mask &
                                                                      reference_isodose_volumetric_mask))

    conformation_number = np.round(np.power(tumorous_structure_volume_enclosed_by_reference_isodose, 2) /
                                   (tumorous_structure_volume * volume_enclosed_by_reference_isodose), 3)

    return conformation_number


def compute_conformal_index(volumetric_dose_map, prescribed_dose, reference_isodose, tumorous_structure_volumetric_mask,
                            oars_volumetric_masks):
    """
    This function computes the conformal index (COIN), which is defined as the product of the conformation number and a
    number that acts as a penalty factor, based on the fractions of OARs' volumes enclosed by the reference isodose
    (Baltas, D., Kolotas, C., Geramani, K., Mould, R. F., Ioannidis, G., Kekchidi, M., & Zamboglou, N. (1998). A conformal
    index (COIN) to evaluate implant quality and dose specification in brachytherapy. International journal of radiation
    oncology, biology, physics, 40(2), 515-524).

    Parameters
    ----------
    volumetric_dose_map : numpy.ndarray
        3D dose map, aligned to the CT series.

    prescribed_dose : float
        Prescribed dose, expressed in Gy.

    reference_isodose : float
        Reference isodose level expressed as a fraction of the prescribed dose.

    tumorous_structure_volumetric_mask : numpy.ndarray
        3D binary mask of the structure across all corresponding slices.

    oars_volumetric_masks : list of numpy.ndarray
        List of 3D binary masks of the structures, across all corresponding slices.

    Returns
    -------
    conformal_index : float
        Conformal index, rounded to three decimal places.
    """

    # Volume is expressed in voxels.
    reference_isodose_volumetric_mask = np.where(volumetric_dose_map >= reference_isodose * prescribed_dose, 1, 0)
    volume_enclosed_by_reference_isodose = np.sum(reference_isodose_volumetric_mask)
    tumorous_structure_volume = np.sum(tumorous_structure_volumetric_mask)
    tumorous_structure_volume_enclosed_by_reference_isodose = np.sum((tumorous_structure_volumetric_mask &
                                                                      reference_isodose_volumetric_mask))

    coin_factor = 1

    for oar_volumetric_mask in oars_volumetric_masks:

        oar_volume_enclosed_by_reference_isodose = np.sum((oar_volumetric_mask & reference_isodose_volumetric_mask))
        oar_volume = np.sum(oar_volumetric_mask)
        coin_factor *= 1 - (oar_volume_enclosed_by_reference_isodose / oar_volume)

    conformal_index = np.round((coin_factor * (np.power(tumorous_structure_volume_enclosed_by_reference_isodose, 2) /
                                              (tumorous_structure_volume * volume_enclosed_by_reference_isodose))), 3)

    return conformal_index


def compute_gradient_index(volumetric_dose_map, prescribed_dose):
    """
    This function computes the gradient index, which is defined as the ratio between the volume enclosed by the 50% isodose
    and the volume enclosed by the 100% (prescribed dose) isodose (Paddick, I., & Lippitz, B. (2006). A simple dose
    gradient measurement tool to complement the conformity index. Journal of neurosurgery, 105(Supplement), 194-201).

    Parameters
    ----------
    volumetric_dose_map : numpy.ndarray
        3D dose map, aligned to the CT series.

    prescribed_dose : float
        Prescribed dose, expressed in Gy.

    Returns
    -------
    gradient_index : float
        Gradient index, rounded to three decimal places.
    """

    # Volume is expressed in voxels.
    prescribed_dose_isodose_volumetric_mask = np.where(volumetric_dose_map >= prescribed_dose, 1, 0)
    volume_enclosed_by_prescribed_dose_isodose = np.sum(prescribed_dose_isodose_volumetric_mask)
    half_prescribed_dose_isodose_volumetric_mask = np.where(volumetric_dose_map >= 0.5 * prescribed_dose, 1, 0)
    volume_enclosed_by_half_prescribed_dose_isodose = np.sum(half_prescribed_dose_isodose_volumetric_mask)

    gradient_index = np.round(volume_enclosed_by_half_prescribed_dose_isodose /
                              volume_enclosed_by_prescribed_dose_isodose, 3)

    return gradient_index