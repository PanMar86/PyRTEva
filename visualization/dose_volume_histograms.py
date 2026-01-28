import pyqtgraph as pg


def plot_dose_volume_histograms(dose_volume_histograms, prescribed_dose):
    """
    This function creates a PyQtGraph PlotWidget displaying normalized cumulative dose–volume histograms for multiple
    structures.

    Parameters
    ----------
    dose_volume_histograms : list of dict
        List of generated DVHs.

    prescribed_dose : float
        Prescribed dose, expressed in Gy.

    Returns
    -------
    figure : pyqtgraph.PlotWidget
        A PyQtGraph PlotWidget object containing the rendered DVH plots. This widget will be embedded (in a later stage)
        in a Qt-based gui layout.
    """

    figure = pg.PlotWidget()

    # Disable mouse actions
    figure.setMenuEnabled(False)
    figure.setMouseEnabled(x = False, y = False)

    # Customize the figure's appearance.
    figure.setStyleSheet("border: none")
    figure.showGrid(x = True, y = True, alpha = 0.25)
    figure.getPlotItem().setTitle("<span style='font-size:12pt; font-weight:bold'>Dose Volume Histograms</span>")
    x_axis = figure.getPlotItem().getAxis('bottom')
    x_axis.setLabel("Dose (Gy)")
    y_axis = figure.getPlotItem().getAxis('left')
    y_axis.setLabel("Volume (%)")

    # Customize the legend box end place it accordingly.
    legend = pg.LegendItem()
    legend.setBrush("#000000")
    legend.setPen("#505050")
    legend.setParentItem(figure.getPlotItem())
    legend.anchor((1, 0), (1, 0), (-5, 55))

    # Save up some space at the right in order for the legend box not to collide with the line plots.
    view_box = figure.getPlotItem().getViewBox()
    view_box.setRange(xRange = (0, prescribed_dose + 10), yRange = (0, 100))

    for color_index, dvh in enumerate(dose_volume_histograms):

        x = dvh['DoseBinEdges']
        y = dvh['NormalizedCumulativeDoseVolumeHistogram']
        label = dvh["StructureName"]
        color = pg.intColor(color_index, hues = len(dose_volume_histograms), alpha = 150)
        dvh_plot = figure.plot(x, y, pen = color)
        legend.addItem(dvh_plot, label)

    return figure