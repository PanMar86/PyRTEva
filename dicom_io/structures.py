import numpy as np
import pydicom
import os
import re


def load_structures(patient_dir_path, ct_series_frame_of_reference_uid):
    """
    This function loads the DICOM RTSTRUCT file located in the "RTSTRUCT" subdirectory of patient's directory,
    and returns the structures along with their contour points referenced to the corresponding slices.

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
        - "StructureType" : str
            Type of the structure.
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

        # First-line structure type identification.
        structure_interpreted_type = structures_data.RTROIObservationsSequence[structure_index].RTROIInterpretedType
        structure_type = identify_structure_type(structure_name, structure_interpreted_type)

        contours = []

        for contour_index in range(len(structures_data.ROIContourSequence[structure_index].ContourSequence)):

            contours.append({"ContourPoints" : np.array(structures_data.ROIContourSequence[structure_index].
                                               ContourSequence[contour_index].ContourData, dtype = np.float64).reshape((-1,3)),
                             "ReferencedSOPInstanceUID" : structures_data.ROIContourSequence[structure_index].
                                                          ContourSequence[contour_index].ContourImageSequence[0].ReferencedSOPInstanceUID})

        structures.append({"StructureName" : structure_name,
                           "StructureType": structure_type,
                           "ContoursOnReferencedImages" : contours})

    return structures


def identify_structure_type(structure_name, structure_interpreted_type):
    """
    This function uses regular expressions in order to classify the structures into five custom types: "Tumorous Structure",
    "Tumorous Structure (Optimization)", "Organ At Risk", "Organ At Risk (Optimization)", "Other".

    Parameters
    ----------
    structure_name : str
        Name of the structure.

    structure_interpreted_type : str
        Interpreted type of the structure (e.g., GTV, CTV, PTV, ORGAN, CONTROL).

    Returns
    -------
    structure_type : str
        Type of the structure.
    """

    # Detect the external body contour.
    if re.search(r"external|body|contour|patient", structure_name.lower()):
        if structure_interpreted_type.lower() == "external":
            structure_type = "External Body Contour"
        # Unknown structure type.
        else:
            structure_type = "Other"

    # Detect the tumorous structures.
    elif (re.search(r"^(gtv|ctv|itv|ptv|boost)", structure_name.lower()) or
          re.search(r"((ring[0-9a-z_ -]*(gtv|ctv|itv|ptv|boost))|((gtv|ctv|itv|ptv|boost)[0-9a-z_ -]*ring))", structure_name.lower())):

        if structure_interpreted_type.lower() == "control":
            structure_type = "Tumorous Structure (Optimization)"
        elif structure_interpreted_type.lower() in ["gtv", "ctv", "itv", "ptv"]:
            structure_type = "Tumorous Structure"
        # Unknown structure type.
        else:
            structure_type = "Other"

    # Detect the organs at risk (OARs).
    elif re.search(r"^[a-z_ -]+(minus|-|exclude|excluding)?[a-z_ -]*(gtv|ctv|itv|ptv)?", structure_name.lower()):
        if structure_interpreted_type.lower() == "control":
            structure_type = "Organ At Risk (Optimization)"
        elif structure_interpreted_type.lower() == "organ":
            structure_type = "Organ At Risk"
        # Unknown structure type.
        else:
            structure_type = "Other"

    # Unknown structure type.
    else:
        structure_type = "Other"

    return structure_type