import json
import os
import sys
import traceback

unittest_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.dirname(unittest_path)  # get path of speos_migration library
sys.path.append(lib_path)

from SPEOS_scripts.camera_sensor.define_cameras import Camera

scdm_file = os.path.join(unittest_path, "input", "poor_geom.scdoc")
results_json = os.path.join(unittest_path, "input", "results_camera.json")


def main():
    DocumentOpen.Execute(scdm_file)
    cam = Camera("Cam", SpeosSim, SpaceClaim)
    cam.set_position(x_reverse=True, y_reverse=True, origin="cam_origin")

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

    cam.set_position(x_reverse=False, y_reverse=False)
    cam_origin_axsys = cam_object.OriginPoint.LinkedObject.Master.Name
    results_dict["camera_origin_axsys"] = cam_origin_axsys
    cam_x_reverse_false = cam_object.XDirectionReverse
    results_dict["camera_x_reverse_false"] = cam_x_reverse_false
    cam_y_reverse_false = cam_object.YDirectionReverse
    results_dict["camera_y_reverse_false"] = cam_y_reverse_false


results_dict = {}
try:
    main()
except Exception:
    print("exception in main")
    results_dict["error"] = traceback.format_exc()

with open(results_json, "w") as file:
    json.dump(results_dict, file, indent=4)
