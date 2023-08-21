import math
import tkinter as tk
from tkinter import filedialog

import matplotlib.pyplot as plt

from ansys_optical_automation.post_process.dpf_lpf_reader import DpfLpfReader
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
        self.ref_alpha = alpha
        self.position = [ray.vImpacts.Get(2).Get(0), ray.vImpacts.Get(2).Get(1), ray.vImpacts.Get(2).Get(2)]
        self.start_position = [
            ray.vImpacts.Get(0).Get(0),  # start position x
            ray.vImpacts.Get(0).Get(1),  # start position y
            ray.vImpacts.Get(0).Get(2),  # start position z
        ]
        self.calc_alpha = []
        self.optical_power = 0

    def ECE_R43(self):
        """
        optical distortion calculation method defined by ECE_R43
        Returns
        -------

        """
        self.optical_power = max(((abs(item - self.ref_alpha)) / 4 for item in self.calc_alpha))


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
            lpf_out = [
                trace.LastDirection.Get(0),
                trace.LastDirection.Get(1),
                math.sqrt(1 - trace.LastDirection.Get(0) ** 2 - trace.LastDirection.Get(1) ** 2),
            ]
            alpha = math.acos(vector_dot_product(lpf_in, lpf_out))
            if lpf_out[1] < 0:
                alpha = -alpha
            else:
                alpha = alpha
            # print(alpha, lpf_out)
            distortion_analysis_info.append(LpfRay(alpha, trace))
    distortion_analysis_info = sorted(
        distortion_analysis_info, key=lambda x: (x.start_position[0], x.start_position[1]), reverse=True
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
            ref[item_idx].calc_alpha.append(data[item_idx].ref_alpha)
            if data_idx == len(data_list[1:]) - 1:
                ref[item_idx].ECE_R43()
    for item in ref:
        print(item.start_position, item.ref_alpha, item.calc_alpha, item.optical_power)
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
    value = []
    for item in data_result:
        x.append(item.start_position[0])
        y.append(item.start_position[1])
        if item.optical_power > 0.1:
            value.append(0)
        else:
            value.append(item.optical_power)
    plt.scatter(x, y, c=value, s=20)
    plt.colorbar()
    plt.show()


def main():
    """
    main function to run windshield distortion study, available methods:
        ECE_R43

    Returns
    -------


    """
    data = []
    for selection in range(5):
        file_name = getfilename("*.lpf")
        if file_name == "":
            print("Complete, no file has been selected")
        else:
            my_lpf = DpfLpfReader(231)
            my_lpf.open_file(file_name)
            data.append(ref_lpf_process(my_lpf))
            print("You have loaded data from: ", file_name)

    if len(data) != 0:
        result = add_lpf_data(data)
        plot_result(result)


main()
