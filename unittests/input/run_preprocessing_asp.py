# Python Script, API Version = V20 Beta
import json
import os
import sys

unittest_path = os.path.dirname(os.path.realpath(__file__))
# unittest_path = r"C:\git\speos_migration\unittests"
unittest_path = r"D:\#ANSYS SPEOS_Concept Proof\ACT\SPEOS_Migration\unittests"
lib_path = os.path.dirname(unittest_path)
sys.path.append(lib_path)

from scdm_scripts.cad_data_postprocessing.preprocessinglibrary import PreProcessingASP

scdm_file = os.path.join(unittest_path, "input", "poor_geom.scdoc")
results_json = os.path.join(unittest_path, "input", "results.json")


def extract_name_for_dict(dict):
    results_dict = {}
    for index in dict:
        for item in range(len(dict[index])):
            name = index.replace("®", " ")
            if name in results_dict:
                results_dict[name].append(dict[index][item].Name)
            else:
                results_dict.update({name: [dict[index][item].Name]})
    return results_dict


def extract_centre_for_dict(comp):
    centre_list = []
    for body in comp.GetBodies():
        x = body.Shape.GetBoundingBox(Matrix.Identity, True).Center.X
        y = body.Shape.GetBoundingBox(Matrix.Identity, True).Center.Y
        z = body.Shape.GetBoundingBox(Matrix.Identity, True).Center.Z
        centre_list.append((x, y, z))
    return centre_list


results_dict = {}
DocumentOpen.Execute(scdm_file)

preproc_asp = PreProcessingASP()
material_dict = preproc_asp.create_dict_by_material()
results_dict.update(extract_name_for_dict(material_dict))
color_dict = preproc_asp.create_dict_by_color()
results_dict.update(extract_name_for_dict(color_dict))

preproc_asp.create_named_selection(color_dict)
preproc_asp.create_named_selection(material_dict)

centre_results_dict = {}
for comp in GetRootPart().GetAllComponents():
    comp_name = comp.GetName()
    preproc_asp.remove_duplicates(comp)
    preproc_asp.stitch_comp(comp)
    centre_results_dict.update({comp_name: extract_centre_for_dict(comp)})
results_dict.update(centre_results_dict)

scdm_file = os.path.join(unittest_path, "input", "poor_geom_updated.scdoc")
DocumentSave.Execute(scdm_file)

with open(results_json, "w") as file:
    json.dump(results_dict, file, indent=4)