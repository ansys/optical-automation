# ----------------------------------------------------------------------------------------
# Script Description:
#
# This script allows users to **invert the orientation of the emissive faces**
# associated with selected Speos surface light sources.
#
# This is especially useful after using the **"Create Sources from Data"** tool,
# where light sources are created based on geometry name matching, but their
# right **emissive face orientation cannot be predicted** reliably during import.
# ----------------------------------------------------------------------------------------
import ctypes

# MessageBox flags
MB_OK = 0x00000000
MB_ICONERROR = 0x00000010
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


# Show error message box
def show_error(message, title="Error"):
    """
    Display a topmost error message box with an error icon.

    This function shows a Windows message box with an error icon that stays
    on top of all other windows. It uses the current foreground window as parent.

    Parameters
    ----------
    message : str
        The message text to display.
    title : str, optional
        The title of the message box window. Default is "Error".

    Returns
    -------
    int
        The result code from the MessageBoxW function (usually MB_OK).
    """
    hwnd = get_foreground_hwnd()
    ctypes.windll.user32.MessageBoxW(hwnd, message, title, MB_OK | MB_ICONERROR | MB_TOPMOST)


# Get selected items
source_selections = Selection.GetActive().Items

# Iterate over each selected item
for selected in source_selections:
    try:
        # Try to find the Speos light source by name
        led_to_reverse = SpeosSim.SourceSurface.Find(selected.Name)
        if led_to_reverse is None:
            show_error("Source '" + selected.Name + "' not found in the Speos light list.", "Not Found")
            continue

        # Reverse the direction of each emissive face
        count = 0
        for face in led_to_reverse.EmissiveFaces:
            face.ReverseDirection = not face.ReverseDirection
            count += 1

        print("✓ Direction reversed for " + str(count) + " face(s) in source: " + selected.Name)

    except Exception as e:
        show_error("Error processing source '" + selected.Name + "': " + str(e), "Exception")
