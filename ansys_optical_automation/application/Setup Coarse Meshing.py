# ----------------------------------------------------------------------------------
# Script Purpose:
# Identify non-optical materials (IsOptic = False) from VOP-SOP.json and apply
# coarse local meshing to the corresponding bodies.
#
# The JSON 'VOP-SOP.json' is located in:
#   C:\Program Files\ANSYS Inc\v252\Optical Products\OpticalLibraries
#
# Each entry:
#   "CatMaterialName": {
#       "Volume": <path or null>,
#       "Surface": <"Polished" or path>,
#       "IsOptic": <true/false>
#   }
# ----------------------------------------------------------------------------------

import json
import os


def get_optical_lib_dir():
    ansys_dir = os.environ.get("ANSYS252_DIR")
    if not ansys_dir:
        raise EnvironmentError("Environment variable 'ANSYS252_DIR' is not defined.")
    v252_root = os.path.dirname(ansys_dir)  # ...\v252
    return os.path.join(v252_root, "Optical Products", "OpticalLibraries")


OPTICAL_LIB_DIR = get_optical_lib_dir()

# Load materials dictionary from JSON
vop_sop_path = os.path.join(OPTICAL_LIB_DIR, "VOP-SOP.json")
if not os.path.isfile(vop_sop_path):
    raise IOError("Material definition file not found: " + vop_sop_path)

with open(vop_sop_path, "r") as f:
    materials = json.load(f)

# List to store the bodies that meet the condition
bodies_to_mesh = []

# Iterate over all bodies in the model
for body in GetActivePart().GetAllBodies():
    material = body.GetMaster().Material

    if material and material.Name:  # If a material is assigned
        material_name = material.Name

        if material_name in materials:
            # Default: treat unknown IsOptic as True (optical) for safety
            is_optic = materials[material_name].get("IsOptic", True)

            if not is_optic:
                bodies_to_mesh.append(body)

# If there are bodies to apply local meshing
if bodies_to_mesh:
    localMeshing = SpeosSim.LocalMeshing.Create()
    localMeshing.Name = "Coarse Meshing"
    localMeshing.MeshingSagLengthValue = 0.5

    geometries = BodySelection.Create(bodies_to_mesh)
    localMeshing.Geometries.Set(geometries.Items)

    print("✓ Coarse Meshing applied to {0} bodies.".format(len(bodies_to_mesh)))
else:
    print("No non-optical bodies found for coarse meshing.")
