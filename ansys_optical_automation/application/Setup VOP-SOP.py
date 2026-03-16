# ======================================================================================
# Script: Create Speos Materials from VOP-SOP.json
#
# Purpose
# -------
# Map CATMaterial names (from CATIA / NX / CAD) to Speos optical materials
# using a JSON file (VOP-SOP.json) located in the official OpticalLibraries folder.
#
# JSON structure (VOP-SOP.json)
# -----------------------------
# {
#   "PMMA": {
#     "Volume": ".../volume_optical_properties/.../PMMA.material",
#     "Surface": "Polished",
#     "IsOptic": true
#   }
# }
#
# Behavior
# --------
# - If Surface == "Polished":
#       Create a full optical material:
#           * VOPType  = Library (volume from JSON)
#           * SOPType  = OpticalPolished
#           * Assign VolumeGeometries to all bodies with that CATMaterial
#
# - If Surface != "Polished":
#       Create a surface-only material:
#           * VOPType  = None
#           * SOPType  = Library (surface from JSON)
#           * Assign VolumeGeometries to the geometry list
#
# Material name matching
# ----------------------
# The script is robust to differences between CAD material names and JSON keys:
# - Handles names with or without ".material"
# - Handles "-" and "_" differences
# - Trims spaces
# - Tries several candidate variants until it finds a match in the JSON
#
# Environment
# -----------
# Uses environment variable:
#   ANSYS252_DIR = C:\Program Files\ANSYS Inc\v252\ANSYS
#
# JSON folder:
#   C:\Program Files\ANSYS Inc\v252\Optical Products\OpticalLibraries
#
# ======================================================================================

import json
import os


# --------------------------------------------------------------------------------------
# Utility: get OpticalLibraries directory from environment variable
# --------------------------------------------------------------------------------------
def get_optical_lib_dir():
    """
    Returns the absolute path to the OpticalLibraries directory
    based on the ANSYS252_DIR environment variable.
    """
    ansys_dir = os.environ.get("ANSYS252_DIR")
    if not ansys_dir:
        raise EnvironmentError("Environment variable 'ANSYS252_DIR' is not defined.")

    # Example:
    # ANSYS252_DIR = C:\Program Files\ANSYS Inc\v252\ANSYS
    # v252_root    = C:\Program Files\ANSYS Inc\v252
    v252_root = os.path.dirname(ansys_dir)

    optical_lib_dir = os.path.join(v252_root, "Optical Products", "OpticalLibraries")

    if not os.path.isdir(optical_lib_dir):
        raise IOError("OpticalLibraries folder not found: " + optical_lib_dir)

    return optical_lib_dir


OPTICAL_LIB_DIR = get_optical_lib_dir()


# --------------------------------------------------------------------------------------
# Utility: resolve optical file paths (relative -> absolute)
# --------------------------------------------------------------------------------------
def resolve_optical_path(path_str):
    """
    Convert a relative path (inside OpticalLibraries) into an absolute path.
    If the path is already absolute or None/empty, it is returned as is.
    """
    if not path_str:
        return None
    if os.path.isabs(path_str):
        return path_str
    return os.path.join(OPTICAL_LIB_DIR, path_str)


# --------------------------------------------------------------------------------------
# Utility: robust mapping from CAD material name to JSON key
# --------------------------------------------------------------------------------------
def normalize_name_base(name):
    """
    Returns a basic normalized version of the material name:
    - Strip spaces at both ends
    - Remove common file extensions (e.g. .material)
    """
    if not name:
        return ""

    name = name.strip()

    # Remove ".material" extension if present (case-insensitive)
    lower = name.lower()
    if lower.endswith(".material"):
        name = name[: -len(".material")]

    # You can extend this if needed (e.g. remove .mirror, .bsdf, etc.)
    return name


def generate_name_candidates(raw_name):
    """
    Generates a set of candidate names to search in the JSON dictionary.
    This makes the matching robust to:
    - With or without ".material"
    - "-" vs "_"
    """
    candidates = set()

    if not raw_name:
        return candidates

    # Base normalized name without extension
    base = normalize_name_base(raw_name)
    if base:
        candidates.add(base)

    # Also consider the raw name itself
    candidates.add(raw_name.strip())

    # Replace "-" <-> "_" variants
    temp_list = list(candidates)
    for c in temp_list:
        candidates.add(c.replace("-", "_"))
        candidates.add(c.replace("_", "-"))

    return candidates


