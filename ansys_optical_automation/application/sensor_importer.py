# Python Script, API Version = V232
from ansys_optical_automation.speos_process.speos_sensors import RadianceSensor


def create_sensor(coordinate_sys):
    """
    create sensor at the location of provided coordinate system with properties from argsDict ACT.

    Parameters
    ----------
    coordinate_sys : SpaceClaim coordinate system
    """
    opt_range = argsDict["range"]
    opt_sensor = RadianceSensor(coordinate_sys.GetName(), SpeosSim, SpaceClaim)
    opt_sensor.set_focal_value(argsDict["observer_distance"] - argsDict["distance_from_origin"])
    opt_sensor.set_position(
        x_reverse=False, y_reverse=False, origin=coordinate_sys, axes=[coordinate_sys.Axes[2], coordinate_sys.Axes[1]]
    )
    opt_sensor.set_type("Colorimetric")
    opt_sensor.set_layer("Source")
    opt_sensor.set_range(
        x_start=opt_range[0],
        x_end=opt_range[1],
        y_start=opt_range[2],
        y_end=opt_range[3],
        x_mirrored=False,
        y_mirrored=False,
    )
    opt_sensor.set_resolution(argsDict["resolution"][0], argsDict["resolution"][1])
    opt_sensor.set_wavelength_resolution(10)
    opt_sensor.set_integration_angle(argsDict["integration_angle"])
    opt_sensor.set_xmp_template(argsDict["xml_template"], take_display=True)


def update_sensor(sensor_coordinate, new_name):
    """
    Update sensor with name obtained from sensor_coordinate to the new parameter from argsDict ACT.

    Parameters
    ----------
    sensor_coordinate : SpaceClaim coordinate
    new_name : str
    """
    opt_range = argsDict["range"]
    opt_sensor = RadianceSensor(sensor_coordinate.GetName().ToString(), SpeosSim, SpaceClaim)
    if opt_sensor.speos_object.Name != new_name:
        opt_sensor.speos_object.Name = new_name
    opt_sensor.set_focal_value(argsDict["observer_distance"] - argsDict["distance_from_origin"])
    opt_sensor.set_position(
        x_reverse=False,
        y_reverse=False,
        origin=sensor_coordinate,
        axes=[sensor_coordinate.Axes[2], sensor_coordinate.Axes[1]],
    )
    opt_sensor.set_range(
        x_start=opt_range[0],
        x_end=opt_range[1],
        y_start=opt_range[2],
        y_end=opt_range[3],
        x_mirrored=False,
        y_mirrored=False,
    )
    opt_sensor.set_resolution(argsDict["resolution"][0], argsDict["resolution"][1])
    opt_sensor.set_integration_angle(argsDict["integration_angle"])


def create_coordinate(theta, phi, distance_from_ref):
    """
    Create a coordinate_system.

    Parameters
    ----------
    theta : int
    phi : int
    distance_from_ref : int

    Returns
    -------
    Spaceclaim coordinate system
    """
    p = Point.Create(
        math.cos(DEG(theta)) * math.cos(DEG(phi)) * MM(distance_from_ref) * (-1 if argsDict["reverse"] == 1 else 1),
        math.cos(DEG(theta)) * math.sin(DEG(phi)) * MM(distance_from_ref),
        math.sin(DEG(theta)) * MM(distance_from_ref),
    )
    direction_x = Direction.Create(-p.X, -p.Y, -p.Z)
    direction_y = Direction.Create(
        -math.sin(DEG(theta)) * math.cos(DEG(phi)) * (-1 if argsDict["reverse"] == 1 else 1),
        -math.sin(DEG(theta)) * math.sin(DEG(phi)),
        math.cos(DEG(theta)),
    )
    result = DatumOriginCreator.Create(p, direction_x, direction_y).CreatedOrigin
    return result


