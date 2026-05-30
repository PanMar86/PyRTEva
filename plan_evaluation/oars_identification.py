from plan_evaluation.oars_lookup_table import oars_encountered_names


def identify_oar_proper_names(dose_volume_histograms, treatment_site):
    """
    This function identifies the proper names of the organs at risk. It uses a dictionary, where each key corresponds
    to a standardized OAR name, while the associated value is a list of variants that may appear in clinical practice
    due to differences in naming conventions.

    dose_volume_histograms : list of dict
        List containing the generated DVHs.

    treatment_site : str
        Treatment site.
    """

    oars_standard_names = []

    for dvh in dose_volume_histograms:

        if dvh["StructureType"] == "Organ At Risk":

            for oar_standard_name, oar_encountered_names in oars_encountered_names.items():

                if dvh["StructureName"].lower() in oar_encountered_names:

                    dvh["StructureName"] = oar_standard_name
                    oars_standard_names.append(oar_standard_name)

                    break

    search_for_special_structures(dose_volume_histograms, oars_standard_names, treatment_site)

    return None


def search_for_special_structures(dose_volume_histograms, oars_standard_names, treatment_site):
    """
    This function handles some special cases regarding the encountered oars' names. On some treatment sites, the planning
    target volume lies (partially or fully) within a structure, which itself is considered an OAR (for example in
    lung cancer, the combined lungs minus the gross tumor volume is an OAR that has to be spared). If both structures
    (the whole structure and the structure that has the gross tumor volume subtracted) are present, no further action is
    taken. If only the whole structure is present, it is quietly assumed that it has been contoured so that it doesn't
    contain the gross tumor volume. In addition, in the case of lung cancer with pneumonectomy, due to improper oar
    naming, the single lung might have been assigned with the standard name "Bilateral whole lungs", "Left lung" or
    "Right lung". In both cases, the renaming is essential so that the corresponding dose constraints can be successfully
    extracted from the related dataframe.

    Parameters
    ----------
    dose_volume_histograms : list of dict
        List containing the generated DVHs.

    oars_standard_names : list of str
        List of standardized OAR names.

    treatment_site : str
        Treatment site.
    """

    # Exclude all irrelevant structures.
    dvhs = [dvh for dvh in dose_volume_histograms if dvh["StructureType"] == "Organ At Risk"]

    if treatment_site == "lung":

        if ("Bilateral whole lungs minus GTV" not in oars_standard_names) and ("Bilateral whole lungs" in oars_standard_names):

            for dvh in dvhs:

                if dvh["StructureName"] == "Bilateral whole lungs":

                    dvh["StructureName"] = "Bilateral whole lungs minus GTV"

                    break

        if ("Ipsilateral lung minus GTV" not in oars_standard_names) and ("Ipsilateral lung" in oars_standard_names):

            for dvh in dvhs:

                if dvh["StructureName"] == "Ipsilateral lung":

                    dvh["StructureName"] = "Ipsilateral lung minus GTV"

                    break

    if treatment_site == "lung_pneumonectomy":

        if "Contralateral lung" not in oars_standard_names:

            for dvh in dvhs:

                if dvh["StructureName"] in ["Bilateral whole lungs", "Left lung", "Right lung"] :

                    dvh["StructureName"] = "Contralateral lung"

                    break

    if treatment_site == "brain":

        if ("Whole brain minus GTV" not in oars_standard_names) and ("Whole brain" in oars_standard_names):

            for dvh in dvhs:

                if dvh["StructureName"] == "Whole brain":

                    dvh["StructureName"] = "Whole brain minus GTV"

                    break

    return None