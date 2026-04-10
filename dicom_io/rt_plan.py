import pydicom
import os


def load_structures_prescribed_doses(patient_dir_path, ct_series_frame_of_reference_uid):
    """
    This function loads the DICOM RTPLAN file located in the "RTPLAN" subdirectory of patient's directory and extracts
    dose prescription-related parameters, such as the prescribed dose and the dose reference type for each provided
    structure.

    Parameters
    ----------
    patient_dir_path : str
        Path to the patient's directory containing an "RTPLAN" subdirectory with the DICOM RTPLAN file.

    ct_series_frame_of_reference_uid : str
        Unique identifier of the patient's coordinate system, associated with the CT series. Used to verify that the
        treatment plan parameters refer to the same coordinate system.

    Returns
    -------
    prescribed_doses : list of dict
        List of dose prescription parameters for the provided structures. Each dictionary contains:
        - "DoseReferenceType" : str
            Dose reference type (e.g., TARGET, ORGAN_AT_RISK).
        - "DoseReferenceDescription" : str
            User-defined description.
        - "PrescribedDose" : float
            Prescribed dose, expressed in Gy.
    """

    treatment_plan_dir = os.path.join(patient_dir_path, "RTPLAN")

    filenames = os.listdir(treatment_plan_dir)

    for filename in filenames:

        if not filename.lower().endswith(".dcm"):

            continue

        else:

            treatment_plan_filename = filename

    treatment_plan_path = os.path.join(treatment_plan_dir, treatment_plan_filename)
    treatment_plan_data = pydicom.dcmread(treatment_plan_path)

    if treatment_plan_data.FrameOfReferenceUID != ct_series_frame_of_reference_uid:

        raise ValueError("There was a frame of reference mismatch. Different frames of reference are not supported.")

    structures_prescribed_doses = []

    for prescribed_dose_index in range(len(treatment_plan_data.DoseReferenceSequence)):

        structure_prescribe_dose = {"DoseReferenceType" : treatment_plan_data.DoseReferenceSequence[prescribed_dose_index].DoseReferenceType,
                                    "DoseReferenceDescription" : treatment_plan_data.DoseReferenceSequence[prescribed_dose_index].DoseReferenceDescription,
                                    "PrescribedDose" : treatment_plan_data.DoseReferenceSequence[prescribed_dose_index].TargetPrescriptionDose}

        structures_prescribed_doses.append(structure_prescribe_dose)

    return structures_prescribed_doses