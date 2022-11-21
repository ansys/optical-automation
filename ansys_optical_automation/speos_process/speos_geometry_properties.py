from ansys_optical_automation.scdm_core.base import BaseSCDM


class GeometryProperties(BaseSCDM):
    """
    Provides the parent class for all Speos Geometry properties types.

    This class contains methods and properties that are common to all geometry properties elements.
    It shouldn't be used by itself. Subclasses should be used instead.
    """

    def __init__(self, name, SpeosSim, SpaceClaim):
        super(BaseSCDM, self).__init__(SpaceClaim, ["V19", "V20", "V21", "V22", "V23"])
        self.speos_sim = SpeosSim
        self.name = name
        self.speos_object = None
        self.geometries_list = []

    def set_geometries(self, geometries):
        """
        set geometries, e.g. bodies and faces, to Speos geometry properties.

        Parameters
        ----------
        geometries : list
            a list of SCDM bodies and faces

        Returns
        -------


        """
        if len(self.geometries_list) == 0:
            selection = self.Selection.Create(geometries)
            self.speos_object.Geometries.Set(selection.Items)
        else:
            self.geometries_list.extend(geometries)
            selection = self.Selection.Create(self.geometries_list)
            self.speos_object.Geometries.Set(selection.Items)


class LocalMeshing(GeometryProperties):
    """
    Provides methods for defining the Speos LocalMeshing.
    """

    def __init__(self, name, SpeosSim, SpaceClaim):
        super(LocalMeshing, self).__init__(name, SpeosSim, SpaceClaim)
        if self.speos_sim.LocalMeshing.Find(name):
            self.speos_object = self.speos_sim.LocalMeshing.Find(name)
            for item in self.speos_object.Geometries.LinkedObjects:
                self.geometries_list.append(item)
        else:
            self.speos_object = self.speos_sim.LocalMeshing.Create()
            self.speos_object.Name = name

    def set_sag(self, sag_mode, sag_value):
        """
        Define Sag Mode and apply a value on it.
        Parameters
        ----------
        sag_mode : str
        In Sag Meshing, 3 kind of modes are available.

        sag_value : float
        Meshing value. Depending of sag_mode value, sag_value might be an int or a float.

        Returns
        -------


        """
        sag_mode = sag_mode.lower()
        if sag_mode == "proportional to face size":
            self.speos_object.MeshingSagMode = self.speos_sim.LocalMeshing.EnumMeshingSagMode.ProportionalFace
            float(sag_value)
            self.speos_object.MeshingSagValue = sag_value
        elif sag_mode == "proportional to body size":
            self.speos_object.MeshingSagMode = self.speos_sim.LocalMeshing.EnumMeshingSagMode.ProportionalBody
            float(sag_value)
            self.speos_object.MeshingSagValue = sag_value
        elif sag_mode == "fixed":
            self.speos_object.MeshingSagMode = self.speos_sim.LocalMeshing.EnumMeshingSagMode.Fixed
            float(sag_value)
            self.speos_object.MeshingSagValue = sag_value
        else:
            error_message = "please provide a valid Sag Mode"
            raise ValueError(error_message)

    def set_step(self, step_mode, step_value):
        """
        Define step values for local meshing.

        Parameters
        ----------
        step_mode : str
            step mode
        step_value : float
            step value

        Returns
        -------


        """
        step_mode = step_mode.lower()
        if step_mode == "proportional to face size":
            self.speos_object.MeshingStepMode = self.speos_sim.LocalMeshing.EnumMeshingStepMode.ProportionalFace
            float(step_value)
            self.speos_object.MeshingStepValue = step_value
        elif step_mode == "proportional to body size":
            self.speos_object.MeshingStepMode = self.speos_sim.LocalMeshing.EnumMeshingStepMode.ProportionalBody
            float(step_value)
            self.speos_object.MeshingStepValue = step_value
        elif step_mode == "fixed":
            self.speos_object.MeshingStepMode = self.speos_sim.LocalMeshing.EnumMeshingStepMode.Fixed
            float(step_value)
            self.speos_object.MeshingStepValue = step_value
        else:
            error_message = "please provide a valid Sag Mode"
            raise ValueError(error_message)


class UVMapping(GeometryProperties):
    """
    Provides methods for defining the Speos UVMapping.
    """

    def __init__(self, name, SpeosSim, SpaceClaim):
        super(UVMapping, self).__init__(name, SpeosSim, SpaceClaim)
        if self.speos_sim.LocalMeshing.Find(name):
            self.speos_object = self.speos_sim.UVMapping.Find(name)
            for item in self.speos_object.Geometries.LinkedObjects:
                self.geometries_list.append(item)
        else:
            self.speos_object = self.speos_sim.UVMapping.Create()
            self.speos_object.Name = name
