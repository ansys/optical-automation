import os
import tkinter as tk
from tkinter import filedialog

from ansys_optical_automation.interop_process.rayfile_converter import RayfileConverter


def getfilename(extension, save=False):
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
    path_to_rayfile = getfilename("*.ray *.sdf *.dat")
    input_file_extension = os.path.splitext(path_to_rayfile)[1].lower()[0:]
    if not (("ray" in input_file_extension) or ("dat" in input_file_extension) or ("sdf" in input_file_extension)):
        msg = "Nonsupported file selected"
        raise TypeError(msg)
    convert = RayfileConverter(path_to_rayfile)
    if "ray" in input_file_extension:
        convert.speos_to_zemax()
    elif ("dat" in input_file_extension) or ("sdf" in input_file_extension):
        convert.zemax_to_speos()


main()
