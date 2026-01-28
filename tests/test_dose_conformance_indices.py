"""
This module provides pytest-based unit tests for validating the implementation of common plan quality metrics functions.
Synthetic data is used to ensure deterministic and reproducible test outcomes. All the values that are used during the
assessments have been calculated independently (manually), using the synthetic data provided by "mock_data" module
functions. Parametrized tests cover a range of prescribed doses and reference isodoses to verify numerical correctness
of the computations.
"""

import pytest
from plan_evaluation.dose_conformance_indices import (compute_homogeneity_index, compute_conformity_index, compute_healthy_tissue_conformity_index,
                                                      compute_conformation_number, compute_conformal_index, compute_gradient_index)
from tests.mock_data import generate_mock_structures_masks, generate_mock_dose_map, generate_mock_dvh


@pytest.fixture(scope="module")
def structures_masks():
    return generate_mock_structures_masks()


@pytest.fixture(scope="module")
def dose_map():
    return generate_mock_dose_map()


@pytest.fixture(scope="module")
def dvh():
    return generate_mock_dvh()


@pytest.mark.parametrize("prescribed_dose, homogeneity_index", [(0.50, - 0.800), (1.00, 0.100), (1.50, 0.400)])
def test_compute_homogeneity_index(prescribed_dose, dvh, homogeneity_index):
    assert compute_homogeneity_index(prescribed_dose, dvh) == homogeneity_index
    return None


@pytest.mark.parametrize("reference_isodose, conformity_index", [(0.50, 0.450), (0.80, 0.281), (0.95, 0.169)])
def test_compute_conformity_index(structures_masks, dose_map, reference_isodose, conformity_index):
    tumorous_structure_volumetric_mask = [structure_mask["VolumetricMask"] for structure_mask in structures_masks
                                          if structure_mask["StructureName"] == "TumorousStructure"][0]
    assert compute_conformity_index(dose_map["VolumetricDoseMap"], dose_map["PrescribedDose"], reference_isodose,
                                    tumorous_structure_volumetric_mask) == conformity_index
    return None


@pytest.mark.parametrize("reference_isodose, healthy_tissue_conformity_index", [(0.50, 0.500), (0.80, 0.500), (0.95, 0.500)])
def test_compute_healthy_tissue_conformity_index(structures_masks, dose_map, reference_isodose, healthy_tissue_conformity_index):
    tumorous_structure_volumetric_mask = [structure_mask["VolumetricMask"] for structure_mask in structures_masks
                                          if structure_mask["StructureName"] == "TumorousStructure"][0]
    assert compute_healthy_tissue_conformity_index(dose_map["VolumetricDoseMap"], dose_map["PrescribedDose"],
                                                   reference_isodose, tumorous_structure_volumetric_mask) == healthy_tissue_conformity_index
    return None


@pytest.mark.parametrize("reference_isodose, conformation_number", [(0.50, 0.225), (0.80, 0.141), (0.95, 0.084)])
def test_compute_conformation_number(structures_masks, dose_map, reference_isodose, conformation_number):
    tumorous_structure_volumetric_mask = [structure_mask["VolumetricMask"] for structure_mask in structures_masks
                                          if structure_mask["StructureName"] == "TumorousStructure"][0]
    assert compute_conformation_number(dose_map["VolumetricDoseMap"], dose_map["PrescribedDose"], reference_isodose,
                                       tumorous_structure_volumetric_mask) == conformation_number
    return None


@pytest.mark.parametrize("reference_isodose, conformal_index", [(0.50, 0.058), (0.80, 0.068), (0.95, 0.057)])
def test_compute_conformal_index(structures_masks, dose_map, reference_isodose, conformal_index):
    tumorous_structure_volumetric_mask = [structure_mask["VolumetricMask"] for structure_mask in structures_masks
                                          if structure_mask["StructureName"] == "TumorousStructure"][0]
    oars_volumetric_masks = [structure_mask["VolumetricMask"] for structure_mask in structures_masks
                             if not (structure_mask["StructureName"] == "TumorousStructure")]
    assert compute_conformal_index(dose_map["VolumetricDoseMap"], dose_map["PrescribedDose"], reference_isodose,
                                   tumorous_structure_volumetric_mask, oars_volumetric_masks) == conformal_index
    return None


def test_gradient_index(dose_map):
    assert compute_gradient_index(dose_map["VolumetricDoseMap"], dose_map["PrescribedDose"]) == 2.667
    return None