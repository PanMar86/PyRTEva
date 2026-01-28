import pandas as pd
from plan_evaluation.dose_constraints_evaluators import (evaluate_maximum_dose_constraint, evaluate_mean_dose_constraint,
                                                         evaluate_volume_dose_constraints, evaluate_dose_volume_constraints,
                                                         evaluate_dose_abs_volume_constraints)
from plan_evaluation.dose_conformance_indices import (compute_homogeneity_index, compute_conformity_index,
                                                      compute_healthy_tissue_conformity_index, compute_conformation_number,
                                                      compute_conformal_index, compute_gradient_index)
from plan_evaluation.dosimetric_indices import (compute_maximum_dose, compute_minimum_dose, compute_mean_dose, compute_Dv)


def evaluate_dose_constraints(oars_dose_volume_histograms, dose_constraints):
    """
    This function assesses whether a set of organs at risk (OARs) satisfies predefined dose constraints (based primarily
    on QUANTEC and RTOG reports) and summarizes the results in a tabular format. For each OAR, maximum dose, mean dose,
    volume-dose and dose-volume constraints are evaluated (whenever the specific type of dose constraint is applicable).
    All OARs have at least one corresponding dose constraint.

    Parameters
    ----------
    oars_dose_volume_histograms : list of dict
        List containing the generated DVHs.

    dose_constraints : pandas.DataFrame
        Dataframe defining dose constraints (one dataframe row per OAR). A dash ("-") indicates that a specific type of
        dose constraint is not applicable for the corresponding OAR. The dataframe contains the following columns:
        - "Organ At Risk (OAR)" : str
            Name of the OAR.
        - "Endpoint" : str
            Expected clinical implications, following the dose constraints violation.
        - "Dmax (Gy)" : float
            Maximum dose constraint, expressed in Gy.
        - "Dmean (Gy)" : float
            Mean dose constraint, expressed in Gy.
        - "Vd (%, Gy)" : list of tuple
            List of volume-dose constraints, expressed in volume fraction and Gy, respectively.
        - "Dv (Gy, %)" : list of tuple
            List of dose–volume constraints, expressed in Gy and volume fraction, respectively.
        - "Dabsv (Gy, cc)" : list of tuple
            List of dose–volume constraints, expressed in Gy and absolute volume (cc), respectively.
        - "Notes" : str
            Additional information regarding the dose constraints.

    Returns
    -------
    evaluation_table : pandas.DataFrame
        Dataframe summarizing the evaluation of dose constraints for each OAR (one dataframe row per OAR). A dash ("-")
        indicates that a specific type of dose constraint is not applicable for the corresponding OAR. The dataframe
        contains the following columns:
        - "Organ At Risk (OAR)" : str
            Name of the OAR.
        - "Dmax (Gy)" : str
            Evaluation result of the maximum dose constraint.
        - "Dmean (Gy)" : str
            Evaluation result of the mean dose constraint.
        - "Vd (%, Gy)" : str
            Evaluation result of the volume-dose constraints.
        - "Dv (Gy, %)" : str
            Evaluation result of the dose–volume constraints.
        - "Dabsv (Gy, cc)" : str
            Evaluation result of the dose-volume constraints.
    """

    # Create the dataframe storing the results.
    columns = ["Organ At Risk (OAR)", "Dmax (Gy)", "Dmean (Gy)",
               "Vd (%, Gy)", "Dv (Gy, %)", "Dabsv (Gy, cc)"]

    num_of_rows = len(oars_dose_volume_histograms)
    evaluation_table = pd.DataFrame("", index = range(num_of_rows), columns=columns)

    row_index = 0

    for oar_dvh in oars_dose_volume_histograms:

        evaluation_table.loc[row_index, "Organ At Risk (OAR)"] = oar_dvh["StructureName"]

        oar_dose_constraints = dose_constraints[dose_constraints["Organ At Risk (OAR)"] == oar_dvh["StructureName"]]

        maximum_dose_constraint = oar_dose_constraints["Dmax (Gy)"].iloc[0]
        mean_dose_constraint = oar_dose_constraints["Dmean (Gy)"].iloc[0]
        volume_dose_constraints = oar_dose_constraints["Vd (%, Gy)"].iloc[0]
        dose_volume_constraints = oar_dose_constraints["Dv (Gy, %)"].iloc[0]
        dose_abs_volume_constraints = oar_dose_constraints["Dabsv (Gy, cc)"].iloc[0]

        if maximum_dose_constraint != "-":
            evaluate_maximum_dose_constraint(oar_dvh, maximum_dose_constraint, evaluation_table, row_index)

        if mean_dose_constraint != "-":
            evaluate_mean_dose_constraint(oar_dvh, mean_dose_constraint, evaluation_table, row_index)

        if volume_dose_constraints != "-":
            evaluate_volume_dose_constraints(oar_dvh, volume_dose_constraints, evaluation_table, row_index)

        if dose_volume_constraints != "-":
            evaluate_dose_volume_constraints(oar_dvh, dose_volume_constraints, evaluation_table, row_index)

        if dose_abs_volume_constraints != "-":
            evaluate_dose_abs_volume_constraints(oar_dvh, dose_abs_volume_constraints, evaluation_table, row_index)

        row_index += 1

    evaluation_table[evaluation_table == ""] = "-"

    return evaluation_table


