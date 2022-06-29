from ansys_optical_automation.scdm_core.base import BaseSCDM


class SynchLayersMaterials(BaseSCDM):
    """Basic that sync information between speos material and CAD layer.

    The class will contain mainly methods to sync information.

    """

    def __init__(self, SpeosSim, SpaceClaim):
        """
        Base class that contains all common used objects. This class serves more as an abstract class.

        Parameters
        ----------
        SpeosSim: SpeosSim object
            SpeosSim.
        SpaceClaim: SpaceClaim object
            SpaceClaim.
        """
        super(SynchLayersMaterials, self).__init__(SpaceClaim, ["V19", "V20", "V21"])
        self.speos_sim = SpeosSim

    def __create_dictionary_from_layers(self):
        """
        Function to create a dictionary from information of layers.

        Returns
        -------
        dict:
            a dictionary with index of layer name and value of geometries of that layer.
        """
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
        """
        Function to get a list of speos volume optical materials in project.

        Returns
        -------
        list:
            a list of name of volume optical materials.
        """
        op_list = []
        cs = self.GetRootPart().CustomObjects
        for item in cs:
            if self.speos_sim.Material.Find(item.Name):
                op_type = self.speos_sim.Material.Find(item.Name).OpticalPropertiesType.ToString()
                if "Surfacic" not in op_type:
                    op_list.append(item.Name)
        return op_list

    def __clean_geo_op_list(self, op_list):
        """
        Function to remove all the CAD linked to the speos optical materials.

        Parameters
        ----------
        op_list: list
            a list of name of volume optical materials.
        """
        for item in op_list:
            op = self.speos_sim.Material.Find(item)
            op.VolumeGeometries.Clear()

    def sync_op_from_layers(self):
        """Function to sync speos volume optical material based on the information of layers."""
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
