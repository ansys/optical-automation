import os
import tkinter as tk
from tkinter import filedialog

from ansys_optical_automation.interop_process.Convert_BSDF_Zemax_to_Speos import convert_zemax_to_speos_bsdf


def getfilename(extension, save=False):
    """
    Parameters
    ----------
    extension : str
        containing the which file extension in *.ending format
    save : Bool
        option to define to open(default) or save. The default is False.

    Returns
    -------
    str
        string containing the selected file path
    """
    root = tk.Tk()
    root.withdraw()
    if not save:
        file_path = filedialog.askopenfilename(filetypes=[("Rayfile", extension)])
    else:
        file_path = filedialog.asksaveasfilename(filetypes=[("Rayfile", extension)])
        if not file_path.endswith(extension.strip("*")):
            file_path += extension.strip("*")
    return file_path


def main():
    """Main script to convert a Zemax BSDF file to a Speos BSDF file"""

    precisionTheta = 1  # 1 #10 #0.5
    precisionPhi = 1  # 10 #1

    BSDF_inputFilepath = getfilename("*.bsdf")
    input_file_extension = os.path.splitext(BSDF_inputFilepath)[1].lower()[0:]
    if not ("bsdf" in input_file_extension) :
        msg = "Nonsupported file selected"
        raise TypeError(msg)

    if "bsdf" in input_file_extension:
        # Speos output file
        BSDF_outputFilepath = os.path.splitext(BSDF_inputFilepath)[0].lower() + '_' + \
                              str(precisionTheta) + '_' + str(precisionPhi) + \
                              '.anisotropicbsdf'
        convert_zemax_to_speos_bsdf(BSDF_inputFilepath,BSDF_outputFilepath,precisionTheta,precisionPhi)


main()
