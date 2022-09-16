import os


def get_lumerical_install_location(version):
    """
    Get the Lumerical installation path.

    Parameters
    ----------
    version : int
        Version of Lumerical in numerical format. For example, ``222`` for 2022 R2.

    Returns
    -------
    str
        Path of the Lumerical installation.

    """
    lumerical_install_dir = os.path.join(os.environ["ProgramFiles"], "Lumerical", "v" + str(version))
    if not os.path.exists(lumerical_install_dir):
        raise TypeError("Request Lumerical is not installed or not installed in the default location")
    return lumerical_install_dir
