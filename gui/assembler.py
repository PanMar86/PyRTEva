from gui.components import (generate_main_window, generate_viewer_panel, generate_composite_panel, generate_status_bar_panel,
                            generate_menu_button, generate_buttonbar)
from gui.callbacks import (load_patient_data, apply_user_preferences, generate_intermediate_data, display_visualisation,
                           display_dose_volume_histograms, display_evaluation_report)
from qtpy.QtWidgets import QPushButton


def assemble_gui(data_container):
    """
    This function assembles the graphical user interface (gui), initializes all gui panels, and connects the user
    interactions (clicked buttons) to their corresponding callback functions.

    Parameters
    ----------
    data_container : dict
        Dictionary acting as a data container used by the callback functions.

    Returns
    -------
    main_window : qtpy.QtWidgets.QWidget
        The assembled gui main window.
    """

    main_window = generate_main_window()

    standard_visualisation_panel = generate_viewer_panel()
    advanced_visualisation_panel = generate_viewer_panel()
    dvh_panel = generate_composite_panel("DVH Panel")
    plan_evaluation_panel = generate_composite_panel("Plan Evaluation Panel")
    status_bar_panel, status_bar = generate_status_bar_panel()

    buttons = []

    load_data_button = QPushButton("Load patient data")
    load_data_button.clicked.connect(lambda: load_patient_data(data_container, status_bar))
    buttons.append(load_data_button)

    process_data_button = QPushButton("Process patient data")
    process_data_button.clicked.connect(lambda: apply_user_preferences(data_container, status_bar))
    process_data_button.clicked.connect(lambda: generate_intermediate_data(data_container, status_bar))
    buttons.append(process_data_button)

    std_visualisations_button = generate_menu_button("Standard visualisations", ["Generate 2D visualisation", "Generate 3D visualisation"])
    std_visualisations_menu = std_visualisations_button.menu()
    std_visualisations_menu.actions()[0].triggered.connect(lambda: display_visualisation(data_container, status_bar, standard_visualisation_panel,
                                                                                         "Standard", "2D"))
    std_visualisations_menu.actions()[1].triggered.connect(lambda: display_visualisation(data_container, status_bar,standard_visualisation_panel,
                                                                                         "Standard", "3D"))
    buttons.append(std_visualisations_button)

    adv_visualisations_button = generate_menu_button("Advanced visualisations", ["Generate DH visualisation", "Generate DG visualisation"])
    adv_visualisations_menu = adv_visualisations_button.menu()
    adv_visualisations_menu.actions()[0].triggered.connect(lambda: display_visualisation(data_container, status_bar, advanced_visualisation_panel,
                                                                                         "Dose Homogeneity", "2D"))
    adv_visualisations_menu.actions()[1].triggered.connect(lambda: display_visualisation(data_container, status_bar, advanced_visualisation_panel,
                                                                                         "Dose Gradient", "2D"))
    buttons.append(adv_visualisations_button)

    dvh_button = QPushButton("Display DVHs")
    dvh_button.clicked.connect(lambda: display_dose_volume_histograms(data_container, status_bar, dvh_panel))
    buttons.append(dvh_button)

    plan_evaluation_button = QPushButton("Evaluate plan")
    plan_evaluation_button.clicked.connect(lambda: display_evaluation_report(data_container, status_bar, plan_evaluation_panel))
    buttons.append(plan_evaluation_button)

    buttonbar = generate_buttonbar(buttons)

    # Add the gui components to the main window.
    main_window.layout().addWidget(buttonbar, 0, 0, 1, 2)
    main_window.layout().addWidget(standard_visualisation_panel, 1, 0, 1, 1)
    main_window.layout().addWidget(advanced_visualisation_panel, 2, 0, 1, 1)
    main_window.layout().addWidget(dvh_panel, 1, 1, 1, 1)
    main_window.layout().addWidget(plan_evaluation_panel, 2, 1, 1, 1)
    main_window.layout().addWidget(status_bar_panel, 3, 0, 1, 2)

    # Set some properties to adjust the space occupied by the gui components.
    main_window.layout().setRowStretch(0, 1)
    main_window.layout().setRowStretch(1, 15)
    main_window.layout().setRowStretch(2, 15)
    main_window.layout().setRowStretch(3, 1)
    main_window.layout().setColumnStretch(0, 1)
    main_window.layout().setColumnStretch(1, 1)

    return main_window