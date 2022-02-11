import json
import os
import sys
import shutil
import traceback
from math import floor

unittest_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.dirname(unittest_path)
sys.path.append(lib_path)

from pyoptics.post_process.dpf_HDRIViewer import dpf_HDRIViewer

vr_file = os.path.join(unittest_path, "example_models", "test_VRLab_export.OptisVR")
results_json = os.path.join(unittest_path, "test_VRLab_results.json")

work_directory = os.path.join(unittest_path, "VRExport")


def check_images_exported(dir):
    created_images = {}
    list_of_files = [os.path.join(dir, file) for file in os.listdir(dir)]
    for file in list_of_files:
        file_MB_size = int(floor(os.stat(file).st_size / 1024))
        created_images[os.path.split(file)[1].lower()] = file_MB_size
    return created_images


def main():
    dpf = dpf_HDRIViewer()
    print(vr_file)
    VR = dpf.OpenFile(vr_file)
    dpf.Export_VRViews(SpeosVRObject = VR, expo_path = work_directory, config_IDs = 0)
    VRExported_List = check_images_exported(work_directory)
    results_dict["VRImages"] = VRExported_List


results_dict = {}
try:
    main()
except Exception:
    print("exception in main")
    results_dict["error"] = traceback.format_exc()

with open(results_json, "w") as file:
    json.dump(results_dict, file, indent=4)

if os.path.isdir(work_directory):
    shutil.rmtree(work_directory)