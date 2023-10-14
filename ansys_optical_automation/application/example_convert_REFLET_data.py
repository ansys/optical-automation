import math
import os
import tkinter as tk
from tkinter import filedialog

import matplotlib.pyplot as plt
import numpy as np

# file = r"D:\Customer\Continental\Reflet\LAB_Anisotropic_BSDF_Surface (4)\test.txt"
#
# phi_list = []
# theta_list = []
# bsdf = []
# with open(file) as myfile:
#     for idx, line in enumerate(myfile):
#         if idx == 0:
#             phi_list = [float(item) for item in line.split()]
#         else:
#             line_content = [float(item) for item in line.split()]
#             theta_list.append(line_content[0])
#             bsdf.append(line_content[1:])
# def get_val(theta, phi):
#     theta_id = theta_list.index(theta)
#     phi_id = phi_list.index(phi)
#     return bsdf[theta_id][phi_id]
#
# theta_2d_ressampled, phi_2d_ressampled = np.meshgrid(np.array(theta_list), np.array(phi_list))
# bsdf_resample = []
# phi_temp = phi_2d_ressampled.reshape(-1)
# theta_temp = theta_2d_ressampled.reshape(-1)
# for idx, item in enumerate(phi_temp):
#     bsdf_resample.append(get_val(theta_temp[idx],phi_temp[idx]))
#
# bsdf_resample = np.array(bsdf_resample)
# bsdf_resample = bsdf_resample.reshape(np.shape(theta_2d_ressampled)[0], np.shape(theta_2d_ressampled)[1])
# print(np.shape(bsdf_resample), np.shape(theta_2d_ressampled))
# # samples on which integrande is known
# theta_rad, phi_rad = np.radians(theta_2d_ressampled), np.radians(phi_2d_ressampled)
# integrande = (1 / math.pi) * bsdf_resample * np.sin(theta_rad)  # *theta for polar integration
# f = interpolate.interp2d(theta_rad, phi_rad, integrande, kind="linear", bounds_error=False, fill_value=0)
# # calculation of integrande as from samples
# r = nquad(f, [[0, math.pi / 2], [0, 2 * math.pi]], opts=[{"epsabs": 0.1}, {"epsabs": 0.1}])
# print(r)

# x = np.linspace(-5, 5, 5)
# y = np.linspace(-4, 4, 5)
# X, Y = np.meshgrid(x, y)
# print(X, Y)
# Z = Y**2 + X**2
# print(Z)


def getfilepath():
    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory()
    return folder_selected


def deg_to_rad(degree_value):
    return degree_value * math.pi / 180.0


def read_reflect_data(file):
    flg = False
    phi_step = 0
    in_theta_list = []
    in_bsdf = []
    with open(file) as myfile:
        for line in myfile:
            if "Phi measure step" in line:
                phi_step = float(line.split(":")[1])
                continue
            if "Theta Lighting" in line:
                flg = True
                continue
            if flg is True:
                content = [float(item) for item in line.split()]
                in_theta_list.append(content[0])
                in_bsdf.append(content[1:])
    in_phi_list = np.arange(-90, 90 + phi_step, phi_step).tolist()
    out_theta_list = [item for item in in_theta_list if item >= 0]
    out_phi_list = np.arange(0, 360 + phi_step, phi_step).tolist()
    return in_theta_list, in_phi_list, out_theta_list, out_phi_list, in_bsdf


def coordinate_convert(o_theta, o_phi):
    i_phi = 0
    i_theta = 0
    if o_phi <= 90 or o_phi >= 270:
        i_theta = -o_theta
        i_phi = o_phi if o_phi <= 90 else o_phi - 360
    else:
        i_theta = o_theta
        i_phi = o_phi - 180
    return i_theta, i_phi


def reflect_coordinate_convert(o_theta, o_phi):
    i_phi = 0
    i_theta = 0
    if o_phi <= 180:
        i_theta = o_theta
        i_phi = o_phi - 90
    else:
        i_theta = -o_theta
        i_phi = o_phi - 270
    return i_theta, i_phi


