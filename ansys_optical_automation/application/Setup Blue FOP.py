# ----------------------------------------------------------------------------------------
# Script Description:
#
# This script applies surface optical properties (SOP) to blue-colored faces within
# model geometries, based on keys defined in 'FOP.json'.
#
# JSON 'FOP.json' (in OpticalLibraries) format:
#   "KeyInBodyName": {
#       "FOP": "relative/or/absolute/path/to/.unpolished"
#   }
# ----------------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
import json
import os
import re


def get_optical_lib_dir():
    ansys_dir = os.environ.get("ANSYS252_DIR")
    if not ansys_dir:
        raise EnvironmentError("Environment variable 'ANSYS252_DIR' is not defined.")
    v252_root = os.path.dirname(ansys_dir)  # ...\v252
    return os.path.join(v252_root, "Optical Products", "OpticalLibraries")


OPTICAL_LIB_DIR = get_optical_lib_dir()


def resolve_optical_path(path_str):
    if not path_str:
        return None
    if os.path.isabs(path_str):
        return path_str
    return os.path.join(OPTICAL_LIB_DIR, path_str)


# Load FOP materials from JSON
fop_json_path = os.path.join(OPTICAL_LIB_DIR, "FOP.json")
if not os.path.isfile(fop_json_path):
    raise IOError("FOP definition file not found: " + fop_json_path)

with open(fop_json_path, "r") as f:
    FOP = json.load(f)

keys = FOP.keys()


# Function to check if a color is blue (with tolerance)
def is_blue_color(color, tolerance=50):
    """
    Determines whether a given color is considered blue based on RGB components.
    """
    return color.B > 100 and color.B - color.R > tolerance and color.B - color.G > tolerance


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
            blue_faces_by_geometry[body_name] = {"key": matched_key, "faces": blue_faces}

# Create and assign materials only to blue faces
for geometry_name, data in blue_faces_by_geometry.items():
    key = data["key"]
    faces = data["faces"]

    # Clean geometry name: remove FOP and key, then strip special characters
    cleaned_name = geometry_name.replace("FOP", "")
    cleaned_name = cleaned_name.replace(key, "")
    cleaned_name = re.sub(r"[^A-Za-z0-9_]", "", cleaned_name)

    # Create a new Speos material
    material = SpeosSim.Material.Create()
    material.Name = "FOP_" + cleaned_name
    material.OpticalPropertiesType = SpeosSim.Material.EnumOpticalPropertiesType.Surfacic
    material.SOPType = SpeosSim.Material.EnumSOPType.Library

    fop_rel = FOP[key].get("FOP")
    fop_full = resolve_optical_path(fop_rel)
    if fop_full:
        material.SOPLibrary = fop_full
    else:
        print("⚠ No valid FOP path for key '{0}'".format(key))

    # Create a face selection and assign it to the material
    oriented_faces = FaceSelection.Create(faces)
    material.OrientedFaces.Set(oriented_faces.Items)

    print("Created material '{0}' with {1} blue face(s).".format(material.Name, len(faces)))
