import glob
import json
import os
import shutil
import subprocess
import sys
import traceback

unittest_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.dirname(unittest_path)
sys.path.append(lib_path)

from ansys_optical_automation.interop_process.Coating_converter_speos_zemax_Analysis import Coating_converter_speos_zemax_Analysis
# from ansys_optical_automation.scdm_core.utils import get_speos_core
# from ansys_optical_automation.zemax_process.base import BaseZOS
from tests.config import SCDM_VERSION

coating_file = os.path.join(unittest_path, "example_models", "test_12_coating.dat")
coating_file_reference = os.path.join(unittest_path, "example_models", "test_12_coating_reference.bsdf180")
results_json = os.path.join(unittest_path, "test_12_coating_results.json")
results_dict = {}

work_directory = os.path.join(unittest_path, "rayfile")


def check_converted_coatingfile(coatingfile_path, file_type):
    """
    function to compare the coatingfile with its reference
    Parameters
    ----------
    coatingfile_path : str
        path to rayfile
    result_dic : dict
        result dictionary containing the unittest results
    key : str
        name of the dictionary key for the test

    Returns
    -------


    """
    file_path = os.path.splitext(coatingfile_path)[0].lower() + "." + file_type
    reference_file = os.path.splitext(coatingfile_path)[0].lower() + "_reference." + file_type
    reference = open(reference_file, "br")
    reference_data = reference.read()
    reference.close()
    input_coating_file = open(coatingfile_path, "br")
    input_coating_file_data = input_coating_file.read()
    input_coating_file.close()
    return reference_data == input_coating_file_data


def main():
    os.mkdir(work_directory)
    # test01
    test_file = os.path.join(work_directory, "test_12_coating.dat")
    test_reference = os.path.join(work_directory, "test12_coating_reference.bsdf180")
    shutil.copyfile(coating_file, test_file)
    shutil.copyfile(coating_file_reference, test_reference)

    coatingfilename = "test_12_coating.dat"
    coatingfolder = work_directory
    user_wavelength_min = 0.
    user_wavelength_max = 0.9
    nb_wavelength = 5
    speos_wavelength_units_um = 1000
    substrate_catalog = "SCHOTT"
    substrate_name = ["N-BK7"]
    nb_digits = 6
    skip_lines = 4
    Coating_converter_speos_zemax_Analysis(coatingfilename, coatingfolder,
                                           substrate_catalog, substrate_name,
                                           user_wavelength_min, user_wavelength_max,
                                           nb_wavelength, speos_wavelength_units_um,
                                           nb_digits,
                                           skip_lines)
    speos_test_file = coatingfolder + "\\Speos\\" + "test12_COATING_MULTIPLELAYERS_AIR_N-BK7.bsdf180"
    renamed_test_file = os.path.join(work_directory, "test_12_coating.bsdf180")
    shutil.copyfile(speos_test_file, renamed_test_file)

    results_dict["coating_convert_bsdf180"] = check_converted_coatingfile(test_file, "bsdf180")
    os.remove(test_file)
    os.remove(test_reference)
    os.remove(os.path.splitext(test_file)[0].lower() + ".bsdf180")


def unittest_run():
    try:
        main()
    except Exception:
        print("exception in main")
        results_dict["error"] = traceback.format_exc()

    with open(results_json, "w") as file:
        json.dump(results_dict, file, indent=4)
