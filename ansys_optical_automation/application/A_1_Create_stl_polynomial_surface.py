#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fit a 2D polynomial surface z = f(x, y) from a Speos .OPT3DMapping file,
generate an STL mesh, and export both the STL and the polynomial model JSON.

This script works standalone or can be imported by another script.
"""

import json
import os

import numpy as np
import trimesh


def build_design_matrix(x: np.ndarray, y: np.ndarray, order: int = 5) -> np.ndarray:
    """
    Build the design matrix for 2D polynomial least-squares fitting.

    Parameters
    ----------
    x, y : ndarray
        Normalized coordinates.
    order : int, optional
        Polynomial total order (default: 5).

    Returns
    -------
    ndarray
        Vandermonde-like matrix of shape (N, (order+1)(order+2)/2).
    """
    terms = []
    for i in range(order + 1):
        for j in range(order + 1 - i):
            terms.append((x**i) * (y**j))
    return np.vstack(terms).T


def evaluate_fitted_surface(coeffs: np.ndarray, x: np.ndarray, y: np.ndarray, order: int = 5) -> np.ndarray:
    """
    Evaluate the fitted polynomial surface z = f(x, y).

    Parameters
    ----------
    coeffs : ndarray
        Polynomial coefficients.
    x, y : ndarray
        Normalized coordinates.
    order : int
        Polynomial order.

    Returns
    -------
    ndarray
        Evaluated z values.
    """
    z = np.zeros_like(x)
    idx = 0
    for i in range(order + 1):
        for j in range(order + 1 - i):
            z += coeffs[idx] * (x**i) * (y**j)
            idx += 1
    return z


def create_polynomial_surface(input_file: str, output_stl: str, output_json: str, order: int = 5) -> None:
    """
    Fit the polynomial surface and export STL + JSON model.

    Parameters
    ----------
    input_file : str
        Path to the .OPT3DMapping file.
    output_stl : str
        Output STL file path.
    output_json : str
        Output polynomial model JSON path.
    order : int, optional
        Polynomial order (default: 5).
    """
    with open(input_file, "r") as f:
        lines = f.readlines()[1:]

    points = [list(map(float, line.strip().split()[:3])) for line in lines if len(line.strip().split()) >= 3]
    points = np.array(points)
    x_raw, y_raw, z = points[:, 0], points[:, 1], points[:, 2]

    x_mean, x_std = x_raw.mean(), x_raw.std()
    y_mean, y_std = y_raw.mean(), y_raw.std()
    x = (x_raw - x_mean) / x_std
    y = (y_raw - y_mean) / y_std

    X_design = build_design_matrix(x, y, order)
    coeffs, _, _, _ = np.linalg.lstsq(X_design, z, rcond=None)

    x_grid_raw = np.linspace(x_raw.min(), x_raw.max(), 100)
    y_grid_raw = np.linspace(y_raw.min(), y_raw.max(), 100)
    xg_raw, yg_raw = np.meshgrid(x_grid_raw, y_grid_raw)
    xg = (xg_raw - x_mean) / x_std
    yg = (yg_raw - y_mean) / y_std
    zg = evaluate_fitted_surface(coeffs, xg, yg, order)

    vertices = np.stack([xg_raw.flatten(), yg_raw.flatten(), zg.flatten()], axis=1)
    faces = []
    res_x, res_y = xg.shape
    for i in range(res_x - 1):
        for j in range(res_y - 1):
            idx = i * res_y + j
            faces.append([idx, idx + 1, idx + res_y])
            faces.append([idx + 1, idx + res_y + 1, idx + res_y])
    mesh = trimesh.Trimesh(vertices=vertices, faces=np.array(faces))
    mesh.export(output_stl)
    print(f"[OK] STL exported to: {output_stl}")

    model = {
        "order": order,
        "coeffs": coeffs.tolist(),
        "x_mean": float(x_mean),
        "x_std": float(x_std),
        "y_mean": float(y_mean),
        "y_std": float(y_std),
        "x_min": float(x_raw.min()),
        "x_max": float(x_raw.max()),
        "y_min": float(y_raw.min()),
        "y_max": float(y_raw.max()),
    }

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)
    print(f"[OK] Model JSON exported to: {output_json}")


def main():
    """Standalone entry point."""

    base_path = (
        r"C:\Users\amarin\OneDrive - ANSYS, Inc\Articules and Trainings ACE"
        r"\3D Texture - Light Guide\#2. Variable pitch"
    )

    input_file = base_path + r"\TL L.3D Texture.2.OPT3DMapping"

    output_stl = base_path + r"\FittedSurface_Global_HighQuality.stl"

    output_json = base_path + r"\FittedSurface_Model.json"

    create_polynomial_surface(
        input_file,
        output_stl,
        output_json,
    )


if __name__ == "__main__":
    main()
