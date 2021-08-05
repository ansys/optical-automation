# Copyright (C) 2020 ANSYS, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

# Python Script, API Version = V20 Beta

import sys
import os

from scdm_scripts.cad_data_postprocessing.preprocessinglibrary import PreProcessingASP
from SPEOS_scripts.SpaceClaimCore.base import BaseSCDM


class Camera(BaseSCDM):
    def __init__(self, name, SpeosSim, SpaceClaim):
        """
        Finds the speos camera sensor with "name" and sets it position and
        orientation using the reference origin point "ENPP_195" and the axis
        system from the part with "name".
        Important: the camera sensor "name" has to be the same as the part
        "name" with the reference point and axis system.
        """
        super(Camera, self).__init__(SpaceClaim, ["V19", "V20", "V21"])
        self.name = name
        self.speos_sim = SpeosSim
        sim = self.speos_sim.SensorCamera.Find(self.name)
        if not sim:
            sim = self.speos_sim.SensorCamera.Create()
            sim.Name = name
        self.object = sim
    
    def set_position(self, x_reverse=False, y_reverse=False, origin=None):
        parts = self.GetRootPart().GetDescendants[self.IPart]()
        for part in parts:  # go through parts and find part with "name"
            if self.name in part.Master.Name:
                axis_sys = part.GetDescendants[self.ICoordinateSystem]()[0]
                # Set origin
                if origin:
                    curves = part.GetDescendants[self.IDesignCurve]()
                    for curve in curves:  # find the origin point under curves
                        if origin in curve.Master.Name:
                            self.object.OriginPoint.Set(curve)
                else:
                    self.object.OriginPoint.Set(axis_sys)
                # Set camera orientation (x and y directions)
                axes = axis_sys.GetDescendants[self.ICoordinateAxis]()
                axis_x = axes[0]
                axis_y = axes[1]
                self.object.XDirection.Set(axis_y)
                self.object.YDirection.Set(axis_x)
                self.object.YDirectionReverse = y_reverse
                self.object.XDirectionReverse = x_reverse
        return self

    def set_distortion(self, distortion_file_name):
        distortion_path = os.path.join(".", "SPEOS input files", distortion_file_name)
        self.object.DistorsionFile = distortion_path
        return self

    def set_transmittance(self, transmittance_file_name):
        transmittance_path = os.path.join(".", "SPEOS input files", transmittance_file_name)
        self.object.TransmittanceFile = transmittance_path
        return self

    def set_sensitivity(self, color, sensitivity_file_name):
        sensitivity_path = os.path.join(".", "SPEOS input files", sensitivity_file_name)
        if color == "red":
            self.object.RedSpectrumFile = sensitivity_path
        elif color == "green":
            self.object.GreenSpectrumFile = sensitivity_path
        elif color == "blue":
            self.object.BlueSpectrumFile = sensitivity_path
        return self
