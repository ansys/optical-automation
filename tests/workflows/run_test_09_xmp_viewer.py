import glob
import json
import os
import shutil
import sys
import traceback

unittest_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.dirname(unittest_path)
sys.path.append(lib_path)

from ansys_optical_automation.post_process.dpf_xmp_viewer import DpfXmpViewer

xmp_folder = os.path.join(unittest_path, "example_models")
results_json = os.path.join(unittest_path, "test_09_xmp_viewer_results.json")

work_directory = os.path.join(unittest_path, "xmp")


def check_filesize(file):
    file_MB_size = round(os.stat(file).st_size / 1024, 2)
    return file_MB_size


def main():
    results_dict = {}
    os.mkdir(work_directory)
    xmp_files = glob.glob(os.path.join(xmp_folder, "*.xmp"))
    for i, file in enumerate(xmp_files):
        shutil.copyfile(file, os.path.join(work_directory, "mytest_xmp_" + str(i) + ".xmp"))
    xmp_files = glob.glob(os.path.join(work_directory, "*.xmp"))
    results_dict["source_list"] = []
    allowed_exports = ["txt", "png", "bmp", "jpg", "tiff", "pf"]
    special_exports = ["ies"]
    for export_type in allowed_exports:
        results_dict["export_" + export_type] = []
    for export_type in special_exports:
        results_dict["export_" + export_type] = []
    for file in xmp_files:
        xmp = DpfXmpViewer()
        xmp.open_file(file)
        results_dict["source_list"].append(xmp.source_list)
        for export_type in allowed_exports:
            export_path = xmp.export(format=export_type)
            results_dict["export_" + export_type].append(check_filesize(export_path))
        for export_type in special_exports:
            if (
                xmp.dpf_instance.ReturnValueType == 1
                and (export_type == "ies")
                and not xmp.dpf_instance.ReturnUnitType == 0
            ):
                export_path = xmp.export(format=export_type)
                results_dict["export_" + export_type].append(check_filesize(export_path))

        xmp.close()
    txt_imports = glob.glob(os.path.join(work_directory, "*.txt"))

    results_dict["xmp_import"] = []
    results_dict["xmp_import_data"] = []
    for txt_data in txt_imports:
        xmp = DpfXmpViewer()
        xmp.read_txt_export(txt_data)
        xmp_import_path = os.path.join(work_directory, "xmp_import.xmp")
        xmp.dpf_instance.SaveFile(xmp_import_path)
        results_dict["xmp_import"].append(check_filesize(xmp_import_path))
        data = xmp.read_txt_export(txt_data, inc_data=True)
        results_dict["xmp_import_data"].append(data)
        xmp.close
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
