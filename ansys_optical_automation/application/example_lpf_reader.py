import math
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


def dot_product(vector1, vector2):
    """
    function to multiply to vectors
    Parameters
    ----------
    vector1 : list
        [x,y,z]
    vector2 : list
        [x,y,z]
    Returns
    -------
    int
    """
    return vector1[0] * vector2[0] + vector1[1] * vector2[1] + vector1[2] * vector2[2]


def vector_normalize(vector):
    """
    get normalized vector.

    Parameters
    ----------
    vector : list
        [x,y,z]

    Returns
    -------
    list
        list representing normalized vector

    """
    vector_magnitude = vector_len(vector)
    return [round(item / vector_magnitude, 1) for item in vector]


def vector_len(vector):
    """
    compute vector length
    Parameters
    ----------
    vector : list
        [x,y,z]

    Returns
    -------
    float
        length of a vector

    """
    return math.sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)


def compute_refactive_power(point_1, point_2, dir_out, dir_in):
    """
    function to compute refractive power of an optical object
    input direction is along z-axis
    Parameters
    ----------
    dir_in: list
        lighting incoming direction
    point_1 : list of x,y,z coordinates
        starting position
    point_2 : list of x,y,z coordinates
        last impact of the ray
    dir_out : list of x,y,z
        last direction of the ray

    Returns
    -------
    the refractive power of the system as float

    """
    if dir_in not in [[0, 0, 1], [0, 1, 0], [1, 0, 0]]:
        raise ValueError("dir in needs to be to an major axis direction")
    dist = math.sqrt(
        0 ** dir_in[0] * (point_1[0] - point_2[0]) ** 2
        + 0 ** dir_in[1] * (point_1[1] - point_2[1]) ** 2
        + 0 ** dir_in[2] * (point_1[2] - point_2[2]) ** 2
    )

    height = dist / dot_product(dir_in, dir_out)
    angle = math.pi / 2 - np.arccos(dot_product(dir_in, dir_out) / (vector_len(dir_in) * vector_len(dir_out)))
    refractive_power = 1 / (
        math.sqrt((height * dir_out[0]) ** 2 + (height * dir_out[1]) ** 2 + (height * dir_out[2]) ** 2)
        * math.cos(angle)
    )
    return refractive_power


def create_diopter_map(lpf_object, sequence_id, export_name, export_path, map_size, map_res):
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
        dir_out = [trace.LastDirection.Get(0), trace.LastDirection.Get(1), trace.LastDirection.Get(2)]
        vector_in = [
            abs(trace.vImpacts.Get(0).Get(0) - trace.vImpacts.Get(1).Get(0)),
            abs(trace.vImpacts.Get(0).Get(1) - trace.vImpacts.Get(1).Get(1)),
            abs(trace.vImpacts.Get(0).Get(2) - trace.vImpacts.Get(1).Get(2)),
        ]
        dir_in = vector_normalize(vector_in)
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
            compute_refactive_power(point_1, point_2, dir_out, dir_in),
        ]
        refractive_power.append(temp_list)
    diopter_map = MapStruct(3, 20, 2, 9, 1, map_size, map_res)
    data = np.zeros((map_res[0], map_res[1]), dtype=list)
    step_x = (map_size[1] - map_size[0]) / map_res[0]
    step_y = (map_size[3] - map_size[2]) / map_res[1]
    for x in range(map_res[0]):
        for y in range(map_res[1]):
            data[x, y] = []
    # TODO current sensor x align with global y, sensor y aligns with global z
    for item in refractive_power:
        x_idx = math.floor((item[1] - map_size[0]) / step_x)
        y_idx = math.floor((item[2] - map_size[2]) / step_y)
        x = map_res[0] - x_idx
        y = map_res[1] - y_idx
        data[x, y].append(item[3])
    for x in range(map_res[0]):
        for y in range(map_res[1]):
            if len(data[x, y]) == 0:
                diopter_map.data[0, x, y, 0] = 0
            else:
                diopter_map.data[0, x, y, 0] = sum(data[x, y]) / len(data[x, y])
    diopter_map.export_name = export_name
    xmp = diopter_map.export_to_xmp(export_path)
    return xmp


file_name = getfilename("*.lpf")
my_lpf = DpfLpfReader(231)
my_lpf.open_file(file_name)
my_lpf.retrieve_traces()
# TODO current sensor x align with global y, sensor y aligns with global z
xmp_size = [-my_lpf.trace_boundary[1], my_lpf.trace_boundary[1], -my_lpf.trace_boundary[2], my_lpf.trace_boundary[2]]
create_diopter_map(my_lpf, 1, "trans", r"c:\temp", xmp_size, [50, 50])
create_diopter_map(my_lpf, 2, "ghost", r"c:\temp", xmp_size, [50, 50])
