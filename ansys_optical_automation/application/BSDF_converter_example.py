import os
import tkinter as tk
from tkinter import filedialog

from ansys_optical_automation.interop_process.Convert_BSDF_Zemax_to_Speos import convert_zemax_to_speos_bsdf, \
    convert_speos_to_zemax_bsdf


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
        file_path = filedialog.askopenfilename(filetypes=[("BSDF", extension)])
    else:
        file_path = filedialog.asksaveasfilename(filetypes=[("BSDF", extension)])
        if not file_path.endswith(extension.strip("*")):
            file_path += extension.strip("*")
    return file_path


def main():
    """Main script to convert a Zemax/Speos BSDF file to a Speos/Zemax BSDF file"""

    BSDF_inputFilepath = getfilename("*.bsdf *.brdf")
    input_file_extension = os.path.splitext(BSDF_inputFilepath)[1].lower()[0:]
    if not ("bsdf" in input_file_extension or "brdf" in input_file_extension):

        msg = "Nonsupported file selected"
        raise TypeError(msg)

    if "bsdf" in input_file_extension:

        convert_zemax_to_speos_bsdf(BSDF_inputFilepath)
        # Speos output file
        BSDF_outputFilepath = (
            os.path.splitext(BSDF_inputFilepath)[0].lower()
            + "_"
            + str(precisionTheta)
            + "_"
            + str(precisionPhi)
            + ".anisotropicbsdf"
        )
        convert_zemax_to_speos_bsdf(BSDF_inputFilepath, BSDF_outputFilepath, precisionTheta, precisionPhi)

    if "brdf" in input_file_extension:
        convert_speos_to_zemax_bsdf(BSDF_inputFilepath,1)

main()
