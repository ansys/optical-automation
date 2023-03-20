import os
import tkinter as tk
from tkinter import filedialog

from ansys_optical_automation.interop_process.BSDF_converter import BsdfStructure


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
    """Main script to convert BSDF files"""

    bsdf_data = BsdfStructure()

    BSDF_inputFilepath = getfilename("*.bsdf *.brdf")
    input_file_extension = os.path.splitext(BSDF_inputFilepath)[1].lower()[0:]
    if not ("bsdf" in input_file_extension or "brdf" in input_file_extension):
        msg = "Nonsupported file selected"
        raise TypeError(msg)

    bool_log = 1
    bsdf_data.import_data(BSDF_inputFilepath, bool_log)
    #bsdf_data.write_zemax_file(bool_log)

    if bsdf_data.bool_success == 1:
        if "bsdf" in input_file_extension:
            bsdf_data.write_speos_anisotropicbsdf_file()

        if "brdf" in input_file_extension:
            bsdf_data.write_zemax_file(bool_log)


main()
