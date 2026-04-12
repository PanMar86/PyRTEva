import numpy as np
import matplotlib
import napari
from napari.utils import Colormap, colormaps


def generate_visualisation(ct_series, ct_series_acquisition_parameters, structures_masks, dose_maps,
                           prescribed_doses, visualization_mode, display_mode, optimization_structures_inclusion):
    """
    This function generates and configures a multi-layer Napari viewer. The visualization and display modes dictate
    which types of layers (CT series, dose map, structure mask, advanced visualization layer) are present on the viewer.

    Parameters
    ----------
    ct_series : list of dict
        List of slices sorted superior to inferior.

    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    structures_masks : list of dict
        List of generated structures masks.

    dose_maps : dict
        Dictionary containing the generated dose maps.

    prescribed_doses : list
        Prescribed dose values, expressed in Gy.

    visualization_mode : str
        Visualization mode. Supported modes are:
        - "Standard" : conventional dose visualization mode.
        - "Dose Homogeneity" : visualization mode that highlights underdosed and overdosed regions.
        - "Dose Gradient" : dose gradient visualization mode.

    display_mode : str
        Display mode. Supported modes are:
        - "2D" : Two-dimensional visualization.
        - "3D" : Three-dimensional visualization.

    optimization_structures_inclusion : bool
        Whether to include the optimization structures or not.

    Returns
    -------
    viewer : napari.Viewer
        Configured napari viewer containing layers dictated by the visualization and display modes.
    """

    # Set up some custom colormaps before the viewer creation.
    custom_colormaps = generate_custom_colormaps()
    colormaps.AVAILABLE_COLORMAPS.clear()
    for custom_colormap in custom_colormaps:
        colormaps.AVAILABLE_COLORMAPS.update({custom_colormap.name : custom_colormap})

    # Switch between different visualization modes.
    if visualization_mode == "Standard":
        viewer, scale = standard_visualisation_mode(ct_series_acquisition_parameters, structures_masks, dose_maps, display_mode, optimization_structures_inclusion)
    elif visualization_mode == "Dose Homogeneity":
        viewer, scale = dose_homogeneity_visualisation_mode(ct_series_acquisition_parameters, structures_masks, dose_maps, prescribed_doses, display_mode)
    elif visualization_mode == "Dose Gradient":
        viewer, scale = dose_gradient_visualisation_mode(ct_series_acquisition_parameters, structures_masks, dose_maps, display_mode)

    # Create the CT Series layer, which is common to all visualization modes.
    for structure_mask in structures_masks:
        if structure_mask["StructureType"] == "External Body Contour":
            ct_series = np.stack([slice["Image"] for slice in ct_series], axis=0)
            # After applying the body contour mask (in order to hide/remove structures outside the patient's anatomy),
            # regions outside patient's anatomy will have zero values, messing up with the proper visualisation of HUs.
            # Adding an offset value before the application of the mask immediately solves the problem.
            maximum_hu_value = np.max(ct_series)
            minimum_hu_value = np.min(ct_series)
            offset = np.abs(minimum_hu_value)
            ct_series += offset
            ct_series = np.where(structure_mask["VolumetricMask"] != 0, ct_series, 0)
            # Revert back to original HU values.
            ct_series -= offset
            viewer.add_image(ct_series, name="CT Series", scale=scale, blending="additive", contrast_limits=[minimum_hu_value, maximum_hu_value])
            break

    # Re-order the CT Series layer.
    viewer.layers.move(viewer.layers.index("CT Series"), 0)

    return viewer


