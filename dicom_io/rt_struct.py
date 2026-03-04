import numpy as np
import pydicom
import os
import re


def load_rt_structures(patient_dir_path, ct_series_frame_of_reference_uid):
    """
    This function loads the DICOM RTSTRUCT file located in the "RTSTRUCT" subdirectory of patient's directory, filters out
    pseudo-structures commonly used for optimization purposes and returns the remaining structures along with their
    contour points referenced to the corresponding slices.

    Parameters
    ----------
    patient_dir_path : str
        Path to the patient directory containing an "RTSTRUCT" subdirectory with the DICOM RTSTRUCT file.

    ct_series_frame_of_reference_uid : str
        Unique identifier of the patient's coordinate system, associated with the CT series. Used to verify that the
        contour points coordinates of the various structures refer το the same coordinate system.

    Returns
    -------
    structures : list of dict
        List of structures. Each dictionary contains:
        - "StructureName" : str
            Name of the structure.
        - "StructureInterpretedType" : str
            Interpreted type of the structure (e.g., ORGAN, CONTROL).
        - "ContoursOnReferencedImages" : list of dict
            List of contour data associated with referenced slices. Each dictionary contains:
            - "ContourPoints" : numpy.ndarray
                N x 3 array of X, Y and Z coordinates, with respect to the patient's coordinate system, expressed in mm.
            - "ReferencedSOPInstanceUID" : str
                Unique identifier of the slice to which this contour corresponds.
    """

    structures_dir = os.path.join(patient_dir_path, "RTSTRUCT")

    filenames = os.listdir(structures_dir)

    for filename in filenames:

        if not filename.lower().endswith(".dcm"):

            continue

        else:
            structures_filename = filename

    structures_path = os.path.join(structures_dir, structures_filename)
    structures_data = pydicom.dcmread(structures_path)

    if structures_data.FrameOfReferenceUID != ct_series_frame_of_reference_uid:

        raise ValueError("There was a frame of reference mismatch. Different frames of reference are not supported.")

    structures = []

    for structure_index in range(len(structures_data.ROIContourSequence)):

        structure_name = structures_data.StructureSetROISequence[structure_index].ROIName
        structure_type = structures_data.RTROIObservationsSequence[structure_index].RTROIInterpretedType

        # Omit all pseudo-structures commonly used during plan optimization.
        if ((re.search("ring", structure_name.lower()) is None) and not
           ((structure_type.lower() == "organ" or structure_type.lower() == "control") and
            (re.search(r"\d", structure_name.lower()) is not None))):

            contours = []

            for contour in range(len(structures_data.ROIContourSequence[structure_index].ContourSequence)):

                contours.append({"ContourPoints" : np.array(structures_data.ROIContourSequence[structure_index].
                                                   ContourSequence[contour].ContourData, dtype = np.float64).reshape((-1,3)),
                                 "ReferencedSOPInstanceUID" : structures_data.ROIContourSequence[structure_index].
                                                              ContourSequence[contour].ContourImageSequence[0].ReferencedSOPInstanceUID})

            structure = {"StructureName" : structure_name,
                         "StructureInterpretedType" : structure_type,
                         "ContoursOnReferencedImages" : contours}
            structures.append(structure)

    return structures