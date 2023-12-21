import csv
import math
import re
import tkinter as tk
from tkinter import filedialog


def convert_line_to_float_list(line: str):
    """
    Function to convert a line of float numbers retrieved from a .txt file to a list of floats. Typically a
    line, when retrieved, is a string of all the characters from the line. First, the function merges the parts of the
    string that are separated by a blank character, and creates a list of strings where each string contains the number
    characters that are separated by a blank space in the original line. Then, in case there are elements of this list
    consisting of solely empty blanks, these elements are removed. Finally, the list of strings is converted to list of
    floats.

    Parameters
    ----------
    line : str
        A string with the content of one line from a .txt file. The line should only include float numbers.

    Returns
    -------
    list
        A list of floats. The floats are the ones separated by blank spaces in the line retrieved from the .txt file.
    """
    # Convert line to list of strings
    line_str_list = re.split("\t", line)

    # Remove empty elements from list
    line_str_list = [value for value in line_str_list if value != ""]

    # Convert list of strings to list of floats
    line_float_list = list(map(float, line_str_list))
    return line_float_list


def select_datafile():
    """
    Function that opens a dialog window for the user to select the file containing the decadic absorbance data. This
    file is in principle a txt, xls, xlsx or dat file. The file content must consist of two columns. The first column
    contains the wavenumber values (cm^-1) and the second column contains the corresponding decadic absorbance values
    (1 ppm-meter).

    Returns
    -------
    str
        A string of the full path of the selected file.
    """
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select file containing decadic absorbance data")
    return file_path


def calculate_transmittance_from_dec_absorbance(dec_absorbance: float):
    """
    Function to calculate the transmittance value from the decadic absorbance value of a material at 1ppm per one meter
    of material.

    Parameters
    ----------
    dec_absorbance : float
        A float representing the decadic absorbance of a material (usually at a specific wavelength). The decadic
        absorbance is physically defined as dec_absorbance=I(0)/I(l), where I(0) is the incident light and I(l)
        absorbance is 10^dec_absorbance = exp(absorbance).

    Returns
    -------
    float
        A float representing the transmittance of a material (usually at a specific wavelength). The transmittance is
        physically defined as transmittance=I(l)/I(0).
    """
    transmittance = 10 ** (-dec_absorbance)  # [ - ] (ppm-meter)
    return transmittance


def calculate_absorption_coef_from_dec_absorbance(dec_absorbance: float):
    """
    Function that calculates the absorption coefficient of a material from the decadic absorbance value of a material at
    1ppm per one meter of material. The absorption coefficient is calculated from the Beer-Lambert law
    I(l)=I(0)exp(-absorption_coef*l) <=> absorption_coef=-ln(transmittance)/l, where I(0) is the incident light and I(l)
    the light transmitted through the propagation distance l.

    Parameters
    ----------
    dec_absorbance : float
        A float representing the decadic absorbance of a material (usually at a specific wavelength). The decadic
        absorbance is physically defined as dec_absorbance=I(0)/I(l).

    Returns
    -------
    float
        A float representing the absorption coefficient (mm^-1) of a material (usually at a specific wavelength).
        NOTE: The relation between absorption coefficient and decadic absorption coefficient is
        dec_absorption_coef=absorption_coef/ln(10).
    """
    transmittance = calculate_transmittance_from_dec_absorbance(dec_absorbance)
    absorption_coef = -math.log(transmittance) / 1e3  # [mm^-1]
    return absorption_coef


def calculate_wavelength_from_wavenumber(wavenumber: float):
    """
    Function that calculates the wavelength (nm) from the wavenumber (cm^-1).

    Parameters
    ----------
    wavenumber : float
        A float representing the wavenumber value (cm^-1)

    Returns
    -------
    float
        A float representing the wavelength value (nm)
    """
    wavelength = 1e7 / wavenumber  # [nm]
    return wavelength


def load_dec_absorbance_data_to_variable():
    """
    Function that locates, opens, and reads the decadic absorbance data file and passes the data into a variable.

    Returns
    -------
    list
        A list variable containing the decadic absorbance data. Each list element is another list of two floats.
        These floats are respectively the wavenumber (cm^-1) and the corresponding decadic absorbance (ppm-meter).
    """
    file_path = select_datafile()
    with open(file_path) as f:
        data_rows = f.readlines()
    data_rows_list = [convert_line_to_float_list(line) for line in data_rows]
    return data_rows_list


def convert_dec_absorbance_data(dec_absorbance_data: list):
    """
    Function that converts the decadic absorbance data to absorption coefficient data in a format that is compatible
    with the syntax of the speos *.material files.

    Parameters
    ----------
    dec_absorbance_data : list
        A list variable containing the decadic absorbance data. Each list element is another list of two floats. These
        floats are respectively the wavenumber (cm^-1) and the corresponding decadic absorbance

    Returns
    -------
    list
        A list variable containing the absorption coefficient data. Each list element is another list of two floats.
        These floats are respectively the wavelength (nm) and the corresponding absorption coefficient (mm^-1).
    """
    absorption_coef_data = [
        [calculate_wavelength_from_wavenumber(row[0]), calculate_absorption_coef_from_dec_absorbance(row[1])]
        for row in dec_absorbance_data
    ]
    return absorption_coef_data


def setup_material_file_for_speos(absorption_coef_data: list):
    """
    A function that creates a Speos *.material file using the provided absorption coefficient data (absorption
    coefficient wrt wavelength), and the assumption that the material has the refractive index and constringence of
    atmospheric air. The function first formulates the file's header as a list of strings. Then it merges the header
    with the absorption coefficient data to create the Speos *.material file with the proper syntax. The file is created
    in the working directory.

    Parameters
    ----------
    absorption_coef_data : list
        A list variable containing the absorption coefficient data. Each list element is
        another list of two floats. These floats are respectively the wavelength (nm) and the corresponding absorption
        coefficient (mm^-1).

    Returns
    -------


    """
    # Set up *.material file for Speos
    refractive_index = 1.00027716  # Atmospheric air
    constringence_value = 89.29  # Atmospheric air
    first_rows = [
        "OPTIS - Material file v13",
        "Material description",
        "Isotropic",
        "Constringence",
        str(refractive_index),
        str(constringence_value),
        str(len(absorption_coef_data)),
    ]

    with open("user_defined_material.material", "w") as g:
        g.write("\n".join(first_rows))
        g.write("\n")
        wr = csv.writer(g, delimiter=" ", lineterminator="\n")
        wr.writerows(absorption_coef_data)
    return


def main():
    """
    The main function of the example performs in sequence three main operations. Reads a data file containing the
    spectral decadic absorbance (decadic absorbance wrt wavenumber), then converts the data to a format compatible with
    the syntax of a speos *.material file, and then creates the respective speos *.material file in the working
    directory.
    This operation is useful for the definition of gases with specific spectral (decadic) absorbance provided by a data
    file.
    ASSUMPTIONS:
    - The provided decadic absorbance is at 1 ppm per one meter of material
    - The provided wavenumber units are [cm^-1]
    - The material has the refractive index and constringence of atmospheric air

    Returns
    -------


    """
    dec_absorbance_data = load_dec_absorbance_data_to_variable()

    absorption_coef_data = convert_dec_absorbance_data(dec_absorbance_data)

    setup_material_file_for_speos(absorption_coef_data)


main()
