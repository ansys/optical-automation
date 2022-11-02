import json
import os
import shutil
import sys
import traceback

unittest_path = os.path.dirname(os.path.realpath(__file__))
unittest_path = os.path.join(unittest_path, "tests")
lib_path = os.path.dirname(unittest_path)  # get path of speos_migration library
sys.path.append(lib_path)

from ansys_optical_automation.scdm_process.material_from_csv import MaterialsFromCSV
from ansys_optical_automation.speos_process.speos_sensors import Camera
from ansys_optical_automation.speos_process.speos_simulations import Simulation

scdm_file = os.path.join(unittest_path, "workflows", "example_models", "test_geometry_01.scdocx")
scdm_file_2 = os.path.join(unittest_path, "workflows", "example_models", "test_05_simexport.scdocx")
results_json = os.path.join(unittest_path, "workflows", "test_05_results.json")

csv_path = os.path.join(unittest_path, "workflows", "example_models", "SPEOS input files", "Materials.csv")
work_directory = os.path.join(unittest_path, "workflows", "example_models")

interactive_geoset = ["Plane"]
output_files = ["Test_simulation.Cam.OPTProjectedGrid", "Test_simulation.Report.html"]
isolated_dir = os.path.join(unittest_path, "workflows", "example_models", "SPEOS isolated files")


def find_sims(selection):
    """
    Parameters
    ----------
    selection
        SpaceClaim Selection

    Returns
    -------
    list contain two item list first item simulation object second item derives the simulation type
    """
    sim_list = []
    for item in selection.Items:
        name = item.GetName()
        if SpeosSim.SimulationDirect.Find(name):
            sim_list.append([name, "direct"])
        elif SpeosSim.SimulationInverse.Find(name):
            sim_list.append([name, "inverse"])
    return sim_list


def main():
    DocumentOpen.Execute(scdm_file)
    # Materials
    material_api = MaterialsFromCSV(SpeosSim, SpaceClaim)
    material_api.create_speos_material(csv_path, work_directory)
    material_api.apply_geo_to_material()
    # Sensor
    cam = Camera("Cam", SpeosSim, SpaceClaim)
    cam.find_axes(origin="cam_origin")
    cam.set_position(x_reverse=True, y_reverse=True)
    cam.set_distortion("OPTIS_Distortion_150deg.OPTDistortion")
    cam.set_transmittance("perfect_transmitance.spectrum")
    cam.set_sensitivity("red", "sRGB_R.spectrum")
    cam.set_sensitivity("green", "sRGB_G.spectrum")
    cam.set_sensitivity("blue", "sRGB_B.spectrum")
    # Test sensor parameters
    cam_object = SpeosSim.SensorCamera.Find("Cam")
    cam_exists = bool(cam_object)
    results_dict["camera_exists"] = cam_exists
    results_dict["distortion"] = cam_object.DistorsionFile
    results_dict["transmittance"] = cam_object.TransmittanceFile
    results_dict["red_spectrum"] = cam_object.RedSpectrumFile
    results_dict["green_spectrum"] = cam_object.GreenSpectrumFile
    results_dict["blue_spectrum"] = cam_object.BlueSpectrumFile

    # Interactive simulation
    interactive = Simulation("Test_simulation", SpeosSim, SpaceClaim, "interactive")
    interactive.select_geometrical_sets(interactive_geoset)
    interactive.define_geometries()
    interactive.add_sensor("Cam")
    interactive.run_simulation()
    interactive.set_grid_params(primary_step=50, secondary_step=25, max_distance=1500, max_incidence=89, min_distance=2)
    interactive.export_grid("Cam")
    # test if simulation exists
    sim_object = SpeosSim.SimulationInteractive.Find("Test_simulation")
    sim_exists = bool(sim_object)
    results_dict["simulation_created"] = sim_exists
    # check if sensor has been added
    sensor_added = bool(sim_object.Sensors[0])
    sensor_name = sim_object.Sensors[0].Name
    results_dict["sensor_added"] = sensor_added
    results_dict["sensor_name"] = sensor_name
    # check grid params
    sim_name = sim_object.Name
    grid_name = sim_name + "." + sensor_name + ".OPTProjectedGrid"
    grid = SpeosSim.ResultProjectedGrid.Find(grid_name)
    grid_params = {
        "secondary_step": grid.SecondaryStep,
        "primary_step": grid.PrimaryStep,
        "max_distance": grid.MaxDistanceFromCamera,
        "max_incidence": grid.MaxIncidence,
        "min_distance": grid.MinDistanceTolerance,
    }
    results_dict["grid_parameters"] = grid_params
    # Check outputs
    output_exists = {}
    for output_file in output_files:
        fname = os.path.join(
            unittest_path, "workflows", "example_models", "SPEOS output files", "test_geometry_01", output_file
        )
        output_exists[output_file] = os.path.isfile(fname)
        os.remove(fname)
    results_dict["output_exists"] = output_exists
    # Check projected grid export
    all_comps = GetRootPart().GetAllComponents()
    grid_exported = False
    curves_exported = []
    for comp in all_comps:
        if "Projected grid_" in comp.GetName():
            curves = comp.GetAllCurves()
            for curve in curves:
                curves_exported.append(curve.GetName())
            grid_exported = True
    results_dict["grid_exported"] = grid_exported
    results_dict["curves_exported"] = curves_exported
    GetActiveWindow().Close()
    DocumentOpen.Execute(scdm_file_2)
    sel = Selection.CreateByGroups("Sim")
    sim_list = find_sims(sel)
    exported = True
    for sim in sim_list:
        current_sim = Simulation(sim[0], SpeosSim, SpaceClaim, sim[1])
        path = current_sim.linked_export_simulation()
        exported = exported and os.path.exists(path)
    results_dict["exported"] = exported
    shutil.rmtree(isolated_dir, True)


results_dict = {}
try:
    main()
except Exception:
    print("exception in main")
    results_dict["error"] = traceback.format_exc()

with open(results_json, "w") as file:
    json.dump(results_dict, file, indent=4)
