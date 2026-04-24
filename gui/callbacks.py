import napari
import pickle
from qtpy.QtWidgets import QApplication, QLabel, QFileDialog, QTableWidget, QTableWidgetItem, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox
from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QColor
from gui.components import generate_report_tables, generate_user_preferences_window, generate_dvh_control_panel
from dicom_io.ct_series import load_ct_series
from dicom_io.structures import load_structures
from dicom_io.dose import load_dose
from dicom_io.plan import load_plan
from dicom_io.validators import validate_directory_structure
from computations.structures_masks import generate_structures_masks
from computations.dose_maps import generate_dose_maps
from computations.dose_volume_histograms import generate_dose_volume_histogram
from visualization.anatomy_dose import generate_visualisation
from visualization.dose_volume_histograms import generate_dose_volume_histogram_plots
from plan_evaluation.oars_identification import identify_oar_proper_names
from plan_evaluation.evaluation import evaluate_dose_constraints, evaluate_dose_conformance, evaluate_dosimetric_indices


def load_patient_data(data_container, status_bar):
    """
    This function triggers the execution of the functions that load and validate all the patient-related DICOM data.

    Parameters
    ----------
    data_container : dict
        Dictionary acting as a (shared) data container used by the callback functions.

    status_bar : qtpy.QtWidgets.QStatusBar
        Status bar.
    """

    patient_dir =  validate_directory_structure(QFileDialog.getExistingDirectory(None, "Select Patient Folder",
                                                                                 data_container["PatientsDirectory"]))

    update_status_bar(status_bar, "Patient data is being imported. Please wait...")

    update_status_bar(status_bar, "CT series and series acquisition parameters are being imported. Please wait...")
    ct_series, ct_series_acquisition_parameters = load_ct_series(patient_dir)
    data_container["CTSeries"] = ct_series
    data_container["SeriesAcquisitionParameters"] = ct_series_acquisition_parameters
    update_status_bar(status_bar, "CT series and series acquisition parameters have been imported successfully.")

    update_status_bar(status_bar, "RT structures are being imported. Please wait...")
    structures = load_structures(patient_dir, data_container["SeriesAcquisitionParameters"]["FrameOfReferenceUID"])
    data_container["Structures"] = structures
    update_status_bar(status_bar, "RT structures have been imported successfully.")

    update_status_bar(status_bar, "Computed dose is being imported...")
    dose = load_dose(patient_dir, data_container["SeriesAcquisitionParameters"]["FrameOfReferenceUID"],
                     data_container["SeriesAcquisitionParameters"]["ImageOrientationPatient"])
    data_container["Dose"] = dose
    update_status_bar(status_bar, "Computed dose has been successfully imported.")

    update_status_bar(status_bar, "Treatment plan parameters are being imported. Please wait...")
    plan_parameters = load_plan(patient_dir, data_container["SeriesAcquisitionParameters"]["FrameOfReferenceUID"])
    prescribed_doses = plan_parameters["PrescribedDoses"]
    data_container["PrescribedDoses"] = prescribed_doses
    update_status_bar(status_bar, "Treatment plan parameters have been imported successfully.")

    update_status_bar(status_bar, "Patient data has been successfully imported.")

    return None


def apply_user_preferences(data_container, status_bar):
    """




    Parameters
    ----------
    data_container : dict
        Dictionary acting as a (shared) data container used by the callback functions.

    status_bar : qtpy.QtWidgets.QStatusBar
        Status bar.
    """

    update_status_bar(status_bar, "User preferences are being applied...")
    user_preferences_window = generate_user_preferences_window(data_container)
    user_preferences_window.exec()

    dose_grid_interpolation_method =  user_preferences_window.findChild(QComboBox,"dose_grid_interpolation_method").currentText()
    data_container["AlgorithmsSettings"]["DoseGridInterpolationMethod"] = dose_grid_interpolation_method
    dose_bin_width = user_preferences_window.findChild(QDoubleSpinBox,"dose_bin_width").value()
    data_container["AlgorithmsSettings"]["DoseBinWidth"] = dose_bin_width
    reference_isodose = user_preferences_window.findChild(QDoubleSpinBox,"reference_isodose").value()
    data_container["AlgorithmsSettings"]["ReferenceIsodose"] = reference_isodose
    additional_structures_inclusion = user_preferences_window.findChild(QCheckBox,"additional_structures_inclusion")
    data_container["AdditionalStructuresInclusion"] = additional_structures_inclusion.isChecked()

    # Store the user-approved structures' types and prescribed doses. Since the dictionaries related to prescribed doses
    # have now slightly different keys, reset the container-list.
    data_container["PrescribedDoses"] = []

    for structure in data_container["Structures"]:

        structure_type = user_preferences_window.findChild(QComboBox, structure["StructureName"].lower() + "_type").currentText()

        if structure["StructureType"] != structure_type:

            structure["StructureType"] = structure_type

        prescribed_dose_widget = user_preferences_window.findChild(QSpinBox, structure["StructureName"].lower() + "_prescribed_dose")

        if prescribed_dose_widget.isEnabled():

            prescribed_dose = prescribed_dose_widget.value()

        else:

            prescribed_dose = None

        data_container["PrescribedDoses"].append({"StructureName" : structure["StructureName"],
                                                  "StructureType" : structure["StructureType"],
                                                  "PrescribedDose" : prescribed_dose})

    update_status_bar(status_bar, "User preferences have been successfully applied.")

    return None


