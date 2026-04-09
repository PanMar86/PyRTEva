import napari
from qtpy.QtWidgets import (QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout, QToolButton, QDialog,
                            QGroupBox, QMenu, QComboBox, QDoubleSpinBox, QScrollArea, QSpinBox, QStatusBar,QTableWidget, QMessageBox,
                            QTabWidget, QHeaderView, QAbstractItemView)
from qtpy.QtCore import Qt, QSize


def generate_main_window():
    """
    This function generates the gui main window (custom styling is applied via a qss file).

    Returns
    -------
    main_window : qtpy.QtWidgets.QWidget
        Main gui window.
    """

    main_window = QWidget()
    main_window.setObjectName("main_window")
    main_window.setWindowTitle("PyRTEva, an experimental radiation therapy plan evaluator, based οn Python")
    make_window_layout = QGridLayout()
    make_window_layout.setContentsMargins(5, 5, 5, 5)
    main_window.setLayout(make_window_layout)

    with open("gui/custom_styles/main_window.qss", mode="r") as main_window_qss:
        main_window.setStyleSheet(main_window_qss.read())

    return main_window


def generate_user_preferences_window(data_container):
    """
    This function generates an auxiliary window that acts as a user interaction panel (custom styling is applied via a qss file).

    Parameters
    ----------
    data_container : dict
    	Shared data container.

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
        	Container of the combo-boxes corresponding to the type of the structures.

        parent_widget : qtpy.QtWidgets.QDialog
            Parent widget of the pop-up message-boxes.
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
        This function activates / deactivates (if necessary) the widget associated with the prescribed dose, each time the user
        assigns a different structure type than the one having already been assigned.

        Parameters
        ----------
        signal_text : str
            User-assigned structure type.

        widget : qtpy.QtWidgets.QSpinBox
            Prescribed dose widget.
        """

        if (signal_text not in ["Tumorous Structure", "Tumorous Structure (Optimization)"]) and widget.isEnabled():

            widget.setValue(0)
            widget.setDisabled(True)

        elif (signal_text in ["Tumorous Structure", "Tumorous Structure (Optimization)"]) and (not widget.isEnabled()):

            widget.setDisabled(False)

        return None


    window = QDialog()
    window.setObjectName("window")
    window.setWindowTitle("User Preferences")
    window.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
    window.setFixedSize(QSize(915, 600))
    window_layout = QVBoxLayout()
    window_layout.setSpacing(10)

    with open("gui/custom_styles/user_preferences_window.qss", mode="r") as user_preferences_window_qss:
        window.setStyleSheet(user_preferences_window_qss.read())

    alg_settings_outer_container = QGroupBox("Algorithms settings")
    alg_settings_outer_container.setObjectName("alg_setting_outer_container")
    alg_settings_outer_container_layout = QVBoxLayout()

    alg_settings_inner_container = QWidget()
    alg_settings_inner_container.setObjectName("alg_settings_inner_container")
    alg_settings_inner_container_layout = QGridLayout()
    alg_settings_inner_container_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

    dose_grid_interpolation_method = QComboBox()
    dose_grid_interpolation_method.setObjectName("dose_grid_interpolation_method")
    dose_grid_interpolation_method.addItems(["linear", "nearest", "slinear", "cubic", "quintic", "pchip"])
    dose_grid_interpolation_method.setCurrentText("cubic")

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

    structures_info_scrollable_area = QScrollArea()
    structures_info_scrollable_area.setObjectName("structures_info_scrollable_area")
    structures_info_scrollable_area.setWidgetResizable(True)

    structures_info_inner_container = QWidget()
    structures_info_inner_container.setObjectName("structures_info_inner_container")
    structures_info_inner_container_layout = QVBoxLayout()

    structure_types = ["Tumorous Structure", "Tumorous Structure (Optimization)", "Organ At Risk",
                       "Organ At Risk (Optimization)", "External Body Contour", "Other"]

    for structure in data_container["Structures"]:

        structure_info = QGroupBox()
        structure_info_layout = QHBoxLayout()
        structure_info_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        structure_type = QComboBox()
        structure_type.setObjectName(structure["StructureName"].lower() + "_type")
        structure_type.addItems(structure_types)
        structure_type.setCurrentText(structure["StructureType"])

        structure_prescribed_dose = QSpinBox()
        structure_prescribed_dose.setObjectName(structure["StructureName"].lower() + "_prescribed_dose")
        structure_prescribed_dose.setRange(0,100)
        structure_prescribed_dose.setSingleStep(1)

        if structure_type.currentText() not in ["Tumorous Structure", "Tumorous Structure (Optimization)"]:

            structure_prescribed_dose.setValue(0)
            structure_prescribed_dose.setDisabled(True)

        else:

            structure_prescribed_dose.setValue(data_container["TreatmentPlan"]["PrescribedDose"])

        # Change the state (if necessary) of the prescribed dose widget according to the user-selected structure type.
        structure_type.currentTextChanged.connect(lambda signal_text, widget = structure_prescribed_dose : change_state_prescribed_dose_widget(signal_text, widget))

        structure_info_layout.addWidget(QLabel(structure["StructureName"]))
        structure_info_layout.addWidget(QLabel("Structure type:"))
        structure_info_layout.addWidget(structure_type)
        structure_info_layout.addWidget(QLabel("Prescribed dose:"))
        structure_info_layout.addWidget(structure_prescribed_dose)
        structure_info.setLayout(structure_info_layout)

        structures_info_inner_container_layout.addWidget(structure_info)

    structures_info_inner_container.setLayout(structures_info_inner_container_layout)

    structures_info_scrollable_area.setWidget(structures_info_inner_container)

    structures_info_message = QLabel(f"They have been detected {len(data_container["Structures"])} structures. There are five structure types in total: "
                                       f"Tumorous Structure, Optimization Tumorous Structure, Organ At Risk, Optimization Organ At Risk and External (Body) Contour. "
                                       f"Please verify that the pre-assigned structure types, as well as the prescribed doses (to the structures for which are applicable) are correct.")
    structures_info_message.setWordWrap(True)

    structures_info_outer_container_layout.addWidget(structures_info_message)
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


