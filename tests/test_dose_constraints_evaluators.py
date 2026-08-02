"""
This module provides pytest-based unit tests for validating the implementation of the constraints evaluation functions.
Synthetic data is used to ensure deterministic and reproducible test outcomes. All clinical scenarios (fulfilled
constraints, partially fulfilled constraints, borderline violated constraints and violated constraints) are taken into
account.
"""

import pytest
from pyrteva.plan_evaluation.dose_constraints_evaluators import (evaluate_maximum_dose_constraint, evaluate_mean_dose_constraint, evaluate_volume_dose_constraints,
                                                                     evaluate_dose_volume_constraints, evaluate_dose_abs_volume_constraints)
from mock_data import generate_mock_dvh, generate_mock_dose_constraints, generate_mock_evaluation_table


@pytest.fixture(scope="module")
def dvh():
    return generate_mock_dvh()


@pytest.fixture(scope="module")
def constraints():
    return generate_mock_dose_constraints()


@pytest.fixture(scope="module")
def evaluation_table():
    return generate_mock_evaluation_table()


def test_evaluate_maximum_dose_constraint(dvh, constraints, evaluation_table):

    cases = ["Fulfilled constraints", "Partially fulfilled constraints", "Borderline violated constraints", "Violated constraints"]

    for case_index in range(len(cases)):
        if cases[case_index] == "Fulfilled constraints":
            assert evaluate_maximum_dose_constraint(dvh, constraints.loc[0, "Dmax (Gy)"], evaluation_table, case_index) == "Pass"
        elif cases[case_index] == "Partially fulfilled constraints":
            assert evaluate_maximum_dose_constraint(dvh, constraints.loc[1, "Dmax (Gy)"], evaluation_table, case_index) == "Pass"
        elif cases[case_index] == "Borderline violated constraints":
            assert evaluate_maximum_dose_constraint(dvh, constraints.loc[2, "Dmax (Gy)"], evaluation_table, case_index) == "Fail"
        elif cases[case_index] == "Violated constraints":
            assert evaluate_maximum_dose_constraint(dvh, constraints.loc[3, "Dmax (Gy)"], evaluation_table, case_index) == "Fail"



def test_evaluate_mean_dose_constraint(dvh, constraints, evaluation_table):

    cases = ["Fulfilled constraints", "Partially fulfilled constraints", "Borderline violated constraints", "Violated constraints"]

    for case_index in range(len(cases)):
        if cases[case_index] == "Fulfilled constraints":
            assert evaluate_mean_dose_constraint(dvh, constraints.loc[0, "Dmean (Gy)"], evaluation_table, case_index) == "Pass"
        elif cases[case_index] == "Partially fulfilled constraints":
            assert evaluate_mean_dose_constraint(dvh, constraints.loc[1, "Dmean (Gy)"], evaluation_table, case_index) == "Pass"
        elif cases[case_index] == "Borderline violated constraints":
            assert evaluate_mean_dose_constraint(dvh, constraints.loc[2, "Dmean (Gy)"], evaluation_table, case_index) == "Fail"
        elif cases[case_index] == "Violated constraints":
            assert evaluate_mean_dose_constraint(dvh, constraints.loc[3, "Dmean (Gy)"], evaluation_table, case_index) == "Fail"



def test_evaluate_volume_dose_constraint(dvh, constraints, evaluation_table):

    cases = ["Fulfilled constraints", "Partially fulfilled constraints", "Borderline violated constraints", "Violated constraints"]

    for case_index in range(len(cases)):
        if cases[case_index] == "Fulfilled constraints":
            assert evaluate_volume_dose_constraints(dvh, constraints.loc[0, "Vd (%, Gy)"], evaluation_table,
                                                    case_index) == "Pass"
        elif cases[case_index] == "Partially fulfilled constraints":
            assert evaluate_volume_dose_constraints(dvh, constraints.loc[1, "Vd (%, Gy)"], evaluation_table,
                                                    case_index) == "Fail"
        elif cases[case_index] == "Borderline violated constraints":
            assert evaluate_volume_dose_constraints(dvh, constraints.loc[2, "Vd (%, Gy)"], evaluation_table,
                                                    case_index) == "Fail"
        elif cases[case_index] == "Violated constraints":
            assert evaluate_volume_dose_constraints(dvh, constraints.loc[3, "Vd (%, Gy)"], evaluation_table,
                                                    case_index) == "Fail"



def test_evaluate_dose_volume_constraint(dvh, constraints, evaluation_table):

    cases = ["Fulfilled constraints", "Partially fulfilled constraints", "Borderline violated constraints", "Violated constraints"]

    for case_index in range(len(cases)):
        if cases[case_index] == "Fulfilled constraints":
            assert evaluate_dose_volume_constraints(dvh, constraints.loc[0, "Dv (Gy, %)"], evaluation_table,
                                                    case_index) == "Pass"
        elif cases[case_index] == "Partially fulfilled constraints":
            assert evaluate_dose_volume_constraints(dvh, constraints.loc[1, "Dv (Gy, %)"], evaluation_table,
                                                    case_index) == "Fail"
        elif cases[case_index] == "Borderline violated constraints":
            assert evaluate_dose_volume_constraints(dvh, constraints.loc[2, "Dv (Gy, %)"], evaluation_table,
                                                    case_index) == "Fail"
        elif cases[case_index] == "Violated constraints":
            assert evaluate_dose_volume_constraints(dvh, constraints.loc[3, "Dv (Gy, %)"], evaluation_table,
                                                    case_index) == "Fail"



def test_evaluate_dose_abs_volume_constraint(dvh, constraints, evaluation_table):

    cases = ["Fulfilled constraints", "Partially fulfilled constraints", "Borderline violated constraints", "Violated constraints"]

    for case_index in range(len(cases)):
        if cases[case_index] == "Fulfilled constraints":
            assert evaluate_dose_abs_volume_constraints(dvh, constraints.loc[0, "Dabsv (Gy, cc)"], evaluation_table,
                                                        case_index) == "Pass"
        elif cases[case_index] == "Partially fulfilled constraints":
            assert evaluate_dose_abs_volume_constraints(dvh, constraints.loc[1, "Dabsv (Gy, cc)"], evaluation_table,
                                                        case_index) == "Fail"
        elif cases[case_index] == "Borderline violated constraints":
            assert evaluate_dose_abs_volume_constraints(dvh, constraints.loc[2, "Dabsv (Gy, cc)"], evaluation_table,
                                                        case_index) == "Fail"
        elif cases[case_index] == "Violated constraints":
            assert evaluate_dose_abs_volume_constraints(dvh, constraints.loc[3, "Dabsv (Gy, cc)"], evaluation_table,
                                                        case_index) == "Fail"