def convert_bsdf(out_theta_list, out_phi_list, in_theta_list, in_phi_list, in_bsdf, rt_value, bsdf_type):
    rt_value = min(rt_value[0] if "BTDF" in bsdf_type else rt_value[1], 1)

    def get_val(theta, phi):
        return in_bsdf[in_theta_list.index(theta)][in_phi_list.index(phi)]

    def get_bsdf_val(theta, phi):
        i_theta, i_phi = reflect_coordinate_convert(theta, phi)
        i_phi = round(i_phi, 3)
        return get_val(i_theta, i_phi)

    def get_bsdf_reflet_val_ave(theta, phi):
        return (get_bsdf_val(theta, phi) + get_bsdf_val(theta, 360 - phi)) / 2.0

    def get_bsdf_reflet_val_sm(theta, phi):
        if phi == 0:
            phi = 360
        i_theta, i_phi = reflect_coordinate_convert(theta, phi)
        i_phi = round(i_phi, 3)
        return get_val(i_theta, i_phi)

    def get_delta(idx, val_list):
        if idx == 0:
            return (val_list[1] - val_list[0]) / 2.0
        elif idx == len(val_list) - 1:
            return (val_list[-1] - val_list[-2]) / 2.0
        else:
            return (val_list[idx + 1] - val_list[idx - 1]) / 2.0

    def get_bsdf_integration(bsdf, theta_idx, phi_idx):
        # bsdf_val = 0
        # if phi_idx == 0:
        #     bsdf_val = (bsdf + get_bsdf_reflet_val_sm(out_theta_list[theta_idx], out_phi_list[phi_idx + 1])) / 4.0
        # elif phi_idx == len(out_phi_list) - 1:
        #     bsdf_val = (bsdf + get_bsdf_reflet_val_sm(out_theta_list[theta_idx], out_phi_list[phi_idx - 1])) / 4.0
        # else:
        #     bsdf_val = bsdf
        if phi_idx == 0:
            return 0
        integration = (
            bsdf
            * math.sin(deg_to_rad(out_theta_list[theta_idx]))
            * deg_to_rad(get_delta(theta_idx, out_theta_list))
            * deg_to_rad(get_delta(phi_idx, out_phi_list))
        )
        if phi_idx == len(out_phi_list) - 1:
            return 2 * integration
        else:
            return integration

    bsdf_integration = 0
    out_bsdf = []
    # print(out_theta_list)
    # print(out_phi_list)
    for o_theta_idx, o_theta in enumerate(out_theta_list):
        out_bsdf_list = []
        for o_phi_idx, o_phi in enumerate(out_phi_list):
            o_bsdf = get_bsdf_reflet_val_sm(o_theta, o_phi)
            bsdf_integration += get_bsdf_integration(o_bsdf, o_theta_idx, o_phi_idx)
            out_bsdf_list.append(o_bsdf)
        out_bsdf.append(out_bsdf_list)
    normalized_bsdf = []
    for bsdf_list in out_bsdf:
        normalized_bsdf.append([bsdf * rt_value / bsdf_integration for bsdf in bsdf_list])
    return normalized_bsdf


def write_header(incident_file_list, file_out, rt_value, bsdf_type):
    rt_value = min(rt_value[0] if "BTDF" in bsdf_type else rt_value[1], 1)

    file_out.write("OPTIS - Anisotropic BSDF surface file v7.0\n")
    file_out.write("0\n")
    file_out.write("Comment\n")
    file_out.write("23\n")
    file_out.write("Measurement description\n")
    file_out.write("1\t0\t0\n")
    if "BRDF" in bsdf_type:
        file_out.write("1\t0\n")
    else:
        file_out.write("0\t1\n")
    file_out.write("0\n")
    file_out.write("1\n")
    file_out.write("0\n")
    file_out.write(str(len(incident_file_list)) + "\n")
    content = "\t".join(
        [
            str(float(os.path.splitext(os.path.basename(incident_file))[0].rsplit("_", 1)[1]) / 10.0)
            for incident_file in incident_file_list
        ]
    )
    file_out.write(content + "\n")
    file_out.write("0\t0\n\n")
    file_out.write("2\n")
    file_out.write("350\t" + str(rt_value * 100) + "\n")
    file_out.write("850\t" + str(rt_value * 100) + "\n")


