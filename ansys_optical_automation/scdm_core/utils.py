import os
import subprocess


def get_scdm_install_location(version):
    """
    Get the SpaceClaim installation path.

    Parameters
    ----------
    version : int
        Version of SpaceClaim in numerical format. For example, ``211`` for 2021 R1.

    Returns
    -------
    str
        Path of the SpaceClaim installation.

    """
    ansys_install_dir = os.environ["AWP_ROOT{}".format(version)]
    scdm_install_dir = os.path.join(ansys_install_dir, "scdm")
    return scdm_install_dir


def run_scdm_batch(scdm_version, api_version, script_file):
    """
    Start a Speos script in batch mode via the ``subprocess.call`` method.

    Parameters
    ----------
    scdm_version : int
        SpaceClaim version.
    api_version : int
        SpaceClaim API version.
    script_file : str
        Full path to the script file.
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
    subprocess.call(command)
