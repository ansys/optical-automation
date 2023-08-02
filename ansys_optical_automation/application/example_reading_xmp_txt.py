import tkinter as tk
from tkinter import filedialog

import matplotlib as mpl
import matplotlib.pyplot as plt
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


# file_dir = getfilename("*.txt")
# file_dir = r"path to xmp"
file_dir = r"C:\temp\mytest_xmp_7.xmpexport.extended.txt_001.txt"
xmp = DpfXmpViewer()
data = xmp.read_txt_export(file_dir, inc_data=True)
# if there is one layer just reshape if there are mor sum them
if data.data.shape[0] == 1:
    test = data.data.reshape(data.data.shape[1:])
else:
    test = np.sum(data.data, 0)

# if not spectral just reshape if ther is to simple integration
if data.data.shape[3] == 1:
    test = test.reshape(data.data.shape[1:2])
else:
    factor = (data.wl_res[1] - data.wl_res[0]) / (data.wl_res[2] - 1)
    plot_data = np.sum(test * factor, 2).transpose()
# plot data in grayscale to compare to speos result select grayscale in speos and adjust maximum
max_scale = 2000
plt.imshow(plot_data, cmap=mpl.colormaps["gray"], vmin=0, vmax=max_scale)
plt.colorbar()
plt.show()