def generate_intermediate_data(data_container, status_bar):
    """
    This function triggers the execution of the functions that generate all the necessary (intermediate) data required
    both for visualization and plan assessment.

    Parameters
    ----------
    data_container : dict
        Dictionary acting as a (shared) data container used by the callback functions.

    status_bar :qtpy.QtWidgets.QStatusBar
        Status bar.
    """

    update_status_bar(status_bar, "Patient data processing has been initiated. Please wait...")

    update_status_bar(status_bar, "Structures masks are being generated. Please wait...")
    structures_masks = generate_structures_masks(data_container["CTSeries"], data_container["SeriesAcquisitionParameters"], data_container["Structures"])
    data_container["Masks"] = structures_masks
    update_status_bar(status_bar, "Structures masks have been generated successfully.")

    update_status_bar(status_bar, "Dose maps are being generated. Please wait...")
    dose_maps = generate_dose_maps(data_container["CTSeries"], data_container["SeriesAcquisitionParameters"],
                                   data_container["Dose"], data_container["AlgorithmsSettings"]["DoseGridInterpolationMethod"])
    data_container["DoseMaps"] = dose_maps
    update_status_bar(status_bar, "Dose maps have been generated successfully.")

    dose_volume_histograms = generate_dose_volume_histogram(data_container["SeriesAcquisitionParameters"], data_container["Masks"],
                                                            data_container["DoseMaps"]["VolumetricDoseMap"], data_container["AlgorithmsSettings"]["DoseBinWidth"],
                                                            data_container["AdditionalStructuresInclusion"])

    data_container["DoseVolumeHistograms"] = dose_volume_histograms
    update_status_bar(status_bar, "Dose volume histograms have been successfully generated.")

    update_status_bar(status_bar, "Patient data processing has been successfully completed.")

    return None


def display_visualisation(data_container, status_bar, visualisation_panel, visualization_mode, display_mode):
    """
    This function triggers the execution of the function that generates and configures a multi-layer Napari viewer. The
    visualization and display modes dictate what type of layers are present on the viewer. The existing blank Napari
    viewer (acting as a placeholder) is removed from the container panel and deleted, prior to the creation of the new
    instance. The viewer is further customized via the "customize_viewer" function.

    Parameters
    ----------
    data_container : dict
        Dictionary acting as a (shared) data container used by the callback functions.

    status_bar : qtpy.QtWidgets.QStatusBar
        Status bar.

    visualisation_panel : qtpy.QtWidgets.QWidget
        Container gui panel, where the napari viewer is embedded.

    visualization_mode : str
        Visualization mode.

    display_mode : str
        Display mode.
    """

    update_status_bar(status_bar, f"{display_mode} {visualization_mode} visualisation mode is being initialized. Please wait...")

    temporary_content  = [child for child in visualisation_panel.children() if isinstance(child, napari._qt.qt_main_window._QtMainWindow)][0]
    visualisation_panel.layout().removeWidget(temporary_content)
    temporary_content.hide()
    temporary_content.deleteLater()

    viewer = generate_visualisation(data_container["CTSeries"], data_container["SeriesAcquisitionParameters"],
                                    data_container["Masks"], data_container["DoseMaps"]["VolumetricDoseMap"],
                                    data_container["PrescribedDoses"], visualization_mode, display_mode,
                                    data_container["AdditionalStructuresInclusion"])

    customize_viewer(viewer)

    viewer_qt_widget = viewer.window._qt_window
    visualisation_panel.layout().addWidget(viewer_qt_widget)

    update_status_bar(status_bar, f"{display_mode} {visualization_mode} visualisation mode has been enabled.")

    return None


def display_dose_volume_histograms(data_container, status_bar, dvh_panel):
    """
    This function triggers the execution of the function that plots the generated dose volume histograms for all
    associated structures. The existing QLabel (acting as a generic placeholder) is removed from the container panel
    and deleted, prior to the creation of the dose volume histograms plot.

    Parameters
    ----------
    data_container : dict
        Dictionary acting as a (shared) data container used by the callback functions.

    status_bar : qtpy.QtWidgets.QStatusBar
        Status bar.

    dvh_panel : qtpy.QtWidgets.QWidget
        Container gui panel, where the dose volume histograms plot is embedded.
    """

    update_status_bar(status_bar, "Dose volume histograms are being generated. Please wait...")

    temporary_content = [child for child in dvh_panel.children() if isinstance(child, QLabel)][0]
    dvh_panel.layout().removeWidget(temporary_content)
    temporary_content.hide()
    temporary_content.deleteLater()

    dvh_plots = generate_dose_volume_histogram_plots(data_container["DoseVolumeHistograms"])
    dvh_control_panel = generate_dvh_control_panel(data_container, dvh_plots)

    dvh_panel.layout().addWidget(dvh_plots)
    dvh_panel.layout().addWidget(dvh_control_panel)

    update_status_bar(status_bar, "Dose volume histograms have been successfully generated.")

    return None


