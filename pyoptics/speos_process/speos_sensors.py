# Python Script, API Version = V21

import os

from pyoptics.scdm_core.base import BaseSCDM


class Sensor(BaseSCDM):
    """
    This is the parent class for all Speos sensor types.
    It contains methods and properties that are mutual for all sensor types.

    This class shouldn't be used by itself, instead subclasses should be used!
    """

    def __init__(self, name, SpeosSim, SpaceClaim):
        """
        Initializes the base Sensor object. This object has a name and some other attributes that are mutual for all
        Speos sensors, but doesn't have a Speos Sensor object and can't be used by simulations as is.

        This is an abstract class.

        Parameters
        ----------
        name: name of the Sensor to be created or found.
        SpeosSim
        SpaceClaim
        """
        super(Sensor, self).__init__(SpaceClaim, ["V19", "V20", "V21"])
        self.name = name
        self.speos_sim = SpeosSim
        self.speos_object = None
        self.axes = None
        self.origin = None

    def find_axes(self, origin=None):
        """
        This method finds a component with the same name as the sensor itself and looks for an axis system and
        an origin point (if available) in it, and saves them as properties in self.

        Parameters
        ----------
        origin: name of the origin point to be used for sensor positioning. Example: origin="EPP_195". This point must
        exist under Curves in the Component of the same name as the Sensor.
        """
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
        """
        This method sets the origin and x and y directions (polar and H0 axes for some intensity sensors) of
        the sensor.

        Parameters
        ----------
        x_reverse: bool. True of False to reverse direction of the X-axis of the sensor
        y_reverse: bool. True of False to reverse direction of the Y-axis of the sensor
        origin: Here a compatible SCDM object can be provided: and axis system or a point.
        axes: list with [x-axis, y-axis] to define orientation of the axis, where x-axis and y-axis are SCDM axis
              objects (not an axis system!). In case of IESNA and Elumdat intensity sensors,
              [polar-axis, and V0/H0-axis] should be provided instead.
        """
        if not self.speos_object:  # if self.speos_object (speos sensor speos_object) is not defined
            raise TypeError("No Speos object defined.")

        if not (self.axes and self.origin) and not (axes and origin):  # if axes and/or origin not defined/provided
            raise NameError("Axes or origin not defined. Use find_axes method or provide axes and origin as input.")

        if not (axes and origin):  # If no inputs provided, use self.axes and self.origin
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
    """
    This class implements methods for the Speos camera sensor definition.
    """

    def __init__(self, name, SpeosSim, SpaceClaim):
        """
        Searches for a Speos Camera sensor with the specified name in the simulation tree. If it is not found, a new
        Speos Camera is created with the specified name.

        Parameters
        ----------
        name: str. Name of the sensor to find/create.
        """
        super(Camera, self).__init__(name, SpeosSim, SpaceClaim)
        speos_object = self.speos_sim.SensorCamera.Find(self.name)
        if not speos_object:  # if camera doesn't exist -> create a new camera
            speos_object = self.speos_sim.SensorCamera.Create()
            speos_object.Name = name
        self.speos_object = speos_object

    def set_distortion(self, distortion_file_name):
        """
        Parameters
        ----------
        distortion_file_name: str. Name of the OPTDistortion file.

        """
        distortion_path = os.path.join(".", "SPEOS input files", distortion_file_name)
        self.speos_object.DistorsionFile = distortion_path
        return self

    def set_transmittance(self, transmittance_file_name):
        """
        Parameters
        ----------
        transmittance_file_name: str. Name of the transmittance spectrum file.
        """
        transmittance_path = os.path.join(".", "SPEOS input files", transmittance_file_name)
        self.speos_object.TransmittanceFile = transmittance_path
        return self

    def set_sensitivity(self, color, sensitivity_file_name):
        """
        Parameters
        ----------
        color: str. Channel color: red, green or blue.
        sensitivity_file_name: str. Name of the sensitivity file.
        """
        sensitivity_path = os.path.join(".", "SPEOS input files", sensitivity_file_name)
        if color == "red":
            self.speos_object.RedSpectrumFile = sensitivity_path
        elif color == "green":
            self.speos_object.GreenSpectrumFile = sensitivity_path
        elif color == "blue":
            self.speos_object.BlueSpectrumFile = sensitivity_path
        return self

    # TODO: color mode.
    #  Camera1.ColorMode = SpeosSim.SensorCamera.EnumColorMode.Monochromatic
    #  Camera1.ColorMode = SpeosSim.SensorCamera.EnumColorMode.Color

    # TODO: set sensitivity for monochrome sensor. Camera1.SpectrumFile


