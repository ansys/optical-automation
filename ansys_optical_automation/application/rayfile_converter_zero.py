import os
import tkinter as tk
from tkinter import filedialog

from ansys_optical_automation.interop_process.rayfile_converter_remove_0 import RayfileConverter_zero


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
    """Main script to convert a rayfile from speos to Zemax or from zemax to speos"""
    path_to_rayfile = getfilename("*.ray *.sdf *.dat")
    input_file_extension = os.path.splitext(path_to_rayfile)[1].lower()[0:]
    if not (("ray" in input_file_extension) or ("dat" in input_file_extension) or ("sdf" in input_file_extension)):
        msg = "Nonsupported file selected"
        raise TypeError(msg)
    convert = RayfileConverter_zero(path_to_rayfile)
    if "ray" in input_file_extension:
        convert.speos_to_zemax()
    elif ("dat" in input_file_extension) or ("sdf" in input_file_extension):
        convert.zemax_to_speos()


main()
