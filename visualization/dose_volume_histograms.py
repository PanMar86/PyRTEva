import pyqtgraph as pg


def generate_dose_volume_histogram_plots(dose_volume_histograms):
    """
    This function creates a PyQtGraph PlotWidget displaying normalized cumulative dose–volume histograms for multiple
    structures.

    Parameters
    ----------
    dose_volume_histograms : list of dict
        List of generated DVHs.

    Returns
    -------
    dvh_plots : pyqtgraph.PlotWidget
        A PyQtGraph PlotWidget object containing the rendered DVH plots. This widget will be embedded (in a later stage)
        in a Qt-based gui layout.
    """

    dvh_plots = pg.PlotWidget()
    dvh_plots.setObjectName("dvh_plots")

    # Disable mouse actions
    dvh_plots.setMenuEnabled(False)
    dvh_plots.setMouseEnabled(x = False, y = False)

    # Customize the figure's appearance.
    dvh_plots.showGrid(x = True, y = True, alpha = 0.25)
    dvh_plots.getPlotItem().setTitle("Dose Volume Histograms")
    x_axis = dvh_plots.getPlotItem().getAxis('bottom')
    x_axis.setLabel("Dose (Gy)")
    y_axis = dvh_plots.getPlotItem().getAxis('left')
    y_axis.setLabel("Volume (%)")

    for color_index, dvh in enumerate(dose_volume_histograms):

        x = dvh['DoseBinEdges']
        y = dvh['NormalizedCumulativeDoseVolumeHistogram']
        label = dvh["StructureName"]
        color = pg.intColor(color_index, hues = len(dose_volume_histograms), alpha = 150)
        dvh_plot = dvh_plots.plot(x, y, pen = color)
        dvh_plot.setObjectName(label.lower())

    return dvh_plots