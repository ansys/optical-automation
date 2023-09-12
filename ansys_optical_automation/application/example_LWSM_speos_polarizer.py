import sys
import tkinter as tk
from tkinter import filedialog

import numpy as np

lumapi_location = r"C:\Program Files\Lumerical\v222\api\python"
sys.path.append(lumapi_location)
import lumapi


class Polarize:
    def __init__(self):
        self.parallel_r = 100
        self.parallel_t = 0
        self.parallel_a = 0
        self.normal_r = 100
        self.normal_t = 0
        self.normal_a = 0

    def process(self):
        self.parallel_r /= 100
        self.parallel_t /= 100
        self.normal_r /= 100
        self.normal_t /= 100
        self.parallel_a = 1 - self.parallel_r - self.parallel_t
        self.normal_a = 1 - self.normal_r - self.normal_t


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
        file_path = filedialog.askopenfilename(filetypes=[("coated", extension)])
    else:
        file_path = filedialog.asksaveasfilename(filetypes=[("coated", extension)])
        if not file_path.endswith(extension.strip("*")):
            file_path += extension.strip("*")
    return file_path


def read_input(coated_file):
    file = open(coated_file, "r")
    incident_angles = 0
    wavelengths = 0
    incident_angles_list = []
    wavelength_list = []
    p_info = []

    for line_id, line in enumerate(file):
        if line_id < 2:
            continue
        if line_id == 2:
            incident_angles, wavelengths = line.strip().split(" ")
            continue
        if line_id == 3:
            wavelength_list = [float(item) for item in line.strip("\t").split()]
            continue
        print(len(line.strip("\t").split()))
        if len(line.strip("\t").split()) != 2 * len(wavelength_list):
            incident_angles_list.append(float(line.strip("\t").split()[0]))
            p_info.append([Polarize() for _ in wavelength_list])
            for item_id, item in enumerate(p_info[-1]):
                print("value: ", 1 + item_id * 2, float(line.strip("\t").split()[1 + item_id * 2]))
                item.parallel_r = float(line.strip("\t").split()[1 + item_id * 2])
                item.parallel_t = float(line.strip("\t").split()[1 + item_id * 2 + 1])
        else:
            for item_id, item in enumerate(p_info[-1]):
                item.normal_r = float(line.strip("\t").split()[item_id * 2])
                item.normal_t = float(line.strip("\t").split()[item_id * 2 + 1])
    file.close()
    if int(incident_angles) != len(p_info):
        raise TypeError("File structure is not correct: incident angle value does not matching")
    if int(wavelengths) != len(wavelength_list):
        raise TypeError("File structure is not correct: wavelength values do not match")
    return incident_angles_list, wavelength_list, p_info


output_file = r"D:\Customer\Valeo\Polarizor\Test"
lsf = r"D:\Customer\Valeo\Polarizor\util_func - modGB (1).lsf"
input_coated_file = getfilename("coated")

theta_list, wavelength_list, polarize_info = read_input(input_coated_file)
phi_list = [0, 90, 180, 270, 360]
for wavelength_idx, wavelength in enumerate(wavelength_list):
    for theta_idx, theta in enumerate(theta_list):
        p = polarize_info[theta_idx][wavelength_idx]
        print(p.parallel_r)
        p.process()

