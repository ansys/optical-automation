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
    frame = 60  # to be defined by user input
    trajectory = GetRootPart().Curves[0]  # to be defined by user selection
    global_normal = Vector.Create(0, 1, 0).Direction.UnitVector  # to be defined by user selection
    focus_point = Point.Create(0, 0, 0)  # to be defined by user selection
    export = False  # to be defined by user selection
    reference_sensor = SpeosSim.SensorRadiance.Find("Ref")  # to be defined by user selection
    reference_simulation = SpeosSim.SimulationInverse.Find("Inverse.1")  # to be defined by user selection
    sensor_list = create_movie_sensors(focus_point, frame, trajectory, global_normal, reference_sensor)
    create_movie_simulation(sensor_list, reference_simulation, export)


main()