class IntensitySensor(Sensor):
    """
    This class implements methods for the Speos intensity sensor.
    """

    def __init__(self, name, SpeosSim, SpaceClaim):
        """
        Searches for a Speos Intensity sensor with the specified name in the simulation tree. If it is not found, a new
        Speos Intensity sensor is created with the specified name.

        Parameters
        ----------
        name: str. Name of the sensor to find/create.
        """
        super(IntensitySensor, self).__init__(name, SpeosSim, SpaceClaim)
        speos_object = self.speos_sim.SensorIntensity.Find(self.name)
        if not speos_object:
            speos_object = self.speos_sim.SensorIntensity.Create()
            speos_object.Name = name
        self.speos_object = speos_object

    def set_format(self, sensor_format=None):
        """
        Parameters
        ----------
        sensor_format: str. Can be: XMP, IESNATypeA, IESNATypeB, IESNATypeC or Eulumdat.
        """
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
        """
        Sets the size of the sensor.

        Parameters
        ----------
        x_start: int or float. X size of the sensor in mm. (positive part)
        x_end: int or float. X size of the sensor in mm. (negative part)
        y_start: int of float. Y size of the sensor in mm. (positive part)
        y_end: int or float. Y size of the sensor in mm. (negative part)
        x_mirrored: bool. Mirrored extend option of the X size of the sensor.
        y_mirrored: bool. Mirrored extend option of the Y size of the sensor.
        """
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
        """

        Parameters
        ----------
        x_sampling: int. Number of samples on the x-axis.
        y_sampling: int. Number of samples on the y-axis.
        """
        if not x_sampling and not y_sampling:
            raise NameError("No inputs provided.")
        if x_sampling:
            self.speos_object.XNbSamples = x_sampling
        if y_sampling:
            self.speos_object.YNbSamples = y_sampling

    def set_resolution(self, x_resolution=None, y_resolution=None):
        """
        Sets resolution of the sensor.

        Parameters
        ----------
        x_resolution: int. x-resolution in mm.
        y_resolution: int. y-resolution in mm.
        """
        if not x_resolution and not y_resolution:
            raise NameError("No inputs provided.")
        if x_resolution:
            self.speos_object.XResolution = x_resolution
        if y_resolution:
            self.speos_object.YResolution = y_resolution

    def set_type(self, sensor_type):
        """
        Parameters
        ----------
        sensor_type: str. Sensor type can be one of 4: photometric, colorimetric, radiometric or spectral.
        """
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
            error_message = (
                "Unsupported sensor type. Supported types: photometric, colorimetric, radiometric, spectral."
            )
            raise ValueError(error_message)

    def set_wavelength(self, w_start=None, w_end=None, w_sampling=None, w_resolution=None):
        """
        Parameters
        ----------
        w_start: int. Start of the wavelength band in nm.
        w_end: int. End of the wavelength band in nm.
        w_sampling: int. Number of spectral samples.
        w_resolution: float. Spectral sampling/resolution (size of one sample), in nm.
        """
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
        """
        Parameters
        ----------
        layer_type: str. Layer option of the sensor, can be on of the 4: source, face, sequence, none.
        """
        layer_type = layer_type.lower()
        if layer_type == "source":
            self.speos_object.LayerType = self.speos_sim.SensorIntensity.EnumLayerType.Source
        elif layer_type == "face":
            self.speos_object.LayerType = self.speos_sim.SensorIntensity.EnumLayerType.Face
        elif layer_type == "sequence":
            self.speos_object.LayerType = self.speos_sim.SensorIntensity.EnumLayerType.Sequence
        elif layer_type == "none":
            self.speos_object.LayerType = getattr(self.speos_sim.SensorIntensity.EnumLayerType, "None")
        else:
            error_message = "Unsupported layer type. Supported types: source, face, sequence, none."
            raise ValueError(error_message)
