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


def vector_add(vector1, vector2):
    """
    return sum of two vectors.

    Parameters
    ----------
    vector1 : SpaceClaim Vector
    vector2 : SpaceClaim Vector

    Returns
    -------
    SpaceClaim Vector

    """
    return Vector.Create(vector1.X + vector2.X, vector1.Y + vector2.Y, vector1.Z + vector2.Z)


def create_movie_sensors(frame_number, trajectory, global_normal, sensor_ref):
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
        z_Direction_vector = Vector.Create(origin.X, origin.Y, origin.Z).Direction.UnitVector
        angle = math.acos(dot_product(z_Direction_vector, global_normal))
        z_project = Vector.Create(
            z_Direction_vector.X * math.cos(angle),
            z_Direction_vector.Y * math.cos(angle),
            z_Direction_vector.Z * math.cos(angle),
        )
        u_Direction_vector = vector_add(-z_project, global_normal).Direction.UnitVector

        sensor_Name = str(position_percentage * 100)[:5]
        result = DatumOriginCreator.Create(
            origin, z_Direction_vector.Direction, u_Direction_vector.Direction
        ).CreatedOrigin
        result.SetName(sensor_Name)

        sensor = sensor_ref.Clone()
        sensor_name = sensor.Name
        sensor = RadianceSensor(sensor_name, SpeosSim, SpaceClaim)
        sensor.speos_object.Name = sensor_Name
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
    frame = 60
    trajectory = GetRootPart().Curves[0]
    global_normal = Vector.Create(0, 1, 0).Direction.UnitVector
    export = False
    reference_sensor = SpeosSim.SensorRadiance.Find("Ref")
    reference_simulation = SpeosSim.SimulationInverse.Find("Inverse.1")
    sensor_list = create_movie_sensors(frame, trajectory, global_normal, reference_sensor)
    create_movie_simulation(sensor_list, reference_simulation, export)


main()
