##################################################################
# materials_from_layers  - Copyright ANSYS. All Rights Reserved.
# ##################################################################
# CREATION:      2021.08.17
# VERSION:       1.0.0
#
# OVERVIEW
# ========
# This script is generated for showing scripting capabilities purpose.
# It contains a class with methods for synchronizing Speos materials with SCDM layers.
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
