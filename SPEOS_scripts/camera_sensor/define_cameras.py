##################################################################
# define_cameras  - Copyright ANSYS. All Rights Reserved.
# ##################################################################
# CREATION:      2021.08.17
# VERSION:       1.0.0
#
# OVERVIEW
# ========
# This script is generated for showing scripting capabilities purpose.
# It contains a class with methods to create and modify Speos camera sensors.
#
#
# ##################################################################
# https://opensource.org/licenses/MIT
#
# Copyright 2021 Ansys, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# The user agrees to this disclaimer and user agreement with the download or usage
# of the provided files.
#
# ##################################################################

# Python Script, API Version = V20 Beta

import sys
import os
from scdm_scripts.cad_data_postprocessing.preprocessinglibrary import PreProcessingASP
from SPEOS_scripts.SpaceClaimCore.base import BaseSCDM


class Sensor(BaseSCDM):
    def __init__(self, name, SpeosSim, SpaceClaim):
        super(Sensor, self).__init__(SpaceClaim, ["V19", "V20", "V21"])
        self.name = name
        self.speos_sim = SpeosSim
        self.speos_object = None
        self.axes = None
        self.origin = None

    def find_axes(self, origin=None):
        origin_point = None
        axes = None
        # go through parts and find part with the same name as self.name
        parts = self.GetRootPart().GetDescendants[self.IPart]()
        for part in parts:
            if self.name in part.Master.Name:
                # Find axis system
                axis_sys = part.GetDescendants[self.ICoordinateSystem]()[0]
                axes = axis_sys.GetDescendants[self.ICoordinateAxis]()
                # Find sensor origin
                if origin:  # if origin point is explicitly defined
                    curves = part.GetDescendants[self.IDesignCurve]()
                    for curve in curves:  # find the origin point under curves
                        if origin in curve.Master.Name:
                            origin_point = curve
                else:  # else define origin using axis system
                    origin_point = axis_sys
        self.axes = axes
        self.origin = origin_point

    def set_position(self, x_reverse=False, y_reverse=False, origin=None, axes=None):
        # if self.speos_object (speos sensor speos_object) is not defined
        if not self.speos_object:
            raise TypeError("No Speos object defined.")
        # if axes and/or origin not defined/provided
        if not (self.axes and self.origin) and not (axes and origin):
            raise NameError("Axes or origin not defined. Use find_axes method or provide axes and origin as input.")
        # axes and origin provided as input have priority. If no inputs provided, use self.axes and self.origin
        if not (axes and origin):
            axes = self.axes
            origin = self.origin
        else:  # if axes and origin are provided as inputs, overwrite properties in self
            self.axes = axes
            self.origin = origin
        # Set sensor origin
        self.speos_object.OriginPoint.Set(origin)
        # Set sensor orientation (x and y directions)
        axis_x = axes[0]
        axis_y = axes[1]
        self.speos_object.XDirection.Set(axis_x)
        self.speos_object.YDirection.Set(axis_y)
        self.speos_object.XDirectionReverse = x_reverse
        self.speos_object.YDirectionReverse = y_reverse
        return self


class Camera(Sensor):
    def __init__(self, name, SpeosSim, SpaceClaim):
        """
        Finds the speos camera sensor with "name" and sets it position and
        orientation using the reference origin point "ENPP_195" and the axis
        system from the part with "name".
        Important: the camera sensor "name" has to be the same as the part
        "name" with the reference point and axis system.
        """
        super(Camera, self).__init__(name, SpeosSim, SpaceClaim)
        speos_object = self.speos_sim.SensorCamera.Find(self.name)
        if not speos_object:  # if camera doesn't exist -> create new camera
            speos_object = self.speos_sim.SensorCamera.Create()
            speos_object.Name = name
        self.speos_object = speos_object

    def set_distortion(self, distortion_file_name):
        distortion_path = os.path.join(".", "SPEOS input files", distortion_file_name)
        self.speos_object.DistorsionFile = distortion_path
        return self

    def set_transmittance(self, transmittance_file_name):
        transmittance_path = os.path.join(".", "SPEOS input files", transmittance_file_name)
        self.speos_object.TransmittanceFile = transmittance_path
        return self

    def set_sensitivity(self, color, sensitivity_file_name):
        sensitivity_path = os.path.join(".", "SPEOS input files", sensitivity_file_name)
        if color == "red":
            self.speos_object.RedSpectrumFile = sensitivity_path
        elif color == "green":
            self.speos_object.GreenSpectrumFile = sensitivity_path
        elif color == "blue":
            self.speos_object.BlueSpectrumFile = sensitivity_path
        return self


