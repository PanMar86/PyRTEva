import napari
from qtpy.QtWidgets import (QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout, QToolButton, QDialog,
                            QGroupBox, QMenu, QComboBox, QDoubleSpinBox, QScrollArea, QSpinBox, QStatusBar,QTableWidget,
                            QMessageBox, QTabWidget, QHeaderView, QAbstractItemView, QCheckBox)
from qtpy.QtCore import Qt, QSize


def generate_main_window():
    """
    This function generates the gui main window.

    Returns
    -------
    main_window : qtpy.QtWidgets.QWidget
        Main gui window.
    """

    main_window = QWidget()
    main_window.setObjectName("main_window")
    main_window.setWindowTitle("PyRTEva, an experimental radiation therapy plan evaluation toolkit, based οn Python")
    main_window_layout = QGridLayout()
    main_window_layout.setContentsMargins(5, 5, 5, 5)
    main_window.setLayout(main_window_layout)

    with open("gui/custom_styles/main_window.qss", mode="r") as main_window_qss:
        main_window.setStyleSheet(main_window_qss.read())

    return main_window


def generate_user_preferences_window(data_container):
    """
    This function generates an auxiliary window that acts as a user interaction panel. The user is allowed to tweak
    various parameters such as the dose grid interpolation method, the dose bin width and the reference isodose. In
    addition, is allowed to edit the pre-assigned type of the structures as well as the prescribed dose to the
    structures for which the concept of prescribed dose is applicable.

    Parameters
    ----------
    data_container : dict
        Dictionary acting as a (shared) data container used by the callback functions.

    Returns
    -------
    window : qtpy.QtWidgets.QDialog
        Auxiliary window.
    """

    def verify_user_preferences(container_widget, parent_widget):
        """
        This function verifies that there is a unique structure, whose type has been assigned to "External Body Contour".

        Parameters
        ----------
        container_widget : qtpy.QtWidgets.QWidget
        	Container of the QComboBox widgets corresponding to the type of the structures.

        parent_widget : qtpy.QtWidgets.QDialog
            Parent widget of the QMessageBox widgets.
        """

        num_body_contours = 0

        for structure_type_widget in container_widget.findChildren(QComboBox):

            if structure_type_widget.currentText() == "External Body Contour":

                num_body_contours += 1

        if num_body_contours == 0:

            QMessageBox.warning(parent_widget, "Non-valid structure types","A structure corresponding to external body contour has not been found.")

        elif num_body_contours > 1:

            QMessageBox.warning(parent_widget,"Non-valid structure types", "Only a single structure's type can be assigned to 'External Body Contour'.")

        else:

            QMessageBox.information(parent_widget, "Success","User preferences have been accepted.")
            parent_widget.close()

        return None


    def change_state_prescribed_dose_widget(signal_text, widget):
        """
        This function activates / deactivates (if necessary) the widget associated with the prescribed dose, each time
        the user assigns a different structure type than the one having already been assigned.

        Parameters
        ----------
        signal_text : str
            User-assigned structure type.

        widget : qtpy.QtWidgets.QSpinBox
            Prescribed dose widget.
        """

        if (signal_text != "Tumorous Structure") and widget.isEnabled():

            widget.setValue(0)
            widget.setDisabled(True)

        elif (signal_text == "Tumorous Structure") and (not widget.isEnabled()):

            widget.setDisabled(False)

        return None


    window = QDialog()
    window.setWindowTitle("User Preferences")
    window.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
    window.setFixedSize(QSize(915, 700))
    window_layout = QVBoxLayout()
    window_layout.setSpacing(10)

    with open("gui/custom_styles/user_preferences_window.qss", mode="r") as user_preferences_window_qss:
        window.setStyleSheet(user_preferences_window_qss.read())

    alg_settings_outer_container = QGroupBox("Algorithms settings")
    alg_settings_outer_container.setObjectName("alg_settings_outer_container")
    alg_settings_outer_container_layout = QVBoxLayout()
    alg_settings_outer_container_layout.setContentsMargins(10,25,10,10)

    alg_settings_inner_container = QWidget()
    alg_settings_inner_container.setObjectName("alg_settings_inner_container")
    alg_settings_inner_container_layout = QGridLayout()
    alg_settings_inner_container_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

    dose_grid_interpolation_method = QComboBox()
    dose_grid_interpolation_method.setObjectName("dose_grid_interpolation_method")
    dose_grid_interpolation_method.addItems(["Linear", "Nearest", "Slinear", "Cubic", "Quintic", "Pchip"])
    dose_grid_interpolation_method.setCurrentText("linear")

    dose_bin_width = QDoubleSpinBox()
    dose_bin_width.setObjectName("dose_bin_width")
    dose_bin_width.setRange(0.01, 0.1)
    dose_bin_width.setSingleStep(0.01)
    dose_bin_width.setValue(0.05)

    reference_isodose = QDoubleSpinBox()
    reference_isodose.setObjectName("reference_isodose")
    reference_isodose.setRange(0.85, 1.10)
    reference_isodose.setSingleStep(0.01)
    reference_isodose.setValue(0.95)

    alg_settings_inner_container_layout.addWidget(QLabel("Dose grid interpolation method:"), 0 ,0)
    alg_settings_inner_container_layout.addWidget(dose_grid_interpolation_method, 0, 1)
    alg_settings_inner_container_layout.addWidget(QLabel("Dose bin width:"), 1, 0)
    alg_settings_inner_container_layout.addWidget(dose_bin_width, 1, 1)
    alg_settings_inner_container_layout.addWidget(QLabel("Reference isodose:"), 2, 0)
    alg_settings_inner_container_layout.addWidget(reference_isodose, 2, 1)
    alg_settings_inner_container.setLayout(alg_settings_inner_container_layout)

    alg_settings_info_message = QLabel("Please select the dose grid interpolation method, "
                                       "the dose bin width of the DVHs and the reference isodose "
                                       "(for which the conformance indices will be computed).")
    alg_settings_info_message.setWordWrap(True)

    alg_settings_outer_container_layout.addWidget(alg_settings_info_message)
    alg_settings_outer_container_layout.addWidget(alg_settings_inner_container)
    alg_settings_outer_container.setLayout(alg_settings_outer_container_layout)

    structures_info_outer_container = QGroupBox("Structures info")
    structures_info_outer_container.setObjectName("structures_info_outer_container")
    structures_info_outer_container_layout = QVBoxLayout()
    structures_info_outer_container_layout.setContentsMargins(10,25,10,20)

    structures_info_mid_container = QWidget()
    structures_info_mid_container_layout = QHBoxLayout()
    structures_info_mid_container_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
    structures_info_mid_container_layout.setContentsMargins(0, 0, 0, 0)

    structures_info_secondary_message = QLabel("Include optimization structures and structures of type 'Other' in the standard visualization and DVH panels:")

    additional_structures_inclusion = QCheckBox()
    additional_structures_inclusion.setObjectName("additional_structures_inclusion")

    structures_info_mid_container_layout.addWidget(structures_info_secondary_message)
    structures_info_mid_container_layout.addWidget(additional_structures_inclusion)
    structures_info_mid_container.setLayout(structures_info_mid_container_layout)

    structures_info_scrollable_area = QScrollArea()
    structures_info_scrollable_area.setObjectName("structures_info_scrollable_area")
    structures_info_scrollable_area.setWidgetResizable(True)

    structures_info_inner_container = QWidget()
    structures_info_inner_container_layout = QVBoxLayout()

    structure_types = ["Tumorous Structure", "Tumorous Structure (Optimization)", "Organ At Risk",
                       "Organ At Risk (Optimization)", "External Body Contour", "Other"]

    for structure in data_container["Structures"]:

        structure_info = QGroupBox()
        structure_info_layout = QHBoxLayout()
        structure_info_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        structure_info_layout.setContentsMargins(0,10,0,10)

        structure_type = QComboBox()
        structure_type.setObjectName(structure["StructureName"].lower() + "_type")
        structure_type.addItems(structure_types)
        structure_type.setCurrentText(structure["StructureType"])

        structure_prescribed_dose = QSpinBox()
        structure_prescribed_dose.setObjectName(structure["StructureName"].lower() + "_prescribed_dose")
        structure_prescribed_dose.setRange(0,100)
        structure_prescribed_dose.setSingleStep(1)

        if structure_type.currentText() != "Tumorous Structure":

            structure_prescribed_dose.setValue(0)
            structure_prescribed_dose.setDisabled(True)

        else:

            # Set the first occurring value in case of multiple prescribed doses (different targets).
            structure_prescribed_dose.setValue(data_container["PrescribedDoses"][0]["PrescribedDose"])

        # Change the state (if necessary) of the prescribed dose widget according to the user-selected structure type.
        structure_type.currentTextChanged.connect(lambda signal_text, widget = structure_prescribed_dose :
                                                  change_state_prescribed_dose_widget(signal_text, widget))

        structure_info_layout.addWidget(QLabel(structure["StructureName"]))
        structure_info_layout.addWidget(QLabel("Structure type:"))
        structure_info_layout.addWidget(structure_type)
        structure_info_layout.addWidget(QLabel("Prescribed dose:"))
        structure_info_layout.addWidget(structure_prescribed_dose)
        structure_info.setLayout(structure_info_layout)

        structures_info_inner_container_layout.addWidget(structure_info)

    structures_info_inner_container.setLayout(structures_info_inner_container_layout)

    structures_info_scrollable_area.setWidget(structures_info_inner_container)

    if len(data_container["PrescribedDoses"]) > 1:

        additional_message = (f"They have also been detected {len(data_container["PrescribedDoses"])} structures, possibly "
                              f"with different prescribed doses associated with them. ")

    else:

        additional_message = ""

    structures_info_principal_message = QLabel(f"They have been detected {len(data_container["Structures"])} structures in total. {additional_message}"
                                               f"Please verify that the pre-assigned structure types, as well as the prescribed doses "
                                               f"(to the structures for which prescribed doses are applicable) are correct.")
    structures_info_principal_message.setWordWrap(True)

    structures_info_outer_container_layout.addWidget(structures_info_principal_message)
    structures_info_outer_container_layout.addWidget(structures_info_mid_container)
    structures_info_outer_container_layout.addWidget(structures_info_scrollable_area)
    structures_info_outer_container.setLayout(structures_info_outer_container_layout)

    apply_button = QPushButton("Apply")
    apply_button.setObjectName("apply_button")
    apply_button.clicked.connect(lambda : verify_user_preferences(structures_info_inner_container, window))

    window_layout.addWidget(apply_button, alignment = Qt.AlignmentFlag.AlignRight)
    window_layout.addWidget(alg_settings_outer_container)
    window_layout.addWidget(structures_info_outer_container)
    window.setLayout(window_layout)

    return window


