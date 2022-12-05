import tkinter as tk
from tkinter import filedialog

from ansys_optical_automation.post_process.dpf_hdri_viewer import DpfHdriViewer


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
    """
    main function to run Observer VR animation.
    Currently, this application only supports running from python console.

    Returns
    -------


    """
    vr_file = getfilename("*.OptisVR *.Speos360")
    time_line_csv = getfilename("*.csv")
    if not vr_file or not time_line_csv:
        msg = "Please select speos vr file and time line csv file"
        raise ImportError(msg)
    VRLab = DpfHdriViewer()
    VRLab.open_file(vr_file)
    VRLab.timeline_animation_run(time_line_csv)


main()