def generate_viewer_panel(panel_name):
    """
    This function generates a panel that acts as a container for a Napari viewer. It sets up a QWidget with a vertical
    box layout (although the widget container is expected to hold only one element) and embeds a blank viewer.The viewer
    is further customized via the "customize_viewer" function. Later on, the blank viewer is replaced by a viewer containing
    all the relevant image layers.

    Parameters
    ----------
    panel_name : str
    	Name of the panel.

    Returns
    -------
    viewer_panel : qtpy.QtWidgets.QWidget
        Panel containing a Napari viewer.
    """

    viewer_panel = QWidget()
    viewer_panel.setObjectName(panel_name)

    viewer = napari.Viewer(show=False)
    customize_viewer(viewer)

    viewer_qt_widget = viewer.window._qt_window

    viewer_panel_layout = QVBoxLayout()
    viewer_panel_layout.setContentsMargins(2, 2, 2, 2)
    viewer_panel_layout.addWidget(viewer_qt_widget)
    viewer_panel.setLayout(viewer_panel_layout)

    return viewer_panel


def generate_composite_panel(panel_name, label):
    """
    This function generates a panel that acts as a generic container. It sets up a QWidget with a vertical box layout
    (although the widget container is expected to hold only one element), embeds a QLabel widget, and applies custom
    styling. Later on, the QLabel is replaced by the actual panel content (a pyqtgraph.PlotWidget corresponding to a
    dose volume histograms plot or a QTabWidget with tabs that correspond to a group of tables representing the plan
    evaluation results).

    Parameters
    ----------
    panel_name : str
        Name of the panel.

    label : str
        Descriptive text appearing on the panel (prior to the appearance of the actual content).

    Returns
    -------
    composite_panel : qtpy.QtWidgets.QWidget
        Panel containing temporary textual content.
    """

    composite_panel = QWidget()
    composite_panel.setObjectName(panel_name)

    temporary_content = QLabel(label)
    temporary_content.setAlignment(Qt.AlignmentFlag.AlignCenter)

    composite_panel_layout = QVBoxLayout()
    composite_panel_layout.setContentsMargins(5, 5, 5, 5)
    composite_panel_layout.addWidget(temporary_content)
    composite_panel.setLayout(composite_panel_layout)

    return composite_panel


def generate_report_tables(report_tables_data):
    """
    This function generates a group of tables so that the plan evaluation results can be displayed. It sets up a
    QTabWidget (with each tab being a QWidget, container of a TableWidget that corresponds to a different table), and
    applies custom styling. Table cells are created but not populated with values; the function only defines the table
    structure and layout.

    Parameters
    ----------
    report_tables_data : dict
        Dictionary containing data corresponding to the plan evaluation results.

    Returns
    -------
    report_tables : qtpy.QtWidgets.QTabWidget
        Group of tables displaying the plan evaluation results.
    """

    report_tables = QTabWidget()

    for table_name, table_data in report_tables_data.items():

        tab = QWidget()
        table = QTableWidget()
        table.setObjectName(table_name)
        table.setRowCount(table_data.shape[0])
        table.setColumnCount(table_data.shape[1])

        # Set headers' alignment.
        table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        table.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        # Adjust column width and row height.
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setFixedHeight(35)
        table.verticalHeader().setDefaultSectionSize(35)

        # Disable editing
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setShowGrid(True)

        tab_layout = QVBoxLayout()
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.addWidget(table)
        tab.setLayout(tab_layout)

        report_tables.addTab(tab, table_name)

    return report_tables


