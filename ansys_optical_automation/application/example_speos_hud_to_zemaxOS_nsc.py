import os
import math
import tkinter as tk    # Used to select files
import shutil           # Used to copy file to Zemax Objects directory

#
from ansys_optical_automation.zemax_process.base import BaseZOS
from ansys_optical_automation.interop_process.speos_hud_to_zemaxOS import SpeosHUDToZemax
from tkinter import filedialog

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
    filePath = filedialog.askopenfilename(
        title=title,
        filetypes=[(fileTypeName, extension)]
    )
    return filePath


def main():
    """
    Main script to convert a set of Speos HUD files to Zemax OpticStudio Non-Sequential Mode

    This script contains the following assumptions:
    1. We have three files exported from Speos:
        a. HUD_SpeosToZemax
        b. HUD surface export
        c. Windshield.STP
    2. Assuming the comment "#Point coordinates start from Eyebox and go to PGU. These are vertices of 4 polylines, so there are 8 vertices, 4 are duplicates" is always used directly preceding the point-by-point data
    3. Assuming three objects + one step file are being imported. Nothing more
    4. Assuming the points and tilt angles are all preceded by "n Point:" or "Z:" or "Y':" or "X'':"
    5. Assuming point-by-point data is duplicated such that lines 6, 4, and 2 may be removed
    6. Assuming object size data is directly preceded by "#Surface dimensions start from freeform and go to PGU. There are 4 edge dimensions per surface"
    7. Assuming sizing data directly precedes the position data, and is duplicated
    8. Assumption: We are using MM units and received m units from Speos
    9. Assume eyebox data is given in the first lines, separate from other position/tilt data
    10. Assume gut ray strikes all objects except windshield at local axis (center)
    11. BIG assumption: We do not need the Horizontal/Vertical angle reports with the X, Y, Z data now
    12. Assume gut ray leaving PGU is at a 180 degree X Tilt wrt the PGU position
    13. Assume gut ray leaving PGU may not be "normal to" the PGU itself. Will allow for some minor optimization of position
        a. Assume gut ray leaving PGU is at object 3

    """
    fullFile = getfilename("*.txt", "text files", "Select the HUD_SpeosToZemax text file...")
    freeformFile = getfilename("*.txt", "text files", "Select the freeform profile text file...")
    freeformFileName = os.path.basename(freeformFile)
    windshieldFile = os.path.basename(getfilename("*.stp", "CAD file", "Select the windshield CAD file..."))

    # Make some connections to the base ZOS
    zos = BaseZOS()
    TheApplication = zos.the_application
    TheSystem = zos.the_application.PrimarySystem


    # Copy the windshield file to the global Zemax directory
    objDir = TheApplication.ObjectsDir

    # Begin by creating a new system in Zemax OpticStudio's Non-Sequential Mode
    TheSystem.New(False)
    TheSystem.MakeNonSequential()

    # Give the file a new name
    osFilename = fullFile[:-4] + "_OSOutput.zmx"
    TheSystem.SaveAs(osFilename)

    # Convert system units to MM as that is what we received from Speos
    TheSystem.SystemData.Units.LensUnits = ZOSAPI.SystemData.ZemaxSystemUnits.Millimeters

    # Call function to parse the data provided by Speos
    convert = SpeosHUDToZemax(fullFile)
    # Call the function to begin the file update of the Zemax file
    convert.NSCFileCreation(TheSystem)