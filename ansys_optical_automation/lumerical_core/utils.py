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
    return lumerical_install_dir
