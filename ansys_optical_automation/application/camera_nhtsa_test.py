# Python Script, API Version = V232
import os

# import sys
# repo_path=r"your repository location"
# sys.path.append(repo_path)
from ansys_optical_automation.speos_process.speos_sensors import Camera
from ansys_optical_automation.speos_process.speos_simulations import Simulation


def import_car(path, position_value):
    """
    function to import car defined by path into position defined by position_value.

    Parameters
    ----------
    path : str
        path defines the location of part to be imported.
    position_value : float
        value about position of car

    Returns
    -------


    """
    param = GetActiveWindow().Groups[0]
    param.SetDimensionValue(MM(position_value))
    name = "Placement_position"
    target = Selection.CreateByNames(name).Filter[ICoordinateSystem]()
    target.SetActive()
    DocumentInsert.Execute(path)


def selection_dialog_window():
    """
    Asks for a file selection.

    Returns
    -------
    str
        File directory selected, otherwise ``False``.
    """
    open_dialog = OpenFileDialog()
    open_dialog.Filter = "ANSYS SPEOS files (*.scdoc;*.scdocx)|*.scdoc;*scdocx|All Files (*.*)|*.*"
    open_dialog.Show()
    if open_dialog.FileName == "":
        MessageBox.Show("You did not select a file.")
        return False
    return open_dialog.FileName


def define_camera(
    my_cam,
    position,
    focal_length=0.8,
    imager_distance=10,
    f_number=20,
    distortion="OPTIS_Distortion_150deg.OPTDistortion",
    transmittance="ANSYS_Transmittance.spectrum",
    horz_pixel=1280,
    vert_pixel=1280,
    width=1.8,
    height=1.8,
    sensitivity=[
        "ANSYS_Sensitivity_Red.spectrum",
        "ANSYS_Sensitivity_Green.spectrum",
        "ANSYS_Sensitivity_Blue.spectrum",
    ],
):
    """
    function to define the camera based on the given parameters
    Parameters
    ----------
    my_cam : ansys_optical_automation.speos_process.speos_sensors.Camera
    position :
    focal_length
    imager_distance
    f_number
    distortion
    transmittance
    horz_pixel
    vert_pixel
    width
    height
    sensitivity

    Returns
    -------


    """
    my_cam.set_position(
        False,
        False,
        position.Items[0],
        [
            position.Items[0].GetDescendants[ICoordinateAxis]()[0],
            position.Items[0].GetDescendants[ICoordinateAxis]()[1],
        ],
    )
    my_cam.speos_object.FocalLength = focal_length
    my_cam.speos_object.ImagerDistance = imager_distance
    my_cam.speos_object.FNumber = f_number
    my_cam.set_distortion(distortion)
    my_cam.set_transmittance(transmittance)
    my_cam.speos_object.HorzPixel = horz_pixel
    my_cam.speos_object.VertPixel = vert_pixel
    my_cam.speos_object.Width = width
    my_cam.speos_object.Height = height
    my_cam.set_sensitivity("red", sensitivity[0])
    my_cam.set_sensitivity("green", sensitivity[1])
    my_cam.set_sensitivity("blue", sensitivity[2])