def write_out(bsdf, out_theta_list, out_phi_list, file_out, bsdf_type):
    separator = "\t"
    file_out.write(str(len(out_theta_list)) + "\t" + str(len(out_phi_list)) + "\n")
    content = separator.join("{:.2f}".format(item) for item in out_phi_list) + "\n"
    file_out.write(content)
    if "BRDF" in bsdf_type:
        for bsdf_idx, bsdf_line in enumerate(bsdf):
            content = "{:.3f}".format(out_theta_list[bsdf_idx]) + "\t"
            content += separator.join("{:.8f}".format(item) for item in bsdf_line) + "\n"
            file_out.write(content)
    else:
        for bsdf_idx, bsdf_line in reversed(list(enumerate(bsdf))):
            content = "{:.3f}".format(180 - out_theta_list[bsdf_idx]) + "\t"
            content += separator.join("{:.8f}".format(item) for item in bsdf_line) + "\n"
            file_out.write(content)


def read_RT(file):
    RT = []
    with open(file) as myfile:
        for line in myfile:
            if "AOI" in line:
                RT_value = line.split()[2:]
                RT.append([float(value) for value in RT_value])
    return RT


def plot_result(theta_list, phi_list, bsdf, tittle):
    h = []
    v = []
    z = []
    for item_list_idx, item_list in enumerate(bsdf):
        for item_idx, item in enumerate(item_list):
            v.append(phi_list[item_idx])
            h.append(theta_list[item_list_idx])
            z.append(item)
    plt.title(os.path.basename(tittle))
    plt.xlabel("theta list")
    plt.ylabel("phi list")
    plt.scatter(h, v, c=z)
    plt.axis("scaled")
    plt.show()


def main():
    def order_method(item):
        f_name = os.path.basename(item)
        name = os.path.splitext(f_name)[0]
        return float(name.split("_")[-1])

    reflet_dir = getfilepath()
    groups = {}
    rt_value_list = []
    for filename in os.listdir(reflet_dir):
        if not filename.endswith("txt"):
            continue
        if "RTfile" in filename:
            rt_value_list = read_RT(os.path.join(reflet_dir, filename))
            continue
        measurement_session = os.path.splitext(filename)[0].rsplit("_", 1)[0]
        if measurement_session not in groups:
            groups[measurement_session] = []
        groups[measurement_session].append(os.path.join(reflet_dir, filename))

    for group in groups:
        groups[group].sort(key=order_method)
        if len(groups[group]) != len(rt_value_list):
            raise ValueError(
                "Please check your measurement data, number of RT values does not match measurement files number"
            )

    for group in groups:
        out_file = os.path.join(reflet_dir, group + ".anisotropicbsdf")
        if os.path.isfile(out_file):
            os.remove(out_file)
        file_out = open(out_file, "a")
        write_header(groups[group], file_out, rt_value_list[0], group)
        for file_idx, file_dir in enumerate(groups[group]):
            in_theta_list, in_phi_list, out_theta_list, out_phi_list, in_bsdf = read_reflect_data(file_dir)
            # plot_result(in_theta_list, in_phi_list, in_bsdf, file_dir)

            if (
                in_theta_list != sorted(in_theta_list)
                or in_phi_list != sorted(in_phi_list)
                or out_theta_list != sorted(out_theta_list)
                or out_phi_list != sorted(out_phi_list)
            ):
                raise ValueError("Please check the measurement setup")
            out_bsdf = convert_bsdf(
                out_theta_list,
                out_phi_list,
                in_theta_list,
                in_phi_list,
                in_bsdf,
                rt_value_list[file_idx],
                group,
            )
            write_out(out_bsdf, out_theta_list, out_phi_list, file_out, group)
        file_out.write("End of file\n")
        file_out.close()


main()
