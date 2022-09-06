import tkinter as tk
from tkinter import filedialog

from ansys_optical_automation.post_process.dpf_xmp_viewer import XmpViewer


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
        file_path = filedialog.askopenfilename(filetypes=[("File", extension)])
    else:
        file_path = filedialog.asksaveasfilename(filetypes=[("File", extension)])
        if not file_path.endswith(extension.strip("*")):
            file_path += extension.strip("*")
    return file_path


def main():
    xmp = XmpViewer()
    path_xmp = getfilename("*.xmp")
    xmp.open_file(path_xmp)
    path_xml = getfilename("*.xml")
    path_export = getfilename("*.txt", True)
    xmp.export_template_measures(path_xml, path_export)


main()
