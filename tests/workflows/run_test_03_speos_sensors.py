import json
import os
import sys
import traceback

unittest_path = os.path.dirname(os.path.realpath(__file__))
unittest_path = os.path.join(unittest_path, "tests")
lib_path = os.path.dirname(unittest_path)  # get path of speos_migration library
sys.path.append(lib_path)

from ansys_optical_automation.speos_process.speos_sensors import Camera
from ansys_optical_automation.speos_process.speos_sensors import IntensitySensor

scdm_file = os.path.join(unittest_path, "workflows", "example_models", "test_geometry_01.scdoc")
results_json = os.path.join(unittest_path, "workflows", "test_03_results.json")


def main():
    DocumentOpen.Execute(scdm_file)
    # Test camera
    cam = Camera("Cam", SpeosSim, SpaceClaim)
    cam.find_axes(origin="cam_origin")
    cam.set_position(x_reverse=True, y_reverse=True)
    cam_object = SpeosSim.SensorCamera.Find("Cam")
    cam_exists = bool(cam_object)
    results_dict["camera_exists"] = cam_exists
    cam_origin = cam_object.OriginPoint.LinkedObject.Master.Name
    results_dict["camera_origin"] = cam_origin
    cam_x_axis = cam_object.XDirection.LinkedObject.AxisType.ToString()
    results_dict["camera_x_axis"] = cam_x_axis
    cam_y_axis = cam_object.YDirection.LinkedObject.AxisType.ToString()
    results_dict["camera_y_axis"] = cam_y_axis
    cam_x_reverse = cam_object.XDirectionReverse
    results_dict["camera_x_reverse_true"] = cam_x_reverse
    cam_y_reverse = cam_object.YDirectionReverse
    results_dict["camera_y_reverse_true"] = cam_y_reverse
    cam.find_axes()
    cam.set_position(x_reverse=False, y_reverse=False)
    cam_origin_axsys = cam_object.OriginPoint.LinkedObject.Master.Name
    results_dict["camera_origin_axsys"] = cam_origin_axsys
    cam_x_reverse_false = cam_object.XDirectionReverse
    results_dict["camera_x_reverse_false"] = cam_x_reverse_false
    cam_y_reverse_false = cam_object.YDirectionReverse
    results_dict["camera_y_reverse_false"] = cam_y_reverse_false

    # test intensity sensors
    intensity = IntensitySensor("IntensityTest", SpeosSim, SpaceClaim)
    intensity_obj = SpeosSim.SensorIntensity.Find("IntensityTest")
    intensity_exists = bool(intensity_obj)
    results_dict["intensity_exists"] = intensity_exists
    intensity.find_axes()
    intensity.set_position()
    results_dict["intensity_origin"] = intensity_obj.OriginPoint.LinkedObject.Master.Name
    intensity_x_axis_type = intensity_obj.XDirection.LinkedObject.AxisType.ToString()
    results_dict["intensity_x_axis_type"] = intensity_x_axis_type
    intensity_y_axis_type = intensity_obj.YDirection.LinkedObject.AxisType.ToString()
    results_dict["intensity_y_axis_type"] = intensity_y_axis_type
    intensity.set_format("iEsnAtyPeA")
    results_dict["intensity_format_A"] = str(intensity_obj.FormatType)
    intensity.set_format("iEsnAtyPeB")
    results_dict["intensity_format_B"] = str(intensity_obj.FormatType)
    intensity.set_format("iEsnAtyPeC")
    results_dict["intensity_format_C"] = str(intensity_obj.FormatType)
    intensity.set_format("eulUmdaT")
    results_dict["intensity_format_eulumdat"] = str(intensity_obj.FormatType)
    intensity.set_format("XmP")
    results_dict["intensity_format_xmp"] = str(intensity_obj.FormatType)
    intensity.set_wavelength(w_start=450, w_end=650, w_sampling=10)
    results_dict["wavelength_start"] = str(intensity_obj.WavelengthStart)
    results_dict["wavelength_end"] = str(intensity_obj.WavelengthEnd)
    results_dict["wavelength_sampling"] = str(intensity_obj.WavelengthNbSamples)
    intensity.set_wavelength(w_resolution=5)
    results_dict["wavelength_resolution"] = str(intensity_obj.WavelengthResolution)
    intensity.set_layer("sOurCe")
    results_dict["layer_source"] = str(intensity_obj.LayerType)
    intensity.set_layer("NOnE")
    results_dict["layer_none"] = str(intensity_obj.LayerType)
    intensity.set_layer("fACE")
    results_dict["layer_face"] = str(intensity_obj.LayerType)
    intensity.set_layer("SeQuENce")
    results_dict["layer_sequence"] = str(intensity_obj.LayerType)
    intensity.set_range(x_start=-59, x_end=41, y_start=-9, y_end=11, x_mirrored=True, y_mirrored=True)
    results_dict["x_start"] = str(intensity_obj.XStart)
    results_dict["x_end"] = str(intensity_obj.XEnd)
    results_dict["y_start"] = str(intensity_obj.YStart)
    results_dict["y_end"] = str(intensity_obj.YEnd)
    results_dict["x_start_mirrored"] = str(intensity_obj.XStart)
    results_dict["y_start_mirrored"] = str(intensity_obj.YStart)
    results_dict["x_mirrored"] = str(intensity_obj.XIsMirrored)
    results_dict["y_mirrored"] = str(intensity_obj.YIsMirrored)
    intensity.set_sampling(x_sampling=100, y_sampling=150)
    results_dict["x_sampling"] = str(intensity_obj.XNbSamples)
    results_dict["y_sampling"] = str(intensity_obj.YNbSamples)
    intensity.set_resolution(x_resolution=1, y_resolution=2)
    results_dict["x_resolution"] = str(intensity_obj.XResolution)
    results_dict["y_resolution"] = str(intensity_obj.YResolution)
    intensity.set_type("pHoTOMetric")
    results_dict["type_photometric"] = str(intensity_obj.SensorType)
    intensity.set_type("coLORiMeTric")
    results_dict["type_colorimetric"] = str(intensity_obj.SensorType)
    intensity.set_type("RadiomeTric")
    results_dict["type_radiometric"] = str(intensity_obj.SensorType)
    intensity.set_type("SPECTRAL")
    results_dict["type_spectral"] = str(intensity_obj.SensorType)


results_dict = {}
try:
    main()
except Exception:
    print("exception in main")
    results_dict["error"] = traceback.format_exc()

with open(results_json, "w") as file:
    json.dump(results_dict, file, indent=4)