def find_material_key(material_name, materials_dict):
    """
    Try to find the corresponding key in VOP-SOP.json for the given CAD material name.

    It generates multiple name variants and returns the first one that exists in
    the materials_dict. If no match is found, returns None.
    """
    if not material_name:
        return None

    candidates = generate_name_candidates(material_name)

    for candidate in candidates:
        if candidate in materials_dict:
            return candidate

    return None


# --------------------------------------------------------------------------------------
# Load JSON dictionary
# --------------------------------------------------------------------------------------
vop_sop_path = os.path.join(OPTICAL_LIB_DIR, "VOP-SOP.json")
if not os.path.isfile(vop_sop_path):
    raise IOError("Material definition file not found: " + vop_sop_path)

with open(vop_sop_path, "r") as f:
    materials = json.load(f)

print("Loaded material definitions from:", vop_sop_path)


# --------------------------------------------------------------------------------------
# Group bodies by material key (JSON key) instead of raw CAD name
# --------------------------------------------------------------------------------------
material_to_bodies = {}

for body in GetActivePart().GetAllBodies():
    master = body.GetMaster()
    if not master:
        continue

    material_obj = master.Material
    if not material_obj or not material_obj.Name:
        continue

    raw_name = material_obj.Name
    key_name = find_material_key(raw_name, materials)

    if key_name is None:
        # Optional debug: show which material names are not in the JSON
        print("No JSON entry for CAD material:", raw_name)
        continue

    if key_name not in material_to_bodies:
        material_to_bodies[key_name] = []

    material_to_bodies[key_name].append(body)


if not material_to_bodies:
    print("No matching materials found between CAD and VOP-SOP.json.")
else:
    print("Found", len(material_to_bodies), "material(s) to create.")


# --------------------------------------------------------------------------------------
# Create Speos materials according to VOP-SOP.json
# --------------------------------------------------------------------------------------
for material_key, bodies_list in material_to_bodies.items():
    props = materials[material_key]

    surface_def = props.get("Surface")
    volume_def = props.get("Volume")

    selection = BodySelection.Create(bodies_list)

    # Create a new Speos material
    new_material = SpeosSim.Material.Create()
    new_material.Name = material_key  # You can use material_key or the raw CAD name

    # ------------------------------------------------------------------
    # Case 1: Full optical material (Volume + Polished surface)
    # ------------------------------------------------------------------
    if surface_def == "Polished":
        new_material.SOPType = SpeosSim.Material.EnumSOPType.OpticalPolished
        new_material.VOPType = SpeosSim.Material.EnumVOPType.Library

        volume_path = resolve_optical_path(volume_def)

        if volume_path and os.path.isfile(volume_path):
            try:
                new_material.VOPLibrary = volume_path
                print("✓ Created material:", material_key, "with VOP:", volume_path)
            except Exception as e:
                print("⚠ Error assigning VOP for material", material_key)
                print("  Path:", volume_path)
                print("  Exception:", str(e))
        else:
            print("⚠", material_key, "has Surface='Polished' but Volume path is missing or invalid.")
            volume_path = None

        new_material.VolumeGeometries.Set(selection.Items)
        print("→ Assigned", len(bodies_list), "geometries to material:", material_key)

    # ------------------------------------------------------------------
    # Case 2: Surface-only material (no Volume)
    # ------------------------------------------------------------------
    else:
        new_material.VOPType = getattr(SpeosSim.Material.EnumVOPType, "None")
        new_material.SOPType = SpeosSim.Material.EnumSOPType.Library

        surface_path = resolve_optical_path(surface_def)

        if surface_path and os.path.isfile(surface_path):
            try:
                new_material.SOPLibrary = surface_path
                print("✓ Created material:", material_key, "with SOP:", surface_path)
            except Exception as e:
                print("⚠ Error assigning SOP for material", material_key)
                print("  Path:", surface_path)
                print("  Exception:", str(e))
        else:
            print("⚠", material_key, "has no valid surface definition.")

        new_material.VolumeGeometries.Set(selection.Items)
        print("→ Assigned", len(bodies_list), "geometries to material:", material_key)


print("Material creation from VOP-SOP.json completed.")