def sensor_lib():
    """
    create sensor lib based on the information defined in argsDict from ACT.
    """
    sensor_lib_name = argsDict["name"] + " Sensor Lib"
    sensor_comps = GetRootPart().GetAllComponents(sensor_lib_name)
    sensor_lib_comp = None
    if sensor_comps.Count == 0:
        sensor_lib_comp = ComponentHelper.CreateAtRoot(sensor_lib_name)
    elif sensor_comps.Count != 1:
        MessageBox.Show("multi components found", "Error")
    else:
        sensor_lib_comp = sensor_comps[0]

    ComponentHelper.SetActive(Selection.Create(sensor_lib_comp))
    coordinate_systems = sensor_lib_comp.GetAllCoordinateSystems()

    origin_ref = argsDict["origin"]
    phi_angles = argsDict["phi_angles"]
    tilt_angles = argsDict["theta_angles"]
    distance_from_ref_center = argsDict["distance_from_origin"]

    if coordinate_systems.Count == 1:  # case there is no coordinates
        for theta_angle in tilt_angles:
            for phi_angle in phi_angles:
                # create coordinate_system for sensor
                sensor_coordinate_system = create_coordinate(theta_angle, phi_angle, distance_from_ref_center)
                # update it to the selected origin_ref
                target_origin_matrix = Matrix.CreateMapping(origin_ref.Frame)
                sensor_coordinate_system.Transform(target_origin_matrix)
                # set the name of coordinate_system
                sensor_coordinate_system.SetName(str(theta_angle) + "_" + str(phi_angle))
                # create radiance sensor
                create_sensor(sensor_coordinate_system)
    elif coordinate_systems.Count == len(phi_angles) * len(tilt_angles) + 1:  # case there are same number of
        # coordinates
        for theta_idx, theta_angle in enumerate(tilt_angles):
            for phi_idx, phi_angle in enumerate(phi_angles):
                # find the coordinate_system to be updated
                coord_sys = coordinate_systems[theta_idx * len(phi_angles) + phi_idx]
                # create coordinate_system to which should be located
                sensor_coordinate_system = create_coordinate(theta_angle, phi_angle, distance_from_ref_center)
                # change transformation matrix
                target_matrix = Matrix.CreateMapping(sensor_coordinate_system.Frame)
                source_matrix = Matrix.CreateMapping(coord_sys.Frame)
                coord_sys.Transform(source_matrix.Inverse)
                coord_sys.Transform(target_matrix)
                Delete.Execute(Selection.Create(sensor_coordinate_system))
                # change transformation matrix
                target_origin_matrix = Matrix.CreateMapping(origin_ref.Frame)
                coord_sys.Transform(target_origin_matrix)
                new_name = str(theta_angle) + "_" + str(phi_angle)
                # update radiance sensor
                update_sensor(coord_sys, new_name)
                # set the name of coordinate_system
                coord_sys.SetName(new_name)
    else:
        Delete.Execute(Selection.Create(sensor_lib_comp))
        sensor_lib_comp = ComponentHelper.CreateAtRoot(sensor_lib_name)
        ComponentHelper.SetActive(Selection.Create(sensor_lib_comp))
        for theta_angle in tilt_angles:
            for phi_angle in phi_angles:
                sensor_coordinate_system = create_coordinate(theta_angle, phi_angle, distance_from_ref_center)
                target_origin_matrix = Matrix.CreateMapping(origin_ref.Frame)
                sensor_coordinate_system.Transform(target_origin_matrix)
                sensor_coordinate_system.SetName(str(theta_angle) + "_" + str(phi_angle))
                create_sensor(sensor_coordinate_system)
    ComponentHelper.SetRootActive(None)


def main():
    """
    main run function to create sensor_lib.
    """
    mode = None
    try:
        argsDict
        mode = 1
    except Exception:
        mode = 0

    if mode == 0:
        error_message = (
            "This application does not support executing from speos, " "please contact support for the usage"
        )
        raise ValueError(error_message)
    sensor_lib()


main()