R_lower = np.zeros((len(theta_list), len(phi_list), len(wavelength_list), 1, 2, 2))
R_upper = np.zeros((len(theta_list), len(phi_list), len(wavelength_list), 1, 2, 2))
T_lower = np.zeros((len(theta_list), len(phi_list), len(wavelength_list), 1, 2, 2))
T_upper = np.zeros((len(theta_list), len(phi_list), len(wavelength_list), 1, 2, 2))
for wavelength_idx in range(len(wavelength_list)):
    p_r = []
    p_t = []
    s_r = []
    s_t = []
    for theta_idx in range(len(theta_list)):
        p = polarize_info[theta_idx][wavelength_idx]
        p_r_item = []
        p_t_item = []
        s_r_item = []
        s_t_item = []
        for phi_idx, phi in enumerate(phi_list):
            s_r_item.append(p.normal_r if phi_idx % 2 == 0 else p.parallel_r)
            s_t_item.append(p.normal_t if phi_idx % 2 == 0 else p.parallel_t)
            p_r_item.append(p.parallel_r if phi_idx % 2 == 0 else p.normal_r)
            p_t_item.append(p.parallel_t if phi_idx % 2 == 0 else p.normal_t)
        s_r.append(s_r_item)
        s_t.append(s_t_item)
        p_r.append(p_r_item)
        p_t.append(p_t_item)
    R_lower[:, :, wavelength_idx, 0, 0, 0] = s_r
    T_lower[:, :, wavelength_idx, 0, 0, 0] = s_t
    R_upper[:, :, wavelength_idx, 0, 0, 0] = s_r
    T_upper[:, :, wavelength_idx, 0, 0, 0] = s_t

    R_lower[:, :, wavelength_idx, 0, 1, 1] = p_r
    T_lower[:, :, wavelength_idx, 0, 1, 1] = p_t
    R_upper[:, :, wavelength_idx, 0, 1, 1] = p_r
    T_upper[:, :, wavelength_idx, 0, 1, 1] = p_t


# print(R_upper[:, :, 0, 0, 1, 1])
# print(R_upper[:, :, 1, 0, 1, 1])
# print(R_upper[:, :, 2, 0, 1, 1])
# print(R_upper[:, :, 3, 0, 1, 1])
# print(R_upper[:, :, 4, 0, 1, 1])
# print(R_upper[:, :, 5, 0, 1, 1])
# theta = [0, 60, 90]
# phi = [0, 90, 180, 270, 360]                         #pol // = phi
# wavelength = [400e-9, 550e-9, 700e-9]
# R_lower = R_upper = T_lower = T_upper = matrix(length(theta), length(phi), length(wavelength), 1, 2, 2)
# R_lower = R_upper = T_lower = T_upper = np.zeros((len(theta), len(phi), len(wavelength), 1, 2, 2))
#
#
# # 400nm                                                 #S Polarization
# R_lower[:, :, 0, 0, 0, 0] = [
#     [0.5,0.5,0.5,0.5,0.5],     #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# T_lower[:, :, 0, 0, 0, 0] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# R_upper[:, :, 0, 0, 0, 0] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# T_upper[:, :, 0, 0, 0, 0] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# R_lower[:, :, 0, 0, 1, 1] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# T_lower[:, :, 0, 0, 1, 1] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# R_upper[:, :, 0, 0, 1, 1] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# T_upper[:, :, 0, 0, 1, 1] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
#
#
#
# # # 550nm
# R_lower[:, :, 1, 0, 0, 0] = [
#     [0.5,0.5,0.5,0.5,0.5],     #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# T_lower[:, :, 1, 0, 0, 0] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# R_upper[:, :, 1, 0, 0, 0] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# T_upper[:, :, 1, 0, 0, 0] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# R_lower[:, :, 1, 0, 1, 1] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# T_lower[:, :, 1, 0, 1, 1] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# R_upper[:, :, 1, 0, 1, 1] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# T_upper[:, :, 1, 0, 1, 1] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
#
#
#
# # # 700nm
# R_lower[:, :, 2, 0, 0, 0] = [
#     [0.5,0.5,0.5,0.5,0.5],     #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# T_lower[:, :, 2, 0, 0, 0] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# R_upper[:, :, 2, 0, 0, 0] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# T_upper[:, :, 2, 0, 0, 0] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# R_lower[:, :, 2, 0, 1, 1] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# T_lower[:, :, 2, 0, 1, 1] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# R_upper[:, :, 2, 0, 1, 1] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
# T_upper[:, :, 2, 0, 1, 1] = [
#     [0.5,0.5,0.5,0.5,0.5],           #[phi1,phi2,phi3,phi4,phi5;(Theta1)
#     [0.5,0.5,0.5,0.5,0.5],           # phi1,phi2,phi3,phi4,phi5;(Theta2)
#     [0.5,0.5,0.5,0.5,0.5]
# ]
#

fdtd = lumapi.FDTD(lsf, hide=True)
fdtd.feval(lsf)
fdtd.simpleRT(1.0, 1.5, True, R_lower, T_lower, R_upper, T_upper, theta_list, phi_list, wavelength_list, output_file)
