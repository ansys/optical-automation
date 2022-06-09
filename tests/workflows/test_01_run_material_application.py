import csv
import json
import os
import sys
import traceback

unittest_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.dirname(unittest_path)  # get path of speos_migration library
sys.path.append(lib_path)

from ansys_optical_automation.scdm_process.material_from_csv import MaterialsFromCSV
from ansys_optical_automation.scdm_process.material_from_layers import (
    SynchLayersMaterials,
)

scdm_file = os.path.join(unittest_path, "workflows", "example_models", "test_geometry_01.scdoc")
results_json = os.path.join(unittest_path, "workflows", "test01_results.json")

csv_path = os.path.join(unittest_path, "workflows", "example_models", "SPEOS input files", "Materials.csv")
work_directory = os.path.join(unittest_path, "workflows")


def extract_speos_materials(csv_path):
    created_materials = {}
    # read csv for materials that should have been created
    with open(csv_path) as myfile:
        reader = csv.reader(myfile)
        for line in reader:  # skips the first header line
            if ("End" not in line) and ("Materialname " not in line) and ("Catia Material" not in line):
                op_name = line[0].rstrip()
                geo_names = get_ops_associated_geos(op_name)
                created_materials[op_name.encode("utf-8")] = geo_names
    return created_materials


def get_ops_associated_geos(op_name):
    geo_names = []
    # find material under speos optical properties
    op = SpeosSim.Material.Find(op_name)
    if op:  # if the speos material (optical property) exists
        # find what geometries are assigned to this material
        geo_count = SpeosSim.Material.Find(op_name).VolumeGeometries.Count
        for cnt in range(geo_count):
            geo = SpeosSim.Material.Find(op_name).VolumeGeometries.Item[cnt]
            geo_names.append(geo.Name.encode("utf-8"))
    return geo_names


def extract_speos_layers():
    bodies_per_layer = {}
    for layer in DocumentHelper.GetActiveDocument().Layers:
        bodies_per_layer[layer.GetName().encode("utf-8")] = []
    for body in GetRootPart().GetAllBodies():
        bodies_per_layer[body.GetMaster().Layer.GetName().encode("utf-8")].append(body.GetName().encode("utf-8"))
    return bodies_per_layer


def main():
    DocumentOpen.Execute(scdm_file)
    material_api = MaterialsFromCSV(SpeosSim, SpaceClaim)
    # create materials from the csv
    material_api.create_speos_material(csv_path, work_directory)
    material_api.apply_geo_to_material()
    # check what materials have been created
    created_materials = extract_speos_materials(csv_path)
    results_dict["speos_materials"] = created_materials
    # create layers and add geos to them
    material_api.apply_geo_to_layer()
    # check if layers have been created and contain all geos
    bodies_per_layer = extract_speos_layers()
    results_dict["speos_layers"] = bodies_per_layer

    # move one surface to an empty layer and sync with materials
    sel = BodySelection.CreateByNames("Surface A 1")
    Layers.MoveTo(sel, "Layer0")
    synch_layers_api = SynchLayersMaterials(SpeosSim, SpaceClaim)
    synch_layers_api.sync_op_from_layers()
    layer_geos = {"Layer0": get_ops_associated_geos("Layer0")}
    results_dict["layer_synch_to_material"] = layer_geos

    # check how many materials and layers exist
    # TODO


results_dict = {}
try:
    main()
except Exception:
    print("exception in main")
    results_dict["error"] = traceback.format_exc()

with open(results_json, "w") as file:
    json.dump(results_dict, file, indent=4)
