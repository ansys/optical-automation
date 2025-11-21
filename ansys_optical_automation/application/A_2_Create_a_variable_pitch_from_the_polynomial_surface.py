#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate a variable-pitch .OPT3DMapping file from a polynomial surface model.

If the JSON model does not exist, this script will try to import and run
`create_polynomial_surface()` from `1_1_create_stl_polynomial_surface.py`.

Everything can also be executed independently (standalone).
"""

import json
import os
from typing import List
from typing import Tuple

import numpy as np

# Try importing the fitting script
try:
    from A_1_Create_stl_polynomial_surface import create_polynomial_surface

    print("[INFO] Successfully imported create_polynomial_surface from 1_1_create_stl_polynomial_surface.py")
except ModuleNotFoundError as e:
    print(f"[ERROR] Could not import Script 1: {e}")
    print("Make sure both scripts are in the same folder or that this folder is in sys.path.")
    raise


# ============================== CONFIG ============================== #

MODEL_JSON = (
    r"C:\Users\amarin\OneDrive - ANSYS, Inc\Articules and Trainings ACE\3D Texture - Light Guide"
    r"\#2. Variable pitch\FittedSurface_Model.json"
)
OUTPUT_MAPPING = (
    r"C:\Users\amarin\OneDrive - ANSYS, Inc\Articules and Trainings ACE\3D Texture - Light Guide"
    r"\#2. Variable pitch\VariablePitch.OPT3DMapping"
)
INPUT_MAPPING = (
    r"C:\Users\amarin\OneDrive - ANSYS, Inc\Articules and Trainings ACE\3D Texture - Light Guide"
    r"\#2. Variable pitch\TL L.3D Texture.2.OPT3DMapping"
)
OUTPUT_STL = (
    r"C:\Users\amarin\OneDrive - ANSYS, Inc\Articules and Trainings ACE\3D Texture - Light Guide"
    r"\#2. Variable pitch\FittedSurface_Global_HighQuality.stl"
)

PITCH_X_START = 2.0
PITCH_X_END = 5.0
PITCH_Y = 1.0
INCLUDE_EDGES = True

X_MIN = None
X_MAX = None
Y_MIN = None
Y_MAX = None

EXTRA_CONSTANTS = ["1", "0", "0", "0", "1", "0", "0.5", "0.5", "1"]
FLOAT_FMT = ".6f"

# ==================================================================== #


def linear_pitch_x(x: float, x_min: float, x_max: float, p_start: float, p_end: float) -> float:
    """Linear interpolation of pitch along X."""
    if x_max == x_min:
        return p_start
    t = np.clip((x - x_min) / (x_max - x_min), 0.0, 1.0)
    return p_start * (1.0 - t) + p_end * t


def generate_points(
    domain: Tuple[float, float, float, float], p_start: float, p_end: float, p_y: float, include_edges: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate (X, Y) grid with variable X pitch and constant Y pitch.

    Parameters
    ----------
    domain : tuple
        (x_min, x_max, y_min, y_max)
    p_start, p_end, p_y : float
        Pitch configuration.
    include_edges : bool
        Whether to force the last row/column at the domain edge.

    Returns
    -------
    X_pts, Y_pts : ndarray
        Flattened arrays of all coordinates.
    """
    x_min, x_max, y_min, y_max = domain
    eps = 1e-12
    if p_start <= 0 or p_end <= 0 or p_y <= 0:
        raise ValueError("All pitch values must be positive.")

    ys = []
    y = y_min
    while y <= y_max + eps:
        ys.append(min(y, y_max))
        y += p_y
    if include_edges and abs(ys[-1] - y_max) > 1e-9:
        ys.append(y_max)

    X_list, Y_list = [], []
    for yy in ys:
        x = x_min
        row = []
        while x <= x_max + eps:
            row.append(min(x, x_max))
            x += linear_pitch_x(x, x_min, x_max, p_start, p_end)
        if include_edges and abs(row[-1] - x_max) > 1e-9:
            row.append(x_max)
        X_list.extend(row)
        Y_list.extend([yy] * len(row))
    return np.asarray(X_list), np.asarray(Y_list)


def eval_poly2d(coeffs: np.ndarray, x_norm: np.ndarray, y_norm: np.ndarray, order: int) -> np.ndarray:
    """Evaluate z = f(x, y) using polynomial coefficients."""
    z = np.zeros_like(x_norm)
    idx = 0
    for i in range(order + 1):
        for j in range(order + 1 - i):
            z += coeffs[idx] * (x_norm**i) * (y_norm**j)
            idx += 1
    return z


def write_opt3d_mapping(
    path: str,
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
    extra_constants: List[str],
    float_fmt: str = ".6f",
) -> None:
    """Write the .OPT3DMapping file."""
    if len(extra_constants) != 9:
        raise ValueError("Exactly 9 extra constants are required.")
    n = len(X)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ffmt = f"{{:{float_fmt}}}"  # noqa: E231
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{n}\n")
        for x, y, z in zip(X, Y, Z):
            formatted_values = " ".join([ffmt.format(x), ffmt.format(y), ffmt.format(z)] + extra_constants)
            f.write(formatted_values + "\n")


def ensure_model_json():
    """Ensure the polynomial model JSON exists; generate it if missing."""
    if os.path.isfile(MODEL_JSON):
        return
    print("[INFO] JSON not found. Running Script 1 via direct import...")
    create_polynomial_surface(INPUT_MAPPING, OUTPUT_STL, MODEL_JSON)
    if not os.path.isfile(MODEL_JSON):
        raise FileNotFoundError(f"Model JSON not generated: {MODEL_JSON}")


def main():
    """Main entry point."""
    ensure_model_json()

    with open(MODEL_JSON, "r", encoding="utf-8") as f:
        model = json.load(f)

    order = int(model["order"])
    coeffs = np.asarray(model["coeffs"], float)
    x_mean, x_std = float(model["x_mean"]), float(model["x_std"])
    y_mean, y_std = float(model["y_mean"]), float(model["y_std"])

    x_min = X_MIN or float(model["x_min"])
    x_max = X_MAX or float(model["x_max"])
    y_min = Y_MIN or float(model["y_min"])
    y_max = Y_MAX or float(model["y_max"])

    X_pts, Y_pts = generate_points((x_min, x_max, y_min, y_max), PITCH_X_START, PITCH_X_END, PITCH_Y, INCLUDE_EDGES)
    x_norm = (X_pts - x_mean) / x_std
    y_norm = (Y_pts - y_mean) / y_std
    Z_pts = eval_poly2d(coeffs, x_norm, y_norm, order)
    write_opt3d_mapping(OUTPUT_MAPPING, X_pts, Y_pts, Z_pts, EXTRA_CONSTANTS, FLOAT_FMT)

    print(f"[OK] Mapping created: {OUTPUT_MAPPING}")
    print(f"[INFO] Total points: {len(X_pts)}")
    print(f"[INFO] Domain X[{x_min}, {x_max}]  Y[{y_min}, {y_max}]")
    print(f"[INFO] Pitch X: {PITCH_X_START} → {PITCH_X_END} | Pitch Y: {PITCH_Y}")


if __name__ == "__main__":
    main()
