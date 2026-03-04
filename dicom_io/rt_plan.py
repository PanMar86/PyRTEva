import pydicom
import os


def load_treatment_plan(patient_dir_path, ct_series_frame_of_reference_uid):
    """
    This function loads the DICOM RTPLAN file located in the "RTPLAN" subdirectory of patient's directory and extracts
    dose prescription-related parameters, such as the prescribed target dose and the planned number of fractions.

    Parameters
    ----------
    patient_dir_path : str
        Path to the patient's directory containing an "RTPLAN" subdirectory with the DICOM RTPLAN file.

    ct_series_frame_of_reference_uid : str
        Unique identifier of the patient's coordinate system, associated with the CT series. Used to verify that the
        treatment plan parameters refer to the same coordinate system.

    Returns
    -------
    treatment_plan_parameters : dict
        Dictionary containing dose prescription parameters. The dictionary contains:
        - "PrescribedDose" : float
            Prescribed dose, expressed in Gy.
        - "NumberOfFractions" : int
            Planned number of treatment fractions.
    """

    treatment_plan_dir = os.path.join(patient_dir_path, "RTPLAN")

    filenames = os.listdir(treatment_plan_dir)

    for filename in filenames:

        if not filename.lower().endswith(".dcm"):

            continue

        else:

            treatment_plan_filename = filename

    treatment_plan_path = os.path.join(treatment_plan_dir, treatment_plan_filename)
    treatment_plan = pydicom.dcmread(treatment_plan_path)

    if treatment_plan.FrameOfReferenceUID != ct_series_frame_of_reference_uid:

        raise ValueError("There was a frame of reference mismatch. Different frames of reference are not supported.")

    treatment_plan_parameters = {"PrescribedDose" : treatment_plan.DoseReferenceSequence[0].TargetPrescriptionDose,
                                 "NumberOfFractions" : treatment_plan.FractionGroupSequence[0].NumberOfFractionsPlanned}

    return treatment_plan_parameters