# PLAXIS 2D Python API Practical Tutorial

## Overview

This repository contains 8 geotechnical numerical analysis projects built with the **PLAXIS 2D 2024 Python API**. The projects progress from beginner to advanced level, covering the most common analysis types in geotechnical engineering practice. All scripts have been tested and verified on **PLAXIS 2D 2024.1.0.1060**.

---

## Project Descriptions

### 01 Slope Stability Analysis
A slope stability analysis using the Strength Reduction Method (Phi-c Reduction). The model features a single Mohr-Coulomb soil layer with a groundwater table. The safety factor (FOS) is extracted directly from the PLAXIS output after incremental multiplier loading. The computed FOS of 1.81 indicates a stable slope with adequate safety margin.

### 02 Excavation Analysis
A multi-stage underwater excavation simulation modeled after a real-world cofferdam problem. The model includes a diaphragm wall (plate element), internal strut (fixed-end anchor), two soil layers (Soft Soil clay and Hardening Soil sand), and interface elements. Three excavation stages are simulated sequentially, with wall bending moments and displacements extracted at each stage.

### 03 Consolidation Settlement Analysis
A time-dependent consolidation settlement analysis of a soft clay foundation under surcharge loading. The model uses the Soft Soil constitutive model with a double-layer profile (soft clay over sand). Settlement and excess pore pressure are tracked over time intervals of 30, 100, and 365 days, demonstrating the gradual dissipation of excess pore pressure and long-term settlement behavior.

### 04 Bearing Capacity Analysis
A strip footing bearing capacity analysis combining Terzaghi's classical formula with PLAXIS numerical simulation. The theoretical ultimate bearing capacity is computed analytically and compared against the PLAXIS result obtained through load-controlled plastic analysis. The comparison provides insight into the difference between classical theory and numerical methods.

### 05 Tunnel Excavation Analysis
A circular tunnel excavation analysis using the contraction method, simulating shield tunneling in soft ground. The model includes a concrete lining (plate element) activated after stress release. Ground surface settlement, lining bending moments, and axial forces are extracted from the output, with results consistent with analytical expectations for circular tunnels in elastic ground.

### 06 Parametric Study
An automated parametric study built on the slope stability model. Three independent parameters are varied systematically: friction angle (φ), cohesion (c), and slope ratio. For each parameter set, PLAXIS runs a full Safety analysis and returns the FOS. Results are visualized using matplotlib, producing three FOS-vs-parameter curves that illustrate the sensitivity of slope stability to each input.

### 07 Seismic Dynamic Response Analysis
A seismic ground response analysis in which a harmonic base excitation (0.1g, 2 Hz) is applied to the bottom of a uniform sand deposit. The dynamic analysis uses Newmark time integration with Rayleigh damping. Surface acceleration and displacement time histories are extracted, and the acceleration amplification factor is computed to characterize the site response.

### 08 Dam Seepage Analysis
A steady-state seepage analysis of a homogeneous earth dam under upstream and downstream water level conditions. A user-defined phreatic line is specified through the dam body to simulate the internal seepage surface. The analysis extracts the hydraulic head distribution, maximum hydraulic gradient, and seepage velocity, which are key indicators for evaluating dam safety against piping and internal erosion.

---

## Key Technical Notes

### Connection
```python
s_i, g_i = new_server("localhost", 10000, password=passwd,
                       timeout=3600, request_timeout=3600)
```
The `timeout` and `request_timeout` parameters must be set to a large value to prevent disconnection during long calculations.

### Mode Switching
```python
g_i.gotostructures()   # Geometry and structural elements
g_i.gotosoil()         # Soil layer assignment
g_i.gotowater()        # Groundwater conditions
g_i.gotomesh()         # Mesh generation
g_i.gotoflow()         # Flow conditions
g_i.gotostages()       # Staged construction
```

### Calculation Types
```python
phase.DeformCalcType = "plastic"          # Plastic
phase.DeformCalcType = "consolidation"    # Consolidation
phase.DeformCalcType = "safety"           # Safety (= 7)
phase.DeformCalcType = "dynamics"         # Dynamic
phase.DeformCalcType = "fullycoupledflowdeformation"  # Fully coupled
```

### Output Server
After calculation, the project must be saved and reopened via the Output server to access all phase results:
```python
g_i.save(r"path\to\file.p2dx")
s_o, g_o = new_server("localhost", 10001, password=passwd,
                       timeout=3600, request_timeout=3600)
s_o.open(r"path\to\file.p2dx")
```

---

## Environment
- PLAXIS 2D 2024.1.0.1060
- Python 3.x
- plxscripting
- matplotlib
- numpy

