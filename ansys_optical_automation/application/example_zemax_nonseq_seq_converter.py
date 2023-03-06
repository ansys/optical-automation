import os
import tkinter as tk
from tkinter import filedialog

from ansys_optical_automation.zemax_process.nonseq_to_seq_functions import (
    OSModeConverter,
)


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
    nscfilename = getfilename("*.zmx")
    input_file_extension = os.path.splitext(nscfilename)[1].lower()[0:]
    if not ("zmx" in input_file_extension):
        msg = "Nonsupported file selected"
        raise TypeError(msg)

    nsc_elements = [14, 5, 8, 5, 13, 16]
    materials = ["", "Mirror", "Mirror", "Mirror", "Mirror", ""]
    reverseflag_ob1 = True

    cv = OSModeConverter()
    cv.nscfilename = nscfilename
    cv.nsc_elements = nsc_elements
    cv.object_materials = materials
    cv.reverseflag_ob1 = reverseflag_ob1

    (list_rotation_matrix, list_position, list_comments) = cv.get_objects_position_info(nsc_elements)
    cv.convert(list_rotation_matrix, list_position, list_comments, reverseflag_ob1)


main()
