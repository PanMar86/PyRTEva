from gui.assembler import assemble_gui
from qtpy.QtWidgets import QApplication


def main():
    """
    This function initializes the data and function settings containers (used by the callback functions), assembles the
    graphical user interface (gui) and launches it.
    """

    data_container = {"PatientsDirectory": "sample_data/dicom_data", "CTSeries": None, "SeriesAcquisitionParameters": None,
                      "Structures": None, "TreatmentPlan": None, "ComputedDose" : None, "StructuresMasks": None,
                      "DoseMaps": None, "DoseVolumeHistograms": None}

    function_settings_container = {"InterpolationMethod" : "linear", "DoseBinWidth" : 0.05, "ReferenceIsodose" : 0.95}

    app = QApplication()
    app_window = assemble_gui(data_container, function_settings_container)
    app_window.showMaximized()
    app.exec()

    return None


main()