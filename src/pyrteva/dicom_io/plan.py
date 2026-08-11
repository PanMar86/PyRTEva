import os
import logging

import pydicom


def load_plan(patient_dir_path, ct_series_frame_of_reference_uid):
    """
    This function loads the DICOM RTPLAN file located in the "RTPLAN" subdirectory of patient's directory and extracts
    dose prescription-related parameters, including the prescribed dose and the dose reference type of each provided
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
    plan_parameters : dict
        Dictionary containing plan parameters. The dictionary contains:
        - "PrescribedDoses" : list of dict
            List of dose prescription parameters for the provided structures. Each dictionary contains:
            - "DoseReferenceType" : str
                Dose reference type (e.g., TARGET, ORGAN_AT_RISK).
            - "DoseReferenceDescription" : str
                User-defined description.
            - "PrescribedDose" : float
                Prescribed dose, expressed in Gy.
    """

    logger = logging.getLogger(__name__)

    plan_dir = os.path.join(patient_dir_path, "RTPLAN")

    filenames = os.listdir(plan_dir)

    for filename in filenames:

        if not filename.lower().endswith(".dcm"):

            continue

        else:

            plan_filename = filename

    plan_path = os.path.join(plan_dir, plan_filename)
    plan_data = pydicom.dcmread(plan_path)

    if plan_data.FrameOfReferenceUID != ct_series_frame_of_reference_uid:

        logger.error("There was a frame of reference mismatch. Different frames of reference are not supported.")
        raise ValueError("There was a frame of reference mismatch. Different frames of reference are not supported.")

    prescribed_doses = []

    for index in range(len(plan_data.DoseReferenceSequence)):

        prescribed_doses.append({"DoseReferenceType" : plan_data.DoseReferenceSequence[index].DoseReferenceType,
                                 "DoseReferenceDescription" : plan_data.DoseReferenceSequence[index].DoseReferenceDescription,
                                 "PrescribedDose" : plan_data.DoseReferenceSequence[index].TargetPrescriptionDose})

    plan_parameters = {"PrescribedDoses" : prescribed_doses}

    logger.info("Treatment plan parameters have been successfully imported.")

    return plan_parameters