import csv
import os

from ansys_optical_automation.scdm_core.base import BaseSCDM


class MaterialsFromCSV(BaseSCDM):
    """Provides for creating Speos materials from material CSV files.

    This base class contains methods for reading a material CSV file and creating
    Speos materials.

    """

    def __init__(self, SpeosSim, SpaceClaim):
        """
        Base class that contains all commonly used objects. This class serves more as an abstract class.

        Parameters
        ----------
        SpeosSim : SpeosSim object
            SpeosSim.
        SpaceClaim : SpaceClaim object
            SpaceClaim.
        """
        super(MaterialsFromCSV, self).__init__(
            SpaceClaim, ["V19", "V20", "V21", "V22", "V23", "V231", "V232", "V241", "V242", "V251"]
        )
        self.speos_sim = SpeosSim

    def __get_real_original(self, item):
        """
        Get real original selection to obtain material information.

        Parameters
        ----------
        item : SpaceClaim part
            SpaceClaim part.

        Returns
        -------
        SpaceClaim part
            SpaceClaim part.
        """
        result = item
        while self.GetOriginal(result):
            result = self.GetOriginal(result)
        return result

    def __create_material_dictionary(self):
        """
        Create a dictionary with an index of material names and values for the SpaceClaim
        part list.

        Returns
        -------
        dict
            Dictionary of material information.
        """
        dict = {}
        root_part = self.GetRootPart()
        all_body = self.PartExtensions.GetAllBodies(root_part)
        for ibody in all_body:
            body = self.__get_real_original(ibody)
            try:
                if body.Material.Name not in dict:
                    dict[body.Material.Name] = self.List[self.IDesignBody]()
                dict[body.Material.Name].Add(ibody)
            except Exception:
                print("Do nothing")
        return dict

    def apply_geo_to_material(self):
        """Apply material according to the material definition."""
        op_list = {}
        all_op = self.GetRootPart().CustomObjects
        for item in all_op:
            op_list[item.Name] = self.List[self.IDesignBody]()

        material_dict = self.__create_material_dictionary()
        for item in material_dict:
            if item in op_list:
                op = self.speos_sim.Material.Find(item)
                try:
                    my_selection = self.BodySelection.Create(material_dict[item])
                    op.VolumeGeometries.Set(my_selection.Items)
                except Exception:
                    print("Not an Optical property")
            else:
                op_created = self.speos_sim.Material.Create()
                op_created.Name = item
                sel = self.BodySelection.Create(material_dict[item])
                op_created.VolumeGeometries.Set(sel.Items)

    def get_total_layers(self):
        """
        Get the names of all layers in the project.

        Returns
        -------
        list
            List of all layer names.
        """
        layer_list = []
        active_doc = self.GetActiveDocument()
        total_layers = active_doc.Layers
        for layer in total_layers:
            layer_list.append(layer.Name)
        return layer_list

    def apply_geo_to_layer(self):
        """Apply geometries to corresponding layers."""
        layer_list = self.get_total_layers()
        geo_dic = self.__create_material_dictionary()

        for item in geo_dic:
            sel = self.Selection.Create(geo_dic[item])
            if item in layer_list:
                self.Layers.MoveTo(sel, item)
            else:
                self.__create_layer(item)
                layer_list.append(item)
                self.Layers.MoveTo(sel, item)

    def __create_layer(self, op_name):
        """
        Create a layer.

        Parameters
        ----------
        op_name : str
            Name for the new layer.
        """
        active_doc = self.GetActiveDocument()
        nb_layer = active_doc.Layers.Count
        try:
            active_doc.Layers[nb_layer - 1].Create(active_doc, op_name, self.Color.Empty)
        except Exception:
            print("A layer with this name already exists.")

    def __create_op(self, fop_name, op_name, sop_name, vop_name, work_directory):
        """
        Create a Speos optical material based on given parameter values.

        Parameters
        ----------
        fop_name : str
            Name of the FOP from the CSV file.
        op_name : str
            Name of the OP from the CSV file.
        sop_name : str
            Name of the SOP from CSV file.
        vop_name : str
            Name of the VOP from the CSV file.
        work_directory : str
            File directory from the CSV file.
        """
        if self.speos_sim.Material.Find(op_name) is None:
            material = self.speos_sim.Material.Create()
            material.Name = op_name
            if fop_name == "True":
                material.OpticalPropertiesType = self.speos_sim.Material.EnumOpticalPropertiesType.Surfacic
            else:
                material.OpticalPropertiesType = self.speos_sim.Material.EnumOpticalPropertiesType.Volumic
                if "Opaque" in vop_name:
                    material.VOPType = self.speos_sim.Material.EnumVOPType.Opaque
                elif "Optic" in vop_name:
                    material.VOPType = self.speos_sim.Material.EnumVOPType.Optic
                else:
                    material.VOPType = self.speos_sim.Material.EnumVOPType.Library
                    material.VOPLibrary = os.path.join(work_directory, "SPEOS input files", vop_name)

            if "Mirror" in sop_name:
                material.SOPType = self.speos_sim.Material.EnumSOPType.Mirror
                start = sop_name.find("Mirror") + 6
                value = int(sop_name[start:])
                material.SOPReflectance = value
            elif "Optical Polished" in sop_name:
                material.SOPType = self.speos_sim.Material.EnumSOPType.OpticalPolished
            else:
                material.SOPType = self.speos_sim.Material.EnumSOPType.Library
                material.SOPLibrary = os.path.join(work_directory, "SPEOS input files", sop_name)

    def create_speos_material(self, csv_path, work_directory):
        """
        Read a CSV file and create an OP.

        Parameters
        ----------
        csv_path: str
            Full path to the CSV file.
        work_directory: str
            Full path to the input material folder. For example ``"D:\\ASP_MaterialFromCsv"``.
        """
        with open(csv_path) as myfile:
            reader = csv.reader(myfile)
            for line in reader:  # skips the first header line
                print(line)
                if ("End" not in line) and ("Materialname " not in line) and ("Catia Material" not in line):
                    op_name = line[0].rstrip()
                    fop_name = line[1]
                    vop_name = line[2]
                    sop_name = line[3]
                    self.__create_layer(op_name)
                    self.__create_op(fop_name, op_name, sop_name, vop_name, work_directory)
