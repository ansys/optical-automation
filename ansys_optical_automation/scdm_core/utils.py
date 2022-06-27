import os


def get_scdm_install_location(version):
    """
    Function to get installation path of SpaceClaim
    Args:
        version (int): version in format <XXX> eg 211

    Returns: path of SCDM installation
    """

    ansys_install_dir = os.environ["AWP_ROOT{}".format(version)]
    scdm_install_dir = os.path.join(ansys_install_dir, "scdm")
    return scdm_install_dir


def get_scdm_batch_command(scdm_version, api_version, script_file):
    """
    Function to get speos batch command to run as subprocess
    Parameters
    ----------
    scdm_version: int
        scdm version
    api_version: int
        scdm api version
    script_file: str
        scdm script file directory

    Returns
    -------
        str: command
    """
    scdm_install_dir = get_scdm_install_location(scdm_version)
    scdm_exe = os.path.join(scdm_install_dir, "SpaceClaim.exe")
    speos_path = os.path.join(
        os.path.dirname(scdm_install_dir), "Optical Products", "Speos", "Bin", "SpeosSC.Manifest.xml"
    )
    command = [
        scdm_exe,
        r"/AddInManifestFile={}".format(speos_path),
        r"/RunScript={}".format(script_file),
        r"/Headless=True",
        r"/Splash=False",
        r"/Welcome=False",
        r"/ExitAfterScript=True",
        r"/ScriptAPI={}".format(api_version),
    ]
    return command
