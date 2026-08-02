import pandas as pd
from pyrteva.plan_evaluation.dose_constraints_evaluators import (evaluate_maximum_dose_constraint, evaluate_mean_dose_constraint,
                                                                 evaluate_volume_dose_constraints, evaluate_dose_volume_constraints,
                                                                 evaluate_dose_abs_volume_constraints)
from pyrteva.plan_evaluation.dose_conformance_indices import (compute_homogeneity_index, compute_conformity_index,
                                                              compute_healthy_tissue_conformity_index, compute_conformation_number,
                                                              compute_gradient_index)
from pyrteva.plan_evaluation.dosimetric_indices import (compute_maximum_dose, compute_minimum_dose, compute_mean_dose, compute_Dv)


def evaluate_dose_constraints(dose_volume_histograms, dose_constraints):
    """
    This function assesses whether a set of organs at risk (OARs) satisfies predefined dose constraints (based primarily
    on QUANTEC and RTOG reports) and summarizes the results in a tabular format. For each OAR, maximum dose, mean dose,
    volume-dose and dose-volume constraints are evaluated (whenever the specific type of dose constraint is applicable).
    All OARs have at least one corresponding dose constraint.

    Parameters
    ----------
    dose_volume_histograms : list of dict
        List containing the generated DVHs.

    dose_constraints : pandas.DataFrame
        Dataframe defining dose constraints. A dash ("-") indicates that a specific type of dose constraint is not
        applicable for the corresponding OAR. The dataframe contains the following columns:
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

    # Identify OARs that have at least one associated dose constraint.
    oars_dvhs = [dvh for dvh in dose_volume_histograms
                 if ((dvh["StructureType"] == "Organ At Risk") and (dvh["StructureName"] in dose_constraints["Organ At Risk (OAR)"].values))]

    num_of_rows = len(oars_dvhs)
    columns = ["Organ At Risk (OAR)", "Dmax (Gy)", "Dmean (Gy)",
               "Vd (%, Gy)", "Dv (Gy, %)", "Dabsv (Gy, cc)"]
    evaluation_table = pd.DataFrame("", index = range(num_of_rows), columns=columns)

    row_index = 0

    for oar_dvh in oars_dvhs:

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
    evaluation_table.sort_values(by="Organ At Risk (OAR)", inplace=True)

    return evaluation_table


def evaluate_dose_conformance(reference_isodose, prescribed_doses, volumetric_dose_map, dose_volume_histograms):
    """
    This function computes commonly used dose conformance indices and summarizes the results in a tabular format.
    Homogeneity index, conformity index, healthy tissue conformity index, conformation number and gradient index are
    computed for each planning target volume (ptv) structure.

    Parameters
    ----------
    reference_isodose : float
        Reference isodose level expressed as a fraction of the prescribed dose.

    prescribed_doses : list of dict
        List of dose prescription parameters for the provided structures.

    volumetric_dose_map : numpy.ndarray
        3D dose map, aligned to the CT series.

    dose_volume_histograms : list of dict
        List containing the generated DVHs.

    Returns
    -------
    evaluation_table : pandas.DataFrame
        Dataframe summarizing dose conformance indices for each structure. The dataframe contains the following columns:
        - "Structure" : str
            Name of the structure.
        - "Homogeneity Index" : float
            Homogeneity Index.
        - "Conformity Index" : float
            Conformity index.
        - "HT Conformity Index" : float
            Healthy tissue conformity index.
        - "Conformation Number" : float
            Conformation Number.
        - "Gradient Index" : float
            Gradient Index.
    """

    # Exclude all irrelevant structures.
    ptv_structures_dvhs = [dvh for dvh in dose_volume_histograms
                           if ((dvh["StructureType"] == "Tumorous Structure") and ("ptv" in dvh["StructureName"].lower()))]

    # They will be used in the future for the computation of COIN index.
    #oars_dvhs = [dvh for dvh in dose_volume_histograms if dvh["StructureType"] == "Organ At Risk"]
    #oars_volumetric_masks = [oar_dvh["VolumetricMask"] for oar_dvh in oars_dvhs]

    num_of_rows = len(ptv_structures_dvhs)
    columns = ["Structure", "Homogeneity Index", "Conformity Index", "HT Conformity Index",
               "Conformation Number", "Gradient Index"]
    evaluation_table = pd.DataFrame("", index=range(num_of_rows), columns=columns)

    for row_index in range(num_of_rows):

        # Find the prescribed dose associated with each ptv structure.
        prescribed_dose = [prescribed_dose["PrescribedDose"] for prescribed_dose in prescribed_doses
                           if prescribed_dose["StructureName"] == ptv_structures_dvhs[row_index]["StructureName"]][0]

        evaluation_table.loc[row_index, "Structure"] = ptv_structures_dvhs[row_index]["StructureName"]

        evaluation_table.loc[row_index, "Homogeneity Index"] = compute_homogeneity_index(prescribed_dose,
                                                                                         ptv_structures_dvhs[row_index])

        evaluation_table.loc[row_index, "Conformity Index"] = compute_conformity_index(reference_isodose, prescribed_dose,
                                                                                       volumetric_dose_map,
                                                                                       ptv_structures_dvhs[row_index]["VolumetricMask"])

        evaluation_table.loc[row_index, "HT Conformity Index"] = compute_healthy_tissue_conformity_index(reference_isodose,prescribed_dose,
                                                                                                         volumetric_dose_map,
                                                                                                         ptv_structures_dvhs[row_index]["VolumetricMask"])

        evaluation_table.loc[row_index, "Conformation Number"] = compute_conformation_number(reference_isodose, prescribed_dose,
                                                                                             volumetric_dose_map,
                                                                                             ptv_structures_dvhs[row_index]["VolumetricMask"])

        evaluation_table.loc[row_index, "Gradient Index"] = compute_gradient_index(prescribed_dose, volumetric_dose_map)

    evaluation_table.sort_values(by="Structure", inplace=True)

    return evaluation_table


def evaluate_dosimetric_indices(dose_volume_histograms):
    """
    This function computes commonly used dosimetric indices and summarizes the results in a tabular format. Maximum,
    minimum, mean and selected Dx indices are computed for each structure (only tumorous structures and oars are included).

    Parameters
    ----------
    dose_volume_histograms : list of dict
        List containing the generated DVHs.

    Returns
    -------
    evaluation_table : pandas.DataFrame
        Dataframe summarizing dosimetric indices for each structure. The dataframe contains the following columns:
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

    # Exclude all irrelevant structures.
    tumorous_structures_and_oars_dvhs = [dvh for dvh in dose_volume_histograms
                                         if ((dvh["StructureType"] == "Tumorous Structure") or (dvh["StructureType"] == "Organ At Risk"))]

    num_of_rows = len(tumorous_structures_and_oars_dvhs)
    columns = ["Structure", "Dmax (Gy)", "Dmin (Gy)", "Dmean (Gy)", "D2 (Gy)", "D95 (Gy)", "D98 (Gy)"]
    evaluation_table = pd.DataFrame("", index=range(num_of_rows), columns=columns)

    for row_index in range(num_of_rows):

        evaluation_table.loc[row_index, "Structure"] = tumorous_structures_and_oars_dvhs[row_index]["StructureName"]
        evaluation_table.loc[row_index, "Dmax (Gy)"] = compute_maximum_dose(tumorous_structures_and_oars_dvhs[row_index])
        evaluation_table.loc[row_index, "Dmin (Gy)"] = compute_minimum_dose(tumorous_structures_and_oars_dvhs[row_index])
        evaluation_table.loc[row_index, "Dmean (Gy)"] = compute_mean_dose(tumorous_structures_and_oars_dvhs[row_index])
        evaluation_table.loc[row_index, "D2 (Gy)"] = compute_Dv(tumorous_structures_and_oars_dvhs[row_index], 2)
        evaluation_table.loc[row_index, "D95 (Gy)"] = compute_Dv(tumorous_structures_and_oars_dvhs[row_index], 95)
        evaluation_table.loc[row_index, "D98 (Gy)"] = compute_Dv(tumorous_structures_and_oars_dvhs[row_index], 98)

    evaluation_table.sort_values(by="Structure", inplace=True)

    return evaluation_table