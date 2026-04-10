from gui.assembler import assemble_gui
from qtpy.QtWidgets import QApplication


def main():
    """
    This function initializes the data and function settings containers (used by the callback functions), assembles the
    graphical user interface (gui) and launches it.
    """

    data_container = {"PatientsDirectory": "sample_data/dicom_data", "SeriesAcquisitionParameters": None,
                      "AlgorithmsSettings": {"DoseGridInterpolationMethod": None, "DoseBinWidth": None, "ReferenceIsodose": None},
                      "CTSeries": None, "Structures": None, "ComputedDose" : None, "StructuresPrescribedDoses": None,
                      "StructuresMasks": None, "DoseMaps": None, "DoseVolumeHistograms": None}

    app = QApplication()
    app_window = assemble_gui(data_container)
    app_window.showMaximized()
    app.exec()

    return None


main()