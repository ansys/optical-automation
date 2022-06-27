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