def evaluate_dose_conformance(dose_maps, prescribed_dose, reference_isodose,
                              tumorous_structures_dose_volume_histograms, oars_dose_volume_histograms):
    """
    This function computes commonly used dose conformance indices and summarizes the results in a tabular format.
    Homogeneity index, conformity index, healthy tissue conformity index, conformation number, conformal index and
    gradient index are computed for each tumorous structure.

    Parameters
    ----------
    dose_maps : dict
        Dictionary containing the generated dose maps.

    prescribed_dose : float
        Prescribed dose, expressed in Gy (it is considered equal to the prescribed dose to PTV).

    reference_isodose : float
        Reference isodose level expressed as a fraction of the prescribed dose.

    tumorous_structures_dose_volume_histograms : list of dict
        List containing the generated DVHs.

    oars_dose_volume_histograms : list of dict
        List containing the generated DVHs.

    Returns
    -------
    evaluation_table : pandas.DataFrame
        Dataframe summarizing dose conformance indices for each tumorous structure (one dataframe row per tumorous
        structure). The dataframe contains the following columns:
        - "Tumorous Structure" : str
            Name of the tumorous structure.
        - "Homogeneity Index" : float
            Homogeneity Index.
        - "Conformity Index" : float
            Conformity index.
        - "HT Conformity Index" : float
            Healthy tissue conformity index.
        - "Conformation Number" : float
            Conformation Number.
        - "Conformal Index" : float
            Conformal Index.
        - "Gradient Index" : float
            Gradient Index.
    """

    columns = ["Tumorous Structure", "Homogeneity Index", "Conformity Index", "HT Conformity Index",
               "Conformation Number", "Conformal Index", "Gradient Index"]

    num_of_rows = len(tumorous_structures_dose_volume_histograms)

    evaluation_table = pd.DataFrame("", index=range(num_of_rows), columns=columns)

    for row_index in range(num_of_rows):

        evaluation_table.loc[row_index, "Tumorous Structure"] = tumorous_structures_dose_volume_histograms[row_index]["StructureName"]

        evaluation_table.loc[row_index, "Homogeneity Index"] = compute_homogeneity_index(prescribed_dose,
                                                                                         tumorous_structures_dose_volume_histograms[row_index])

        evaluation_table.loc[row_index, "Conformity Index"] = compute_conformity_index(dose_maps["VolumetricDoseMap"],
                                                              prescribed_dose, reference_isodose,
                                                              tumorous_structures_dose_volume_histograms[row_index]["VolumetricMask"])

        evaluation_table.loc[row_index, "HT Conformity Index"] = compute_healthy_tissue_conformity_index(dose_maps["VolumetricDoseMap"],
                                                                 prescribed_dose, reference_isodose,
                                                                 tumorous_structures_dose_volume_histograms[row_index]["VolumetricMask"])

        evaluation_table.loc[row_index, "Conformation Number"] = compute_conformation_number(dose_maps["VolumetricDoseMap"],
                                                                 prescribed_dose, reference_isodose,
                                                                 tumorous_structures_dose_volume_histograms[row_index]["VolumetricMask"])

        oars_volumetric_masks = [oar_dvh["VolumetricMask"] for oar_dvh in oars_dose_volume_histograms]
        evaluation_table.loc[row_index, "Conformal Index"] = compute_conformal_index(dose_maps["VolumetricDoseMap"],
                                                             prescribed_dose, reference_isodose,
                                                             tumorous_structures_dose_volume_histograms[row_index]["VolumetricMask"],
                                                             oars_volumetric_masks)

        evaluation_table.loc[row_index, "Gradient Index"] = compute_gradient_index(dose_maps["VolumetricDoseMap"], prescribed_dose)

    return evaluation_table


def evaluate_dosimetric_indices(dose_volume_histograms):
    """
    This function computes commonly used dosimetric indices and summarizes the results in a tabular format. Maximum,
    minimum, mean and selected Dx indices are computed for each structure.

    Parameters
    ----------
    dose_volume_histograms : list of dict
        List containing the generated DVHs.

    Returns
    -------
    evaluation_table : pandas.DataFrame
        Dataframe summarizing dosimetric indices for each structure (one dataframe row per structure). The dataframe
        contains the following columns:
        - "Structure" : str
            Structure's name.
        - "Dmax (Gy)" : float
            Maximum dose received by the structure, expressed in Gy.
        - "Dmin (Gy)" : float
            Minimum dose received by the structure, expressed in Gy.
        - "Dmean (Gy)" : float
            Mean dose received by the structure, expressed in Gy.
        - "D2 (Gy)" : float
            Minimum dose received by 2% of the structure's volume, expressed in Gy.
        - "D95 (Gy)" : float
            Minimum dose received by 95% of the structure's volume, expressed in Gy.
        - "D98 (Gy)" : float
            Minimum dose received by 98% of the structure's volume, expressed in Gy.
    """

    columns = ["Structure", "Dmax (Gy)", "Dmin (Gy)", "Dmean (Gy)", "D2 (Gy)", "D95 (Gy)", "D98 (Gy)"]

    num_of_rows = len(dose_volume_histograms)
    evaluation_table = pd.DataFrame("", index=range(num_of_rows), columns=columns)

    for row_index in range(num_of_rows):

        evaluation_table.loc[row_index, "Structure"] = dose_volume_histograms[row_index]["StructureName"]
        evaluation_table.loc[row_index, "Dmax (Gy)"] = compute_maximum_dose(dose_volume_histograms[row_index])
        evaluation_table.loc[row_index, "Dmin (Gy)"] = compute_minimum_dose(dose_volume_histograms[row_index])
        evaluation_table.loc[row_index, "Dmean (Gy)"] = compute_mean_dose(dose_volume_histograms[row_index])
        evaluation_table.loc[row_index, "D2 (Gy)"] = compute_Dv(dose_volume_histograms[row_index], 2)
        evaluation_table.loc[row_index, "D95 (Gy)"] = compute_Dv(dose_volume_histograms[row_index], 95)
        evaluation_table.loc[row_index, "D98 (Gy)"] = compute_Dv(dose_volume_histograms[row_index], 98)

    return evaluation_table