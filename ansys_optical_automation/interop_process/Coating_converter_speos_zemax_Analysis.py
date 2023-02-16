import io
import os
import shutil

from comtypes.client import CreateObject

from ansys_optical_automation.zemax_process.base import BaseZOS


class Coating_converter_speos_zemax_Analysis:
    def make_bsdf180(self, coatingfullfilename1, coatingfullfilename2, bsdf180fullfilename):
        """
        function that makes a bsdf180 from 2 coating files.

        Parameters
        ----------
        coatingfullfilename1 : string
            Path of coating 1
        coatingfullfilename2 : string
            Path of coating 2
        bsdf180fullfilename : string
            Path of the bsdf180

        Returns
        -------
        Nothing

        """
        # Create the BSDF180 that combines the two coatings
        bsdf_viewer = CreateObject("SimpleBSDFSurfaceViewer.Application")
        # Builds BSDF 180
        bsdf_viewer.BuildBSDF180(coatingfullfilename1, coatingfullfilename2)
        bsdf_viewer.SaveFile(bsdf180fullfilename)

    def check_wavelength_range(
        self, the_system, substrate_catalog, material_1, user_wavelength_min, user_wavelength_max, nb_wavelength
    ):
        """
        function that checks that the user wavelength range is within the material wavelength range

        Parameters
        ----------
        the_system : ZOSAPI.IOpticalSystem Interface Reference
        substrate_catalog : string
            Material catalog
        material_1 : string
            Material
        user_wavelength_min : float
            User wavelength min
        user_wavelength_max : float
            User wavelength min
        nb_wavelength : integer
            Number of wavelengths

        Returns
        -------
        wavelength_min: float
            Minimum wavelength
        wavelength_max: float
            Maximum wavelength
        wavelength_delta: float
            Wavelength delta

        """

        # Open the material catalog and check the wavelength ranges
        my_material_catalog = the_system.Tools.OpenMaterialsCatalog()
        my_material_catalog.SelectedCatalog = substrate_catalog
        my_material_catalog.SelectedMaterial = material_1
        material_1_minwave = my_material_catalog.MinimumWavelength
        material_1_maxwave = my_material_catalog.MaximumWavelength
        my_material_catalog.Close()

        if material_1_minwave > user_wavelength_min:
            wavelength_min = material_1_minwave
        else:
            wavelength_min = user_wavelength_min
        if user_wavelength_max > material_1_maxwave:
            wavelength_max = material_1_maxwave
        else:
            wavelength_max = user_wavelength_max
        wavelength_delta = (wavelength_max - wavelength_min) / (nb_wavelength - 1)

        return wavelength_min, wavelength_max, wavelength_delta

    def make_transmission_vs_angle_analysis(self, zosapi, the_system, resultfullfilename):
        """
        function that checks that the user wavelength range is within the material wavelength range

        Parameters
        ----------
        zosapi
        the_system : ZOSAPI.IOpticalSystem Interface Reference
        resultfullfilename : string
            Path of result file

        Returns
        -------
        bool_result: boolean
            True if result file is created

        """
        my_transmission_vs_angle = the_system.Analyses.New_Analysis(zosapi.Analysis.AnalysisIDM.TransmissionvsAngle)
        my_transmission_vs_angle.ApplyAndWaitForCompletion()
        my_transmission_vs_angle_results = my_transmission_vs_angle.GetResults()
        bool_result = my_transmission_vs_angle_results.GetTextFile(resultfullfilename)
        my_transmission_vs_angle.Close()

        return bool_result

    def read_transmission_vs_angle_result(self, resultfullfilename, skip_lines, coating_data):
        """
        function that reads the result file from the transmission vs angle analysis

        Parameters
        ----------
        resultfullfilename : string
            Path of result file
        skip_lines : integer
            number of lines that are ignored at each loop
        coating_data : integer
            list that contains the results

        Returns
        -------
        nb_angle_of_incidence: integer
            Number of angle of incidences in the result
        coating_data : integer
            list that contains the results

        """
        # Reading the transmission file
        bfile = io.open(resultfullfilename, "r", encoding="utf-16-le")
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

    def write_speos_coating_file(
        self,
        file_id1,
        name1,
        nb_digits,
        nb_angle_of_incidence,
        nb_wavelength,
        wavelength_min,
        wavelength_max,
        speos_wavelength_units_um,
        coating_data,
    ):
        """
        function that writes the speos coating file from the data read in the transmission vs angle analysis

        Parameters
        ----------
        file_id1 : integer
            File identifier
        name1 : string
            name of the coating
        nb_angle_of_incidence : integer
            Number of angles of incidences
        nb_wavelength : integer
            Number of wavelengths
        wavelength_min : float
            Minimum wavelength
        wavelength_max : float
            Maximum wavelength
        speos_wavelength_units_um : integer
            Conversion value to go from speos units to um. For example if speos is in nm, it is 1000
        coating_data : list
            list that contains the results

        Returns
        -------


        """
        myformat = "{:." + str(nb_digits) + "f}"

        # Writing the file
        file_id1.write("OPTIS - Coated surface file v1.0\n")
        file_id1.write(name1 + "\n")
        file_id1.write(str(nb_angle_of_incidence) + " " + str(nb_wavelength) + "\n")

        # 1st line
        for wavelength_index in range(nb_wavelength):
            wavelength = round(
                wavelength_min + wavelength_index * (wavelength_max - wavelength_min) / (nb_wavelength - 1), 3
            )
            file_id1.write("\t" + " " + myformat.format(speos_wavelength_units_um * wavelength) + " " + "\t")
        file_id1.write("\n")
        # Loop to read the data
        for angle_index in range(nb_angle_of_incidence):
            # 1st column: angle of incidence
            angleofincidence = float(coating_data[angle_index][0])
            file_id1.write(myformat.format(angleofincidence) + " \t")
            for wavelength_index in range(nb_wavelength):
                offset = angle_index + wavelength_index * (nb_angle_of_incidence + 1)
                reflectance_ppol_1 = float(coating_data[offset][2])
                transmittance_ppol_1 = float(coating_data[offset][4])
                file_id1.write(
                    myformat.format(100 * reflectance_ppol_1)
                    + "\t"
                    + myformat.format(100 * transmittance_ppol_1)
                    + "\t"
                )
            file_id1.write("\n\t")
            for wavelength_index in range(nb_wavelength):
                offset = angle_index + wavelength_index * (nb_angle_of_incidence + 1)
                reflectance_spol_1 = float(coating_data[offset][1])
                transmittance_spol_1 = float(coating_data[offset][3])
                file_id1.write(
                    myformat.format(100 * reflectance_spol_1)
                    + "\t"
                    + myformat.format(100 * transmittance_spol_1)
                    + "\t"
                )
            file_id1.write("\n")
        file_id1.close()
        # print("File " + coatingfilename1 + " created")
        coating_data.clear()
        # os.remove(resultfullfilename)

    def __init__(
        self,
        coatingfilename,
        coatingfolder,
        substrate_catalog,
        substrate_name,
        user_wavelength_min,
        user_wavelength_max,
        nb_wavelength,
        speos_wavelength_units_um,
        nb_digits,
        skip_lines,
    ):
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
        substrate_name : string
            Names of the materials
        user_wavelength_min : float
            Minimum user wavelength
        user_wavelength_max : float
            Maximum user wavelength
        nb_wavelength = integer
            Number of wavelengths
        speos_wavelength_units_um : integer
            Conversion value to go from speos units to um. For example if speos is in nm, it is 1000
        nb_digits : integer
            Number of digits of the converted data
        skip_lines : integer
            number of lines that are ignored at each loop - angle of incidence resolution
        Returns
        -------

        """

        zos = BaseZOS()
        # load local variables
        zosapi = zos.zosapi
        the_application = zos.the_application
        the_system = zos.the_system

        coatingfullfilename = coatingfolder + "\\" + coatingfilename
        print(coatingfullfilename)

        # Set up primary optical system
        the_system = the_application.PrimarySystem
        sample_dir = the_application.SamplesDir
        coating_dir = the_application.CoatingDir
        destination_file = coating_dir + "\\" + coatingfilename
        # print(destination_file)
        if not coatingfullfilename.lower() == destination_file.lower():
            shutil.copy(coatingfullfilename, destination_file)
        # Make new file
        test_file = sample_dir + r"\coating.zos"
        # print(test_file)
        the_system.New(False)
        the_system.SaveAs(test_file)
        # Coating catalog
        the_system.SystemData.Files.CoatingFile = coatingfilename
        # Aperture
        the_system_data = the_system.SystemData
        the_system_data.Aperture.ApertureValue = 1
        the_lde = the_system.LDE
        surface_0 = the_lde.GetSurfaceAt(0)
        surface_1 = the_lde.GetSurfaceAt(1)
        # Check the material catalog
        if not the_system.SystemData.MaterialCatalogs.IsCatalogInUse(substrate_catalog):
            the_system.SystemData.MaterialCatalogs.AddCatalog(substrate_catalog)
        coating_list = surface_1.CoatingData.GetAvailableCoatings()
        coating_list_length = coating_list.Length
        wave = 1
        the_system.Save()

        # Check if the user wavelengths are within the wavelength range of the substrates
        for j in range(len(substrate_name)):
            material_1 = substrate_name[j]
            material_2_name = "AIR"
            material_2 = ""
            wavelength_min, wavelength_max, wavelength_delta = self.check_wavelength_range(
                the_system, substrate_catalog, material_1, user_wavelength_min, user_wavelength_max, nb_wavelength
            )

            # Read the coatings in the coating file
            for i in range(coating_list_length):
                # print(coating_list[i])
                coating_name = coating_list[i]
                if not coating_name == "None":
                    name1 = str(coating_name) + "_" + str(material_2_name) + "_" + str(material_1)
                    name2 = str(coating_name) + "_" + str(material_1) + "_" + str(material_2_name)
                    coatingfilename1 = name1 + ".coated"
                    coatingfilename2 = name2 + ".coated"
                    coatingfolder_speos = coatingfolder + "\\Speos"
                    if not (os.path.exists(coatingfolder_speos) and os.path.isdir(coatingfolder_speos)):
                        os.makedirs(coatingfolder_speos)
                    coatingfullfilename1 = coatingfolder_speos + "\\" + coatingfilename1
                    coatingfullfilename2 = coatingfolder_speos + "\\" + coatingfilename2
                    file_id1 = open(coatingfullfilename1, "w")
                    file_id2 = open(coatingfullfilename2, "w")

                    coating_data = list()

                    # Extract coating data when going from air to substrate
                    surface_0.Material = material_2  # AIR
                    surface_1.Material = material_1
                    surface_1.Coating = coating_name

                    # Need to loop for all wavelength
                    for wavelength_index in range(nb_wavelength):
                        wavelength = round(
                            wavelength_min + wavelength_index * (wavelength_max - wavelength_min) / (nb_wavelength - 1),
                            3,
                        )
                        the_system.SystemData.Wavelengths.GetWavelength(wave).Wavelength = wavelength
                        # the_system.Save()

                        resultfullfilename = coatingfolder + "\\My_Transmission_vs_angle_" + name1 + ".txt"
                        bool_result = self.make_transmission_vs_angle_analysis(zosapi, the_system, resultfullfilename)
                        # if bool_result == False:
                        # print("The result file was not created!")

                        nb_angle_of_incidence, coating_data = self.read_transmission_vs_angle_result(
                            resultfullfilename, skip_lines, coating_data
                        )

                    self.write_speos_coating_file(
                        file_id1,
                        name1,
                        nb_digits,
                        nb_angle_of_incidence,
                        nb_wavelength,
                        wavelength_min,
                        wavelength_max,
                        speos_wavelength_units_um,
                        coating_data,
                    )
                    print("File " + coatingfilename1 + " created")
                    os.remove(resultfullfilename)

                    # Extract coating data when going from substrate to air
                    surface_0.Material = material_1
                    surface_1.Material = material_2  # AIR
                    surface_1.Coating = coating_name

                    for wavelength_index in range(nb_wavelength):
                        wavelength = round(
                            wavelength_min + wavelength_index * (wavelength_max - wavelength_min) / (nb_wavelength - 1),
                            3,
                        )
                        the_system.SystemData.Wavelengths.GetWavelength(wave).Wavelength = wavelength

                        resultfullfilename2 = coatingfolder + "\\My_Transmission_vs_angle_" + name2 + ".txt"
                        bool_result = self.make_transmission_vs_angle_analysis(zosapi, the_system, resultfullfilename2)
                        if not bool_result:
                            print("The result file was not created!")

                        nb_angle_of_incidence, coating_data = self.read_transmission_vs_angle_result(
                            resultfullfilename2, skip_lines, coating_data
                        )

                    self.write_speos_coating_file(
                        file_id2,
                        name2,
                        nb_digits,
                        nb_angle_of_incidence,
                        nb_wavelength,
                        wavelength_min,
                        wavelength_max,
                        speos_wavelength_units_um,
                        coating_data,
                    )
                    print("File " + coatingfilename2 + " created")
                    os.remove(resultfullfilename2)

                    # Create the BSDF180 that combines the two coatings
                    bsdf180filename = (
                        str(coating_name) + "_" + str(material_2_name) + "_" + str(material_1) + ".bsdf180"
                    )
                    bsdf180fullfilename = coatingfolder_speos + "\\" + bsdf180filename
                    self.make_bsdf180(coatingfullfilename1, coatingfullfilename2, bsdf180fullfilename)
                    print("File " + bsdf180filename + " created\n")

        os.remove(destination_file)
        os.remove(test_file)
        # This will clean up the connection to OpticStudio.
        # Note that it closes down the server instance of OpticStudio, so you for maximum performance do not do
        # this until you need to.
        del zos
