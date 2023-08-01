import tkinter as tk
from tkinter import filedialog

import numpy as np

from ansys_optical_automation.post_process.dpf_xmp_viewer import DpfXmpViewer

# import sys
# repo_path=r"your repository location"
# sys.path.append(repo_path)


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


file_dir = getfilename("*.txt")
xmp = DpfXmpViewer()
data = xmp.read_txt_export(file_dir, inc_data=True)
test = data.data.reshape((5, 5, 81))
print(data.wl_res)
print(test[:, :, 0])
print(np.sum(test * 5, 2).transpose())
