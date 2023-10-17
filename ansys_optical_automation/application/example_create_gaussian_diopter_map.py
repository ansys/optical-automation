import numpy as np

# repo_path=r"your repository location"
# sys.path.append(repo_path)
from ansys_optical_automation.post_process.dpf_xmp_viewer import MapStruct


def gaussian(xy, x0, y0, sigma_x, sigma_y, H):
    """
    2D gaussian function
    Parameters
    ----------
    xy : tuple of floats
        tuple of x,y
    x0 : float
        x offset
    y0 : float
        y offset
    sigma_x : float
        Gaussian size in X
    sigma_y : float
        Gaussian size in y
    H : float
        height of gaussian

    Returns
    -------
    float
    value of gausian function at x,y with given sigma's and H
    """
    x, y = xy
    ax = 1 / (2 * sigma_x**2)
    ay = 1 / (2 * sigma_y**2)
    gaussian_value = H * np.exp(-ax * ((x - x0) ** 2) - ay * ((y - y0) ** 2))
    return gaussian_value


diopter_map = MapStruct(3, 20, 0, 9, 1, [-10, 10, -10, 10], [50, 50])
x_values = np.arange(-10, 10.0, 20 / 50)
y_values = np.arange(-10, 10.0, 20 / 50)
for x in range(50):
    for y in range(50):
        diopter_map.data[0, x, y, 0] = gaussian((x_values[x], y_values[y]), 0, 0, 5, 10, 0.5)

xmp = diopter_map.export_to_xmp(r"c:\temp")
