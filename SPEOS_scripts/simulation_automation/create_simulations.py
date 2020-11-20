# Use API V20 Beta !!!

import sys
SCDM_VERSION = 211
API_VERSION = "V20"

from scdm_scripts.cad_data_postprocessing.preprocessinglibrary import PreProcessingASP
from SPEOS_scripts.SCLib import scdm_api_import as sc


class Simulation:
    def __init__(self, name, SpeosSim, scdm_version, api_version, kind="inverse"):
        """
     Initialize Simulation class. Takes name as input and searches for an 
     existing simulation with this name.
     param name: name of the simulation to look for.
     param kind: kind/type of the simulation: either "inverse" or "direct"
     """
        self.speos_sim = SpeosSim
        self.name = name
        if kind == "inverse":
            self.object = self.speos_sim.SimulationInverse.Find(name)
        elif kind == "direct":
            self.object = self.speos_sim.SimulationDirect.Find(name)
        self.my_bodies = []
        sc.perform_imports(scdm_version, api_version)

    def select_geometries(self, component_list):
        """
     adds all geometries from components provided in component_list to the simulation's bodies list
     param component_list: list with component names, e.g. ["part1", "part2"]
     :return:
     """
        self.component_list = component_list
        root = sc.GetRootPart()
        all_components = root.GetDescendants[sc.IComponent]()
        print(all_components)
        for component in all_components:
            if component.GetName() in self.component_list:
                bodies = component.GetDescendants[sc.IDesignBody]()
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
        all_parts = sc.GetRootPart().GetDescendants[sc.IPart]()
        PreProcASP = PreProcessingASP(SCDM_VERSION, API_VERSION)
        for one_part in all_parts:
            part_geosets = PreProcASP._PreProcessingASP__create_geometrical_set_names_list(one_part)
            for geoset in geosets_list:
                if geoset in part_geosets:
                    part_geosets_dict = PreProcASP._PreProcessingASP__convert_list_to_dict(one_part)
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
        selection = sc.BodySelection.Create(self.my_bodies)
        self.object.Geometries.Set(selection)
        return self
    
    def run_simulation(self):     
        """
     Computes simulation
     """
        self.object.Compute()
       
   

class SimulationInverse(Simulation):
    #def __init__(self, name, SpeosSim):
    #    Simulation.__init__(self, name, SpeosSim)

    def set_n_of_passes(self, passes):
        """
     Sets number of passes for the inverse simulation
     param passes: number of passes to set
     :return:
     """
        self.passes = passes
        self.object.NbPassesLimit = passes
        return self

