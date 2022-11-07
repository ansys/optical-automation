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
    temp_list = [
        round(point_2[0], 1),
        round(point_2[1], 1),
        round(point_2[2], 1),
        compute_refactive_power(point_1, point_2, last_dir),
    ]
    refractive_power.append(temp_list)
# my_list = sorted(refractive_power, key=lambda x: (x[1], x[2]))
my_list = refractive_power
diopter_map = MapStruct(3, 20, 9, 1, [-800, 800, 300, 900], [160, 60])
# TODO rework needed here not very efficient and not working yet
data = np.zeros((160, 60), dtype=list)
step_x = (800 - (-800)) / 160
step_y = (900 - 300) / 60
for x in range(160):
    for y in range(60):
        data[x, y] = []
for item in my_list:
    x_values = np.arange(-800.0, 800.0, step_x)
    y_values = np.arange(300.0, 900.0, step_y)
    x_values = x_values.tolist()
    y_values = y_values.tolist()
    x_values.append(item[1])
    y_values.append(item[2])
    x_values.sort()
    y_values.sort()
    x = x_values.index(item[1])
    y = y_values.index(item[2])
    if x > 159:
        x -= 1
    if y > 59:
        y -= 1
    data[x, y].append(item[3])

for x in range(160):
    print(str(100 * x / 160) + "%")
    for y in range(60):
        if len(data[x, y]) == 0:
            diopter_map.data[0, x, y, 0] = 0
        else:
            diopter_map.data[0, x, y, 0] = sum(data[x, y]) / len(data[x, y])

xmp = diopter_map.export_to_xmp(r"c:\temp")
