from pathlib import Path
from qtpy.QtWidgets import QApplication
from pyrteva.gui.assembler import assemble_gui


def main():
    """
    This function initializes the data and function settings containers (used by the callback functions), assembles the
    graphical user interface (gui) and launches it.
    """

    patients_dir = str(Path(__file__).resolve().parents[0]/"assets"/"sample_data"/"dicom_data")

    data_container = {"PatientsDirectory": patients_dir,
                      "AlgorithmsSettings": {"DoseGridInterpolationMethod": None, "DoseBinWidth": None, "ReferenceIsodose": None},
                      "CTSeries": None, "SeriesAcquisitionParameters": None, "Structures": None, "Dose" : None, "PrescribedDoses": None,
                      "Masks": None, "DoseMaps": None, "DoseVolumeHistograms": None, "AdditionalStructuresInclusion": None,
                      "TreatmentSite": None, "FractionationScheme": None}

    app = QApplication()
    app_window = assemble_gui(data_container)
    app_window.showMaximized()
    app.exec()

    return None

if __name__ == "__main__":
    main()