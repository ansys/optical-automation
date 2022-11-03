import glob
import json
import os
import shutil
import sys
import traceback
from math import floor

unittest_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.dirname(unittest_path)
sys.path.append(lib_path)

from ansys_optical_automation.post_process.dpf_xmp_viewer import DpfXmpViewer

xmp_folder = os.path.join(unittest_path, "example_models")
results_json = os.path.join(unittest_path, "test_09_xmp_viewer_results.json")
xml_test_files = [
    [
        os.path.join(unittest_path, "example_models", "Test_09_xmp_viewer.Test_intColorimetric.xmp"),
        os.path.join(unittest_path, "example_models", "int.xml"),
    ],
    [
        os.path.join(unittest_path, "example_models", "Test_09_xmp_viewer.Test_irraColorimetric.xmp"),
        os.path.join(unittest_path, "example_models", "irra.xml"),
    ],
    [
        os.path.join(unittest_path, "example_models", "Test_09_xmp_viewer.Test_radColorimetric.xmp"),
        os.path.join(unittest_path, "example_models", "rad.xml"),
    ],
]
spectral_test_file = os.path.join(unittest_path, "example_models", "Test_09_xmp_viewer.Test_radSpectral.xmp")
work_directory = os.path.join(unittest_path, "xmp")


def check_file_size(file):
    file_size = floor(os.stat(file).st_size / 10)
    return file_size


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
    xmp = DpfXmpViewer()
    for export_type in allowed_exports:
        results_dict["export_" + export_type] = []
    for export_type in special_exports:
        results_dict["export_" + export_type] = []
    for file in xmp_files:
        xmp.open_file(file)
        results_dict["source_list"].append(xmp.source_list)
        for export_type in allowed_exports:
            export_path = xmp.export(format=export_type)
            results_dict["export_" + export_type].append(check_file_size(export_path))
        for export_type in special_exports:
            if (
                xmp.dpf_instance.ReturnValueType == 1
                and (export_type == "ies")
                and not xmp.dpf_instance.ReturnUnitType == 0
            ):
                export_path = xmp.export(format=export_type)
                results_dict["export_" + export_type].append(check_file_size(export_path))
    txt_imports = glob.glob(os.path.join(work_directory, "*.txt"))

    results_dict["xmp_import"] = []
    results_dict["xmp_import_data"] = []
    for i, txt_data in enumerate(txt_imports):
        xmp.read_txt_export(txt_data)
        xmp_import_path = os.path.join(work_directory, "import" + str(i) + ".xmp")
        xmp.dpf_instance.SaveFile(xmp_import_path)
        results_dict["xmp_import"].append(check_file_size(xmp_import_path))
        data = xmp.read_txt_export(txt_data, inc_data=True)
        results_dict["xmp_import_data"].append(data)
    results_dict["xmp_measures"] = []
    for i, comb in enumerate(xml_test_files):
        xmp.open_file(comb[0])
        export_path = os.path.join(work_directory, "export" + str(i) + ".txt")
        xmp.export_template_measures(comb[1], export_path)
        results_dict["xmp_measures"].append(check_file_size(export_path))
    xmp.open_file(spectral_test_file)
    results_dict["spectral"] = xmp.rect_export_spectrum(0, 0, 5, 5)
    xmp.close()
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
