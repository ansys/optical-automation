import os
import tkinter as tk
from tkinter import filedialog

from ansys_optical_automation.interop_process.speos_hud_to_zemaxOS import (
    SpeosHUDToZemax,
)


def getfilename(extension, fileTypeName, title):
    """
    Parameters
    ----------
    extension : str
        Defining the extension of the file we need to open or move
    fileTypeName : str
        Defining the name of the file time we will be trying to pull, for viewing in the file dialog
    title : str
        Defining the title of the file dialog window

    Returns
    -------
    filePath : str
        String containing the full path of the selected file

    """
    root = tk.Tk()
    root.withdraw()
    filePath = filedialog.askopenfilename(title=title, filetypes=[(fileTypeName, extension)])
    return filePath


def main():
    """
    Main script to convert a set of Speos HUD files to Zemax OpticStudio Non-Sequential Mode
    """
    fullFile = getfilename("*.txt", "text files", "Select the HUD_SpeosToZemax text file...")
    freeformFile = getfilename("*.txt", "text files", "Select the freeform profile text file...")
    freeformFileName = os.path.basename(freeformFile)
    windshieldStart = getfilename("*.stp", "CAD file", "Select the windshield CAD file...")
    windshieldFile = os.path.basename(windshieldStart)

    # Call function to parse the data provided by Speos
    SpeosHUDToZemax(fullFile, freeformFile, freeformFileName, windshieldStart, windshieldFile)


main()
