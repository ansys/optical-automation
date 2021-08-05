##################################################################
# Sync SPEOS Materials from Layers V1  - Copyright ANSYS. All Rights Reserved.
# ##################################################################
# CREATION:      2021.02.16
# VERSION:       1.1.0
#
# OVERVIEW
# ========
# This script is generated for showing scripting capabilities purpose.
# It will perform following action:
#     1. Synchronizes the geometries that are assigned to layers with the Speos materials list
#
# Example usage:
#       Action = SynchLayersMaterials(SpeosSim, SpaceClaim)
#       Action.sync_op_from_layers()
#
# ##################################################################
# ANSYS  script is provided as is, without. ANSYS  assumes neither
# warranty, nor guarantee nor any other liability of any kind for the contents
# of the provided script.
# The tool has been prepared for training and demonstration purpose, but may in
# reality not fulfill entirely to your purpose. User is free to modify by its own
# the following script.

# Therefore, ANSYS assumes no liability of any kind for the loss of data or
# any other damage resulting from the usage of the provided data.
# ANSYS OPTIS reserves the right to undertake technical changes without further
# notification which could lead to changes in the provided data.

# The user agrees to this disclaimer and user agreement with the download or usage
# of the provided files.

# ##################################################################

# Python Script, API Version = V20 Beta

import clr
from SPEOS_scripts.SpaceClaimCore.base import BaseSCDM


class SynchLayersMaterials(BaseSCDM):
    def __init__(self, SpeosSim, SpaceClaim):
        super(SynchLayersMaterials, self).__init__(SpaceClaim, ["V19", "V20", "V21"])
        self.speos_sim = SpeosSim

    def __create_dictionary_from_layers(self):
        dic = {}
        root_part = self.GetRootPart()
        all_bodies = self.PartExtensions.GetAllBodies(root_part)
        for item in all_bodies:
            if "DesignBodyGeneral" in str(item.GetType()):
                layer_name = item.Master.Layer.Name
            else:
                layer_name = item.Layer.Name
            if layer_name not in dic:
                dic.update({layer_name: self.List[self.IDesignBody]()})
            dic[layer_name].Add(item)
        return dic

    def __get_op_list(self):
        op_list = []
        cs = self.GetRootPart().CustomObjects
        for item in cs:
            if self.speos_sim.Material.Find(item.Name):
                op_list.append(item.Name)
        return op_list

    def __clean_geo_op_list(self, op_list):
        for item in op_list:
            op = self.speos_sim.Material.Find(item)
            op.VolumeGeometries.Clear()

    def sync_op_from_layers(self):
        op_list = self.__get_op_list()
        dic = self.__create_dictionary_from_layers()
        self.__clean_geo_op_list(op_list)
        for item in dic:
            if item not in op_list:
                op_created = self.speos_sim.Material.Create()
                op_created.Name = item
                sel = self.Selection.Create(dic[item])
                op_created.VolumeGeometries.Set(sel.Items)
            else:
                op = self.speos_sim.Material.Find(item)
                sel = self.Selection.Create(dic[item])
                op.VolumeGeometries.Set(sel.Items)
