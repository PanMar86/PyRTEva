from pyrteva.plan_evaluation.dosimetric_indices import (compute_maximum_dose, compute_mean_dose, compute_Vd, compute_Dv,
                                                        compute_Dabsv)


def evaluate_maximum_dose_constraint(oar_dose_volume_histogram, dose_constraint, evaluation_table, row_index):
    """
    This function computes the maximum dose received by the OAR and compares it against the corresponding dose constraint.
    The evaluation result is stored in the provided evaluation table.

    Parameters
    ----------
    oar_dose_volume_histogram : dict
        Dictionary containing the generated DVH.

    dose_constraint : float
        Allowable maximum dose for the OAR, expressed in Gy.

    evaluation_table : pandas.DataFrame
        Dataframe used to store evaluation results.

    row_index : int
        Index of the row in evaluation_table where the evaluation result should be stored.
    """

    maximum_dose = compute_maximum_dose(oar_dose_volume_histogram)

    if maximum_dose < dose_constraint:

        evaluation_table.loc[row_index, "Dmax (Gy)"] = f"{maximum_dose} (Pass)"

        return "Pass"

    else:

        evaluation_table.loc[row_index, "Dmax (Gy)"] = f"{maximum_dose} (Fail)"

        return "Fail"


def evaluate_mean_dose_constraint(oar_dose_volume_histogram, dose_constraint, evaluation_table, row_index):
    """
    This function computes the mean dose received by the OAR and compares it against the corresponding dose constraint.
    The evaluation result is stored in the provided evaluation table.

    Parameters
    ----------
    oar_dose_volume_histogram : dict
        Dictionary containing the generated DVH.

    dose_constraint : float
        Allowable mean dose for the OAR, expressed in Gy.

    evaluation_table : pandas.DataFrame
        Dataframe used to store evaluation results.

    row_index : int
        Index of the row in evaluation_table where the evaluation result should be stored.
    """

    mean_dose = compute_mean_dose(oar_dose_volume_histogram)

    if mean_dose < dose_constraint:

        evaluation_table.loc[row_index, "Dmean (Gy)"] = f"{mean_dose} (Pass)"

        return "Pass"

    else:

        evaluation_table.loc[row_index, "Dmean (Gy)"] = f"{mean_dose} (Fail)"

        return "Fail"


def evaluate_volume_dose_constraints(oar_dose_volume_histogram, dose_constraints, evaluation_table, row_index):
    """
    This function computes the percentage of the OAR's volume receiving a dose greater than or equal to a given
    threshold (dictated by the dose constraint) and compares it against the corresponding dose constraint. Multiple
    volume-dose type constraints are allowed. The evaluation result is stored in the provided evaluation table.

    Parameters
    ----------
    oar_dose_volume_histogram : dict
        Dictionary containing the generated DVH.

    dose_constraints : list of tuple
        List containing the volume-dose pairs that constitute the dose constraints. A volume-dose pair is expressed in
        (%, Gy) respectively.

    evaluation_table : pandas.DataFrame
        Dataframe used to store evaluation results.

    row_index : int
        Index of the row in evaluation_table where the evaluation result should be stored.
    """

    if isinstance(dose_constraints, tuple):
        dose_constraints = [dose_constraints]

    pass_rate = 0

    for constraint in dose_constraints:

        vd = compute_Vd(oar_dose_volume_histogram, constraint[1])
        evaluation_table.loc[row_index, "Vd (%, Gy)"] += f"V{constraint[1]} = {vd} "

        if vd < constraint[0]:

            pass_rate += 1

    if pass_rate == len(dose_constraints):

        evaluation_table.loc[row_index, "Vd (%, Gy)"] += "(Pass)"

        return "Pass"

    else:

        evaluation_table.loc[row_index, "Vd (%, Gy)"] += "(Fail)"

        return "Fail"


def evaluate_dose_volume_constraints(oar_dose_volume_histogram, dose_constraints, evaluation_table, row_index):
    """
    This function computes the minimum dose being received by a given percentage of the OAR's volume (dictated by the
    dose constraint) and compares it against the corresponding dose constraint. Multiple dose-volume type constraints
    are allowed. The evaluation result is stored in the provided evaluation table.

    Parameters
    ----------
    oar_dose_volume_histogram : dict
        Dictionary containing the generated DVH.

    dose_constraints : list of tuple
        List containing the dose-volume pairs that constitute the dose constraints. A dose-volume pair is expressed in
        (Gy, %) respectively.

    evaluation_table : pandas.DataFrame
        Dataframe used to store evaluation results.

    row_index : int
        Index of the row in evaluation_table where the evaluation result should be stored.
    """

    if isinstance(dose_constraints, tuple):
        dose_constraints = [dose_constraints]

    pass_rate = 0

    for constraint in dose_constraints:

        dv = compute_Dv(oar_dose_volume_histogram, constraint[1])

        evaluation_table.loc[row_index, "Dv (Gy, %)"] += f"D{constraint[1]} = {dv} "

        if dv < constraint[0]:

            pass_rate += 1

    if pass_rate == len(dose_constraints):

        evaluation_table.loc[row_index, "Dv (Gy, %)"] += "(Pass)"

        return "Pass"

    else:

        evaluation_table.loc[row_index, "Dv (Gy, %)"] += "(Fail)"

        return "Fail"


def evaluate_dose_abs_volume_constraints(oar_dose_volume_histogram, dose_constraints, evaluation_table, row_index):
    """
    This function computes the minimum dose being received by a given (absolute) volume of the OAR (dictated by the dose
    constraint) and compares it against the corresponding dose constraint. Multiple dose-volume type constraints are
    allowed. The evaluation result is stored in the provided evaluation table.

    Parameters
    ----------
    oar_dose_volume_histogram : dict
        Dictionary containing the generated DVH.

    dose_constraints : list of tuple
        List containing the dose-volume pairs that constitute the dose constraints. A dose-volume pair is expressed in
        (Gy, cc) respectively.

    evaluation_table : pandas.DataFrame
        Dataframe used to store evaluation results.

    row_index : int
        Index of the row in evaluation_table where the evaluation result should be stored.
    """

    if isinstance(dose_constraints, tuple):
        dose_constraints = [dose_constraints]

    pass_rate = 0

    for constraint in dose_constraints:

        dabsv = compute_Dabsv(oar_dose_volume_histogram, constraint[1])
        evaluation_table.loc[row_index, "Dabsv (Gy, cc)"] += f"D{constraint[1]} = {dabsv} "

        if dabsv < constraint[0]:

            pass_rate += 1

    if pass_rate == len(dose_constraints):

        evaluation_table.loc[row_index, "Dabsv (Gy, cc)"] += "(Pass)"

        return "Pass"

    else:

        evaluation_table.loc[row_index, "Dabsv (Gy, cc)"] += "(Fail)"

        return "Fail"