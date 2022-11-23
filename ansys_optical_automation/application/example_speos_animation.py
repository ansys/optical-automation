from ansys_optical_automation.speos_process.speos_sensors import RadianceSensor


def dot_product(vector1, vector2):
    """
    return a dot product of two vectors.

    Parameters
    ----------
    vector1 : SpaceClaim Vector
    vector2 : SpaceClaim Vector

    Returns
    -------
    float
        result of vector dot product

    """
    return vector1.X * vector2.X + vector1.Y * vector2.Y + vector1.Z * vector2.Z


def create_movie_sensors(focus, frame_number, trajectory, global_normal, sensor_ref):
    """
    create a list of radiance sensors based on trajectory and frame rate provided.

    Parameters
    ----------
    focus : SpaceClaim point
        point defines focus point
    frame_number : int
        number of frames of movie.
    trajectory : SpaceClaim Curve
        path the radiance sensor travels
    global_normal : SpaceClaim vector
        unit z-vector of global coordinate
    sensor_ref : Speos radiance sensor

    Returns
    -------
    list
        a list of Speos radiance sensors
    """
    sensor_list = []
    for i in range(frame_number):
        position_percentage = float(i) / (frame_number - 1)
        origin = trajectory.Evaluate(position_percentage).Point
        z_direction_vector = (origin - focus).Direction.UnitVector
        cos_angle = dot_product(z_direction_vector, global_normal)
        z_project = Vector.Create(
            z_direction_vector.X * cos_angle,
            z_direction_vector.Y * cos_angle,
            z_direction_vector.Z * cos_angle,
        )
        u_direction_vector = (-z_project + global_normal).Direction.UnitVector

        sensor_name = str(position_percentage * 100)[:5]
        result = DatumOriginCreator.Create(
            origin, z_direction_vector.Direction, u_direction_vector.Direction
        ).CreatedOrigin
        result.SetName(sensor_name)

        sensor = sensor_ref.Clone()
        sensor_name = sensor.Name
        sensor = RadianceSensor(sensor_name, SpeosSim, SpaceClaim)
        sensor.speos_object.Name = sensor_name
        sensor.set_position(True, False, result, [result.Axes[2], result.Axes[1]])
        sensor_list.append(sensor.speos_object.Subject)
    return sensor_list


def create_movie_simulation(sensor_list, simulation_ref, export=False):
    """
    create speos simulation required for creating movie.

    Parameters
    ----------
    sensor_list : list
        a list of Speos radiance sensors
    simulation_ref : Speos simulation
    export : bool
        True if exported to .speos file to run externally, False otherwise to run locally

    Returns
    -------


    """
    simulation = simulation_ref.Clone()
    simulation.Name = "Movie"
    sel = Selection.Create(sensor_list)
    simulation.Sensors.Set(sel.Items)
    if export is False:
        simulation.Compute()
    else:
        print("to export")


def main():
    """
    main function to this application of create movie from ansys speos.
    """
    frame = 1
    InputHelper.PauseAndGetInput("Please provide frame rate", frame)  # frame rate to be provided by user
    frame = int(frame)

    trajectory = None
    response = InputHelper.PauseAndGetInput(
        "Please select a curve for camera trajectory"
    )  # curve selection to be defined by user selection
    if response.Success:
        selection = response.PrimarySelection
        if selection.GetItems[IDesignCurve]().Count != 1:
            MessageBox.Show("Please select 1 curve")
            return
        trajectory = selection.GetItems[IDesignCurve]()[0]
    else:
        return

    global_normal = None
    response = InputHelper.PauseAndGetInput(
        "Please select a axis for global zenith direction"
    )  # axis selection to be defined by user selection
    if response.Success:
        selection = response.PrimarySelection
        if selection.GetItems[ICoordinateAxis]().Count != 1:
            MessageBox.Show("Please select 1 axis")
            return
        global_normal = selection.GetItems[ICoordinateAxis]()[0]
        global_normal = global_normal.Shape.Geometry.Direction.UnitVector
    else:
        return

    focus_point = None
    response = InputHelper.PauseAndGetInput(
        "Please select a axis for coordinate system for camera focus point"
    )  # coordinate system selection to be defined by user selection
    if response.Success:
        selection = response.PrimarySelection
        if selection.GetItems[ICoordinateSystem]().Count != 1:
            MessageBox.Show("Please select 1 axis")
            return
        focus_point = selection.GetItems[ICoordinateSystem]()[0]
        focus_point = Point.Create(focus_point.Frame.Origin.X, focus_point.Frame.Origin.Y, focus_point.Frame.Origin.Z)
    else:
        return

    export = False
    response = InputHelper.PauseAndGetInput(
        "Please select true if to export, other false to not export"
    )  # to be defined by user selection
    if response.Success:
        export = True
    else:
        export = False

    reference_sensor = None
    response = InputHelper.PauseAndGetInput(
        "Please select a radiane sensor for animation simulation"
    )  # radiance sensor to be defined by user selection
    if response.Success:
        selection = response.PrimarySelection
        if selection.Count != 1:
            MessageBox.Show("Please select 1 selection")
            return
        radiance_sensor_name = selection.Items[0].Name
        if not SpeosSim.SensorRadiance.Find(radiance_sensor_name):
            MessageBox.Show("Please select radiance sensor")
            return
        reference_sensor = SpeosSim.SensorRadiance.Find(radiance_sensor_name)
    else:
        return

    reference_simulation = None
    response = InputHelper.PauseAndGetInput(
        "Please select a inverse simulation for animation simulation"
    )  # inverse simulation to be defined by user selection
    if response.Success:
        selection = response.PrimarySelection
        if selection.Count != 1:
            MessageBox.Show("Please select 1 selection")
            return
        reference_simulation_name = selection.Items[0].Name
        if not SpeosSim.SimulationInverse.Find(reference_simulation_name):
            MessageBox.Show("Please select inverse simulation")
            return
        reference_simulation = SpeosSim.SimulationInverse.Find(reference_simulation_name)
    else:
        return

    sensor_list = create_movie_sensors(focus_point, frame, trajectory, global_normal, reference_sensor)
    create_movie_simulation(sensor_list, reference_simulation, export)


main()
