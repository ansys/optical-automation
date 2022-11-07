import tkinter as tk
from tkinter import filedialog

import numpy as np

from ansys_optical_automation.post_process.dpf_lpf_reader import DpfLpfReader
from ansys_optical_automation.post_process.dpf_xmp_viewer import MapStruct


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
        file_path = filedialog.askopenfilename(filetypes=[("LPFfile", extension)])
    else:
        file_path = filedialog.asksaveasfilename(filetypes=[("LPFfile", extension)])
        if not file_path.endswith(extension.strip("*")):
            file_path += extension.strip("*")
    return file_path


def compute_refactive_power(point_1, point_2, dir):
    """
    Parameters
    ----------
    point_1
    point_2
    dir_1
    dir_2

    Returns
    -------


    """
    dist = np.sqrt((point_1[1] - point_2[1]) ** 2 + (point_1[2] - point_2[2]) ** 2)
    height = dist / dir[2]
    angle = np.pi / 2 - np.arccos(dir[2] / np.sqrt(dir[0] ** 2 + dir[1] ** 2 + dir[2] ** 2))
    refractive_power = 1 / (
        np.sqrt((height * dir[0]) ** 2 + (height * dir[1]) ** 2 + (height * dir[2]) ** 2) * np.cos(angle)
    )
    return refractive_power


file_name = getfilename("*.lpf")
my_lpf = DpfLpfReader()
my_lpf.open_file(file_name)

xmp_nb = my_lpf.dpf_instance.GetNbOfXMPs()
print(my_lpf.trace_count)
names = my_lpf.dpf_instance.GetSensorNames()
for name in names:
    print(name.Ptr())
sequences = []
sequence_tuple = []
my_lpf.retrieve_traces()
print(my_lpf.sequence_impacts)
print(my_lpf.trace_count)
refractive_power = []
my_sequence = 1
for trace in my_lpf.sequences[my_sequence]:
    last_dir = [trace.LastDirection.Get(0), trace.LastDirection.Get(1), trace.LastDirection.Get(2)]
    point_1 = [trace.vImpacts.Get(1).Get(0), trace.vImpacts.Get(1).Get(1), trace.vImpacts.Get(1).Get(2)]
    point_2 = [
        trace.vImpacts.Get(my_lpf.sequence_impacts[my_sequence] - 1).Get(0),
        trace.vImpacts.Get(my_lpf.sequence_impacts[my_sequence] - 1).Get(1),
        trace.vImpacts.Get(my_lpf.sequence_impacts[my_sequence] - 1).Get(2),
    ]
    list = [
        round(point_2[0], 1),
        round(point_2[1], 1),
        round(point_2[2], 1),
        compute_refactive_power(point_1, point_2, last_dir),
    ]
    refractive_power.append(list)
my_list = sorted(refractive_power, key=lambda x: (x[1], x[2]))

diopter_map = MapStruct(3, 20, 9, 1, [-800, 800, 300, 900], [160, 60])
step_x = (800 - (-800)) / 160
step_y = (900 - 300) / 60
x_values = np.arange(-800.0, 800.0, step_x)
y_values = np.arange(300.0, 900.0, step_y)
print(y_values)
index = 0
# TODO rework needed here not very efficient and not working yet
for x in range(160):
    for y in range(60):
        my_value = []
        for item in my_list:
            if x_values[x] < item[1] < x_values[x] + step_x:
                if y_values[y] < item[2] < y_values[y] + step_y:
                    my_value.append(item[3])
        if len(my_value) == 0:
            diopter_map.data[0, x, y, 0] = 0
        else:
            diopter_map.data[0, x, y, 0] = sum(my_value) / len(my_value)

xmp = diopter_map.export_to_xmp(r"c:\temp")
