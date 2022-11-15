import time

from ansys_optical_automation.post_process.dpf_hdri_viewer import DpfHdriViewer


def animation_run(file):
    """
    function to run animation in observer result.

    Parameters
    ----------
    file : str
        file path of VR file.

    Returns
    -------


    """
    VRLab = DpfHdriViewer()
    VRLab.open_file(file)
    VRLab.dpf_instance.Show(1)
    while True:
        VRLab.set_source_power(100, 10)
        time.sleep(3)
        VRLab.set_source_power(1, 50)
        time.sleep(3)
        VRLab.set_source_power(1, 100)
        time.sleep(3)
        VRLab.set_source_power(1, 150)
        time.sleep(3)
        VRLab.set_source_power(1, 200)
        time.sleep(3)
        VRLab.set_source_power(1, 300)
        time.sleep(3)


def main():
    """
    main function to run Observer VR animation.

    Returns
    -------


    """
    file = r"C:\Users\plu\OneDrive - ANSYS, Inc\Optis Europe NoPeaks.OptisVR"
    animation_run(file)


main()
