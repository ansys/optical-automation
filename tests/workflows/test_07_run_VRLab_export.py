import json
import os
import shutil
import sys
import traceback
from math import floor

unittest_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.dirname(unittest_path)
sys.path.append(lib_path)

from ansys_optical_automation.post_process.dpf_hdri_viewer import DpfHdriViewer

vr_file = os.path.join(unittest_path, "example_models", "test_07_VRLab_export.OptisVR")
results_json = os.path.join(unittest_path, "test_07_VRLab_results.json")

work_directory = os.path.join(unittest_path, "VRExport")


def check_images_exported(dir):
    created_images = {}
    list_of_files = [os.path.join(dir, file) for file in os.listdir(dir)]
    for file in list_of_files:
        file_MB_size = int(floor(os.stat(file).st_size / 1024))
        created_images[os.path.split(file)[1].lower()] = file_MB_size
    return created_images


def main():
    results_dict = {}
    dpf = DpfHdriViewer()
    print(vr_file)
    dpf.open_file(vr_file)
    dpf.export_vr_views(export_path=work_directory, config_ids=0)
    vr_exported_list = check_images_exported(work_directory)
    results_dict["VRImages"] = vr_exported_list
    return results_dict

def unittest_run():
    results_dict = {}
    try:
        results_dict = main()
    except Exception:
        print("exception in main")
        results_dict["error"] = traceback.format_exc()

    with open(results_json, "w") as file:
        json.dump(results_dict, file, indent=4)

    if os.path.isdir(work_directory):
        shutil.rmtree(work_directory)
