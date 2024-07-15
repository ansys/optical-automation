import math
import tkinter as tk
from tkinter import filedialog

import matplotlib.pyplot as plt

from ansys_optical_automation.post_process.dpf_lpf_reader import DpfLpfReader
from ansys_optical_automation.post_process.dpf_xmp_viewer import MapStruct
from ansys_optical_automation.scdm_core.utils import degree
from ansys_optical_automation.scdm_core.utils import radiance
from ansys_optical_automation.scdm_core.utils import vector_dot_product
from ansys_optical_automation.scdm_core.utils import vector_normalize


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


class LpfRay:
    """
    this class defines the windshield distortion calculation using Lpf file property
    """

    def __init__(self, alpha, ray):
        self.rays = [ray]
        self.end_direction = [
            vector_normalize(
                [
                    ray.LastDirection.Get(0),
                    ray.LastDirection.Get(1),
                    ray.LastDirection.Get(2),
                ]
            )
        ]
        self.ref_alpha = alpha
        self.position = [ray.vImpacts.Get(2).Get(0), ray.vImpacts.Get(2).Get(1), ray.vImpacts.Get(2).Get(2)]
        self.start_position = [
            ray.vImpacts.Get(0).Get(0),  # start position x
            ray.vImpacts.Get(0).Get(1),  # start position y
            ray.vImpacts.Get(0).Get(2),  # start position z
        ]
        self.calc_alpha = []
        self.ini_pos = [self.start_position]
        self.optical_distortion = 0
        self.optical_diopter = 0

    def ECE_R43(self):
        """
        optical distortion calculation method defined by ECE_R43
        Returns
        -------

        """
        max_distortion = 0
        distortion = 0
        for idx, item in enumerate(self.end_direction[1:]):
            v3Radius_vector = [
                self.ini_pos[0][0] - self.ini_pos[idx + 1][0],
                self.ini_pos[0][1] - self.ini_pos[idx + 1][1],
                self.ini_pos[0][2] - self.ini_pos[idx + 1][2],
            ]
            v3Radius_vector = vector_normalize(v3Radius_vector)
            current_distortion = math.fabs(vector_dot_product(item, self.end_direction[0]))
            current_distortion = 0.0 if current_distortion > 1.0 else degree(math.acos(current_distortion))
            v3Radius = [
                v3Radius_vector[0]
                - vector_dot_product(v3Radius_vector, self.end_direction[0]) * self.end_direction[0][0],
                v3Radius_vector[1]
                - vector_dot_product(v3Radius_vector, self.end_direction[0]) * self.end_direction[0][1],
                v3Radius_vector[2]
                - vector_dot_product(v3Radius_vector, self.end_direction[0]) * self.end_direction[0][2],
            ]
            v3Radius = vector_normalize(v3Radius)
            current_distortion = math.copysign(current_distortion, -vector_dot_product(v3Radius, item))
            if math.fabs(current_distortion) > max_distortion:
                max_distortion = math.fabs(current_distortion)
                distortion = current_distortion
        self.optical_distortion = distortion
        self.optical_diopter = radiance(distortion) / 0.012


def ref_lpf_process(data, sequence=True):
    """
    function to process lpf files to be used for distortion calculation.

    Parameters
    ----------
    data : DpfLpfReader
        DpfLpfReader that contains LPF information
    sequence : bool
        sequence study

    """
    trace_count = data.dpf_instance.GetNbOfTraces()
    traces = data.pdf_speos.Vector_COptRayPath()
    print(trace_count)
    traces.Resize(trace_count)
    error = data.dpf_instance.GetRayPathBundle(traces.ToSpan())
    data.error_manager(error)
    distortion_analysis_info = []
    if sequence:
        for trace in traces:
            lpf_in = vector_normalize(
                [
                    trace.vImpacts.Get(1).Get(0) - trace.vImpacts.Get(0).Get(0),
                    trace.vImpacts.Get(1).Get(1) - trace.vImpacts.Get(0).Get(1),
                    trace.vImpacts.Get(1).Get(2) - trace.vImpacts.Get(0).Get(2),
                ]
            )
            lpf_out = vector_normalize(
                [
                    trace.LastDirection.Get(0),
                    trace.LastDirection.Get(1),
                    trace.LastDirection.Get(2),
                ]
            )
            alpha = math.acos(vector_dot_product(lpf_in, lpf_out))
            distortion_analysis_info.append(LpfRay(alpha, trace))
    distortion_analysis_info = sorted(
        distortion_analysis_info, key=lambda x: (x.start_position[2], x.start_position[1]), reverse=True
    )
    return distortion_analysis_info


