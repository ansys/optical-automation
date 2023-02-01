import io
import os
import shutil

#from ansys_optical_automation.post_process.dpf_base import DataProcessingFramework
from ansys_optical_automation.zemax_process.base import BaseZOS
from comtypes.client import CreateObject


class CoatingConverter:
    def __init__(self, coatingfilename, coatingfolder, substrate_catalog, substrate_names):
        """
        function that converts a Zemax coating / substrate into a speos coating file and a bsdf180
        The function reads the data from the Transmission vs Angle analysis
        The settings are not implemented in ZOS-API for this analysis.
        So the settings by default should be set to
        - incident angles  from 0 to 90
        - surface to 1

        Parameters
        ----------
        coatingfilename : string
            Name of the coating file to convert
        coatingfolder : string
            Path to the coating file
        substrate_catalog : string
            Catalog of the materials
        substrate_names : list
            list of names of the materials

        """

        self.coatingfolder = coatingfolder
        self.substrate_catalog = substrate_catalog
        self.substrate_names = substrate_names

        self.zos = BaseZOS()
        self.the_system = self.zos.the_application.PrimarySystem
        self.bool_copy = 0

        # Defining a test file
        TestFile = coatingfolder + "\\coating.zos"

        # Set up primary optical system
        coating_dir = self.zos.the_application.CoatingDir
        destination_file = os.path.join(coating_dir, coatingfilename)
        self.coating_file = os.path.join(coatingfolder, coatingfilename)
        if not self.coating_file.lower() == destination_file.lower():
            shutil.copy(self.coating_file, destination_file)
            self.bool_copy = 1

        # Coating catalog
        self.the_system.SystemData.Files.CoatingFile = coatingfilename

        # Aperture
        the_system_data = self.the_system.SystemData
        the_system_data.Aperture.ApertureValue = 1
        the_lde = self.the_system.LDE
        self.surface_0 = the_lde.GetSurfaceAt(0)
        self.surface_1 = the_lde.GetSurfaceAt(1)
        # Check the material catalog
        if not self.the_system.SystemData.MaterialCatalogs.IsCatalogInUse(substrate_catalog):
            self.the_system.SystemData.MaterialCatalogs.AddCatalog(substrate_catalog)
        self.coating_list = self.surface_1.CoatingData.GetAvailableCoatings()
        self.the_system.SaveAs(TestFile)

    def convert_zemax_to_speos(self, wavelength_min, wavelength_max, nb_wavelength, unit, nb_digits, skip_lines,
                               bool_bsdf180):
        """
        function that converts a Zemax coating / substrate into a speos coating file and a bsdf180

        Parameters
        ----------
        wavelength_min : float
            Minimum wavelength
        wavelength_max : float
            Maximum wavelength
        nb_wavelength : integer
            Number of wavelengths
        unit : integer
            Conversion value to go from speos units to um. For example if speos is in nm, it is 1000
        nb_digits : integer
            Number of digits in the speos coating file
        skip_lines : integer
            number of lines to skip when reading the data from the transmission analysis
        bool_bsdf180 : boolean
            1 to create a bsdf180 / 0 otherwise

        """
        # Check if the user wavelengths are within the wavelength range of the substrates
        for substrate_name in self.substrate_names:
            material_2_name = "AIR"
            material_2 = ""
            wavelength_min, wavelength_max = self.__check_wavelength_range(
                substrate_name, wavelength_min, wavelength_max
            )

            # Read the coatings in the coating file
            for coating_idx in range(self.coating_list.Length):
                coating_name = self.coating_list[coating_idx]
                if not coating_name == "None":
                    coating_file_1_name = str(coating_name) + "_" + str(material_2_name) + "_" + str(substrate_name)
                    coating_file_2_name = str(coating_name) + "_" + str(substrate_name) + "_" + str(material_2_name)
                    coating_file_1 = coating_file_1_name + ".coated"
                    coating_file_2 = coating_file_2_name + ".coated"
                    coatingfolder_speos = os.path.join(self.coatingfolder, "Speos")
                    if not (os.path.exists(coatingfolder_speos) and os.path.isdir(coatingfolder_speos)):
                        os.makedirs(coatingfolder_speos)

                    # # Extract coating data when going from air to substrate
                    self.surface_0.Material = material_2  # AIR
                    self.surface_1.Material = substrate_name
                    self.surface_1.Coating = coating_name

                    self.__write_speos_coating_file(
                        coating_file_1_name,
                        nb_digits,
                        nb_wavelength,
                        wavelength_min,
                        wavelength_max,
                        unit,
                        skip_lines,
                    )
                    print("File " + coating_file_1 + " created")

                    # Extract coating data when going from substrate to air
                    self.surface_0.Material = substrate_name
                    self.surface_1.Material = material_2  # AIR
                    self.surface_1.Coating = coating_name

                    self.__write_speos_coating_file(
                        coating_file_2_name,
                        nb_digits,
                        nb_wavelength,
                        wavelength_min,
                        wavelength_max,
                        unit,
                        skip_lines,
                    )
                    print("File " + coating_file_2 + " created")

                    # Create the BSDF180 that combines the two coatings
                    bsdf180filename = (
                        str(coating_name) + "_" + str(material_2_name) + "_" + str(substrate_name) + ".bsdf180"
                    )
                    bsdf180file_dir = os.path.join(coatingfolder_speos, bsdf180filename)
                    coating_file_1_dir = os.path.join(self.coatingfolder, "Speos", coating_file_1)
                    coating_file_2_dir = os.path.join(self.coatingfolder, "Speos", coating_file_2)
                    if bool_bsdf180 == 1:
                        self.__make_bsdf180(coating_file_1_dir, coating_file_2_dir, bsdf180file_dir)
                        print("File " + bsdf180filename + " created\n")

        if self.bool_copy == 1:
            os.remove(self.coating_file)
        # This will clean up the connection to OpticStudio.
        # Note that it closes down the server instance of OpticStudio, so you for maximum performance do not do
        # this until you need to.
        del self.zos
        # zos = None

    def __make_bsdf180(self, coating_file_1, coating_file_2, speos_bsdf180):
        """
        function that makes a bsdf180 from 2 coating files.

        Parameters
        ----------
        coating_file_1 : string
            Path of coating 1
        coating_file_2 : string
            Path of coating 2
        speos_bsdf180 : string
            Path of the bsdf180

        Returns
        -------
        Nothing

        """
        # Create the BSDF180 that combines the two coatings
        #bsdf_viewer = DataProcessingFramework(extension=".bsdf180", application="SimpleBSDFSurfaceViewer.Application")
        #bsdf_viewer.dpf_instance.BuildBSDF180(coating_file_1, coating_file_2)
        #bsdf_viewer.dpf_instance.SaveFile(speos_bsdf180)

        bsdf_viewer = CreateObject("SimpleBSDFSurfaceViewer.Application222")
        # # Builds BSDF 180
        bsdf_viewer.BuildBSDF180(coating_file_1, coating_file_2)
        bsdf_viewer.SaveFile(speos_bsdf180)

    def __check_wavelength_range(self, substrate_material, user_wavelength_min, user_wavelength_max):
        """
        function that checks that the user wavelength range is within the material wavelength range

        Parameters
        ----------
        substrate_material : string
            Material
        user_wavelength_min : float
            User wavelength min
        user_wavelength_max : float
            User wavelength min

        Returns
        -------
        wavelength_min: float
            Minimum wavelength
        wavelength_max: float
            Maximum wavelength

        """

        # Open the material catalog and check the wavelength ranges
        my_material_catalog = self.the_system.Tools.OpenMaterialsCatalog()
        my_material_catalog.SelectedCatalog = self.substrate_catalog
        my_material_catalog.SelectedMaterial = substrate_material
        material_1_minwave = my_material_catalog.MinimumWavelength
        material_1_maxwave = my_material_catalog.MaximumWavelength
        my_material_catalog.Close()

        wavelength_min = max(material_1_minwave, user_wavelength_min)
        wavelength_max = min(material_1_maxwave, user_wavelength_max)

        return wavelength_min, wavelength_max

    def __check_transmission_vs_angle_result(self, coating_data, result_file_dir, skip_lines):
        """
        function that reads the result file from the transmission vs angle analysis

        Parameters
        ----------
        result_file_dir : string
            Path of result file
        skip_lines : integer
            number of lines that are ignored at each loop

        Returns
        -------
        nb_angle_of_incidence: integer
            Number of angle of incidences in the result
        coating_data : integer
            list that contains the results

        """

        my_transmission_vs_angle = self.the_system.Analyses.New_Analysis(
            self.zos.zosapi.Analysis.AnalysisIDM.TransmissionvsAngle
        )
        my_transmission_vs_angle.ApplyAndWaitForCompletion()
        my_transmission_vs_angle_results = my_transmission_vs_angle.GetResults()
        bool_result = my_transmission_vs_angle_results.GetTextFile(result_file_dir)
        my_transmission_vs_angle.Close()
        if not bool_result:
            msg = "cannot checks that the user wavelength range is within the material wavelength range"
            raise ValueError(msg)

        # Reading the transmission file
        bfile = io.open(result_file_dir, "r", encoding="utf-16-le")
        header_line = bfile.readline()
        while header_line[1:10].strip() != "Angle":
            header_line = bfile.readline()
        # Now reading the content
        # Angle S - Reflect P - Reflect S - Transmit    P - Transmit
        index_angle_of_incidence = 0
        data_line = "start"
        while not len(data_line) == 1:
            data_line = bfile.readline()
            data_line = data_line.split("\t")
            data_line = data_line[0:5]  # only keeping the first 5 values
            # Miss 3 lines
            for index_line in range(skip_lines):
                bfile.readline()
            coating_data.append(data_line)
            index_angle_of_incidence = index_angle_of_incidence + 1
            # print(index_angle_of_incidence)
            # nb_angle_of_incidence = len(coating_data)
        nb_angle_of_incidence = index_angle_of_incidence - 1
        bfile.close()

        return nb_angle_of_incidence, coating_data

    def __write_speos_coating_file(
        self,
        coating_file_name,
        nb_digits,
        nb_wavelength,
        wavelength_min,
        wavelength_max,
        speos_wavelength_unit,
        skip_lines,
    ):
        """
        function that writes the speos coating file from the data read in the transmission vs angle analysis

        Parameters
        ----------
        skip_lines
        coating_file_name : string
            name of the coating
        nb_wavelength : integer
            Number of wavelengths
        wavelength_min : float
            Minimum wavelength
        wavelength_max : float
            Maximum wavelength
        speos_wavelength_unit : integer
            Conversion value to go from speos units to um. For example if speos is in nm, it is 1000

        Returns
        -------


        """
        coating_file_dir = os.path.join(self.coatingfolder, "Speos", coating_file_name + ".coated")
        coating_file_output = open(coating_file_dir, "w")

        # Need to loop for all wavelength
        # coating_data = None
        coating_data = []
        wavelength_delta = (wavelength_max - wavelength_min) / (nb_wavelength - 1)
        for wavelength_index in range(nb_wavelength):
            wavelength = round(wavelength_min + wavelength_index * wavelength_delta, 3)
            self.the_system.SystemData.Wavelengths.GetWavelength(1).Wavelength = wavelength
            # the_system.Save()

            result_file_dir = os.path.join(self.coatingfolder, "My_Transmission_vs_angle_" + coating_file_name + ".txt")
            nb_angle_of_incidence, coating_data = self.__check_transmission_vs_angle_result(
                coating_data, result_file_dir, skip_lines
            )

        myformat = "{:." + str(nb_digits) + "f}"

        # Writing the file
        coating_file_output.write("OPTIS - Coated surface file v1.0\n")
        coating_file_output.write(coating_file_name + "\n")
        coating_file_output.write(str(nb_angle_of_incidence) + " " + str(nb_wavelength) + "\n")

        # 1st line
        for wavelength_index in range(nb_wavelength):
            wavelength = round(
                wavelength_min + wavelength_index * (wavelength_max - wavelength_min) / (nb_wavelength - 1), 3
            )
            coating_file_output.write("\t" + " " + myformat.format(speos_wavelength_unit * wavelength) + " " + "\t")
        coating_file_output.write("\n")
        # Loop to read the data
        for angle_index in range(nb_angle_of_incidence):
            # 1st column: angle of incidence
            angleofincidence = float(coating_data[angle_index][0])
            coating_file_output.write(myformat.format(angleofincidence) + " \t")
            for wavelength_index in range(nb_wavelength):
                offset = angle_index + wavelength_index * (nb_angle_of_incidence + 1)
                reflectance_ppol_1 = float(coating_data[offset][2])
                transmittance_ppol_1 = float(coating_data[offset][4])
                coating_file_output.write(
                    myformat.format(100 * reflectance_ppol_1)
                    + "\t"
                    + myformat.format(100 * transmittance_ppol_1)
                    + "\t"
                )
            coating_file_output.write("\n\t")
            for wavelength_index in range(nb_wavelength):
                offset = angle_index + wavelength_index * (nb_angle_of_incidence + 1)
                reflectance_spol_1 = float(coating_data[offset][1])
                transmittance_spol_1 = float(coating_data[offset][3])
                coating_file_output.write(
                    myformat.format(100 * reflectance_spol_1)
                    + "\t"
                    + myformat.format(100 * transmittance_spol_1)
                    + "\t"
                )
            coating_file_output.write("\n")
        coating_file_output.close()
        # print("File " + coatingfilename1 + " created")
        coating_data.clear()
        # os.remove(resultfullfilename)
        os.remove(result_file_dir)
