import math
import os

import numpy as np

from ansys_optical_automation.post_process.dpf_rayfile import DpfRay
from ansys_optical_automation.post_process.dpf_rayfile import DpfRayfile


def vector_multi(vec1, vec2):
    """
    function to multiply to vectors
    Parameters
    ----------
    vec1 : list
        [x,y,z]
    vec2 : list
        [x,y,z]
    Returns
    -------
    int
    """
    return vec1[0] * vec2[0] + vec1[1] * vec2[1] + vec1[2] * vec2[2]


def vector_len(vec):
    """
    compute vector length
    Parameters
    ----------
    vec : list
        [x,y,z]

    Returns
    -------
    float

    """
    return np.sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)


def create_ray(point, direction, wl, e):
    """
    Parameters
    ----------
    point : list
        [x,y,z]
    direction : list
        [x,y,z]
    wl : float
        wl in microns
    e : float
        energy fraction between 0 and 1

    Returns
    -------
    DpfRay object

    """
    x_dir = [1, 0, 0]
    y_dir = [0, 1, 0]
    z_dir = [0, 0, 1]
    l_dir = vector_multi(x_dir, direction) / (vector_len(x_dir) * vector_len(direction))
    m_dir = vector_multi(y_dir, direction) / (vector_len(y_dir) * vector_len(direction))
    n_dir = vector_multi(z_dir, direction) / (vector_len(z_dir) * vector_len(direction))
    my_ray = DpfRay(point[0], point[1], point[2], l_dir, m_dir, n_dir, wl, e)
    return my_ray


def main():
    step_size = 30
    x_min = 1310
    x_max = 1700
    y_min = -690
    y_max = 690
    radius = 12
    x_range = np.arange(x_min, x_max, step_size)
    y_range = np.arange(y_min, y_max, step_size)
    file_path = r"c:\temp"
    sample = 5.0
    for item in range(int(sample)):
        radius_vector = [0, 0, 0]
        if item != 0:
            radius_vector = [
                0,
                math.cos(2 * math.pi / (sample - 1) * item),
                math.sin(2 * math.pi / (sample - 1) * item),
            ]
        radius_vector = [item * radius for item in radius_vector]
        my_rayfile = DpfRayfile(file_path=None)
        ray_number = 0
        for x in x_range:
            for y in y_range:
                my_rayfile.rays.append(
                    create_ray(
                        [
                            0 + radius_vector[0],
                            y + step_size / 2 + radius_vector[1],
                            x + step_size / 2 + radius_vector[2],
                        ],
                        [1, 0, 0],
                        0.555,
                        1,
                    )
                )
                ray_number += 1
        my_rayfile.set_ray_count(ray_number)
        my_rayfile.file_path = os.path.join(file_path, "ray_" + str(item) + ".ray")
        my_rayfile.export_to_speos()


main()
