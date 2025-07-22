# ----------------------------------------------------------------------------------
# Script Purpose:
# This script defines a dictionary to manage optical and non-optical materials 
# used in simulations imported from Catia. Each key in the dictionary corresponds 
# to a specific `CatMaterial` name. The associated value is a set of attributes:
#
#   - "Volume": Path to the volume material characterization file (if any)
#   - "Surface": Either a surface material path or a surface condition (e.g., "Polished")
#   - "IsOptic": Boolean flag indicating whether the material is optical
#
# The goal is to identify which materials require fine meshing based on their optical
# relevance. Optical materials (IsOptic = True) demand finer meshing to accurately model
# light interactions. Non-optical materials (IsOptic = False) can use coarser meshing to
# speed up the simulation.
#
# The script iterates over all bodies in the active model, checks their assigned 
# material, and if the material is found in the dictionary and marked as non-optical,
# it adds them to a list for coarse meshing.
#
# At the end, if any non-optical bodies are found, a "Coarse Meshing" setup is 
# created and applied to these bodies to optimize simulation performance.
# ----------------------------------------------------------------------------------

import os

# Base path
path = r"C:\Users\amarin\OneDrive - ANSYS, Inc\Things\Usefull scripts\Simulation setups from Catia\Materials"

# Dictionary of materials with the IsOptic field
materials = {
    "Black PC": {
        "Volume": None,
        "Surface": os.path.join(path, "CAR-PAINT-MescalitoBlack1600.anisotropicbsdf"),
        "IsOptic": False
    },
    "PMMA Clear": {
        "Volume": os.path.join(path, "PMMA.material"),
        "Surface": "Polished",
        "IsOptic": True
    },
    "Complete_Metallized": {
        "Volume": None,
        "Surface": os.path.join(path, "Al.mirror"),
        "IsOptic": False
    },
    "PMMA_Red": {
        "Volume": os.path.join(path, "PMMA BASF Lumogene F red 300.material"),
        "Surface": "Polished",
        "IsOptic": True
    }
}

# List to store the bodies that meet the condition
bodies_to_mesh = []

# Iterate over all bodies in the model
for body in GetActivePart().GetAllBodies():
    material = body.GetMaster().Material

    if material and material.Name:  # If a material is assigned
        material_name = material.Name

        # If the material name is in the dictionary
        if material_name in materials:
            # If IsOptic is False, add the body to the list
            if not materials[material_name]["IsOptic"]:
                bodies_to_mesh.append(body)

# If there are bodies to apply local meshing
if bodies_to_mesh:
    localMeshing = SpeosSim.LocalMeshing.Create()
    localMeshing.Name = "Coarse Meshing"
    localMeshing.MeshingSagLengthValue = 0.5

    geometries = BodySelection.Create(bodies_to_mesh)
    localMeshing.Geometries.Set(geometries.Items)
