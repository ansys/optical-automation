import os
import subprocess


def get_lumerical_install_location(version):
    """
    Get the Lumerical installation path.

    Parameters
    ----------
    version : int
        Version of Lumerical in numerical format. For example, ``211`` for 2021 R1.

    Returns
    -------
    str
        Path of the Lumerical installation.

    """
    ansys_install_dir = os.path.dirname(os.path.dirname(os.environ["AWP_ROOT{}".format(version)]))
    lumerical_install_dir = os.path.join(ansys_install_dir, "Lumerical", "v{}".format(version), "bin")
    return lumerical_install_dir


def run_lumerical_batch(application, application_version, script_file):
    """
    Start a Lumerical application script in batch mode via the ``subprocess.call`` method.

    Parameters
    ----------
    application : str
        lumerical_solver.
    application_version : int
        application version.
    script_file : str
        Full path to the lumerical script file.
    """
    application_install_dir = get_lumerical_install_location(application_version)
    application_exe = os.path.join(application_install_dir, application.lower() + ".exe")
    command = [
        application_exe,
        r"-run",
        r"{}".format(script_file),
        r"-logall",
        r"-exit",
        r"-hide",
    ]
    subprocess.call(command)
