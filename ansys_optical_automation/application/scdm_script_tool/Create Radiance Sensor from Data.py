# ----------------------------------------------------------------------------------------
# Script Description:
#
# This script automates the creation of Radiance Sensors based on geometric elements 
# found in the model. Each sensor requires three inputs:
#
#   • An origin point curve      → named: Radiance_Sensor_Origin_<index>
#   • An X direction line curve  → named: Radiance_Sensor_XDirection_<index>
#   • A Y direction line curve  → named: Radiance_Sensor_YDirection_<index>
#
# For each set of curves sharing the same <index>, a radiance sensor is created using
# a predefined configuration template.
#
# Workflow:
# 1. Search both the root part and all subcomponents for curves matching the naming pattern.
# 2. Extract and group curves into origin, X direction, and Y direction dictionaries by index.
# 3. Identify common indices where all three components (origin, X, Y) exist.
# 4. For each complete triplet, create a new Radiance Sensor with:
#       - Origin, X, Y directions assigned
#       - Colorimetric mode
#       - Fixed resolution settings (0.1 x 0.1)
#
# If no valid triplets are found, a user-friendly message box is displayed.
# ----------------------------------------------------------------------------------------
import re
import clr
import ctypes
from ctypes import wintypes

# === Windows MessageBox setup ===

# MessageBox flags
MB_OK = 0x00000000
MB_ICONINFORMATION = 0x00000040
MB_TOPMOST = 0x00040000

# Get handle to foreground window
def get_foreground_hwnd():
    """
    Retrieves the handle to the foreground window.

    Returns
    -------
    int
        Handle (HWND) of the current foreground window.
    """
    return ctypes.windll.user32.GetForegroundWindow()

# Function to show a topmost message box
def show_message(message, title="Message"):
    """
    Displays a message box on top of all windows.

    The message box will be shown with an information icon and will stay on top
    of all other windows.

    Parameters
    ----------
    message : str
        The text to display in the message box.
    title : str, optional
        The title of the message box window. Default is "Message".
    """
    hwnd = get_foreground_hwnd()
    ctypes.windll.user32.MessageBoxW(hwnd, message, title, MB_OK | MB_ICONINFORMATION | MB_TOPMOST)

# === STEP 1: Find all curves and classify them by type and index ===
origin_curves = {}
xdir_curves = {}
ydir_curves = {}

# Search curves in the root part
for curve in GetRootPart().Curves:
    name = curve.GetName()
    if name.startswith("Radiance_Sensor_Origin_"):
        index = re.findall(r"\d+$", name)
        if index:
            origin_curves[int(index[0])] = curve
    elif name.startswith("Radiance_Sensor_XDirection_"):
        index = re.findall(r"\d+$", name)
        if index:
            xdir_curves[int(index[0])] = curve
    elif name.startswith("Radiance_Sensor_YDirection_"):
        index = re.findall(r"\d+$", name)
        if index:
            ydir_curves[int(index[0])] = curve

# Search curves in all components
for comp in GetRootPart().GetAllComponents():
    for curve in comp.GetAllCurves():
        name = curve.GetName()
        if name.startswith("Radiance_Sensor_Origin_"):
            index = re.findall(r"\d+$", name)
            if index:
                origin_curves[int(index[0])] = curve
        elif name.startswith("Radiance_Sensor_XDirection_"):
            index = re.findall(r"\d+$", name)
            if index:
                xdir_curves[int(index[0])] = curve
        elif name.startswith("Radiance_Sensor_YDirection_"):
            index = re.findall(r"\d+$", name)
            if index:
                ydir_curves[int(index[0])] = curve

# === STEP 2: Match indices only if they have all three directions ===
common_indices = sorted(set(origin_curves) & set(xdir_curves) & set(ydir_curves))

# === STEP 3: Error popup if no complete sensors found ===
if not common_indices:
    show_message("No complete sensor triplet (origin, X, Y) was found in the model.", "No Sensors Found")
else:
    # === STEP 4: Create sensors ===
    for i, index in enumerate(common_indices):
        try:
            origin_curve = origin_curves[index]
            xdir_curve = xdir_curves[index]
            ydir_curve = ydir_curves[index]

            # Create point selections
            origin_point = Selection.Create(origin_curve.GetChildren[ICurvePoint]()[0])
            xdir_point = Selection.Create(xdir_curve)
            ydir_point = Selection.Create(ydir_curve)

            # Create and configure sensor
            radiance = SpeosSim.SensorRadiance.Create()
            radiance.Name = "Radiance_" + str(i)
            radiance.OriginPoint.Set(origin_point.Items)
            radiance.XDirection.Set(xdir_point.Items)
            radiance.YDirection.Set(ydir_point.Items)
            radiance.SensorType = SpeosSim.SensorRadiance.EnumSensorType.Colorimetric
            radiance.XResolution = 0.1
            radiance.YResolution = 0.1

            print("✓ Created sensor:", radiance.Name)

        except Exception as error:
            show_message("Error while creating sensor #" + str(i) + ": " + str(error), "Sensor Creation Error")