def add_lpf_data(data_list):
    """
    function to add lpf data for windshield distortion study.

    Parameters
    ----------
    data_list : list
        a list of ref_lpf_process: first as reference ray data followed by sampling ray data

    Returns
    -------


    """
    ref = data_list[0]
    for data_idx, data in enumerate(data_list[1:]):
        for item_idx, item in enumerate(ref):
            ref[item_idx].rays.append(data[item_idx].rays[0])
            ref[item_idx].end_direction.append(data[item_idx].end_direction[0])
            ref[item_idx].ini_pos.append(data[item_idx].start_position)
            ref[item_idx].calc_alpha.append(data[item_idx].ref_alpha)
            if data_idx == len(data_list[1:]) - 1:
                ref[item_idx].ECE_R43()
    # for item in ref:
    #     print(item.start_position, item.ref_alpha, item.calc_alpha, item.optical_power)
    return ref


def plot_result(data_result):
    """
    function to plot result for windshield distortion data.

    Parameters
    ----------
    data_result : list
        a list of data in format: [x, y, optical power]

    Returns
    -------


    """
    x = []
    y = []
    distortion_value = []
    diopter_value = []
    distortion_max = 0
    diopter_max = 0
    for item in data_result:
        x.append(item.start_position[1])
        y.append(item.start_position[2])
        distortion_value.append(item.optical_distortion)
        diopter_value.append(item.optical_diopter)
        distortion_max = max(distortion_max, item.optical_distortion)
        diopter_max = max(diopter_max, item.optical_diopter)

    # plot distortion map
    plt.scatter(x, y, c=distortion_value, s=10, marker="s")
    plt.axis("scaled")
    plt.colorbar()
    # cbar.set_ticks(np.arange(0, distortion_max + distortion_max / 10.0, distortion_max / 10.0))
    plt.clim(-1, 1)
    plt.set_cmap("bwr")
    plt.title("Distortion Map (Degree)")
    plt.show()

    # plot diopter map
    plt.scatter(x, y, c=diopter_value, s=10, marker="s")
    plt.axis("scaled")
    plt.colorbar()
    # cbar.set_ticks(np.arange(0, diopter_max + diopter_max / 10.0, diopter_max / 10.0))
    plt.clim(-1, 1)
    plt.set_cmap("bwr")
    plt.title("Diopter Map (Diopter)")

    plt.show()


def plot_result_xmp(data_result):
    """
    function to plot result for windshield distortion data into XMP file.

    Parameters
    ----------
    data_result : list
        a list of data in format: [x, y, optical power]

    Returns
    -------


    """
    x = []
    y = []
    distortion_value = []
    diopter_value = []
    distortion_max = 0
    diopter_max = 0
    for item in data_result:
        x.append(item.start_position[1])
        y.append(item.start_position[2])
        distortion_value.append(item.optical_distortion)
        diopter_value.append(item.optical_diopter)
        distortion_max = max(distortion_max, item.optical_distortion)
        diopter_max = max(diopter_max, item.optical_diopter)

    x_axis = sorted(list(set(x)), reverse=True)
    y_axis = sorted(list(set(y)), reverse=True)
    distortion_value_map = MapStruct(
        3, 20, 0, 9, 1, [min(x_axis), max(x_axis), min(y_axis), max(y_axis)], [len(x_axis), len(y_axis)]
    )
    distortion_value_map.export_name = "distortion_map"
    diopter_value_map = MapStruct(
        3, 20, 0, 9, 1, [min(x_axis), max(x_axis), min(y_axis), max(y_axis)], [len(x_axis), len(y_axis)]
    )
    diopter_value_map.export_name = "optical_power_map"
    for y_idx, y_item in enumerate(y_axis):
        for x_idx, x_item in enumerate(x_axis):
            distortion_value_map.data[0, x_idx, y_idx, 0] = distortion_value[y_idx * len(x_axis) + x_idx]
            diopter_value_map.data[0, x_idx, y_idx, 0] = diopter_value[y_idx * len(x_axis) + x_idx]
    distortion_value_map.export_to_xmp(r"c:\temp")
    diopter_value_map.export_to_xmp(r"c:\temp")


def main():
    """
    main function to run windshield distortion study, available methods:
        ECE_R43

    Returns
    -------


    """
    data = []
    speos_version = 241
    for selection in range(5):
        file_name = getfilename("*.lpf; *.lp3")
        if file_name == "":
            print("Complete, no file has been selected")
        else:
            my_lpf = DpfLpfReader(speos_version)
            my_lpf.open_file(file_name)
            print("You have loaded data from: ", file_name, " has number of rays:")
            data.append(ref_lpf_process(my_lpf))

    if len(data) != 0:
        result = add_lpf_data(data)
        plot_result(result)
        # plot_result_xmp(result)


main()
