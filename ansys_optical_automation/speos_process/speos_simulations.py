# Python Script, API Version = V21

from ansys_optical_automation.scdm_core.base import BaseSCDM
from ansys_optical_automation.scdm_process.preprocessing_library import PreProcessingASP


class Simulation(BaseSCDM):
    """
    Provides methods for creating, modifying, and running Speos simulations.
    """

    def __init__(self, name, SpeosSim, SpaceClaim, kind="inverse"):
        """
        Initialize the ``Simulation`` class. Takes name as the input and searches for an
        existing simulation with this name.

        Parameters
        ----------
        name : str
            Name of the simulation to find or create.
        SpeosSim : SpeosSim
            SpeosSim.
        SpaceClaim : SpaceClaim
            SpaceClaim
        kind : str, optional
            Type of the simulation. Options are ``"inverse"``, ``"direct"``, and ``"interactive"``.
        """
        super(Simulation, self).__init__(SpaceClaim, ["V19", "V20", "V21"])
        self.PreProcASP = PreProcessingASP(SpaceClaim)
        self.speos_sim = SpeosSim
        self.name = name
        self.kind = kind
        self.rays = 10
        self.computed = False
        self.grid = None
        if kind == "inverse":
            sim = self.speos_sim.SimulationInverse.Find(name)
            if sim:
                self.object = sim
            else:
                self.object = self.speos_sim.SimulationInverse.Create()
                self.object.Name = name
        elif kind == "direct":
            sim = self.speos_sim.SimulationDirect.Find(name)
            if sim:
                self.object = sim
            else:
                self.object = self.speos_sim.SimulationDirect.Create()
                self.object.Name = name
        elif kind == "interactive":
            sim = self.speos_sim.SimulationInteractive.Find(name)
            if sim:
                self.object = sim
            else:
                self.object = self.speos_sim.SimulationInteractive.Create()
                self.object.Name = name
        else:
            # TODO throw an error: unknown simulation type
            pass

        self.my_bodies = []
        self.component_list = []

    def select_geometries(self, component_list):
        """
        Add all geometries from components provided in a component list to the simulation's list of bodies.

        Parameters
        ----------
        component_list : list
            List with component names. For example, ``["part1", "part2"]``.
        """
        self.component_list = component_list
        root = self.GetRootPart()
        all_components = root.GetDescendants[self.IComponent]()
        for component in all_components:
            if component.Content.Master.DisplayName in self.component_list:
                bodies = component.GetDescendants[self.IDesignBody]()
                self.my_bodies.extend(bodies)
        return self

    def select_geometrical_sets(self, geosets_list):
        """
        Add all geometries from Catia geometrical sets provided in a list to
        the simulation's list of bodies.

        Parameters
        ----------
        geosets_list : list
            List with the names of Catia geometrical sets to add. For example, ``["geo_set1", "geo_set2"]``.
        """
        part_geosets = self.PreProcASP._PreProcessingASP__create_geometrical_set_names_list(
            self.GetRootPart(), bodies_only=False
        )
        for geoset in geosets_list:
            if geoset in part_geosets:
                part_geosets_dict = self.PreProcASP._PreProcessingASP__convert_list_to_dict(
                    self.GetRootPart(), bodies_only=False
                )
                bodies = part_geosets_dict[geoset]
                self.my_bodies.extend(bodies)
        return self

    def define_geometries(self):
        """
        Add all bodies from the simulation's list of bodies (self.my_bodies) to the
        simulation geometries. This works Like the green ``validate`` button in Speos.
        """
        selection = self.BodySelection.Create(self.my_bodies)
        self.object.Geometries.Set(selection.Items)
        return self

    def set_rays_limit(self, rays):
        """
        Set the computation limit by either the maximum number of rays (for direct and inverse simulations)
        or the number passes (for inverse simulations).

        Parameters
        ----------
        rays : int
            Number of rays or passes to set the limit of the simulation to.
        """
        self.rays = rays
        if self.kind == "direct":  # direct simulation
            self.object.NbRays = rays
        elif self.kind == "inverse":  # inverse simulation
            self.object.NbPassesLimit = rays
        # elif self.kind == "interactive":  # interactive simulation
        #    self.object.RayNumber = rays
        return self

    def export_grid(self, sensor_name):
        """
        Export the projected grid as a SpaceClaim component.

        Parameters
        ----------
        sensor_name : str
            Name of the sensor with the grid to import as a geometry.
        """
        grid_name = ".".join([self.name, sensor_name, "OPTProjectedGrid"])
        print(grid_name)
        if self.kind == "interactive" and self.computed:
            projected_grid = self.speos_sim.ResultProjectedGrid.Find(grid_name)
            print(projected_grid)
            projected_grid.ExportProjectedGridAsGeometry()
        return self

    def save_grid(self, sensor_name, save_name):
        """
        # TODO Save components in the main script in SpaceClaim
        """
        grid_name = ".".join([self.name, sensor_name, "OPTProjectedGrid", "CATPart"])
        # find the created component
        components = self.PreProcASP.find_component("Projected grid_")
        component = components[len(components) - 1]
        # save the created component as CATPart
        # grid_name = "Projected grid_"
        # self.ComponentHelper.ImportComponentGroups(component)
        self.Copy.ToClipboard(self.Selection.Create(component))
        self.CreateNewDocument()
        self.Paste.FromClipboard()
        # options = ExportOptions.Create()
        self.DocumentSave.Execute(grid_name)
        self.CloseDocument()

        # delete the created component
        # result = self.Delete.Execute(self.Selection.Create(component))
        return self

    def set_grid_params(self, primary_step=20, secondary_step=4, max_distance=1500, max_incidence=89, min_distance=2):
        """
        Set the parameters of the projected grid for the generated camera.

        Parameters
        ----------
        primary_step : int, optional
            Primary step of the grid. The default is ``20``.
        secondary_step : int, optional
            Secondary step of the grid. The default is ``4``.
        max_distance : float, optional
            Maximum distance between a pixel and the camera in millimeters. The default is ``1500``.
        max_incidence : float, optional
            Maximum angle (degree) under which two projected pixels are to be connected by a line.
            The default is ``89``.
        min_distance : float or int, optional
           Distance tolerance in millimeters for which two adjacent pixels are to be connected
           by a line. The default is ``2``.
        """
        sensor_name = self.object.Sensors[0].Name
        grid_name = self.name + "." + sensor_name + ".OPTProjectedGrid"
        print(grid_name)
        grid = self.speos_sim.ResultProjectedGrid.Find(grid_name)
        if grid:
            self.grid = grid
            grid.SecondaryStep = secondary_step
            grid.PrimaryStep = primary_step
            grid.MaxDistanceFromCamera = max_distance
            grid.MaxIncidence = max_incidence
            grid.MinDistanceTolerance = min_distance
        return self

    def run_simulation(self):
        """Run simulation on the local CPU."""
        self.object.Compute()
        self.computed = True
        return self

    def add_sensor(self, sensor_name):
        """
        Add a sensor to the simulation.

        Parameters
        ----------
        sensor_name : str
            Name of the sensor.
        """
        # camera sensor
        sensor_object = self.speos_sim.SensorCamera.Find(sensor_name)
        if sensor_object:
            self.object.Sensors.Set(sensor_object)
        # radiance sensor
        sensor_object = self.speos_sim.SensorRadiance.Find(sensor_name)
        if sensor_object:
            self.object.Sensors.Set(sensor_object)
        # irradiance sensor
        sensor_object = self.speos_sim.SensorIrradiance.Find(sensor_name)
        if sensor_object:
            self.object.Sensors.Set(sensor_object)
        # intensity sensor
        sensor_object = self.speos_sim.SensorIntensity.Find(sensor_name)
        if sensor_object:
            self.object.Sensors.Set(sensor_object)
        return self
