##################################################################
# create_simulations  - Copyright ANSYS. All Rights Reserved.
# ##################################################################
# CREATION:      2021.08.17
# VERSION:       1.0.0
#
# OVERVIEW
# ========
# This script is generated for showing scripting capabilities purpose.
# It contains a class with methods to create and modify Speos simulations.
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
from scdm_scripts.cad_data_postprocessing.preprocessinglibrary import PreProcessingASP
from SPEOS_scripts.SpaceClaimCore.base import BaseSCDM


class Simulation(BaseSCDM):
    def __init__(self, name, SpeosSim, SpaceClaim, kind="inverse"):
        """
        Initialize Simulation class. Takes name as input and searches for an
        existing simulation with this name.
        param name: name of the simulation to look for.
        param kind: kind/type of the simulation: either "inverse" or "direct"
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
            # throw an error: unknown simulation type
            pass

        self.my_bodies = []

    def select_geometries(self, component_list):
        """
        adds all geometries from components provided in component_list to the simulation's bodies list
        param component_list: list with component names, e.g. ["part1", "part2"]
        :return:
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
        adds all geometries from geometrical sets provided in geosets_list to
        the simulation's bodies list
        param component_geosets_listlist: list with names of geometrical sets to add,
        e.g. ["geo_set1", "geo_set2"]
        :return:
        """
        part_geosets = self.PreProcASP._PreProcessingASP__create_geometrical_set_names_list(self.GetRootPart(),
                                                                                 bodies_only=False)
        for geoset in geosets_list:
            if geoset in part_geosets:
                part_geosets_dict = self.PreProcASP._PreProcessingASP__convert_list_to_dict(self.GetRootPart(),
                                                                                    bodies_only=False)
                bodies = part_geosets_dict[geoset]
                self.my_bodies.extend(bodies)
        return self

    def define_geometries(self):
        """
        Adds all bodies from the simulation's bodies list (self.my_bodies) to the
        simulation geometries.
        param:
        :return:
        """
        selection = self.BodySelection.Create(self.my_bodies)
        self.object.Geometries.Set(selection.Items)
        return self

    def set_rays_limit(self, rays):
        """
        Set computation limit by the maximum number of rays (for direct and inverse simulations)
        or passes (for inverse simulations)
        param rays: the number of rays/passes to set the limit of simulation to
        :return:
        """
        self.rays = rays
        if self.kind == "direct":  # direct simulation
            self.object.NbRays = rays
        elif self.kind == "inverse":  # inverse simulation
            self.object.NbPassesLimit = rays
        #elif self.kind == "interactive":  # interactive simulation
        #    self.object.RayNumber = rays
        return self

    def export_grid(self, sensor_name, save_name):
        # export projected grid as a component
        grid_name = ".".join([self.name, sensor_name, "OPTProjectedGrid"])
        print(grid_name)
        if self.kind == "interactive" and self.computed:
            projected_grid = self.speos_sim.ResultProjectedGrid.Find(grid_name)
            print(projected_grid)
            projected_grid.ExportProjectedGridAsGeometry()
        return self

    def save_grid(self, sensor_name, save_name):
        """
        # TODO save components in the main script in spaceclaim
        """
        grid_name = ".".join([self.name, sensor_name, "OPTProjectedGrid", "CATPart"])
        # find the created component
        components = self.PreProcASP.find_component("Projected grid_")
        component = components[len(components) - 1]
        # save the created component as CATPart
        # grid_name = "Projected grid_"
        #self.ComponentHelper.ImportComponentGroups(component)
        self.Copy.ToClipboard(self.Selection.Create(component))
        self.CreateNewDocument()
        self.Paste.FromClipboard()
        # options = ExportOptions.Create()
        self.DocumentSave.Execute(grid_name)
        self.CloseDocument()

        # delete the created component
        # result = self.Delete.Execute(self.Selection.Create(component))
        return self

    def set_grid_params(self, primary_step=20, secondary_step=4, max_distance=1500,
                        max_incidence=89, min_distance=2):
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
        """
        Computes simulation
        """
        self.object.Compute()
        self.computed = True
        return self

    def add_sensor(self, sensor_name):
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
