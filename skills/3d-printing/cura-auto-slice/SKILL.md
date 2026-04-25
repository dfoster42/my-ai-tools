---
name: cura-auto-slice
description: Automated STL analysis, bed arrangement, and AI-optimized slicing using CuraEngine. Use when you need to slice multiple models with custom settings based on their geometry.
---

# Cura Auto Slice

This skill provides automated workflows for preparing 3D print files (G-code) from STLs using `CuraEngine`. It analyzes model geometry to suggest optimal print settings and arranges models on the bed to avoid collisions.

## Key Features

- **Geometry Analysis**: Automatically detects model volume, height, and thin features.
- **AI-Optimized Settings**: 
    - Adjusts layer height (0.12mm to 0.28mm) based on model height and volume.
    - Scales infill (10% to 40%) for small or tall models to ensure strength.
    - Modifies print speeds (40mm/s to 70mm/s) based on feature size.
- **Collision Avoidance**: Arranges multiple STLs on a 300x300mm bed using a shelf-packing algorithm.
- **Direct Slicing**: Generates robust `CuraEngine` commands that include all necessary machine and extruder-level overrides.

## Workflow

1. **Analysis**: Use `scripts/smart_arrange.py <directory>` to analyze a folder of STLs.
2. **Review**: Review the suggested settings and layout coordinates.
3. **Execution**: Run the generated `CuraEngine` command to produce the final `output.gcode`.

## Resource Locations

- **Main Script**: `scripts/smart_arrange.py`
- **Machine Definitions**: Uses Longer LK5 Pro and FDMPrinter defaults from the system's Cura application bundle.