def generate_treatment_parameters_window():
    """
    This function generates an auxiliary window that acts as a user interaction panel. The user is allowed to select
    the treatment site as well as the fractionation scheme.

    Returns
    -------
    window : qtpy.QtWidgets.QDialog
        Auxiliary window.
    """

    window = QDialog()
    window.setWindowTitle("Treatment Parameters")
    window.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
    window.setFixedSize(QSize(370, 200))
    window_layout = QVBoxLayout()
    window_layout.setSpacing(10)

    with open("gui/custom_styles/treatment_parameters_window.qss", mode="r") as treatment_parameters_window_qss:
        window.setStyleSheet(treatment_parameters_window_qss.read())

    treatment_parameters_outer_container = QGroupBox()
    treatment_parameters_outer_container.setObjectName("treatment_parameters_outer_container")
    treatment_parameters_outer_container_layout = QVBoxLayout()
    treatment_parameters_outer_container_layout.setContentsMargins(10,10,10,10)

    treatment_parameters_inner_container = QWidget()
    treatment_parameters_inner_container.setObjectName("treatment_parameters_inner_container")
    treatment_parameters_inner_container_layout = QGridLayout()
    treatment_parameters_inner_container_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

    treatment_site = QComboBox()
    treatment_site.setObjectName("treatment_site")
    treatment_site.addItem("Lung")
    treatment_site.setCurrentText("Lung")

    fractionation_scheme = QComboBox()
    fractionation_scheme.setObjectName("fractionation_scheme")
    fractionation_scheme.addItem("Conventional")
    fractionation_scheme.setCurrentText("Conventional")

    treatment_parameters_inner_container_layout.addWidget(QLabel("Treatment Site:"), 0, 0)
    treatment_parameters_inner_container_layout.addWidget(treatment_site, 0, 1)
    treatment_parameters_inner_container_layout.addWidget(QLabel("Dose Fractionation Scheme:"), 1, 0)
    treatment_parameters_inner_container_layout.addWidget(fractionation_scheme, 1, 1)
    treatment_parameters_inner_container.setLayout(treatment_parameters_inner_container_layout)

    principal_message = QLabel("Please select the treatment site as well as the dose fractionation scheme.")
    principal_message.setWordWrap(True)

    treatment_parameters_outer_container_layout.addWidget(principal_message)
    treatment_parameters_outer_container_layout.addWidget(treatment_parameters_inner_container)
    treatment_parameters_outer_container.setLayout(treatment_parameters_outer_container_layout)

    apply_button = QPushButton("Apply")
    apply_button.setObjectName("apply_button")
    apply_button.clicked.connect(lambda: window.close())

    window_layout.addWidget(apply_button, alignment = Qt.AlignmentFlag.AlignRight)
    window_layout.addWidget(treatment_parameters_outer_container)
    window.setLayout(window_layout)

    return window


