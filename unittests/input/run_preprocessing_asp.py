# Python Script, API Version = V20 Beta
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


def extract_name_for_dict(objects_dict):
    """
    function to extract names of objects from dict of SCDM bodies
    Args:
        objects_dict: dict with values equal to list of SCDM bodies

    Returns: dictionary with body names instead of objects

    """
    names_dict = {}
    for key in objects_dict:
        for item in objects_dict[key]:
            name = key.encode("utf-8")
            if name not in names_dict:
                names_dict[name] = []
            names_dict[name].append(item.Name)
    return names_dict


def extract_centre_for_dict(component):
    """
    Extract centre point of a body
    Args:
        component: SCDM component object

    Returns: list of X,Y,Z center coordinates

    """
    centre_list = []
    for body in component.GetBodies():
        x = body.Shape.GetBoundingBox(Matrix.Identity, True).Center.X
        y = body.Shape.GetBoundingBox(Matrix.Identity, True).Center.Y
        z = body.Shape.GetBoundingBox(Matrix.Identity, True).Center.Z
        centre_list.append((x, y, z))
    return centre_list


results_dict = {}
DocumentOpen.Execute(scdm_file)

preproc_asp = PreProcessingASP()
material_dict = preproc_asp.create_dict_by_material()
results_dict["materials"] = extract_name_for_dict(material_dict)
color_dict = preproc_asp.create_dict_by_color()
results_dict["colors"] = extract_name_for_dict(color_dict)


preproc_asp.create_named_selection(color_dict)
preproc_asp.create_named_selection(material_dict)
results_dict["name_selection"] = [group.Name.encode("utf-8") for group in  GetActiveWindow().Groups]

results_dict["center_coord"] = {}
for comp in GetRootPart().GetAllComponents():
    comp_name = comp.GetName()
    preproc_asp.remove_duplicates(comp)
    preproc_asp.stitch_comp(comp)
    results_dict["center_coord"][comp_name] = extract_centre_for_dict(comp)

scdm_file = os.path.join(unittest_path, "input", "poor_geom_updated.scdoc")
DocumentSave.Execute(scdm_file)

with open(results_json, "w") as file:
    json.dump(results_dict, file, indent=4)
