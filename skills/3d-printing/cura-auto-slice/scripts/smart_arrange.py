import struct
import sys
import os
import math

# --- CONFIGURATION (Longer LK5 Pro Defaults) ---
BED_SIZE_X = 300
BED_SIZE_Y = 300
PADDING = 10  # mm between models

# Baseline settings from your "Lots of Numbers" profile
BASE_SETTINGS = {
    "speed_print": 60,
    "infill_sparse_density": 10,
    "layer_height": 0.2,
    "adhesion_type": "brim",
    "brim_line_count": 8,
    "retraction_hop_enabled": "True",
    "roofing_layer_count": 1,
    "flooring_layer_count": 1,
    "wall_thickness": 0.8,
    "top_bottom_thickness": 0.8,
    "material_print_temperature": 210,
    "material_bed_temperature": 60,
    "skirt_line_count": 1,
    "skirt_gap": 3.0,
    "speed_layer_0": 20,
    "cool_fan_enabled": "True",
    "cool_fan_full_at_height": 0.5,
    "retraction_amount": 6.5,
    "retraction_speed": 25,
    "infill_pattern": "'grid'",
    "acceleration_enabled": "False",
    "jerk_enabled": "False",
    "top_layers": 4,
    "bottom_layers": 4,
    "wall_line_count": 2,
    "optimize_wall_printing_order": "True",
    "skin_monotonic": "True",
    "speed_travel": 120,
    "retraction_enable": "True",
    "cool_min_layer_time": 5
}

def get_stl_bounds(filepath):
    """Calculates dimensions of an STL file."""
    try:
        with open(filepath, 'rb') as f:
            header = f.read(80)
            if not header: return None
            count_data = f.read(4)
            if len(count_data) < 4: return None
            num_triangles = struct.unpack('<I', count_data)[0]
            
            # Simple check for binary vs ASCII
            filesize = os.path.getsize(filepath)
            expected_binary_size = 80 + 4 + (num_triangles * 50)
            
            min_xyz = [float('inf')] * 3
            max_xyz = [float('-inf')] * 3

            if filesize == expected_binary_size:
                # Binary STL
                for _ in range(num_triangles):
                    f.seek(12, 1) # Skip normal
                    for _ in range(3): # Read 3 vertices
                        v = struct.unpack('<fff', f.read(12))
                        for i in range(3):
                            min_xyz[i] = min(min_xyz[i], v[i])
                            max_xyz[i] = max(max_xyz[i], v[i])
                    f.seek(2, 1) # Skip attribute byte count
            else:
                # ASCII Fallback
                f.seek(0)
                for line in f:
                    parts = line.split()
                    if len(parts) == 4 and parts[0] == b'vertex':
                        v = [float(x) for x in parts[1:]]
                        for i in range(3):
                            min_xyz[i] = min(min_xyz[i], v[i])
                            max_xyz[i] = max(max_xyz[i], v[i])
            
            size = [max_xyz[i] - min_xyz[i] for i in range(3)]
            return {"size": size, "min": min_xyz, "max": max_xyz}
    except Exception as e:
        return None

def optimize_settings(name, size):
    """AI logic to recommend settings based on model size."""
    x, y, z = size
    vol = x * y * z
    settings = BASE_SETTINGS.copy()
    reasoning = []

    # 1. Infill Density Logic
    if vol < 500: # Very tiny (e.g. 8x8x8mm)
        settings["infill_sparse_density"] = 40
        reasoning.append("Tiny model: High infill (40%) for structural strength.")
    elif z > 150: # Very tall
        settings["infill_sparse_density"] = 20
        reasoning.append("Tall model: Increased infill (20%) for stability at height.")

    # 2. Speed Logic
    if x < 10 or y < 10: # Thin/Tiny parts
        settings["speed_print"] = 40
        reasoning.append("Thin features: Reduced speed (40mm/s) for detail.")
    elif vol > 50000: # Massive block
        settings["speed_print"] = 70
        reasoning.append("Large volume: Increased speed (70mm/s) to save time.")

    # 3. Layer Height Logic
    if z < 5: # Flat object
        settings["layer_height"] = 0.12
        reasoning.append("Flat object: Fine layers (0.12mm) for smooth top surface.")
    elif vol > 100000: # Giant object
        settings["layer_height"] = 0.28
        reasoning.append("Giant object: Thick layers (0.28mm) for speed.")

    return settings, reasoning

def arrange_models(models):
    """Simple 'Shelf' packing algorithm to avoid collisions."""
    sorted_models = sorted(models, key=lambda m: m['size'][1], reverse=True)
    
    current_x = PADDING
    current_y = PADDING
    shelf_height = 0
    placements = []

    for m in sorted_models:
        w, d = m['size'][0] + PADDING, m['size'][1] + PADDING
        
        if current_x + w > BED_SIZE_X:
            current_x = PADDING
            current_y += shelf_height
            shelf_height = 0
        
        if current_y + d > BED_SIZE_Y:
            print(f"Warning: {m['name']} does not fit on the bed!")
            continue
        
        # Center the model at the calculated position
        pos_x = current_x + (w / 2) - (BED_SIZE_X / 2)
        pos_y = current_y + (d / 2) - (BED_SIZE_Y / 2)
        
        placements.append({
            "name": m['name'],
            "path": m['path'],
            "x": round(pos_x, 2),
            "y": round(pos_y, 2),
            "settings": m['settings'],
            "reasoning": m['reasoning']
        })
        
        current_x += w
        shelf_height = max(shelf_height, d)
        
    return placements

def main(directory):
    stl_files = [f for f in os.listdir(directory) if f.lower().endswith('.stl')]
    if not stl_files:
        print("No STL files found.")
        return

    models = []
    print("--- AI Model Analysis ---")
    for f in stl_files:
        path = os.path.join(directory, f)
        bounds = get_stl_bounds(path)
        if bounds:
            opt_settings, reasoning = optimize_settings(f, bounds['size'])
            models.append({
                "name": f,
                "path": path,
                "size": bounds['size'],
                "settings": opt_settings,
                "reasoning": reasoning
            })
            print(f"\nModel: {f}")
            for r in reasoning: print(f" - {r}")

    placements = arrange_models(models)
    
    # Generate CuraEngine command
    engine_path = "/Applications/Ultimaker Cura.app/Contents/Resources/CuraEngine"
    fdm_def = "/Applications/Ultimaker Cura.app/Contents/Resources/share/cura/resources/definitions/fdmprinter.def.json"
    printer_def = "/Applications/Ultimaker Cura.app/Contents/Resources/share/cura/resources/definitions/longer_lk5pro.def.json"
    
    # We apply global settings first, then extruder-specific settings
    cmd = f'"{engine_path}" slice -j "{fdm_def}" -j "{printer_def}" -o "output.gcode"'
    
    # Global settings
    for key, val in BASE_SETTINGS.items():
        cmd += f' -s {key}={val}'

    print("\n--- Final Layout ---")
    for p in placements:
        print(f"Placed {p['name']} at X:{p['x']} Y:{p['y']}")
        # For each model, we specify the extruder and its specific overrides
        cmd += f' -e0 -l "{p["path"]}" -s mesh_position_x={p["x"]} -s mesh_position_y={p["y"]}'
        for key, val in p['settings'].items():
            cmd += f' -s {key}={val}'

    print("\n--- Command to run ---")
    print(cmd)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main(".")
