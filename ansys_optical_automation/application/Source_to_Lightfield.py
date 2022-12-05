# Python Script, API Version = V23

from ansys_optical_automation.speos_process.speos_sensors import LightFieldSensor
from ansys_optical_automation.speos_process.speos_sensors import LocalMeshing

# import sys
# repo_path = r"your_repo_path"
# sys.path.append(repo_path)


def import_Dome(path):
    world_origin = GetRootPart().CoordinateSystems[-1]
    Selection.Create(world_origin).SetActive()
    DocumentInsert.Execute(path)


def set_dome(surface_name, size):
    dome_surface = Selection.CreateByNames(surface_name)
    InputHelper.PauseAndGetInput("Please enter a scale value", size)
    world_origin_point = GetRootPart().CoordinateSystems[-1].Frame.Origin
    Scale.Execute(dome_surface, world_origin_point, size)


def set_LocalMeshing(geometries, name, sag_mode, sag_value):
    localMeshing = LocalMeshing(name, SpeosSim, SpaceClaim)
    localMeshing.set_geometries(geometries)
    localMeshing.set_sag(sag_mode, sag_value)


def define_LightfieldSensor(sensor_name, sensor_type, incident_sampling, azimuth_sampling, geometries):
    lightField = LightFieldSensor(sensor_name, SpeosSim, SpaceClaim)
    lightField.set_faces(geometries)
    lightField.set_type(sensor_type)
    lightField.set_sampling(incident_sampling, azimuth_sampling)


def define_DirectSim(sim_name, sensor_name):
    pass


def main():
    pass


main()
