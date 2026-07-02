"""
This module provides pytest-based unit tests for validating the implementation of common dosimetric indices functions.
Synthetic data is used to ensure deterministic and reproducible test outcomes. All the values that are used during the
assessments have been calculated independently (manually), using the synthetic data provided by "mock_data" module
functions. Parametrized tests cover a range of dose-volume pairs to verify numerical correctness of the computations
(for whichever functions the dose-volume pairs are applicable).
"""

import pytest
from pyrteva.plan_evaluation.dosimetric_indices import (compute_maximum_dose, compute_minimum_dose, compute_mean_dose,
                                                            compute_Vd, compute_Dv, compute_Dabsv)
from mock_data import generate_mock_dvh


@pytest.fixture(scope="module")
def dvh():
    return generate_mock_dvh()


def test_compute_maximum_dose(dvh):
    assert compute_maximum_dose(dvh) == 0.95
    return None


def test_compute_minimum_dose(dvh):
    assert compute_minimum_dose(dvh) == 0.05
    return None


def test_compute_mean_dose(dvh):
    assert compute_mean_dose(dvh) == 0.44
    return None

@pytest.mark.parametrize("volume, dose", [(100, 0), (60, 0.3), (37.5, 0.55), (0, 1)])
def test_compute_Vd(dvh, volume, dose):
    assert compute_Vd(dvh, dose) == volume
    return None


@pytest.mark.parametrize("volume, dose", [(100, 0), (65, 0.25), (60, 0.30), (0, 1)])
def test_compute_Dv(dvh, volume, dose):
    assert compute_Dv(dvh, volume) == dose
    return None


@pytest.mark.parametrize("volume, dose", [(0.06, 0), (0.036, 0.30), (0.02 ,0.65), (0, 1)])
def test_compute_Dabsv(dvh, volume, dose):
    assert compute_Dabsv(dvh, volume) == dose
    return None