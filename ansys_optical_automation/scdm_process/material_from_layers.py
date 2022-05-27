# Python Script, API Version = V21

from ansys_optical_automation.scdm_core.base import BaseSCDM


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
                op_type = self.speos_sim.Material.Find(item.Name).OpticalPropertiesType.ToString()
                if "Surfacic" not in op_type:
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