def standard_visualisation_mode(ct_series_acquisition_parameters, structures_masks, dose_maps, display_mode, optimization_structures_inclusion):
    """
    This function creates and configures a multi-layer napari viewer. The viewer contains layers associated with the
    CT series, the dose map and the structures masks.

    Parameters
    ----------
    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    structures_masks : list of dict
        List of generated structures masks.

    dose_maps : dict
        Dictionary containing the generated dose maps.

    display_mode : str
        Display mode. Supported modes are:
        - "2D" : Two-dimensional visualization.
        - "3D" : Three-dimensional visualization.

    optimization_structures_inclusion : bool
        Whether to include the optimization structures or not.

    Returns
    -------
    viewer : napari.Viewer
        Configured napari viewer containing layers associated with the CT series, the dose map
        and the structures masks.

    scale : list of float
        Spatial scaling applied to the viewer layers.
    """

    if display_mode == "2D":
        viewer = napari.Viewer(ndisplay=2, show = False)
        scale = ct_series_acquisition_parameters["PixelSpacing"]
    elif display_mode == "3D":
        viewer = napari.Viewer(ndisplay=3, show = False)
        scale = [ct_series_acquisition_parameters["SliceThickness"], ct_series_acquisition_parameters["PixelSpacing"][0],
                 ct_series_acquisition_parameters["PixelSpacing"][1]]

    # Determine the structures that will be included in the standard visualization mode.
    if optimization_structures_inclusion:
        included_structure_types = ["Tumorous Structure", "Tumorous Structure (Optimization)", "Organ At Risk", "Organ At Risk (Optimization)"]
    elif not optimization_structures_inclusion:
        included_structure_types = ["Tumorous Structure", "Organ At Risk"]

    # Create the various visualization layers.
    for structure_mask in structures_masks:
        if structure_mask["StructureType"] == "External Body Contour":
            # Create the dose map layer.
            dose_map = np.where(structure_mask["VolumetricMask"] != 0, dose_maps["VolumetricDoseMap"], 0)
            # In some cases, the heavy skewness of the dose distribution in conjunction with the normalization step
            # and the automatic set-up of the contrast limits prior to the visualization, produces extreme color
            # saturation. Therefore, the contrast limits are set manually.
            maximum_dose = np.max(dose_map)
            viewer.add_image(dose_map, name = "Dose Map", scale = scale, opacity = 0.50,
                             blending = "additive", contrast_limits = [0, maximum_dose], colormap = "turbo")
        elif structure_mask["StructureType"] in included_structure_types:
            viewer.add_image(structure_mask["VolumetricMask"], name = structure_mask["StructureName"], scale = scale,
                             opacity = 0.30, blending = "additive", contrast_limits = [0, 1], visible = False)

    # Re-order the Dose Map layer.
    viewer.layers.move(viewer.layers.index("Dose Map"), 0)

    return viewer, scale


def dose_homogeneity_visualisation_mode(ct_series_acquisition_parameters, structures_masks, dose_maps, prescribed_doses, display_mode):
    """
    This function creates and configures a multi-layer napari viewer. The viewer contains layers associated with the
    CT series and the dose homogeneity maps of the tumorous structures. The dose homogeneity maps serve as a mean of
    visualizing the deviations from the prescribed dose (which might be different for each tumorous structure).
    The contrast window of each homogeneity map is centered with respect to the prescribed dose value, so that in
    conjunction with a diverging colormap, the underdosed and overdosed regions inside the tumorous structures are
    clearly highlighted.

    Parameters
    ----------
    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    structures_masks : list of dict
        List of generated structures masks.

    dose_maps : dict
        Dictionary containing the generated dose maps.

    prescribed_doses : list of dict
        List of dose prescription parameters for each structure.

    display_mode : str
        Display mode. Supported modes are:
        - "2D" : Two-dimensional visualization.

    Returns
    -------
    viewer : napari.Viewer
        Configured napari viewer containing layers associated with the CT series and the dose homogeneity maps.

    scale : list of float
        Spatial scaling applied to the viewer layers.
    """

    if display_mode == "2D":
        viewer = napari.Viewer(ndisplay = 2, show = False)
        scale = ct_series_acquisition_parameters["PixelSpacing"]
    elif display_mode == "3D":
        raise ValueError("3D Dose Homogeneity mode is not supported in the current version.")

    # Create the various visualization layers.
    for structure_mask in structures_masks:
        if structure_mask["StructureType"] == "Tumorous Structure":
            prescribed_dose = [prescribed_dose["PrescribedDose"] for prescribed_dose in prescribed_doses
                               if prescribed_dose["StructureName"] == structure_mask["StructureName"]][0]
            dose_homogeneity_map = np.where(structure_mask["VolumetricMask"], dose_maps["VolumetricDoseMap"], 0)
            minimum_dose = np.min(dose_homogeneity_map[dose_homogeneity_map != 0])
            maximum_dose = np.max(dose_homogeneity_map)
            # https://matplotlib.org/stable/users/explain/colors/colormaps.html
            # It is highly recommended that a diverging colormap be used for the proper visualization of the
            # dose homogeneity map.
            contrast_window_width = 2 * np.max([maximum_dose - prescribed_dose, prescribed_dose - minimum_dose])
            viewer.add_image(dose_homogeneity_map, name = f"Homogeneity Map ({structure_mask["StructureName"]})", scale=scale, opacity=0.70,
                             blending="additive", contrast_limits=[prescribed_dose - (contrast_window_width / 2), prescribed_dose + (contrast_window_width / 2)],
                             colormap="seismic", visible=False)

    return viewer, scale