def generate_status_bar_panel(panel_name):
    """
    This function generates a panel that acts as a container for a status bar. It sets up a QWidget with a vertical box
    layout (although the widget container is expected to hold only one element), embeds a QStatusBar widget, and applies
    custom styling.

    Parameters
    ----------
    panel_name : str
        Name of the panel.

    Returns
    -------
    status_bar_panel : qtpy.QtWidgets.QWidget
        Panel containing a status bar.

    status_bar : qtpy.QStatusBar
        Status bar contained within the panel, used to display progress messages to the user.
    """

    status_bar_panel = QWidget()
    status_bar_panel.setObjectName(panel_name)

    status_bar = QStatusBar()
    status_bar.showMessage("Ready")
    status_bar.setStyleSheet("font-size: 15px; color: #E8E8F0; border: none")

    status_bar_panel_layout = QVBoxLayout()
    status_bar_panel_layout.setContentsMargins(5, 5, 5, 5)
    status_bar_panel_layout.addWidget(status_bar)
    status_bar_panel.setLayout(status_bar_panel_layout)

    return status_bar_panel, status_bar


def generate_button(label):
    """
    This function generates a clickable button (used to trigger the execution of specific callback functions) and applies
    custom styling. It sets up a QPushButton widget, and applies custom styling.

    Parameters
    ----------
    label : str
         Descriptive text appearing on the button.

    Returns
    -------
    button : qtpy.QtWidgets.QPushButton
       Clickable button.
    """

    button = QPushButton(label)
    button.setFixedWidth(200)
    button.setFixedHeight(30)

    return button


def generate_menu_button(label, menu_item_labels):
    """
    This function generates a dropdown menu, used to group clickable buttons of similar functionality. It sets up a
    QMenu and a QToolButton widget (that expands when clicked to show the available QAction objects), and applies custom
    styling.

    Parameters
    ----------
    label : str
        Descriptive text appearing on the button.

    menu_item_labels : list of str
        List containing strings that act as descriptive text appearing on the QAction objects.

    Returns
    -------
    button : qtpy.QtWidgets.QToolButton
        Clickable button corresponding to a dropdown menu.
    """

    button = QToolButton()
    button.setText(label)
    button.setFixedWidth(200)
    button.setFixedHeight(30)
    button.setPopupMode(QToolButton.InstantPopup)

    menu = QMenu(button)
    menu.setFixedWidth(200)

    for item_label in menu_item_labels:
        menu.addAction(item_label)

    button.setMenu(menu)

    return button


def generate_buttonbar(button_bar_name, buttons):
    """
    This function generates a button bar that acts as a container for the gui buttons. It sets up a QWidget with a
    horizontal box layout, embeds the QPushbutton and QToolButton widgets that correspond to the gui buttons, and applies
    custom styling.

    Parameters
    ----------
    button_bar_name : str
        Name of the button bar.

    buttons : list of QPushButton/QToolButton
        List containing the gui buttons to be added to the button bar.

    Returns
    -------
    buttonbar : QWidget
        Buttonbar.
    """

    buttonbar = QWidget()
    buttonbar.setObjectName(button_bar_name)
    buttonbar_layout = QHBoxLayout()
    buttonbar_layout.setContentsMargins(5, 5, 5, 5)
    buttonbar_layout.setSpacing(5)

    for button in buttons:
        buttonbar_layout.addWidget(button)

    buttonbar_layout.addStretch()

    buttonbar.setLayout(buttonbar_layout)

    return buttonbar


def customize_viewer(viewer):
    """
    This function modifies the given (blank) Napari viewer to create a minimal, dark-themed version suitable for
    gui-embedding. A series of control buttons are "deactivated" (hided) on purpose, so that there is no signal matching
    due to the existence of two napari viewers, embedded on the gui.

    Parameters
    ----------
    viewer : napari.viewer.Viewer
        Napari viewer whose interface elements will be modified.
    """

    viewer.window._qt_window.menuBar().setVisible(False)
    viewer.window._qt_window.statusBar().setVisible(False)

    viewer.window._qt_viewer.setStyleSheet("background-color: black")
    viewer.window._qt_viewer.viewerButtons.setVisible(False)
    viewer.window._qt_viewer.layerButtons.setVisible(False)
    viewer.window._qt_viewer._welcome_widget.setVisible(False)

    return None