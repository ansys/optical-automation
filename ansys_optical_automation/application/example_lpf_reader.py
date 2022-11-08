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
    function to compute refractive power of an optical object
    input direction is along x-axis
    Parameters
    ----------
    point_1 : list of x,y,z coordinates
        starting position
    point_2 : list of x,y,z coordinates
        last impact of the ray
    dir : list of x,y,z
        last direction of the ray

    Returns
    -------
    the refractive power of the system as float

    """
    dist = np.sqrt((point_1[1] - point_2[1]) ** 2 + (point_1[2] - point_2[2]) ** 2)
    height = dist / dir[2]
    angle = np.pi / 2 - np.arccos(dir[2] / np.sqrt(dir[0] ** 2 + dir[1] ** 2 + dir[2] ** 2))
    refractive_power = 1 / (
        np.sqrt((height * dir[0]) ** 2 + (height * dir[1]) ** 2 + (height * dir[2]) ** 2) * np.cos(angle)
    )
    return refractive_power


def create_diopter_map(
    lpf_object, sequence_id, export_name, export_path=r"c:\temp", map_size=[-900, 900, 600, 1200], map_res=[360, 120]
):
    """
    function to create a diopter map based on the simple refractive power computation
    the map will be build based on the last impact yz position
    Parameters
    ----------
    lpf_object : DpfLpfReader object
        LPF reader object with loaded file
    sequence_id : int
        sequence id for which to create the diopter map
    export_name : str
        name of the exported XMP file
    export_path : str
        path to which to export the xmp
    map_size : list of floats
        [XMin, XMax, YMin, YMax] map dimensions
    map_res : list of ints
        resolution in [x,y]

    Returns
    -------
    DpfXmpViewer object

    """
    refractive_power = []
    for trace in lpf_object.sequences[sequence_id]:
        last_dir = [trace.LastDirection.Get(0), trace.LastDirection.Get(1), trace.LastDirection.Get(2)]
        point_1 = [trace.vImpacts.Get(1).Get(0), trace.vImpacts.Get(1).Get(1), trace.vImpacts.Get(1).Get(2)]
        point_2 = [
            trace.vImpacts.Get(lpf_object.sequence_impacts[sequence_id] - 1).Get(0),
            trace.vImpacts.Get(lpf_object.sequence_impacts[sequence_id] - 1).Get(1),
            trace.vImpacts.Get(lpf_object.sequence_impacts[sequence_id] - 1).Get(2),
        ]
        temp_list = [
            round(point_2[0], 1),
            round(point_2[1], 1),
            round(point_2[2], 1),
            compute_refactive_power(point_1, point_2, last_dir),
        ]
        refractive_power.append(temp_list)
    my_list = refractive_power
    diopter_map = MapStruct(3, 20, 9, 1, map_size, map_res)
    diopter_map.export_name = export_name
    data = np.zeros((map_res[0], map_res[1]), dtype=list)
    step_x = (map_size[1] - (map_size[0])) / map_res[0]
    step_y = (map_size[3] - (map_size[2])) / map_res[1]
    for x in range(map_res[0]):
        for y in range(map_res[1]):
            data[x, y] = []
    for item in my_list:
        x_values = np.arange(map_size[0], map_size[1], step_x)
        y_values = np.arange(map_size[2], map_size[3], step_y)
        x_values = x_values.tolist()
        y_values = y_values.tolist()
        x_values.append(item[1])
        y_values.append(item[2])
        x_values.sort()
        y_values.sort()
        x = map_res[0] + 1 - x_values.index(item[1])
        y = map_res[1] + 1 - y_values.index(item[2])
        if not (x > map_res[0] and y > map_res[1]):
            data[x, y].append(item[3])

    for x in range(map_res[0]):
        for y in range(map_res[1]):
            if len(data[x, y]) == 0:
                diopter_map.data[0, x, y, 0] = 0
            else:
                diopter_map.data[0, x, y, 0] = sum(data[x, y]) / len(data[x, y])
    xmp = diopter_map.export_to_xmp(export_path)
    return xmp


file_name = getfilename("*.lpf")
my_lpf = DpfLpfReader()
my_lpf.open_file(file_name)
my_lpf.retrieve_traces()
xmp_trans = create_diopter_map(my_lpf, 1, "trans")
xmp_trans = create_diopter_map(my_lpf, 2, "ghost", map_res=[180, 60])
