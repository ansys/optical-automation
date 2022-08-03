import json
import os
import sys
import traceback

unittest_path = os.path.dirname(os.path.realpath(__file__))
unittest_path = os.path.join(unittest_path, "tests")
lib_path = os.path.dirname(unittest_path)  # get path of speos_migration library
sys.path.append(lib_path)

from ansys_optical_automation.speos_process.speos_simulations import Simulation

scdm_file = os.path.join(unittest_path, "workflows", "example_models", "test_geometry_01.scdocx")
results_json = os.path.join(unittest_path, "workflows", "test_04_results.json")

test_geometries = ["Component1"]
test_geoset = ["Component1"]
interactive_geoset = ["Plane"]


def main():
    DocumentOpen.Execute(scdm_file)
    # create a simulation
    simulation = Simulation("Test_simulation", SpeosSim, SpaceClaim, "inverse")
    # test if simulation exists
    sim_object = SpeosSim.SimulationInverse.Find("Test_simulation")
    sim_exists = bool(sim_object)
    results_dict["simulation_created"] = sim_exists

    # select geometries in the geoset
    simulation.select_geometrical_sets(test_geoset)
    number_of_selected_geos = len(simulation.my_bodies)
    results_dict["number_of_selected_bodies_in_geoset"] = number_of_selected_geos

    # select geometries in the component
    simulation.select_geometries(test_geometries)
    number_of_selected_geos = len(simulation.my_bodies)
    results_dict["number_of_selected_bodies_in_component"] = number_of_selected_geos

    # add geometries to the simulation
    simulation.define_geometries()
    number_of_geos_defined = sim_object.Geometries.Count
    results_dict["number_of_geos_defined"] = number_of_geos_defined

    # set rays limit
    simulation.set_rays_limit(500)
    # check rays limit
    num_of_passes = int(simulation.object.NbPassesLimit.ToString())
    results_dict["number_of_passes"] = num_of_passes


results_dict = {}
try:
    main()
except Exception:
    print("exception in main")
    results_dict["error"] = traceback.format_exc()

with open(results_json, "w") as file:
    json.dump(results_dict, file, indent=4)
