import json
import os
import shutil
import sys
import traceback

unittest_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.dirname(unittest_path)
sys.path.append(lib_path)

from ansys_optical_automation.interop_process.coating_converter import CoatingConverter

# from ansys_optical_automation.scdm_core.utils import get_speos_core
# from ansys_optical_automation.zemax_process.base import BaseZOS

coating_file = os.path.join(unittest_path, "example_models", "test_12_coating.dat")
bsdf180_file_reference = os.path.join(unittest_path, "example_models", "test_12_coating_reference.bsdf180")
coating1_file_reference = os.path.join(
    unittest_path, "example_models", "test_12_coating_air_substrate_reference.coated"
)
coating2_file_reference = os.path.join(
    unittest_path, "example_models", "test_12_coating_substrate_air_reference.coated"
)
results_json = os.path.join(unittest_path, "test_12_coatingfile_results.json")
results_dict = {}

work_directory = os.path.join(unittest_path, "coatingfile")


def check_converted_coated_coatingfile(coatingfile_path):
    """
    function to compare the coatingfile with its reference
    Parameters
    ----------
    coatingfile_path : string
        full path to the coating file

    Returns
    -------
    reference_data : string
        text of the coating file
    -------


    """
    # file_path = os.path.splitext(coatingfile_path)[0].lower() + "." + file_type
    file_name = os.path.splitext(coatingfile_path)[0].lower()
    file_extension = os.path.splitext(coatingfile_path)[1].lower()
    reference_file = file_name + "_reference" + file_extension
    reference = open(reference_file, "r")
    reference_data = reference.read()
    reference.close()
    input_coating_file = open(coatingfile_path, "r")
    input_coating_file_data = input_coating_file.read()
    input_coating_file.close()
    return reference_data == input_coating_file_data


def main():
    os.mkdir(work_directory)
    # test01
    test_file = os.path.join(work_directory, "test_12_coating.dat")
    test_bsdf180_reference = os.path.join(work_directory, "test12_coating_reference.bsdf180")
    test_coating1_reference = os.path.join(work_directory, "test_12_coating1_reference.coated")
    test_coating2_reference = os.path.join(work_directory, "test_12_coating2_reference.coated")
    shutil.copyfile(coating_file, test_file)
    shutil.copyfile(bsdf180_file_reference, test_bsdf180_reference)
    shutil.copyfile(coating1_file_reference, test_coating1_reference)
    shutil.copyfile(coating2_file_reference, test_coating2_reference)

    coatingfilename = "test_12_coating.dat"
    coatingfolder = work_directory
    user_wavelength_min = 0.31
    user_wavelength_max = 0.9
    nb_wavelength = 5
    speos_wavelength_units_um = 1000
    substrate_catalog = "SCHOTT"
    substrate_name = ["N-BK7"]
    nb_digits = 6
    skip_lines = 4
    mycoatingtest = CoatingConverter(
        coatingfilename,
        coatingfolder,
        substrate_catalog,
        substrate_name
    )
    CoatingConverter.convert_zemax_to_speos(mycoatingtest, user_wavelength_min, user_wavelength_max, nb_wavelength,
                                            speos_wavelength_units_um, nb_digits, skip_lines)

    speos_bsdf180_test_file = os.path.join(coatingfolder, "Speos", "COATING_MULTIPLELAYERS_AIR_N-BK7.bsdf180")
    speos_coating1_test_file = os.path.join(coatingfolder, "Speos", "COATING_MULTIPLELAYERS_AIR_N-BK7.coated")
    speos_coating2_test_file = os.path.join(coatingfolder, "Speos", "COATING_MULTIPLELAYERS_N-BK7_AIR.coated")
    bsdf180_test_file = os.path.join(work_directory, "test_12_coating.bsdf180")
    coating1_test_file = os.path.join(work_directory, "test_12_coating1.coated")
    coating2_test_file = os.path.join(work_directory, "test_12_coating2.coated")
    shutil.copyfile(speos_bsdf180_test_file, bsdf180_test_file)
    shutil.copyfile(speos_coating1_test_file, coating1_test_file)
    shutil.copyfile(speos_coating2_test_file, coating2_test_file)

    results_dict["coating1_convert_coated"] = check_converted_coated_coatingfile(coating1_test_file)
    results_dict["coating2_convert_coated"] = check_converted_coated_coatingfile(coating2_test_file)
    # No check of bsdf180 for now
    # os.remove(test_file)
    # os.remove(test_bsdf180_reference)
    # os.remove(test_coating1_reference)
    # os.remove(test_coating2_reference)
    # os.remove(os.path.splitext(test_file)[0].lower() + ".bsdf180")
    shutil.rmtree(work_directory)


def unittest_run():
    try:
        main()
    except Exception:
        print("exception in main")
        results_dict["error"] = traceback.format_exc()

    with open(results_json, "w") as file:
        json.dump(results_dict, file, indent=4)
