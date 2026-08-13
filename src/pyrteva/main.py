import logging
from pathlib import Path

from qtpy.QtWidgets import QApplication

from pyrteva.gui.assembler import assemble_gui


def main():
    """
    This function acts as the application's entry point.
    """

    logs_dir = Path(Path.home()/"pyrteva_logs")
    Path.mkdir(logs_dir, exist_ok = True)
    logging.basicConfig(level=logging.INFO, filename=logs_dir/"log.txt",
                        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s")

    patients_dir = Path(__file__).resolve().parents[0]/"assets"/"sample_data"/"dicom_data"

    data_container = {"PatientsDirectory": patients_dir,
                      "AlgorithmsSettings": {"DoseGridInterpolationMethod": None, "DoseBinWidth": None, "ReferenceIsodose": None},
                      "CTSeries": None, "SeriesAcquisitionParameters": None, "Structures": None, "Dose" : None, "PrescribedDoses": None,
                      "Masks": None, "DoseMaps": None, "DoseVolumeHistograms": None, "AdditionalStructuresInclusion": None,
                      "TreatmentSite": None, "FractionationScheme": None}

    app = QApplication()
    app_window = assemble_gui(data_container)
    app_window.showMaximized()
    app.exec()

if __name__ == "__main__":
    main()