class IntensitySensor(Sensor):
    def __init__(self, name, SpeosSim, SpaceClaim):
        super(IntensitySensor, self).__init__(name, SpeosSim, SpaceClaim)
        speos_object = self.speos_sim.SensorIntensity.Find(self.name)
        if not speos_object:
            speos_object = self.speos_sim.SensorIntensity.Create()
            speos_object.Name = name
        self.speos_object = speos_object

    def set_format(self, sensor_format=None):
        if not sensor_format:
            raise NameError("Format input not provided.")
        sensor_format = sensor_format.lower()
        if sensor_format == "xmp":
            self.speos_object.FormatType = self.speos_sim.SensorIntensity.EnumFormatType.XMP
        elif sensor_format == "iesnatypea":
            self.speos_object.FormatType = self.speos_sim.SensorIntensity.EnumFormatType.IESNATypeA
        elif sensor_format == "iesnatypeb":
            self.speos_object.FormatType = self.speos_sim.SensorIntensity.EnumFormatType.IESNATypeB
        elif sensor_format == "iesnatypec":
            self.speos_object.FormatType = self.speos_sim.SensorIntensity.EnumFormatType.IESNATypeC
        elif sensor_format == "eulumdat":
            self.speos_object.FormatType = self.speos_sim.SensorIntensity.EnumFormatType.Eulumdat
        else:
            raise ValueError("Wrong input value. Choose from XMP, IESNATypeA, IESNATypeB, IESNATypeC or Eulumdat.")

    def set_range(self, x_start=None, x_end=None, y_start=None, y_end=None, x_mirrored=None, y_mirrored=None):
        if not x_start and not x_end and not y_start and not y_end and not x_mirrored and not y_mirrored:
            raise NameError("No inputs provided.")
        if x_mirrored:
            self.speos_object.XIsMirrored = x_mirrored
        if y_mirrored:
            self.speos_object.YIsMirrored = y_mirrored
        if x_start and not self.speos_object.XIsMirrored:
            self.speos_object.XStart = x_start
        if x_end:
            self.speos_object.XEnd = x_end
        if y_start and not self.speos_object.YIsMirrored:
            self.speos_object.YStart = y_start
        if y_end:
            self.speos_object.YEnd = y_end

    def set_sampling(self, x_sampling=None, y_sampling=None):
        if not x_sampling and not y_sampling:
            raise NameError("No inputs provided.")
        if x_sampling:
            self.speos_object.XNbSamples = x_sampling
        if y_sampling:
            self.speos_object.YNbSamples = y_sampling

    def set_resolution(self, x_resolution=None, y_resolution=None):
        if not x_resolution and not y_resolution:
            raise NameError("No inputs provided.")
        if x_resolution:
            self.speos_object.XResolution = x_resolution
        if y_resolution:
            self.speos_object.YResolution = y_resolution

    def set_type(self, sensor_type):
        sensor_type = sensor_type.lower()
        if sensor_type == "photometric":
            self.speos_object.SensorType = self.speos_sim.SensorIntensity.EnumSensorType.Photometric
        elif sensor_type == "colorimetric":
            self.speos_object.SensorType = self.speos_sim.SensorIntensity.EnumSensorType.Colorimetric
        elif sensor_type == "radiometric":
            self.speos_object.SensorType = self.speos_sim.SensorIntensity.EnumSensorType.Radiometric
        elif sensor_type == "spectral":
            self.speos_object.SensorType = self.speos_sim.SensorIntensity.EnumSensorType.Spectral
        else:
            error_message = "Unsupported sensor type. Supported types: photometric, colorimetric, radiometric, spectral."
            raise ValueError(error_message)

    def set_wavelength(self, w_start=None, w_end=None, w_sampling=None, w_resolution=None):
        if not w_start and not w_end and not w_sampling and not w_resolution:
            raise NameError("No inputs provided.")
        if w_start:
            self.speos_object.WavelengthStart = w_start
        if w_end:
            self.speos_object.WavelengthEnd = w_end
        if w_sampling:
            self.speos_object.WavelengthNbSamples = w_sampling
        if w_resolution:
            self.speos_object.WavelengthResolution = w_resolution

    def set_layer(self, layer_type):
        layer_type = layer_type.lower()
        if layer_type == "source":
            self.speos_object.LayerType = self.speos_sim.SensorIntensity.EnumLayerType.Source
        elif layer_type == "face":
            self.speos_object.LayerType = self.speos_sim.SensorIntensity.EnumLayerType.Face
        elif layer_type == "sequence":
            self.speos_object.LayerType = self.speos_sim.SensorIntensity.EnumLayerType.Sequence
        elif layer_type == "none":
            self.speos_object.LayerType = self.speos_sim.SensorIntensity.EnumLayerType.None
        else:
            error_message = "Unsupported layer type. Supported types: source, face, sequence, none."
            raise ValueError(error_message)
