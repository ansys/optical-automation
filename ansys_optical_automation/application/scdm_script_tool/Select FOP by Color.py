# ----------------------------------------------------------------------------------------
# Script Description:
#
# This script applies surface optical properties (SOP) to blue-colored faces within 
# model geometries, based on predefined pattern recognition in geometry names.
#
# Main Objectives:
#   • Detect whether the geometry name contains a key defined in the `FOP` dictionary 
#     (e.g., "VDI42", "VDI27"), which maps to corresponding `.unpolished` SOP files.
#   • Identify faces that are blue (any shade) using a tolerance threshold in RGB.
#   • For geometries with a matching key:
#       - Filter all blue faces
#       - Group them per geometry
#       - Create a custom Speos surfacic material referencing the appropriate SOP file
#
# How it works:
#   1. Iterate over all bodies in the model.
#   2. Check if the body's name contains any of the `FOP` keys.
#   3. For matching geometries, evaluate each face’s color using `ColorHelper`.
#   4. If the face is identified as blue (based on RGB component difference),
#      it is added to a list for material assignment.
#   5. A new Speos material is created per geometry and applied to its blue faces only.
# ----------------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
import clr
import os
import re
from System.Drawing import Color

# Base path for FOP materials
path = r"C:\Users\amarin\OneDrive - ANSYS, Inc\Things\Usefull scripts\Simulation setups from Catia\Materials"

# Dictionary of FOP materials
FOP = {
    "VDI42": {
        "FOP": os.path.join(path, "AgieCharmillesVDI_Chemical-Etching-42.unpolished")
    },
    "VDI27": {
        "FOP": os.path.join(path, "AgieCharmillesVDI_Chemical-Etching-27.unpolished")
    }
}

keys = FOP.keys()

# Function to check if a color is blue (with tolerance)
def is_blue_color(color, tolerance=50):
    """
    Determines whether a given color is considered blue based on RGB components.

    A color is considered blue if its blue component is significantly higher
    than the red and green components by at least the specified tolerance.

    Parameters
    ----------
    color : System.Drawing.Color
        The color to evaluate.
    tolerance : int, optional
        Minimum difference required between the blue component and the red/green
        components to consider the color as blue. Default is 50.

    Returns
    -------
    bool
        True if the color is considered blue, False otherwise.
    """
    return (
        color.B > 100 and
        color.B - color.R > tolerance and
        color.B - color.G > tolerance
    )

# Dictionary to group blue faces by geometry name
blue_faces_by_geometry = {}

# Loop through all bodies in the model
for body in GetRootPart().GetAllBodies():
    body_name = body.GetName()
    matched_key = None
    for key in keys:
        if key in body_name:
            matched_key = key
            break

    if matched_key:
        blue_faces = []
        for face in body.Faces:
            face_selection = FaceSelection.Create(face)
            face_color = ColorHelper.GetColor(face_selection)
            if is_blue_color(face_color):
                blue_faces.append(face)

        if blue_faces:
            blue_faces_by_geometry[body_name] = {
                "key": matched_key,
                "faces": blue_faces
            }

# Create and assign materials only to blue faces
for geometry_name in blue_faces_by_geometry:
    data = blue_faces_by_geometry[geometry_name]
    key = data["key"]
    faces = data["faces"]

    # Clean geometry name: remove FOP and key, then strip special characters
    cleaned_name = geometry_name.replace("FOP", "")
    cleaned_name = cleaned_name.replace(key, "")
    cleaned_name = re.sub(r'[^A-Za-z0-9_]', '', cleaned_name)

    # Create a new Speos material
    material = SpeosSim.Material.Create()
    material.Name = "FOP_" + cleaned_name
    material.OpticalPropertiesType = SpeosSim.Material.EnumOpticalPropertiesType.Surfacic
    material.SOPType = SpeosSim.Material.EnumSOPType.Library
    material.SOPLibrary = FOP[key]["FOP"]

    # Create a face selection and assign it to the material
    oriented_faces = FaceSelection.Create(faces)
    material.OrientedFaces.Set(oriented_faces.Items)

    print("Created material '" + material.Name + "' with " + str(len(faces)) + " blue face(s).")
