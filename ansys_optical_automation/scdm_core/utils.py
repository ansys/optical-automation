import math
import os
import subprocess

import numpy as np


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


def get_speos_core(version):
    """
    get speos core path for version
    Parameters
    ----------
    version : str
        Ansys Version used

    Returns
    -------
    str
        path to speos core executable

    """
    ansys_install_dir = os.environ["AWP_ROOT{}".format(version)]
    speos_core_dir = os.path.join(ansys_install_dir, r"Optical Products", r"Viewers", r"SPEOSCore.exe")
    return speos_core_dir


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


def vector_len(vector):
    """
    compute vector length
    Parameters
    ----------
    vector : list
        [x,y,z]

    Returns
    -------
    float
        length of a vector

    """
    return math.sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)


def vector_normalize(vector):
    """
    get normalized vector.

    Parameters
    ----------
    vector : list
        [x,y,z]

    Returns
    -------
    list
        list representing normalized vector

    """
    vector_magnitude = vector_len(vector)
    return [item / vector_magnitude for item in vector]


def vector_dot_product(vector1, vector2):
    """
    function to multiply to vectors
    Parameters
    ----------
    vector1 : list
        [x,y,z]
    vector2 : list
        [x,y,z]
    Returns
    -------
    float
    """
    return vector1[0] * vector2[0] + vector1[1] * vector2[1] + vector1[2] * vector2[2]


def degree(rad):
    """
    function to convert unit radian to degree.

    Parameters
    ----------
    rad : float

    Returns
    -------
    float

    """
    return np.rad2deg(rad)


def radiance(deg):
    """
    function to convert unit degree to radian.

    Parameters
    ----------
    deg : float

    Returns
    -------
    float

    """
    return np.deg2rad(deg)
