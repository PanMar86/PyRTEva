import napari
from qtpy.QtWidgets import (QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout, QToolButton, QMenu,
                            QStatusBar,QTableWidget, QTabWidget, QHeaderView, QAbstractItemView)
from qtpy.QtCore import Qt


def generate_main_window():
    """
    This function generates the gui main window. It sets up a QWidget (acting as the main window), and applies
    custom styling.

    Returns
    -------
    window : qtpy.QtWidgets.QWidget
        Main gui window.
    """

    main_window = QWidget()
    main_window.setWindowTitle("PyRTEva, an experimental radiation therapy plan evaluator, based οn Python")
    main_window.setGeometry(100, 100, 1200, 800)
    main_window.setStyleSheet("background-color: #1E1E2F; border: 2px solid #6B6F83; border-radius: 6px")

    window_layout = QGridLayout()
    window_layout.setSpacing(5)
    window_layout.setContentsMargins(5, 5, 5, 5)
    main_window.setLayout(window_layout)

    return main_window


def generate_viewer_panel(panel_name):
    """
    This function generates a panel that acts as a container for a Napari viewer. It sets up a QWidget with a vertical
    box layout (although the widget container is expected to hold only one element), embeds a blank viewer, and applies
    custom styling. The viewer is further customized via the "customize_viewer" function. Later on, the blank viewer is
    replaced by a viewer containing all the relevant image layers.

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
    viewer_panel.setStyleSheet("background-color: #23263A; border: 2px solid #6B6F83; border-radius: 6px")

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
    composite_panel.setStyleSheet("background-color: black; border: 2px solid #6B6F83; border-radius: 6px")

    temporary_content = QLabel(label)
    temporary_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
    temporary_content.setStyleSheet("font-size: 18px; color: #E8E8F0; background-color:transparent; border: none")

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
    report_tables.setStyleSheet(""" QTabWidget::pane {border: none; padding-left: 0px; padding-top: 4px; padding-right: 0px; padding-bottom: 0px}
                                       QTabBar {border: none}
                                       QTabBar::tab {background-color: #3B3F58; color: #E8E8F0; border: 1px solid #6B6F83; border-radius: 2px;
                                                     margin-right: 5px; width: 180px; height: 24px; font-size: 13px}
                                       QTabBar::tab:hover {border-color: #B5B5BA}               
                                       QTabBar::tab:pressed {border-color: black}
                                       QTabBar::tab:selected {border-color: #B5B5BA}
                                       QTableWidget {gridline-color: #6B6F83; background-color: black; color: #E8E8F0} 
                                       QTabWidget QTableWidget QHeaderView::section:horizontal {background-color: #7D510B;
                                                                                                color: #E8E8F0;
                                                                                                border: 1px solid #6B6F83}   
                                       QTabWidget QTableWidget QHeaderView::section:vertical   {background-color: black;
                                                                                                color: #E8E8F0;
                                                                                                border: 1px solid #6B6F83}                                                                      
                                       QToolTip {background-color: #3B3F58; color: #E8E8F0; border: 1px solid #6B6F83;
                                                 border-radius: 2px; padding: 2px; font-size: 14px}""")

    for table_name, table_data in report_tables_data.items():

        tab = QWidget()
        tab.setStyleSheet("QWidget {border: none; font-size: 15px}")

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
    status_bar_panel.setStyleSheet("background-color: black; border: 2px solid #6B6F83; border-radius: 6px")

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
    button.setStyleSheet(""" QPushButton {font-size: 14px; background-color: #3B3F58; color: #E8E8F0; border: 1px solid #6B6F83; border-radius: 2px}
                             QPushButton:hover {border-color: #B5B5BA}               
                             QPushButton:pressed {border-color: #6B6F83}""")

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
    button.setStyleSheet(""" QToolButton::menu-indicator {image: none} 
                             QToolButton {font-size: 14px; background-color: #3B3F58; color: #E8E8F0; border: 1px solid #6B6F83; border-radius: 2px}
                             QToolButton:hover {border-color: #B5B5BA}
                             QToolButton:pressed {border-color: #6B6F83}""")

    menu = QMenu(button)
    menu.setFixedWidth(200)

    for item_label in menu_item_labels:
        menu.addAction(item_label)

    menu.setStyleSheet(""" QMenu {background-color: #3B3F58; border: none}
                           QMenu::item {font-size: 14px; background-color: #3B3F58; color: #E8E8F0; border: 1px solid #6B6F83; border-radius: 2px; 
                                        padding-left: 25px; padding-top: 5px; padding-bottom: 5px}
                           QMenu::item:selected {border-color: #B5B5BA}
                           QMenu::item:pressed {border-color: #6B6F83}""")

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
    buttonbar.setStyleSheet("background-color: #1E1E2F; border: 2px solid #6B6F83; border-radius: 6px")

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