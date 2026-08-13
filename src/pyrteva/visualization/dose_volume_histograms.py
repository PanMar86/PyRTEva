import logging

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
    dvhs_plot : pyqtgraph.widgets.PlotWidget.PlotWidget
        Object containing the rendered dose volume histogram figures. This widget will be embedded (in a later stage)
        in a Qt-based gui layout.
    """

    logger = logging.getLogger(__name__)

    dvhs_plot = pg.PlotWidget()
    dvhs_plot.setObjectName("dvh_plots")

    # Disable mouse actions
    dvhs_plot.setMenuEnabled(False)
    dvhs_plot.setMouseEnabled(x = False, y = False)

    # Customize the figure's appearance.
    dvhs_plot.showGrid(x = True, y = True, alpha = 0.25)
    dvhs_plot.getPlotItem().setTitle("Dose Volume Histograms")
    x_axis = dvhs_plot.getPlotItem().getAxis('bottom')
    x_axis.setLabel("Dose (Gy)")
    y_axis = dvhs_plot.getPlotItem().getAxis('left')
    y_axis.setLabel("Volume (%)")

    for color_index, dvh in enumerate(dose_volume_histograms):

        x = dvh['DoseBinEdges']
        y = dvh['NormalizedCumulativeDoseVolumeHistogram']
        label = dvh["StructureName"]
        color = pg.intColor(color_index, hues = len(dose_volume_histograms), alpha = 150)
        dvh_plot = dvhs_plot.plot(x, y, pen = color)
        dvh_plot.setObjectName(label.lower())

    logger.info("Dose volume histograms have been plotted.")

    return dvhs_plot