def generate_viewer_panel():
    """
    This function generates a panel that acts as a container for a napari viewer, and embeds a blank viewer. Later on,
    the blank viewer is replaced by a viewer containing all the relevant image layers.

    Returns
    -------
    viewer_panel : qtpy.QtWidgets.QWidget
        Panel containing a blank napari viewer.
    """

    viewer_panel = QWidget()
    viewer_panel_layout = QVBoxLayout()
    viewer_panel_layout.setContentsMargins(2, 2, 2, 2)

    viewer = napari.Viewer(show=False)
    customize_viewer(viewer)

    viewer_qt_widget = viewer.window._qt_window

    viewer_panel_layout.addWidget(viewer_qt_widget)
    viewer_panel.setLayout(viewer_panel_layout)

    return viewer_panel


def generate_composite_panel(label):
    """
    This function generates a panel that acts as a generic container, and embeds a QLabel widget. Later on, the QLabel is
    replaced by the actual panel content.

    Parameters
    ----------
    label : str
        Descriptive text appearing on the panel (prior to the appearance of the actual content).

    Returns
    -------
    composite_panel : qtpy.QtWidgets.QWidget
        Panel containing temporary textual content.
    """

    composite_panel = QWidget()
    composite_panel_layout = QHBoxLayout()
    composite_panel_layout.setContentsMargins(5, 5, 5, 5)

    temporary_content = QLabel(label)
    temporary_content.setAlignment(Qt.AlignmentFlag.AlignCenter)

    composite_panel_layout.addWidget(temporary_content)
    composite_panel.setLayout(composite_panel_layout)

    return composite_panel


