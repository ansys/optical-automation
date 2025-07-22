# ----------------------------------------------------------------------------------------
# Script Description:
#
# This script restores the original surface optical properties (SOP) of Speos materials 
# that were previously "disconnected" with "Deactivate SOP".
#
# This restoration script reactivates the previously disabled SOPs by:
#
#   • Checking if the selected material is of type "Surfacic"
#   • Verifying if its SOP type is currently set to `OpticalPolished`
#   • Reverting the SOP type back to `Library`, which re-enables the linked surface property
#   • Cleaning up the material name by removing the `"--- POLISHED ---"` suffix (if present)
#
# If any material is not of type Surfacic, or is not marked as OpticalPolished, 
# an informative message box will notify the user.
# ----------------------------------------------------------------------------------------
import clr
import ctypes
from ctypes import wintypes

# MessageBox flags
MB_OK = 0x00000000
MB_ICONINFORMATION = 0x00000040
MB_TOPMOST = 0x00040000

# Get handle to foreground window
def get_foreground_hwnd():
    return ctypes.windll.user32.GetForegroundWindow()

# Function to show a topmost message box
def show_message(message, title="Message"):
    hwnd = get_foreground_hwnd()
    ctypes.windll.user32.MessageBoxW(hwnd, message, title, MB_OK | MB_ICONINFORMATION | MB_TOPMOST)

material_selections = Selection.GetActive().Items

for material in material_selections:
    try:
        material__ = SpeosSim.Material.Find(material.Name)
        if material__ is None:
            show_message("Property " + str(material.Name) + " not found in the material list", "Material Not Found")
        else:
            if material__.OpticalPropertiesType == SpeosSim.Material.EnumOpticalPropertiesType.Surfacic:
                if material__.SOPType == SpeosSim.Material.EnumSOPType.OpticalPolished:
                    material__.SOPType = SpeosSim.Material.EnumSOPType.Library
                    if "--- POLISHED ---" in material__.Name:
                        material__.Name = material__.Name.replace("--- POLISHED ---", "")
                        material__.Compute()
                    # No popup here — silent success
                else:
                    show_message("Material " + str(material__.Name) + " is not defined as OpticalPolished", "Not OpticalPolished")
            else:
                show_message("Property " + str(material.Name) + " is not a Surfacic material", "Wrong Type")
    except Exception as error:
        show_message("Error processing material " + str(material.Name) + ": " + str(error), "Error")

