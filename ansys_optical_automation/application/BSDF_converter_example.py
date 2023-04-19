import tkinter as tk
from tkinter import filedialog
#import sys
#repo_path="your_dir"
#sys.path.append(repo_path)
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

    bool_log = 1
    bsdf_data = BsdfStructure()
    bsdf_data.filename_input = getfilename("*.bsdf *.brdf *.anisotropicbsdf")
    print("The file to convert is: " + bsdf_data.filename_input)

    msg = (
        "Select the output format \n "
        "1 = .bsdf (Zemax) \n "
        "2 = .brdf (Speos) - Not yet supported \n "
        "3 = .anisotropicbsdf\n"
        "Enter >> "
    )
    output_choice = int(input(msg))

    if not (output_choice in [1, 3]):
        msg = "Wrong output format"
        raise TypeError(msg)
    else:
        bsdf_data.import_data(bool_log)
        if output_choice == 1:
            bsdf_data.write_zemax_file(bool_log)
        if output_choice == 3:
            bsdf_data.write_speos_anisotropicbsdf_file()


main()
