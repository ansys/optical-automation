# Python Script, API Version = V232
import math

# import sys
# repo_path = r"your_repo_path"
# sys.path.append(repo_path)
from ansys_optical_automation.speos_process.speos_sensors import RadianceSensor


def main():
    Radiance = RadianceSensor("Radiance_from_View", SpeosSim, SpaceClaim)
    Radiance.Command.Execute("FlyThroughCamera")
    InputHelper.PauseAndGetInput("Adjust the window to the desired point of view and validate")
    Camera = GetActiveWindow().GetCameraFrame()
    HFOV = round(GetActiveWindow().HorizontalFieldOfView * 180 / math.pi, 0)
    VFOV = round(GetActiveWindow().VerticalFieldOfView * 180 / math.pi, 0)
    DatumCS = DatumOriginCreator.Create(Camera)
    cs = DatumCS.CreatedOrigin
    cs.SetName("ObserverOriginRadianceSensor")

    Radiance.set_definition_type("observer")
    Radiance.set_type("colorimetric")
    Radiance.set_observer_point(cs)
    Radiance.set_observer_directions(cs.Axes[2], cs.Axes[1])
    Radiance.set_fov(HFOV, VFOV, HFOV * 10, VFOV * 10)

    MessageBox.Show(
        "A Radiance Sensor was created with "
        + str(int(HFOV))
        + "°x"
        + str(int(VFOV))
        + r"° field of view \n and 0.1° central resolution"
    )
    Radiance.Command.Execute("FlyThroughCamera")
    Radiance.Command.Execute("OrthographicCamera")


main()