def display_evaluation_report(data_container, status_bar, evaluation_panel):
    """
    This function triggers the execution of the functions that split the generated dose volume histograms (DVHs) into
    three groups (corresponding to tumorous structures, OARs and OARs with at least one corresponding dose constraint
    respectively), and evaluate the treatment plan based on a group of dosimetric indices, the dose conformance (with
    respect to the tumorous structures) and the compliance with the associated dose constraints. The existing QLabel
    (acting as a generic placeholder) is removed from the container panel and deleted, prior to the creation of the
    evaluation report tables. Finally, the gui status bar is updated to reflect the progress status.

    Parameters
    ----------
    data_container : dict
        Shared data container.

    status_bar : qtpy.QtWidgets.QStatusBar
        Status bar.

    evaluation_panel : qtpy.QtWidgets.QWidget
        Container gui panel, where the evaluation report tables are embedded.
    """

    update_status_bar(status_bar, "Plan evaluation report is being generated. Please wait...")

    temporary_content = [child for child in evaluation_panel.children() if isinstance(child, QLabel)][0]
    evaluation_panel.layout().removeWidget(temporary_content)
    temporary_content.hide()
    temporary_content.deleteLater()

    with open("plan_evaluation/dose_constraints/conventional_fractionation/lung_cancer_dose_constraints.pkl", mode="rb") as f:
        dose_constraints = pickle.load(f)

    # Map the oars' encountered names to standard names and identify any redundant structures.
    identify_oar_proper_names(data_container["DoseVolumeHistograms"])

    dosimetric_indices_evaluation = evaluate_dosimetric_indices(data_container["DoseVolumeHistograms"])
    dose_constraints_evaluation = evaluate_dose_constraints(data_container["DoseVolumeHistograms"], dose_constraints)
    dose_conformance_evaluation = evaluate_dose_conformance(data_container["AlgorithmsSettings"]["ReferenceIsodose"],
                                                            data_container["PrescribedDoses"],
                                                            data_container["DoseMaps"]["VolumetricDoseMap"],
                                                            data_container["DoseVolumeHistograms"])

    report_tables_data = {"Dosimetric Indices" : dosimetric_indices_evaluation,
                          "Dose Conformance" : dose_conformance_evaluation,
                          "Dose Constraints" : dose_constraints,
                          "Dose Constraints Evaluation" : dose_constraints_evaluation}

    report_tables = generate_report_tables(report_tables_data)

    # Insert plan evaluation results to the corresponding tables.
    for table_name, table_data in report_tables_data.items():

        table = report_tables.findChildren(QTableWidget, table_name)[0]
        table.setHorizontalHeaderLabels(table_data.columns.tolist())

        for row_index in range(table_data.shape[0]):

            for col_index in range(table_data.shape[1]):

                table_item_value = str(table_data.iloc[row_index, col_index])
                table_item = QTableWidgetItem(table_item_value)
                table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table_item.setToolTip(table_item.text())

                if "Pass" in table_item_value:

                    table_item.setForeground(QBrush(QColor("green")))

                elif "Fail" in table_item_value:

                    table_item.setForeground(QBrush(QColor("red")))

                table.setItem(row_index, col_index, table_item)

    evaluation_panel.layout().addWidget(report_tables)

    update_status_bar(status_bar, "Plan evaluation report has been successfully generated.")

    return None


def update_status_bar(status_bar, message):
    """
    This function updates the gui status bar with the provided message. It forces the gui to process events immediately
    to ensure that the message is displayed properly.

    Parameters
    ----------
    status_bar : QStatusBar
        Status bar.

    message : str
        Message to be displayed.
    """

    status_bar.showMessage(message)
    QApplication.processEvents()

    return None


def customize_viewer(viewer):
    """
    This function modifies the given Napari viewer to create a minimal, dark-themed version suitable for
    gui-embedding. A series of control buttons are "deactivated" (hided) on purpose, so that there is no
    signal mixing due to the existence of two napari viewers, embedded on the gui.

    Parameters
    ----------
    viewer : napari.viewer.Viewer
        Napari viewer whose interface elements will be modified.
    """
    viewer.window._qt_window._qt_viewer.setStyleSheet("background-color: black")
    viewer.window._qt_window._qt_viewer.viewerButtons.setVisible(False)
    viewer.window._qt_window._qt_viewer.layerButtons.setVisible(False)
    viewer.window._qt_window.menuBar().setVisible(False)
    viewer.window._qt_window.statusBar()._activity_item.setVisible(False)

    layers = viewer.layers
    for layer in layers:
        for widget in viewer.window._qt_window._qt_viewer.controls.widgets[layer].children():
            if type(widget) is napari._qt.widgets.qt_mode_buttons.QtModeRadioButton:
                widget.setVisible(False)

    return None