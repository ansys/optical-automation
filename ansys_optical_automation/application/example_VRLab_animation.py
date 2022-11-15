import csv
import time
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


def animation_run(speos_file, csv_file):
    """
    function to run animation in observer result.

    Parameters
    ----------
    speos_file : str
        file path of VR file.
    csv_file : str
        file path of time line csv file

    Returns
    -------


    """
    VRLab = DpfHdriViewer()
    VRLab.open_file(speos_file)
    source_list = VRLab.get_source_list()
    csv_source_list = []
    csv_source_animation = []
    with open(csv_file) as file:
        content = csv.reader(file, delimiter=",")
        First_Row = True
        for row in content:
            if First_Row:
                csv_source_list = [item for item in row][1:]
            else:
                csv_source_animation.append([float(item) for item in row])
            First_Row = False
    animation_time_step = csv_source_animation[1][0] - csv_source_animation[0][0]
    if len(csv_source_list) != len(source_list):
        msg = "selected timeline csv file does not match with the speos vr file"
        raise ImportError(msg)

    if set(csv_source_list) != set(source_list):
        print("will assume source using index")
        VRLab.dpf_instance.Show(1)
        while True:
            for csv_source_config in csv_source_animation:
                for source_idx, source in enumerate(csv_source_list):
                    VRLab.set_source_power(source_idx, csv_source_config[source_idx + 1])
                time.sleep(animation_time_step)
    else:
        print("will use name to set source in animation")
        VRLab.dpf_instance.Show(1)
        while True:
            for csv_source_config in csv_source_animation:
                for source_idx, source in enumerate(csv_source_list):
                    VRLab.set_source_power(source, csv_source_config[source_idx + 1])
                time.sleep(animation_time_step)


def main():
    """
    main function to run Observer VR animation.

    Returns
    -------


    """
    vr_file = getfilename("*.OptisVR *.Speos360")
    time_line_csv = getfilename("*.csv")
    if not vr_file or not time_line_csv:
        msg = "Please select speos vr file and time line csv file"
        raise ImportError(msg)
    animation_run(vr_file, time_line_csv)


main()
