# ----------------------------------------------------------------------------------------
# Script Description:
#
# This script mimics the behavior of the legacy Deactivate SOP feature that was 
# available in Speos for Catia. Its main function is to replace the surface optical 
# property (SOP) of selected materials with a generic polished surface type.
#
# The idea is that when users want to "disconnect", the script will:
#   • Check if the selected material has a surfacic optical property.
#   • Change its SOP type to "OpticalPolished".
#   • Rename the material by appending " --- POLISHED --- " to indicate the override.
#
# Steps:
# 1. Loop through all selected materials from the active selection.
# 2. Skip any materials already marked as polished.
# 3. For each valid material:
#       - Check if it exists in the current Speos material list.
#       - If its optical property type is "Surfacic", convert it to "OpticalPolished".
#       - Rename it to reflect the change.
#       - If not surfacic, show an informative message.
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
    """
    Get the handle (HWND) of the current foreground window.

    This function uses the Windows API to retrieve the window handle
    of the application that currently has the user's focus.

    Returns
    -------
    int
        Handle (HWND) of the foreground window.
    """
    return ctypes.windll.user32.GetForegroundWindow()

# Function to show a topmost message box
def show_message(message, title="Message"):
    """
    Display a topmost message box with an information icon.

    This function shows a Windows message box that stays on top of all windows.
    It retrieves the handle of the current foreground window to anchor the message box.

    Parameters
    ----------
    message : str
        The message text to display.
    title : str, optional
        The title of the message box. Default is "Message".

    Returns
    -------
    int
        The result code from the MessageBoxW function (usually MB_OK).
    """
    hwnd = get_foreground_hwnd()
    ctypes.windll.user32.MessageBoxW(hwnd, message, title, MB_OK | MB_ICONINFORMATION | MB_TOPMOST)

material_selections = Selection.GetActive().Items

for material in material_selections:
    try:
        # Skip if material name already contains "--- POLISHED ---"
        if "--- POLISHED ---" in material.Name:
            continue

        material__ = SpeosSim.Material.Find(material.Name)
        if material__ is None:
            show_message("Property " + str(material.Name) + " not found in the material list", "Material Not Found")
        else:
            if material__.OpticalPropertiesType == SpeosSim.Material.EnumOpticalPropertiesType.Surfacic:
                material__.SOPType = SpeosSim.Material.EnumSOPType.OpticalPolished
                material__.Name = material__.Name + " --- POLISHED --- "
            else:
                show_message("Property " + str(material.Name) + " is not an FOP!", "Wrong Type")
    except Exception as error:
        show_message("Error processing material " + str(material.Name) + ": " + str(error), "Error")