# ----------------------------------------------------------------------------------------
# Script Description:
#
# This script is designed to bridge the material setup between Catia and Speos by using 
# a dictionary-based mapping approach. The idea is to allow users to define materials 
# directly within Catia using `CATMaterial` names, and then automatically map these 
# names to fully characterized optical materials in Speos.
#
# The dictionary `materials` acts as a reference table:
#   - Each key corresponds to the name of a `CATMaterial` assigned in Catia.
#   - Each value is a set of attributes containing:
#       • "Volume": Path to the volume optical property file (VOP) in Speos
#       • "Surface": Either a polished flag or a path to a surface optical property (SOP) file
#
# This structure allows the automatic creation of Speos optical materials based on 
# geometry imported from Catia, enhancing productivity and ensuring consistency in 
# simulation setups. It enables customers who are more comfortable working in Catia 
# to seamlessly prepare their models for optical simulations without deep knowledge 
# of Speos material configuration.
#
# The script does the following:
#   1. Groups all geometries by their assigned `CATMaterial` name.
#   2. Checks if this material exists in the predefined `materials` dictionary.
#   3. Creates appropriate Speos materials:
#       - For polished surfaces with volume definition, creates full optical materials.
#       - For non-volume materials with SOP libraries, creates surface-only materials.
#   4. Assigns each created material to the corresponding geometries.
#
# This workflow democratizes simulation setup and accelerates deployment of optical 
# simulations across design teams by leveraging familiar tools like Catia.
# ----------------------------------------------------------------------------------------

import os

# Base path
path = r"C:\Users\amarin\OneDrive - ANSYS, Inc\Things\Usefull scripts\Simulation setups from Catia\Materials"

# Dictionary of materials
materials = {
    "Black PC": {
        "Volume": None,
        "Surface": os.path.join(path, "CAR-PAINT-MescalitoBlack1600.anisotropicbsdf")
    },
    "PMMA Clear": {
        "Volume": os.path.join(path, "PMMA.material"),
        "Surface": "Polished"
    },
    "Complete_Metallized": {
        "Volume": None,
        "Surface": os.path.join(path, "Al.mirror")
    },
    "PMMA_Red": {
        "Volume": os.path.join(path, "EVONIK_PLEXIGLAS-8N-RED-3V143.material"),
        "Surface": "Polished"
    }
}

# Group bodies by material
material_to_bodies = {}
for body in GetActivePart().GetAllBodies():
    material_obj = body.GetMaster().Material
    if material_obj:
        material_name = material_obj.Name
        if material_name not in material_to_bodies:
            material_to_bodies[material_name] = []
        material_to_bodies[material_name].append(body)

# Create Speos materials for those with "Polished" surface
for material_name in material_to_bodies:
    if material_name in materials:
        props = materials[material_name]

        bodies_list = material_to_bodies[material_name]
        selection = BodySelection.Create(bodies_list)

        if props["Surface"] == "Polished":
            # Create new material with volume
            new_material = SpeosSim.Material.Create()
            new_material.Name = material_name
            new_material.SOPType = SpeosSim.Material.EnumSOPType.OpticalPolished
            new_material.VOPType = SpeosSim.Material.EnumVOPType.Library

            volume_path = props["Volume"]
            if volume_path:
                new_material.VOPLibrary = volume_path
                print("✓ Created material: " + material_name + " with VOP: " + volume_path)
            else:
                print("⚠ " + material_name + " has Surface 'Polished' but Volume is None")

            new_material.VolumeGeometries.Set(selection.Items)
            print("→ Assigned " + str(len(bodies_list)) + " geometries to material: " + material_name)

        elif props["Volume"] is None:
            # Create new material with surface of type library
            new_material = SpeosSim.Material.Create()
            new_material.Name = material_name
            new_material.VolumeGeometries.Set(selection.Items)

            new_material.VOPType = SpeosSim.Material.EnumVOPType.None
            new_material.SOPType = SpeosSim.Material.EnumSOPType.Library

            surface_path = props["Surface"]
            new_material.SOPLibrary = surface_path
            print("✓ Created material: " + material_name + " with SOP: " + surface_path)
            print("→ Assigned " + str(len(bodies_list)) + " geometries to material: " + material_name)
