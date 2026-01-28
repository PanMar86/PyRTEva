import re
from copy import deepcopy
from plan_evaluation.oars_mapping import oars_encountered_names


def identify_structures(dose_volume_histograms, dose_constraints):
    """
    This function splits the generated dose volume histograms (DVHs) into three groups: The first group contains DVHs
    that correspond to tumorous structures, the second one contains DVHs that correspond to organs at risk (OARs). The
    last one is a subset of the second and contains DVHs that correspond to (OARs), for which at least one dose
    constraint has been published (by QUANTEC or RTOG). OARs' names are mapped to standardized names using a predefined
    lookup table.

    Parameters
    ----------
    dose_volume_histograms : list of dict
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
    structures_dose_volume_histograms : dict
        Dictionary containing the three DVH groups. The dictionary contains:
        - "TumorousStructuresDoseVolumeHistograms" : list of dict
            List of DVHs corresponding to tumorous structures.
        - "OARsDoseVolumeHistograms" : list of dict
            List of DVHs corresponding to OARs.
        - "OARsWithConstraintsDoseVolumeHistograms" : list of dict
            List of DVHs corresponding to OARs that have at least one associated dose constraint.
    """

    dvhs = deepcopy(dose_volume_histograms)

    tumorous_structures_dvhs = []
    oars_dvhs = []

    oars_standard_names = []

    for dvh in dvhs:

        # Search for OARs
        if ((re.search(r"(\d+[-_ ]*[a-z]*[-_ ]*ptv)|(ptv[-_ ]*\d+[-_ ]*[a-z]*)|(boost)", dvh["StructureName"].lower()) is None)
                and (re.fullmatch(r"ptv|itv|ctv|gtv", dvh["StructureName"].lower()) is None)):

            # Map OARs' names to standardized names, using a predefined lookup table.
            for oar_standard_name, oar_encountered_names in oars_encountered_names.items():

                if dvh["StructureName"].lower() in oar_encountered_names:

                    dvh["StructureName"] = oar_standard_name
                    oars_standard_names.append(oar_standard_name)
                    oars_dvhs.append(dvh)

        else:

            tumorous_structures_dvhs.append(dvh)

    search_for_special_structures(oars_dvhs, oars_standard_names)

    # Identify OARs that have at least one associated dose constraint.
    oars_with_constraints_dvhs = [oar_dvh for oar_dvh in oars_dvhs if oar_dvh["StructureName"] in dose_constraints["Organ At Risk (OAR)"].values]

    structures_dose_volume_histograms = {"TumorousStructuresDoseVolumeHistograms" : tumorous_structures_dvhs,
                                         "OARsDoseVolumeHistograms" : oars_dvhs,
                                         "OARsWithConstraintsDoseVolumeHistograms" : oars_with_constraints_dvhs}

    return structures_dose_volume_histograms


def search_for_special_structures(oars_dose_volume_histograms, oars_standard_names):
    """
    This function handles some special cases where the target volume lies within a structure, which itself is considered
    an OAR (for example in lung cancer, the combined lungs minus the gross tumor volume is an OAR that has to be spared).
    If both structures (the whole structure and the structure that has the gross tumor volume subtracted) are present,
    then the whole structure is deleted and not evaluated further. If only the whole structure is present, it is quietly
    assumed that it has been contoured so that it doesn't contain the gross tumor volume, and it is renamed accordingly.
    The renaming process is essential so that the corresponding dose constraints can be successfully extracted from the
    related dataframe.

    Currently handled special cases:
    - "Bilateral whole lungs" vs. "Bilateral whole lungs minus GTV".
    - "Ipsilateral lung" vs. "Ipsilateral lung minus GTV".

    Parameters
    ----------
    oars_dose_volume_histograms : list of dict
        List containing the generated DVHs.

    oars_standard_names : list of str
        List of standardized OAR names.

    Returns
    -------
    None
    """

    if ("Bilateral whole lungs minus GTV" not in oars_standard_names) and ("Bilateral whole lungs" in oars_standard_names):

        for dvh in oars_dose_volume_histograms:

            if dvh["StructureName"] == "Bilateral whole lungs":

                dvh["StructureName"] = "Bilateral whole lungs minus GTV"

                break

    elif ("Bilateral whole lungs minus GTV" in oars_standard_names) and ("Bilateral whole lungs" in oars_standard_names):

        for index in range(len(oars_dose_volume_histograms)):

            if oars_dose_volume_histograms[index]["StructureName"] == "Bilateral whole lungs":

                oars_dose_volume_histograms.pop(index)

                break

    if ("Ipsilateral lung minus GTV" not in oars_standard_names) and ("Ipsilateral lung" in oars_standard_names):

        for dvh in oars_dose_volume_histograms:

            if dvh["StructureName"] == "Ipsilateral lung":

                dvh["StructureName"] = "Ipsilateral lung minus GTV"

                break

    elif ("Ipsilateral lung" in oars_standard_names) and ("Ipsilateral lung minus GTV" in oars_standard_names):

        for index in range(len(oars_dose_volume_histograms)):

            if oars_dose_volume_histograms[index]["StructureName"] == "Ipsilateral lung":

                oars_dose_volume_histograms.pop(index)

                break

    return None