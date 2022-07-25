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

from ansys_optical_automation.interop_process.rayfile_converter import RayfileConverter
from ansys_optical_automation.post_process.dpf_rayfile import DpfRayfile
from tests.config import SCDM_VERSION

ray_file = os.path.join(unittest_path, "example_models", "test_08_ray.ray")
dat_file = os.path.join(unittest_path, "example_models", "test_08_dat.dat")
sdf_file = os.path.join(unittest_path, "example_models", "test_08_sdf.sdf")
sim_path = os.path.join(unittest_path, "example_models", "ray_test.speos")
ray_file_reference = os.path.join(unittest_path, "example_models", "test_08_ray_reference.sdf")
dat_file_reference = os.path.join(unittest_path, "example_models", "test_08_dat_reference.ray")
sdf_file_reference = os.path.join(unittest_path, "example_models", "test_08_sdf_reference.ray")
results_json = os.path.join(unittest_path, "test_08_rayfile_results.json")
results_dict = {}

work_directory = os.path.join(unittest_path, "rayfile")
os.mkdir(work_directory)


def check_converted_rayfile(rayfile_path, file_type):
    """
    function to compare the rayfile with its reference
    Parameters
    ----------
    rayfile_path : str
        path to rayfile
    result_dic : dict
        result dictionary containing the unittest results
    key : str
        name of the dictionary key for the test

    Returns
    -------


    """
    rayfile_path = os.path.splitext(rayfile_path)[0].lower() + "." + file_type
    reference_file = os.path.splitext(rayfile_path)[0].lower() + "_reference." + file_type
    reference = open(reference_file, "br")
    reference_data = reference.read()
    reference.close()
    input_ray_file = open(rayfile_path, "br")
    input_ray_file_data = input_ray_file.read()
    input_ray_file.close()
    return reference_data == input_ray_file_data


def verify_data_load(rayfile_path):
    """
    Function to load the rayfile data and store it within a result dictonary
    Parameters
    ----------
    rayfile_path : str
        path to rayfile
    result_dic : dict
        result dictionary containing the unittest results
    key : str
        name of the dictionary key for the test

    Returns
    -------


    """
    loaded_data = DpfRayfile(rayfile_path)
    result = []
    result.append(loaded_data.photometric_power)
    result.append(loaded_data.radiometric_power)
    result.append(loaded_data.rays_number)
    for ray in loaded_data.rays:
        result.append(ray.coordinate_x)
        result.append(ray.coordinate_y)
        result.append(ray.coordinate_z)
        result.append(ray.radiation_l)
        result.append(ray.radiation_m)
        result.append(ray.radiation_n)
        result.append(ray.wavelength)
        result.append(ray.energy)
    return result


def get_speos_core(version):
    """
    get speos core path for version
    Parameters
    ----------
    version : str
        Ansys Version used

    Returns
    -------
    str
        path to speos core executable

    """
    ansys_install_dir = os.environ["AWP_ROOT{}".format(version)]
    speos_core_dir = os.path.join(ansys_install_dir, r"Optical Products", r"Viewers", r"SPEOSCore.exe")
    return speos_core_dir


def check_speos_sim(rayfile_path):
    shutil.move(rayfile_path, os.path.join(work_directory, "ray.ray"))
    shutil.copyfile(sim_path, os.path.join(work_directory, "speos.speos"))
    run_sim = os.path.join(work_directory, "speos.speos")
    executable = get_speos_core(SCDM_VERSION)
    command = [executable, r"-C", r"-S", r"0000", run_sim]
    subprocess.call(command)

    html_file = glob.glob(os.path.join(work_directory, "*.html"))
    result = bool(html_file)
    os.remove(os.path.join(work_directory, "ray.ray"))
    os.remove(os.path.join(work_directory, "speos.speos"))
    return result


def main():
    # test01
    test_file = os.path.join(work_directory, "test_08_sdf.sdf")
    shutil.copyfile(sdf_file, test_file)
    results_dict["sdf_content"] = verify_data_load(test_file)
    os.remove(test_file)
    # test02
    test_file = os.path.join(work_directory, "test_08_dat.dat")
    shutil.copyfile(dat_file, test_file)
    results_dict["dat_content"] = verify_data_load(test_file)
    os.remove(test_file)
    # test03
    test_file = os.path.join(work_directory, "test_08_ray.ray")
    shutil.copyfile(ray_file, test_file)
    results_dict["ray_content"] = verify_data_load(test_file)
    os.remove(test_file)
    # test04
    test_file = os.path.join(work_directory, "test_08_dat.dat")
    test_reference = os.path.join(work_directory, "test_08_dat_reference.ray")
    shutil.copyfile(dat_file, test_file)
    shutil.copyfile(dat_file_reference, test_reference)
    convert = RayfileConverter(test_file)
    convert.zemax_to_speos()
    convert.close()
    results_dict["dat_convert_ray"] = check_converted_rayfile(test_file, "ray")
    os.remove(test_file)
    os.remove(test_reference)
    os.remove(os.path.splitext(test_file)[0].lower() + ".ray")
    # test05
    test_file = os.path.join(work_directory, "test_08_ray.ray")
    test_reference = os.path.join(work_directory, "test_08_ray_reference.sdf")
    shutil.copyfile(ray_file, test_file)
    shutil.copyfile(ray_file_reference, test_reference)
    convert = RayfileConverter(test_file)
    convert.speos_to_zemax()
    convert.close()
    results_dict["ray_convert_sdf"] = check_converted_rayfile(test_file, "sdf")
    os.remove(test_file)
    os.remove(test_reference)
    os.remove(os.path.splitext(test_file)[0].lower() + ".sdf")
    # test06
    test_file = os.path.join(work_directory, "test_08_sdf.sdf")
    test_reference = os.path.join(work_directory, "test_08_sdf_reference.ray")
    shutil.copyfile(sdf_file, test_file)
    shutil.copyfile(sdf_file_reference, test_reference)
    convert = RayfileConverter(test_file)
    convert.zemax_to_speos()
    convert.close()
    results_dict["sdf_convert_ray"] = check_converted_rayfile(test_file, "ray")
    os.remove(test_file)
    os.remove(test_reference)
    os.remove(os.path.splitext(test_file)[0].lower() + ".ray")
    # test07
    test_file = os.path.join(work_directory, "test_08_sdf.sdf")
    shutil.copyfile(sdf_file, test_file)
    convert = RayfileConverter(test_file)
    convert.zemax_to_speos()

    results_dict["sdf_ray_sim"] = check_speos_sim(os.path.splitext(test_file)[0].lower() + ".ray")
    # test08
    test_file = os.path.join(work_directory, "test_08_dat.dat")
    shutil.copyfile(dat_file, test_file)
    convert = RayfileConverter(test_file)
    convert.zemax_to_speos()
    results_dict["dat_ray_sim"] = check_speos_sim(os.path.splitext(test_file)[0].lower() + ".ray")


try:
    main()
except Exception:
    print("exception in main")
    results_dict["error"] = traceback.format_exc()

with open(results_json, "w") as file:
    json.dump(results_dict, file, indent=4)

shutil.rmtree(work_directory)
