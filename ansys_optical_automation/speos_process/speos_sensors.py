import os

from ansys_optical_automation.scdm_core.base import BaseSCDM


class Sensor(BaseSCDM):
    """
    Provides the parent class for all Speos sensor types.

    This class contains methods and properties that are common to all sensor types.
    It shouldn't be used by itself. Subclasses should be used instead.
    """

    def __init__(self, name, SpeosSim, SpaceClaim):
        """
        Initialize the base sensor object.

        The base sensor object has a name and some other attributes that are common to all
        Speos sensors. It does not have a Speos sensor object and cannot be used by
        simulations as is.

        This is an abstract class.

        Parameters
        ----------
        name : str
            Name of the sensor to create or find.
        SpeosSim : SpeosSim
            SpeosSim.
        SpaceClaim : SpaceClaim object
            SpaceClaim object.
        """
        super(Sensor, self).__init__(
            SpaceClaim, ["V19", "V20", "V21", "V22", "V23", "V231", "V232", "V241", "V242", "V251"]
        )
        self.name = name
        self.speos_sim = SpeosSim
        self.speos_object = None
        self.axes = None
        self.origin = None

    def find_axes(self, origin=None):
        """
        Find a component with the same name as the sensor, look in it for an axis system and
        an origin point (if available), and save them as properties in self.

        Parameters
        ----------
        origin : SpaceClaim curve object, optional
            Name of the origin point to use for sensor positioning. For example, ``origin="EPP_195"``.
            This point must exist under ``Curves`` in the component of the same name as the sensor.
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
        Set the origin and x and y directions of the sensor.

        For some intensity sensors, set the origin and polar-axis and V0/H0-axis.

        Parameters
        ----------
        x_reverse : bool, optional
            Whether to reverse the direction of the X-axis of the sensor. The default is ``False``.
        y_reverse : bool, optional
            Whether to reverse the direction of the Y-axis of the sensor. The default is ``False``.
        origin : text or integer, optional
            SpaceClaim axis system or a point. The default is ``None``.
        axes : list, optional
            List in the format ``[x-axis, y-axis]`` that defines the orientation of the axis, where
            ``x-axis`` and ``y-axis`` are SCDM axis objects (not an axis system). For IESNA and
            Elumdat intensity sensors, provide the polar-axis and V0/H0-axis instead.
        """
        if not self.speos_object:  # if self.speos_object (speos sensor speos_object) is not defined
            raise TypeError("No Speos object is defined.")

        if not (self.axes and self.origin) and not (axes and origin):  # if axes and/or origin not defined/provided
            raise NameError(
                "Axes or origin are not defined. Use the find_axes method or provide axes or origin as input."
            )

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
    Provides methods for defining the Speos camera sensor.
    """

    def __init__(self, name, SpeosSim, SpaceClaim):
        """
        Searches for a Speos camera sensor in the simulation tree. If the specified name is not found, a new
        Speos camera sensor is created with this name.

        Parameters
        ----------
        name : str
            Name of the sensor to find or create.
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
        distortion_file_name : str
            Name of the OPT distortion file.
        """
        distortion_path = os.path.join(".", "SPEOS input files", distortion_file_name)
        self.speos_object.DistorsionFile = distortion_path
        return self

    def set_transmittance(self, transmittance_file_name):
        """
        Parameters
        ----------
        transmittance_file_name : str
            Name of the transmittance spectrum file.
        """
        transmittance_path = os.path.join(".", "SPEOS input files", transmittance_file_name)
        self.speos_object.TransmittanceFile = transmittance_path
        return self

    def set_sensitivity(self, color, sensitivity_file_name):
        """
        Parameters
        ----------
        color : str
            Channel color. Options are ``"red"``, ``"green"``, and ``"blue"``.
        sensitivity_file_name : str
            Name of the sensitivity file.
        """
        sensitivity_path = os.path.join(".", "SPEOS input files", sensitivity_file_name)
        color = color.lower()
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
    Provides methods for the Speos intensity sensor.
    """

    def __init__(self, name, SpeosSim, SpaceClaim):
        """
        Searches for a Speos intensity sensor in the simulation tree. If the specified name is
        not found, a new Speos intensity sensor is created with this name.

        Parameters
        ----------
        name : str
            Name of the sensor to find or create.
        SpeosSim : SpeosSim
            SpeosSim.
        SpaceClaim : SpaceClaim object
            SpaceClaim object.
        """
        super(IntensitySensor, self).__init__(name, SpeosSim, SpaceClaim)
        speos_object = self.speos_sim.SensorIntensity.Find(self.name)
        if not speos_object:
            speos_object = self.speos_sim.SensorIntensity.Create()
            speos_object.Name = name
        self.speos_object = speos_object
        self.sensor_format = None

    def set_format(self, sensor_format=None):
        """
        Set the sensor format.

        Parameters
        ----------
        sensor_format : str
            Format of the sensor. Options are ``"XMP"``, ``"IESNATypeA"``, ``"IESNATypeB"``,
            ``"IESNATypeC"``, and ``"Eulumdat"``.
        """
        if not sensor_format:
            raise NameError("Format input not provided.")
        self.sensor_format = sensor_format.lower()
        if self.sensor_format == "xmp":
            self.speos_object.FormatType = self.speos_sim.SensorIntensity.EnumFormatType.XMP
        elif self.sensor_format == "iesnatypea":
            self.speos_object.FormatType = self.speos_sim.SensorIntensity.EnumFormatType.IESNATypeA
        elif self.sensor_format == "iesnatypeb":
            self.speos_object.FormatType = self.speos_sim.SensorIntensity.EnumFormatType.IESNATypeB
        elif self.sensor_format == "iesnatypec":
            self.speos_object.FormatType = self.speos_sim.SensorIntensity.EnumFormatType.IESNATypeC
        elif self.sensor_format == "eulumdat":
            self.speos_object.FormatType = self.speos_sim.SensorIntensity.EnumFormatType.Eulumdat
        else:
            raise ValueError("Wrong input value. Choose from XMP, IESNATypeA, IESNATypeB, IESNATypeC or Eulumdat.")

    def set_range(self, x_start=None, x_end=None, y_start=None, y_end=None, x_mirrored=False, y_mirrored=False):
        """
        Set the sensor size.

        Parameters
        ----------
        x_start : int or float, optional
            X size of the sensor in millimeters for the positive part.
            The default is ``None``.
        x_end : int or float, optional
            X size of the sensor in millimeters for the negative part.
            The default is ``None``.
        y_start : int of float, optional
            Y size of the sensor in millimeters for the positive part.
            The default is ``None``.
        y_end : int or float, optional
            Y size of the sensor in millimeters for the negative part.
            The default is ``None``.
        x_mirrored : bool, optional
            Mirrored extend option of the X size of the sensor.
            The default is ``False``.
        y_mirrored : bool, optional
            Mirrored extend option of the Y size of the sensor.
            The default is ``False``.
        """
        if not all([x_start, x_end, y_start, y_end]):
            raise NameError("No inputs are provided.")
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
        """Set the number of samples on the axes.

        Parameters
        ----------
        x_sampling : int, optionl
            Number of samples on the X-axis. The default is ``None``.
        y_sampling : int
            Number of samples on the Y-axis. The default is ``None``.
        """
        if not x_sampling and not y_sampling:
            raise NameError("No inputs provided.")
        if x_sampling:
            self.speos_object.XNbSamples = x_sampling
        if y_sampling:
            self.speos_object.YNbSamples = y_sampling

    def set_resolution(self, x_resolution=None, y_resolution=None):
        """
        Set the resolution of the sensor.

        Parameters
        ----------
        x_resolution : int, optional
            X resolution of the sensor in millimeters. The default is ``None``.
        y_resolution : int, optional
            Y resolution of the sensor in millimeters. The default is ``None``.
        """
        if not x_resolution and not y_resolution:
            raise NameError("No inputs are provided.")
        if x_resolution:
            self.speos_object.XResolution = x_resolution
        if y_resolution:
            self.speos_object.YResolution = y_resolution

    def set_type(self, sensor_type):
        """Set the sensor type.

        Parameters
        ----------
        sensor_type : str
            Type of the sensor. Options are ``"photometric"``, ``"colorimetric"``, ``"radiometric"``
            and ``"spectral"``.
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
        """Set the wavelength of the sensor.

        Parameters
        ----------
        w_start : int, optional
            Start of the wavelength band in nanometers. The default is ``None``.
        w_end : int, optional
            End of the wavelength band in nanometers. The default is ``None``.
        w_sampling : int, optional
            Number of spectral samples. The default is ``None``.
        w_resolution : float, optional
            Spectral sampling or resolution (size of one sample) in nanometers.
            The default is ``None``.
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
        """Set the layer type of the sensor.

        Parameters
        ----------
        layer_type : str
            Layer type of the sensor. Options are ``"source"``, ``"face"``, ``"sequence"``,
            and ``"none"``.
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

    def set_integration_angle(self, integration_value):
        """
        set integration angle of the radiance sensor

        Parameters
        ----------
        integration_value
        """
        if self.sensor_format == "xmp" or self.sensor_format is None:
            raise ValueError("Cannot assign integration values")
        else:
            self.speos_object.IntegrationAngle = integration_value


class RadianceSensor(Sensor):
    """
    Provides methods for the Speos Radiance sensor.
    """

    def __init__(self, name, SpeosSim, SpaceClaim):
        """
        Searches for a Speos Radiance sensor in the simulation tree. If the specified name is
        not found, a new Speos Radiance sensor is created with this name.

        Parameters
        ----------
        name : str
            Name of the sensor to find or create.
        SpeosSim : SpeosSim
            SpeosSim.
        SpaceClaim : SpaceClaim object
            SpaceClaim object.
        """
        super(RadianceSensor, self).__init__(name, SpeosSim, SpaceClaim)
        speos_object = self.speos_sim.SensorRadiance.Find(self.name)
        if not speos_object:
            speos_object = self.speos_sim.SensorRadiance.Create()
            speos_object.Name = name
        self.speos_object = speos_object

    def set_focal_value(self, focal_value):
        """
        Set focal value of the radiance sensor

        Parameters
        ----------
        focal_value : float
        """
        opt_sensor_type = self.speos_object.ObserverType.ToString()
        if opt_sensor_type == "Observer":
            error_message = "current radiance sensor observer type is not set to be focal"
            raise ValueError(error_message)
        else:
            self.speos_object.Focal = focal_value

    def set_type(self, sensor_type):
        """
        set type of the radiance sensor

        Parameters
        ----------
        sensor_type : str
        """
        sensor_type = sensor_type.lower()
        if sensor_type == "photometric":
            self.speos_object.SensorType = self.speos_sim.SensorRadiance.EnumSensorType.Photometric
        elif sensor_type == "radiometric":
            self.speos_object.SensorType = self.speos_sim.SensorRadiance.EnumSensorType.Radiometric
        elif sensor_type == "colorimetric":
            self.speos_object.SensorType = self.speos_sim.SensorRadiance.EnumSensorType.Colorimetric
        elif sensor_type == "spectral":
            self.speos_object.SensorType = self.speos_sim.SensorRadiance.EnumSensorType.Spectral
        else:
            error_message = "please provide a valid radiance sensor type"
            raise ValueError(error_message)

    def set_layer(self, layer_type):
        """
        set the layer type of the radiance sensor

        Parameters
        ----------
        layer_type : str
        """
        layer_type = layer_type.lower()
        if layer_type == "source":
            self.speos_object.LayerType = self.speos_sim.SensorRadiance.EnumLayerType.Source
        elif layer_type == "face":
            self.speos_object.LayerType = self.speos_sim.SensorRadiance.EnumLayerType.Face
        elif layer_type == "sequence":
            self.speos_object.LayerType = self.speos_sim.SensorRadiance.EnumLayerType.Sequence
        elif layer_type == "none":
            self.speos_object.LayerType = getattr(self.speos_sim.SensorRadiance.EnumLayerType, "None")
        else:
            error_message = "please provide a valid radiance layer type"
            raise ValueError(error_message)

    def set_observer_type(self, observer_type):
        """
        set observer type of the radiance sensor

        Parameters
        ----------
        observer_type : str
        """
        observer_type = observer_type.lower()
        if observer_type == "observer":
            self.speos_object = self.speos_sim.SensorRadiance.EnumObserverType.Observer
        elif observer_type == "focal":
            self.speos_object = self.speos_sim.SensorRadiance.EnumObserverType.Focal
        else:
            error_message = "please provide a radiance type as observer or focal"
            raise ValueError(error_message)

    def set_definition_type(self, definition_type):
        """
        set radiancec sensor definition type.

        Parameters
        ----------
        definition_type : str
            type as observer or frame

        Returns
        -------


        """
        definition_type = definition_type.lower()
        if definition_type.lower() == "observer":
            self.speos_object.DefinitionFrom = self.speos_sim.SensorRadiance.EnumDefinitionFrom.Observer
        elif definition_type.lower() == "frame":
            self.speos_object.DefinitionFrom = self.speos_sim.SensorRadiance.EnumDefinitionFrom.Frame
        else:
            error_message = "please provide a radiance type as observer or frame"
            raise ValueError(error_message)

    def set_xmp_template(self, xml_file, take_dimension=False, take_display=False):
        """
        set the xmp template.

        Parameters
        ----------
        xml_file : str
            path of xml file
        take_dimension : bool
            True if setting of dimension used from xml, otherwise False
        take_display : bool
            True if setting of XMP display used from xml, otherwise False

        Returns
        -------


        """
        if os.path.isfile(xml_file):
            self.speos_object.XMPTemplateFile = xml_file
        else:
            msg = "Provided XML file is not found"
            raise ValueError(msg)

        if take_dimension:
            self.speos_object.DimensionFromFile = True
        if take_display:
            self.speos_object.DisplayPropertiesFromFile = True

    def set_range(self, x_start=None, x_end=None, y_start=None, y_end=None, x_mirrored=False, y_mirrored=False):
        """
        Set the sensor size.

        Parameters
        ----------
        x_start : int or float, optional
            X size of the sensor in millimeters for the positive part.
            The default is ``None``.
        x_end : int or float, optional
            X size of the sensor in millimeters for the negative part.
            The default is ``None``.
        y_start : int of float, optional
            Y size of the sensor in millimeters for the positive part.
            The default is ``None``.
        y_end : int or float, optional
            Y size of the sensor in millimeters for the negative part.
            The default is ``None``.
        x_mirrored : bool, optional
            Mirrored extend option of the X size of the sensor.
            The default is ``False``.
        y_mirrored : bool, optional
            Mirrored extend option of the Y size of the sensor.
            The default is ``False``.
        """
        if not all([x_start, x_end, y_start, y_end]):
            raise NameError("No inputs are provided.")
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

    def set_sampling(self, x_sampling, y_sampling):
        """
        set x and y sampling of the radiance sensor

        Parameters
        ----------
        x_sampling : int
        y_sampling : int
        """
        self.speos_object.XNbSamples = x_sampling
        self.speos_object.YNbSamples = y_sampling

    def set_resolution(self, x_resolution, y_resolution):
        """
        set x and y resolution of the radiance sensor

        Parameters
        ----------
        x_resolution
        y_resolution
        """
        self.speos_object.XResolution = x_resolution
        self.speos_object.YResolution = y_resolution

    def set_wavelength_resolution(self, resolution):
        """
        set wavelength resolution of the radiance sensor

        Parameters
        ----------
        resolution : float
        """
        opt_sensor_type = self.speos_object.SensorType.ToString()
        if opt_sensor_type != "Colorimetric" and opt_sensor_type != "Spectral":
            error_message = "current radiance sensor type does not have Wavelength attribute"
            raise ValueError(error_message)
        if resolution >= 100:
            error_message = "resolution not recommended"
            raise ValueError(error_message)
        else:
            self.speos_object.WavelengthResolution = resolution

    def set_integration_angle(self, integration_value):
        """
        set integration angle of the radiance sensor

        Parameters
        ----------
        integration_value
        """
        self.speos_object.IntegrationAngle = integration_value

    def set_observer_point(self, observer_point):
        """
        set observer point of the radiance sensor (Definition from Observer)

        Parameters
        ----------
        observer_point : point or origin (coordinate system)
        """
        self.speos_object.ObserverPoint.Set(observer_point)

    def set_observer_directions(self, front_direction, top_direction):
        """
        set front and top directions of the radiance sensor (Definition from Observer)

        Parameters
        ----------
        front_direction : axis or line
        top_direction : axis or line
        """
        self.speos_object.FrontDirection.Set(front_direction)
        self.speos_object.TopDirection.Set(top_direction)

    def set_fov(self, horizontal_fov, vertical_fov, horizontal_sampling, vertical_sampling):
        """
        set field of view and sampling of the radiance sensor (Definition from Observer)

        Parameters
        ----------
        horizontal_fov : float
        vertical_fov : float
        horizontal_sampling : float
        vertical_sampling : float
        """
        self.speos_object.HPlane = horizontal_fov
        self.speos_object.VPlane = vertical_fov
        self.speos_object.HNbSamples = horizontal_sampling
        self.speos_object.VNbSamples = vertical_sampling