def prepare_sim_setup(cam_name, sim_name, part_names, cam_model):
    """
    Prepares a simulation model based on the given input:
    creates/edits the Camera with name cam_name based on the predefined Ccam_model,
        positions it at axissystem "Cam_pos_1"
    creates/edits the Simulation with name sim_name
    adds all geometries of the parts given in part_names
    Parameters
    ----------
    cam_name :  str
        camera name to edit/create
    sim_name :  str
        simulation name to edit/create
    part_names : list[str]
        list of partnames to be added to the simulation
    cam_model : int
        predefine camera model ID

    Returns
    -------
    ansys_optical_automation.speos_process.speos_simulations.Simulation object

    """
    name = "Cam_pos_1"  # Axis system in Berline and in SUV
    target = Selection.CreateByNames(name).Filter[ICoordinateSystem]()
    Cam_1 = Camera(cam_name, SpeosSim, SpaceClaim)

    if cam_model == 1:  # Based on Camera model V1
        parameters = [
            0.8,
            10,
            20,
            "OPTIS_Distortion_150deg.OPTDistortion",
            "ANSYS_Transmittance.spectrum",
            1280,
            1280,
            1.8,
            1.8,
            [
                "ANSYS_Sensitivity_Red.spectrum",
                "ANSYS_Sensitivity_Green.spectrum",
                "ANSYS_Sensitivity_Blue.spectrum",
            ],
        ]
        define_camera(
            Cam_1,
            target,
            parameters[0],
            parameters[1],
            parameters[2],
            parameters[3],
            parameters[4],
            parameters[5],
            parameters[6],
            parameters[7],
            parameters[8],
            parameters[9],
        )

    if cam_model == 2:  # Based on Camera model V1
        parameters = [
            0.8,
            10,
            20,
            "OPTIS_Distortion_190deg.OPTDistortion",
            "ANSYS_Transmittance.spectrum",
            1280,
            1280,
            1.8,
            1.8,
            [
                "ANSYS_Sensitivity_Red.spectrum",
                "ANSYS_Sensitivity_Green.spectrum",
                "ANSYS_Sensitivity_Blue.spectrum",
            ],
        ]
        define_camera(
            Cam_1,
            target,
            parameters[0],
            parameters[1],
            parameters[2],
            parameters[3],
            parameters[4],
            parameters[5],
            parameters[6],
            parameters[7],
            parameters[8],
            parameters[9],
        )

    sim_cam = Simulation(sim_name, SpeosSim, SpaceClaim, "inverse")
    sim_cam.select_geometries(part_names)  # new
    sim_cam.define_geometries()  # new
    sim_cam.object.Sensors.Set(Cam_1.speos_object)
    return sim_cam


def main():
    """
    Adds a car to an already loaded nhtsa testscene
    creates a camera based on the "Cam_pos_1" axis system
    runs/exports the speos simulations
    Returns
    -------

    """
    try:
        argsDict
        mode = 1
    except Exception:
        if len(args) == 0:
            mode = 0
        else:
            mode = 2

    if mode == 1:
        camera_model = argsDict["camera_model"]
        car_model = argsDict["car_model"]
        position_value = argsDict["position_value"]

        import_car(car_model, position_value)
        part_names = []
        for part in GetRootPart().Components:
            part_names.append(part.GetName())
        ###
        # Define Sim
        sim_cam = prepare_sim_setup("Camera", "Cam_Sim", part_names, camera_model)
        sim_cam.object.Compute()

    elif mode == 2:
        # This section defines the inputs which might be replaced by Optislang or the user on usage
        camera_model = 1
        car_model = "SUV_22R2"
        Ansys_SPEOS_file = os.path.join(os.getcwd(), "Scene_22R2.scdocx")
        if "Berline_22R2" in car_model:
            position_value = 682.2  # Berline =682.2mm
            car_path = os.path.join(os.getcwd(), "ANSYS_Berline/Berline_22R2.scdocx")
        if "SUV_22R2" in car_model:
            position_value = 546.123  # SUV=546.123mm
            car_path = os.path.join(os.getcwd(), "ANSYS_SUV/SUV_22R2.scdocx")

        # this section is the normal script part
        # Open File
        importOptions = ImportOptions.Create()
        DocumentOpen.Execute(Ansys_SPEOS_file, importOptions)
        import_car(car_path, position_value)

        part_names = []
        for part in GetRootPart().Components:
            part_names.append(part.GetName())
        sim_cam = prepare_sim_setup("Camera", "Cam_Sim", part_names, camera_model)
        # Save File
        options = ExportOptions.Create()
        DocumentSave.Execute(Ansys_SPEOS_file, options)
        # This section is added to export an additonal Solution file for computation on HPC or GPU
        # Export speos-file
        speos_path = os.path.join(os.getcwd(), "SPEOS isolated files")
        if not os.path.isdir(speos_path):
            os.mkdir(speos_path)
        sim_cam.object.Export(os.path.join(speos_path, "Cam_Sim.speos"))

    elif mode == 0:
        ###
        # Input Camera model number
        ###
        camera_model = 1

        InputHelper.PauseAndGetInput("Please provide a camera model number (2 models availables)", camera_model)
        part_names = []  # new
        position_value = 682.2
        car_path = selection_dialog_window()
        InputHelper.PauseAndGetInput("Please provide height value of selected car", position_value)

        import_car(car_path, position_value)
        for part in GetRootPart().Components:
            part_names.append(part.GetName())
        ###
        # Define Sim
        sim_cam = prepare_sim_setup("Camera", "Cam_Sim", part_names, camera_model)
        sim_cam.object.Compute()


main()
