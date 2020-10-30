import json
import os
import sys

unittest_path = os.path.dirname(os.path.realpath(__file__))
# unittest_path = r"C:\git\speos_migration\unittests"
lib_path = os.path.dirname(unittest_path)
sys.path.append(lib_path)

from scdm_scripts.cad_data_postprocessing.preprocessinglibrary import PreProcessingASP

scdm_file = os.path.join(unittest_path, "input", "poor_geom.scdoc")
results_json = os.path.join(unittest_path, "input", "results.json")

results_dict = {}
DocumentOpen.Execute(scdm_file)

preproc_asp = PreProcessingASP()
material_dict = preproc_asp.create_dict_by_material()
color_dict = preproc_asp.create_dict_by_color()

preproc_asp.create_named_selection(color_dict)
preproc_asp.create_named_selection(material_dict)

scdm_file = os.path.join(unittest_path, "input", "poor_geom_updated.scdoc")
DocumentSave.Execute(scdm_file)

with open(results_json, "w") as file:
    json.dump(results_dict, file, indent=4)

