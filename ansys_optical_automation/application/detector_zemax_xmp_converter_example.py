import os
import tkinter as tk
from tkinter import filedialog

from ansys_optical_automation.interop_process.Convert_Zemax_Detectors_to_XMP import Convert_detectordata_to_xmp


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
        file_path = filedialog.askopenfilename(filetypes=[("DetectorFile", extension)])
    else:
        file_path = filedialog.asksaveasfilename(filetypes=[("DetectorFile", extension)])
        if not file_path.endswith(extension.strip("*")):
            file_path += extension.strip("*")
    return file_path


def main():
    """Main script to convert detector data from Zemax to Speos (xmp)"""
    path_to_detectordatafile = getfilename("*.ddr *.txt")
    input_file_extension = os.path.splitext(path_to_detectordatafile)[1].lower()[0:]
    if not (("ddr" in input_file_extension) or ("txt" in input_file_extension)):
        msg = "Nonsupported file selected"
        raise TypeError(msg)
    xmpFilePath = Convert_detectordata_to_xmp(path_to_detectordatafile, input_file_extension, True)

main()