def dose_gradient_visualisation_mode(ct_series_acquisition_parameters, structures_masks, dose_maps, display_mode):
    """
    This function creates and configures a multi-layer napari viewer. The viewer contains layers associated with the
    CT series, the structures masks and the dose gradient maps of the planning target volumes (PTVs). The dose gradient
    maps serve as a mean of visualizing the magnitude of the dose gradient in the region between the PTVs and the patient's
    external surface.

    Parameters
    ----------
    ct_series_acquisition_parameters : dict
        Dictionary containing acquisition parameters.

    structures_masks : list of dict
        List of generated structures masks.

    dose_maps : dict
        Dictionary containing the generated dose maps.

    display_mode : str
        Display mode. Supported modes are:
        - "2D" : Two-dimensional visualization.

    Returns
    -------
    viewer : napari.Viewer
        Configured napari viewer containing layers associated with the CT series, the PTV volumetric mask
        and the dose gradient map.

    scale : list of float
        Spatial scaling applied to the viewer layers.
    """

    if display_mode == "2D":
        viewer = napari.Viewer(ndisplay = 2, show = False)
        scale = ct_series_acquisition_parameters["PixelSpacing"]
    elif display_mode == "3D":
        raise ValueError("3D Dose Gradient mode is not supported in the current version.")

    for structure_mask in structures_masks:
        if structure_mask["StructureType"] == "External Body Contour":
            body_contour_mask = structure_mask["VolumetricMask"]
            break

    for structure_mask in structures_masks:
        # Identify all the structures masks associated with planning target volumes (ptvs).
        if (structure_mask["StructureType"] == "Tumorous Structure") and ("ptv" in structure_mask["StructureName"].lower()):
            # The following mask is used to exclude the ptv region from the patient's anatomy.
            gradient_shell_mask = structure_mask["VolumetricMask"] ^ body_contour_mask
            dose_gradient = np.gradient(dose_maps["VolumetricDoseMap"], ct_series_acquisition_parameters["SpacingBetweenSlices"],
                                        ct_series_acquisition_parameters["PixelSpacing"][0], ct_series_acquisition_parameters["PixelSpacing"][1])
            dose_gradient_magnitude = np.sqrt(np.power(dose_gradient[0],2) + np.power(dose_gradient[1],2) + np.power(dose_gradient[2],2))
            dose_gradient_map = np.where(gradient_shell_mask, dose_gradient_magnitude, 0)
            maximum_dose_gradient = np.max(dose_gradient_map)
            viewer.add_image(dose_gradient_map, name = f"Gradient Map ({structure_mask["StructureName"]}) ", scale = scale, blending= "additive",
                             contrast_limits = [0, maximum_dose_gradient], colormap = "hot", visible=False)
            viewer.add_image(structure_mask["VolumetricMask"], name = structure_mask["StructureName"], scale = scale, opacity = 0.30, blending= "additive",
                             contrast_limits = [0, 1], visible=False)

    return viewer, scale


def generate_custom_colormaps():
    """
    This function builds a set of colormaps combining standard Matplotlib sequential colormaps and
    manually defined, two-color colormaps.

    Returns
    -------
    custom_cmaps : list of napari.utils.Colormap
        A list of customized colormaps compatible with Napari.
    """

    cmaps_names = ["afmhot", "cividis", "copper", "gist_heat", "gray", "hot",
                   "inferno",  "magma", "plasma", "seismic", "turbo", "viridis"]

    # These colormaps consist of only two (rgba type) colors.
    degenerated_cmaps = {"blue": [[0, 0, 0, 1],[0, 0, 1, 1]], "bronze": [[0, 0, 0, 1], [0.8, 0.5, 0.2, 1]],
                         "green": [[0, 0, 0, 1], [0, 1, 0, 1]], "orange": [[0, 0, 0, 1], [1, 0.5, 0, 1]],
                         "pink": [[0, 0, 0, 1], [1, 0, 1, 1]], "purple": [[0, 0, 0, 1], [0.5, 0, 0.5, 1]],
                         "red": [[0, 0, 0, 1], [1, 0, 0, 1]], "turquoise": [[0, 0, 0, 1], [0, 1, 1, 1]],
                         "white": [[0, 0, 0, 1], [1, 1, 1, 1]], "yellow": [[0, 0, 0, 1], [1, 1, 0, 1]]}

    custom_cmaps = []

    for cmap_name in cmaps_names:

        base_cmap = matplotlib.colormaps[cmap_name]
        colors = base_cmap(np.arange(base_cmap.N))

        # First color of the colormap is set to black, so that the visualized structures blend seamlessly with the black
        # canvas. Gray colormap doesn't need to be altered.
        if cmap_name != "gray":

            colors[0] = [0, 0, 0, 1]

        custom_cmap = Colormap(colors, name = cmap_name.lower())
        custom_cmaps.append(custom_cmap)

    for name, colors  in degenerated_cmaps.items():

        custom_cmap = Colormap(colors = [colors[0], colors[1]], name = name)
        custom_cmaps.append(custom_cmap)

    return custom_cmaps