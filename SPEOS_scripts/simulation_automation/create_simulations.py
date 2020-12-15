# Copyright (C) 2020 ANSYS, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

# IMPORTANT!!!
# Use API V20 Beta !!!

import sys
SCDM_VERSION = 211
API_VERSION = "V20"

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
        super(Simulation, self).__init__(SpaceClaim, ["V19", "V20"])
        self.PreProcASP = PreProcessingASP(SpaceClaim)
        self.speos_sim = SpeosSim
        self.name = name
        self.kind = kind
        self.rays = 10
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
        #print(component_list)
        root = self.GetRootPart()
        all_components = root.GetDescendants[self.IComponent]()
        #print(all_components)
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
        all_parts = self.GetRootPart().GetDescendants[self.IPart]()

        for one_part in all_parts:
            part_geosets = self.PreProcASP._PreProcessingASP__create_geometrical_set_names_list(one_part)
            for geoset in geosets_list:
                if geoset in part_geosets:
                    part_geosets_dict = self.PreProcASP._PreProcessingASP__convert_list_to_dict(one_part)
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
        self.object.Geometries.Set(selection)
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
            pass
        elif self.kind == "inverse":  # inverse simulation
            self.object.NbPassesLimit = rays
        elif self.kind == "interactive":  # interactive simulation
            self.object.RayNumber = rays
        return self
    
    def run_simulation(self):     
        """
     Computes simulation
     """
        self.object.Compute()
