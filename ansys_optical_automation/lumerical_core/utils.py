import os

if "nt" in os.name:
    import winreg
else:
    pass


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
    lumerical = r"Lumerical v" + str(version)
    lumerical_install_dir = None
    try:
        a_key = winreg.OpenKey(
            winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE),
            os.path.join("Software", "ANSYS, Inc.", lumerical),
            0,
            winreg.KEY_READ,
        )
        lumerical_data = winreg.QueryValueEx(a_key, "installFolder")
        lumerical_install_dir = lumerical_data[0]
        winreg.CloseKey(a_key)
    except EnvironmentError:
        raise EnvironmentError("Request Lumerical is not installed or not installed in the default location")
    return lumerical_install_dir
