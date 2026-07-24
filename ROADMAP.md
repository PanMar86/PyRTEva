# Roadmap

This document provides a list of planned improvements as well as future directions for PyRTEva.
Development priorities might change as the project is continuously evolving.


## Short-term 

### Features
- Support for additional treatment sites (H&N, prostate)
- Additional visualization modes

## Medium-term

### Features
- Interactive highlighting of DVHs corresponding to violated dose constraints
- Inspectable DVHs via mouse hovering
- Surface DVHs
- Automated treatment plan evaluation report generation
- Support for CT windowing (WL and WW)
- Sagittal and coronal view modes
- User-defined dose constraints
- Support for additional fractionation schemes (SRS, SBRT)

### Refactoring
- Extension of the dose grid interpolation function (additional CT series - dose grid spatial arrangements)
- Generalization of the equations mapping 3D space point coordinates to CT series voxels
- Optimization of the structures masks generation function
- Creation of CSV files describing dose constraints, and modification 
  of the associated functions (migrating from pandas dataframes)
- Handling of GUI freezing during heavy computations
- Appropriate event handling for multiple napari viewers