from ansys_optical_automation.speos_process.speos_sensors import RadianceSensor


def main():
    Command.Execute("FlyThroughCamera")
    InputHelper.PauseAndGetInput("Adjust the window to the desired point of view and validate")
    Camera = GetActiveWindow().GetCameraFrame()
    HFOV = round(GetActiveWindow().HorizontalFieldOfView * 180 / 3.14, 0)
    VFOV = round(GetActiveWindow().VerticalFieldOfView * 180 / 3.14, 0)
    DatumCS = DatumOriginCreator.Create(Camera)
    cs = DatumCS.CreatedOrigin
    cs.SetName("ObserverOriginRadianceSensor")

    Radiance = RadianceSensor("Radiance_from_View", SpeosSim, SpaceClaim)
    Radiance.set_observer_type("observer")
    Radiance.set_type("colorimetric")
    Radiance.set_observer_point(cs)
    Radiance.set_observer_directions(cs.Axes[2], cs.Axes[1])
    Radiance.set_fov(HFOV, VFOV, HFOV * 10, VFOV * 10)

    MessageBox.Show(
        "A Radiance Sensor was created with "
        + str(int(HFOV))
        + "°x"
        + str(int(VFOV))
        + "° field of view \nand 0.1° central resolution"
    )
    Command.Execute("FlyThroughCamera")
    Command.Execute("OrthographicCamera")


main()