def generate_dvh_control_panel(data_container, dvhs_plot):
    """
    This function generates a panel that acts as a container for the buttons used to change the visibility of each
    dose volume histogram figure.

    Parameters
    ----------
    data_container : dict
        Dictionary acting as a (shared) data container used by the callback functions.
    dvhs_plot : pyqtgraph.widgets.PlotWidget.PlotWidget
        Object containing the rendered dose volume histogram figures.

    Returns
    -------
    dvh_control_panel : QWidget.QGroupBox
        Dose volume histograms control panel.
    """

    def change_visibility_dvh_figure(dvh_figure):
        """
        This function changes the visibility of each dose volume histogram figure.

        Parameters
        ----------
        dvh_figure : pyqtgraph.graphicsItems.PlotDataItem.PlotDataItem
            Object containing the rendered dose volume histogram figure.
        """

        if dvh_figure.isVisible():

            dvh_figure.setVisible(False)

        else:

            dvh_figure.setVisible(True)

    dvh_control_panel = QGroupBox()
    dvh_control_panel.setObjectName("dvh_control_panel")
    dvh_control_panel_layout = QVBoxLayout()
    dvh_control_panel_layout.setContentsMargins(0, 30, 0, 40)

    dvh_buttons_scrollable_area = QScrollArea()
    dvh_buttons_scrollable_area.setObjectName("dvh_buttons_scrollable_area")
    dvh_buttons_scrollable_area.setWidgetResizable(True)

    dvh_buttons = QGroupBox()
    dvh_buttons.setObjectName("dvh_buttons")
    dvh_buttons_layout = QVBoxLayout()
    dvh_buttons_layout.setSpacing(10)
    dvh_buttons_layout.setContentsMargins(20, 20, 10, 20)
    dvh_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    for dvh in data_container["DoseVolumeHistograms"]:

        dvh_button = QPushButton(dvh["StructureName"])
        dvh_button.setObjectName(dvh["StructureName"].lower())

        # Find the associated figure and connect the button's click event.
        dvh_figure = [dvh_figure for dvh_figure in dvhs_plot.getPlotItem().listDataItems() if dvh_figure.objectName() == dvh_button.objectName()][0]
        dvh_button.clicked.connect(lambda signal, dvh_figure = dvh_figure : change_visibility_dvh_figure(dvh_figure))

        dvh_buttons_layout.addWidget(dvh_button)

    dvh_buttons.setLayout(dvh_buttons_layout)

    dvh_buttons_scrollable_area.setWidget(dvh_buttons)

    info_message = QLabel("Enable / Disable DVH")
    info_message.setAlignment(Qt.AlignmentFlag.AlignCenter)

    dvh_control_panel_layout.addWidget(info_message)
    dvh_control_panel_layout.addWidget(dvh_buttons_scrollable_area)
    dvh_control_panel.setLayout(dvh_control_panel_layout)

    return dvh_control_panel


