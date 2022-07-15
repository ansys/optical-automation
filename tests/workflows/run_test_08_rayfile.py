import os
import sys

unittest_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.dirname(unittest_path)
sys.path.append(lib_path)

from ansys_optical_automation.post_process.dpf_rayfile import DpfRayfile

ray_file = os.path.join(unittest_path, "example_models", "test_08_ray.ray")
dat_file = os.path.join(unittest_path, "example_models", "test_08_dat.dat")
sdf_file = os.path.join(unittest_path, "example_models", "test_08_sdf.sdf")
results_json = os.path.join(unittest_path, "test_08_rayfile_results.json")

work_directory = os.path.join(unittest_path, "rayfile")


def check_converted_rayfile(rayfile_path, result_dic, key):
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
    file_type = os.path.splitext(rayfile_path)[1].lower()
    reference_file = os.path.splitext(rayfile_path)[0].lower() + "reference" + file_type
    reference = open(reference_file, "r")
    reference = reference.read()
    input_ray_file = open(rayfile_path, "r")
    input_ray_file = input_ray_file.read()
    result_dic[key] = reference == input_ray_file
    return result_dic


def verify_data_load(rayfile_path, result_dic, key):
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
    result_dic[key] = result
    return result_dic
