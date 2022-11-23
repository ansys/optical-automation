import math
import os
import time


def rotation_study(theta_inc, phi_inc, source, simulation, export_dir):
    """
    function to apply rotation light source study and export simulation

    Parameters
    ----------
    theta_inc : float
        theta increment
    phi_inc : float
        phi increment
    source : str
        name of speos Ambient Natural Light source
    simulation : str
        name of speos simulation
    export_dir : str
        direcotry to export simulations

    Returns
    -------


    """
    if not SpeosSim.SourceAmbientNaturalLight.Find(source):
        msg = "This application only supports ambient natural light source"
        raise ValueError(msg)
    speos_sun = SpeosSim.SourceAmbientNaturalLight.Find(source)
    speos_sun.SunType = SpeosSim.SourceAmbientNaturalLight.EnumSunType.Manual
    speos_sim = SpeosSim.SimulationInverse.Find(simulation)
    for theta in range(theta_inc, 90, theta_inc):
        for phi in range(0, 360, phi_inc):
            x = math.sin(DEG(theta)) * math.sin(DEG(phi))
            y = math.sin(DEG(theta)) * math.cos(DEG(phi))
            z = math.cos(DEG(theta))
            sun_direction = SketchLine.Create(Point.Create(0, 0, 0), Point.Create(x, y, z)).CreatedCurves[0]
            speos_sun.Name = theta.ToString() + "_" + phi.ToString()
            speos_sun.SunDirection.Set(sun_direction)
            time.sleep(1)
            speos_sim.Export(os.path.join(export_dir, theta.ToString() + "_" + phi.ToString()))
            sun_direction.Delete()
    speos_sun.Name = source


def main():
    """
    main function to run rotation study.

    Returns
    -------


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
    theta_inc = argsDict["theta_increment"]
    phi_inc = argsDict["phi_increment"]
    speos_light = argsDict["speos_source"]
    speos_simulation = argsDict["speos_simulation"][0]
    export_path = argsDict["export_path"]
    rotation_study(theta_inc, phi_inc, speos_light, speos_simulation, export_path)


main()
