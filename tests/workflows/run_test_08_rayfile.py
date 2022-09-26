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
from ansys_optical_automation.scdm_core.utils import get_speos_core
from ansys_optical_automation.zemax_process.base import BaseZOS
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


def check_speos_sim(rayfile_path):
    """
    Function runs a rayfile in a speos sim to test it
    Parameters
    ----------
    rayfile_path : str
        points to the rayfile to test

    Returns
    -------
    bool True if succeed False if failed
    """
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


def check_zos_sim(rayfile_path):
    """
    Function runs a sdf rayfile in a zemax sim to test it
    Parameters
    ----------
    rayfile_path : str
        points to the rayfile to test

    Returns
    -------
    bool True if succeed False if failed
    """
    # Moving the source file to the working directory
    sourcefilename = "ray.sdf"
    shutil.move(rayfile_path, os.path.join(os.sep, work_directory, r"Objects\Sources\Source Files", sourcefilename))
    zos = BaseZOS()
    zosapi = zos.zosapi
    the_application = zos.the_application
    the_system = zos.the_system

    testfile = os.path.join(work_directory, "test_sourcefile.zos")
    the_system.New(False)
    the_system.SaveAs(testfile)
    if not the_system.IsProjectDirectory:
        the_system.ConvertToProjectDirectory(work_directory)

    # Add source and detector
    the_system.MakeNonSequential()
    the_nce = the_system.NCE
    the_nce.AddObject()

    the_application.BeginMessageLogging()

    my_source = the_nce.GetObjectAt(1)
    typeset_source_file = my_source.GetObjectTypeSettings(zosapi.Editors.NCE.ObjectType.SourceFile)
    typeset_source_file.FileName1 = sourcefilename  # enter the correct filename
    # Typeset_SourceFile.FileName1 = '10 mm collimated_invalid.dat'
    my_source.ChangeType(typeset_source_file)
    my_source.GetObjectCell(zosapi.Editors.NCE.ObjectColumn.Par1).IntegerValue = 5  # layout rays
    my_source.GetObjectCell(zosapi.Editors.NCE.ObjectColumn.Par2).IntegerValue = 1000  # analysis rays
    my_source.GetObjectCell(zosapi.Editors.NCE.ObjectColumn.Par3).DoubleValue = 1.0  # power
    # Object_1.GetObjectCell(ZOSAPI.Editors.NCE.ObjectColumn.Par8).DoubleValue = 0.47 #wavenumber
    # Object_1.GetObjectCell(ZOSAPI.Editors.NCE.ObjectColumn.Par9).DoubleValue = 0.47 #colour

    my_detector = the_nce.GetObjectAt(2)
    typeset_detector_rectangle = my_source.GetObjectTypeSettings(zosapi.Editors.NCE.ObjectType.DetectorRectangle)
    my_detector.ChangeType(typeset_detector_rectangle)
    num_x_pixels = 10
    num_y_pixels = 10
    half_x_width = 5
    half_y_width = 5

    my_detector.GetObjectCell(zosapi.Editors.NCE.ObjectColumn.Par1).DoubleValue = half_x_width
    my_detector.GetObjectCell(zosapi.Editors.NCE.ObjectColumn.Par2).DoubleValue = half_y_width
    my_detector.GetObjectCell(zosapi.Editors.NCE.ObjectColumn.Par3).IntegerValue = num_x_pixels
    my_detector.GetObjectCell(zosapi.Editors.NCE.ObjectColumn.Par4).IntegerValue = num_y_pixels

    # Create ray trace
    nsc_raytrace = the_system.Tools.OpenNSCRayTrace()
    nsc_raytrace.SplitNSCRays = False
    nsc_raytrace.ScatterNSCRays = False
    nsc_raytrace.UsePolarization = False
    nsc_raytrace.IgnoreErrors = True
    nsc_raytrace.SaveRays = False
    nsc_raytrace.Run()
    nsc_raytrace.WaitForCompletion()
    # bool_success = NSCRayTrace.Succeeded  # doesn't work here
    nsc_raytrace.Close()

    the_system.SaveAs(testfile)

    if the_application.RetrieveLogMessages() == "":
        bool_success = True
    else:
        bool_success = False

    the_application.ClearMessageLog()

    # print("Source file success: %s" % (str(bool_success)))
    return bool_success


def main():
    os.mkdir(work_directory)
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
    # test09
    test_file = os.path.join(work_directory, "test_08_ray.ray")
    shutil.copyfile(ray_file, test_file)
    convert = RayfileConverter(test_file)
    convert.speos_to_zemax()
    results_dict["ray_sdf_sim"] = check_speos_sim(os.path.splitext(test_file)[0].lower() + ".sdf")


def unittest_run():
    try:
        main()
    except Exception:
        print("exception in main")
        results_dict["error"] = traceback.format_exc()

    with open(results_json, "w") as file:
        json.dump(results_dict, file, indent=4)

    shutil.rmtree(work_directory)