def generate_report_tables(report_tables_data):
    """
    This function generates a group of tables so that the plan evaluation results can be displayed. Table cells are
    created but not populated with values; the function only defines the table structure and layout.

    Parameters
    ----------
    report_tables_data : dict
        Dictionary containing data corresponding to the plan evaluation results.

    Returns
    -------
    report_tables : qtpy.QtWidgets.QTabWidget
        Group of (empty) tables.
    """

    report_tables = QTabWidget()

    for table_name, table_data in report_tables_data.items():

        tab = QWidget()
        tab_layout = QVBoxLayout()
        tab_layout.setContentsMargins(10, 10, 10, 10)

        table = QTableWidget()
        table.setObjectName(table_name.lower())
        table.setRowCount(table_data.shape[0])
        table.setColumnCount(table_data.shape[1])
        table.setHorizontalHeaderLabels(table_data.columns.tolist())

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setDefaultSectionSize(35)
        table.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setShowGrid(True)

        tab_layout.addWidget(table)
        tab.setLayout(tab_layout)

        report_tables.addTab(tab, table_name)

    return report_tables


def generate_status_bar_panel():
    """
    This function generates a panel that acts as a container for a status bar.

    Returns
    -------
    status_bar_panel : qtpy.QtWidgets.QWidget
        Panel containing a status bar.

    status_bar : qtpy.QtWidgets.QStatusBar
        Status bar contained within the panel, used to display progress messages to the user.
    """

    status_bar_panel = QWidget()
    status_bar_panel.setObjectName("status_bar_panel")
    status_bar_panel_layout = QVBoxLayout()
    status_bar_panel_layout.setContentsMargins(5, 5, 5, 5)

    status_bar = QStatusBar()
    status_bar.setObjectName("status_bar")
    status_bar.showMessage("Ready")

    status_bar_panel_layout.addWidget(status_bar)
    status_bar_panel.setLayout(status_bar_panel_layout)

    return status_bar_panel, status_bar


def generate_menu_button(label, menu_items_labels):
    """
    This function generates a button corresponding to a dropdown menu, which is used to group buttons (QAction widgets)
    of similar functionality.

    Parameters
    ----------
    label : str
        Descriptive text appearing on the button.

    menu_items_labels : list of str
        List containing strings that act as descriptive text appearing on the QAction widgets.

    Returns
    -------
    button : qtpy.QtWidgets.QToolButton
        Button corresponding to a dropdown menu.
    """

    button = QToolButton()
    button.setText(label)
    button.setPopupMode(QToolButton.InstantPopup)

    menu = QMenu(button)

    for item_label in menu_items_labels:

        menu.addAction(item_label)

    button.setMenu(menu)

    return button


def generate_buttonbar(buttons):
    """
    This function generates a button bar that acts as a container for the gui buttons.

    Parameters
    ----------
    buttons : list of QPushButton/QToolButton widgets.
        List containing the gui buttons to be added to the button bar.

    Returns
    -------
    buttonbar : QWidget
        Buttonbar.
    """

    buttonbar = QWidget()
    buttonbar.setObjectName("buttonBar")
    buttonbar_layout = QHBoxLayout()
    buttonbar_layout.setContentsMargins(5, 5, 5, 5)
    buttonbar_layout.setSpacing(5)
    buttonbar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

    for button in buttons:
        buttonbar_layout.addWidget(button)

    buttonbar.setLayout(buttonbar_layout)

    return buttonbar


def customize_viewer(viewer):
    """
    This function modifies a (blank) napari viewer to create a minimal version, suitable for gui-embedding. A series of
    control buttons are "deactivated" (hided) on purpose, so that there is no signal mixing due to the existence of two
    napari viewers, embedded on the gui.

    Parameters
    ----------
    viewer : napari.viewer.Viewer
        Napari viewer.
    """

    viewer.window._qt_window._qt_viewer.setStyleSheet("background-color: black")
    viewer.window._qt_window._qt_viewer.viewerButtons.setVisible(False)
    viewer.window._qt_window._qt_viewer.layerButtons.setVisible(False)
    viewer.window._qt_window._qt_viewer._welcome_widget.setVisible(False)
    viewer.window._qt_window.menuBar().setVisible(False)
    viewer.window._qt_window.statusBar().setVisible(False)

    return None