import bisect
import math
import os

import numpy as np
from scipy import interpolate
from scipy.integrate import nquad

# =========================================
# Speos BSDF Help files
# https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v222/en/Optis_UG_LAB/Optis/UG_Lab/structure_of_anisotropic_bsdf_files_81025.html
# Zemax BSDF Help files
# https://support.zemax.com/hc/en-us/articles/1500005486801-BSDF-Data-Interchange-file-format-specification
# =========================================


class BsdfStructure:
    """
    class of BSDF data contains method to host bsdf data
    """

    def __init__(self):
        """
        That functions initializes an object of the class.

        filename_input: string
            filename of the imported bsdf
        zemax_or_speos: string
            string = "zemax" or "speos". Zemax or Speos imported file
        output_choice: integer
            1 for .bsdf (Zemax),2 for .brdf (Speos) - Not yet supported, 3 = .anisotropicbsdf\n
        scattertype: list
            list of string. Can be ["BRDF"], ["BTDF"] or ["BRDF","BTDF"]
        symmetry: string
            The string can be "Asymmetrical", "PlaneSymmetrical". This is used for Zemax BSDF files.
            If "PlaneSymmetrical", the software will recreate the data for phi between 180-360.
        wavelength: list
            list of wavelengths
        samplerotation: list
            list of sample rotations
        incidence: list
            list of angles of incidence
        bsdfdata_scattertype: list
            list of scattertype BRDF or BTDF for each BSDF block
        bsdfdata_wavelength: list
            list of wavelengths for each BSDF block
        bsdfdata_samplerotation: list
            list of sample rotations for each BSDF block
        bsdfdata_incidence: list
            list of angle of incidence for each BSDF block
        bsdfdata_tisdata: list
            list of total integrated scatter for each BSDF block
        bsdfdata_theta: list
            list of theta angles for each BSDF block
        bsdfdata_phi: list
            list of phi angles for each BSDF block
        bsdfdata: list
            list of block of bsdf data
            The data is listed in that order: wavelength > sample_rotation > angleofincidence
        """
        self.filename_input = None
        self.zemax_or_speos = None
        self.output_choice = None
        self.scattertype = None
        self.symmetry = None
        self.wavelength = None
        self.samplerotation = None
        self.incidence = None
        self.bsdfdata_scattertype = None
        self.bsdfdata_wavelength = None
        self.bsdfdata_samplerotation = None
        self.bsdfdata_incidence = None
        self.bsdfdata_tisdata = {"transmission_reflection", "wavelength", "sample_rotation", "angleofincidence"}
        self.bsdfdata_theta = {"transmission_reflection", "wavelength", "sample_rotation", "angleofincidence"}
        self.bsdfdata_phi = {"transmission_reflection", "wavelength", "sample_rotation", "angleofincidence"}
        self.bsdfdata = {"transmission_reflection", "wavelength", "sample_rotation", "angleofincidence", "theta", "phi"}

    def import_data(self, bool_log=True):
        """
        Read the filename of the object (filename_input) and imports the data into the class

        Parameters
        ----------
        bool_log : boolean
            0 no report
            1 report values
        """
        input_file_extension = os.path.splitext(self.filename_input)[1].lower()[0:]
        if not (input_file_extension in [".bsdf", ".brdf", ".anisotropicbsdf"]):
            msg = "Nonsupported file selected"
            raise TypeError(msg)
        if input_file_extension == ".bsdf":
            self.zemax_or_speos = "zemax"
            self.read_zemax_bsdf(bool_log)
            self.converter_coordinate_system_bsdf(1, bool_log)
            self.normalize_bsdf_data(bool_log)

        if input_file_extension == ".brdf":
            self.zemax_or_speos = "speos"
            self.read_speos_brdf(bool_log)
            # self.phi_theta_output()

        if input_file_extension == ".anisotropicbsdf":
            self.zemax_or_speos = "speos"
            self.read_speos_anisotropicbsdf(bool_log)
            self.calculate_tis_data(bool_log)

        # Restriction: we don't convert BTDF between Speos and Zemax
        # The index of refraction is not taken into account
        for index_RT in range(len(self.scattertype)):
            if self.scattertype[index_RT] == "BTDF":
                # For unit tests we will still test the BTDF conversion
                if self.output_choice is not None:
                    if self.zemax_or_speos == "zemax" and self.output_choice == 3:
                        msg = "BTDF data conversions are not supported between Zemax and Speos"
                        raise TypeError(msg)
                    if (len(self.scattertype)) == 2:
                        if self.zemax_or_speos == "speos" and self.output_choice == 1:
                            msg = (
                                "WARNING! \n"
                                "BTDF data conversions are not supported between Speos and Zemax \n"
                                "Only BRDF data will be converted.\n"
                                "Press Enter to continue.\n"
                            )
                            input(msg)

    def read_speos_brdf(self, bool_log):
        """
        That function reads a Speos brdf file

        Parameters
        ----------
        bool_log : boolean
            0 no report
            1 report values
        """

        # Reading file
        if bool_log == 1:
            print("Reading Speos BSDF file: " + str(self.filename_input) + "...\n")

        bfile = open(self.filename_input, "r")

        input_file_extension = os.path.splitext(self.filename_input)[1].lower()[0:]
        if "brdf" in input_file_extension:
            symmetry = "Asymmetrical"
        # Read the header
        if bool_log == 1:
            print("Reading header of Speos BSDF.....")
        # Row 1 : header
        headerLine = bfile.readline()
        header = headerLine[:-1].split(" ")
        version = header[len(header) - 1]
        if float(version[1:]) < 8.0:
            msg = "The format is not supported. Open and save the file with the BSDF viewer to update the format."
            raise TypeError(msg)
        if bool_log == 1:
            print("Header = " + str(headerLine))
        # Row 2 : text 0 or binary 1
        textorbinaryLine = bfile.readline()
        textorbinary = textorbinaryLine[:-1].split("\t")
        if textorbinary[0] == 0:
            msg = "The BSDF data cannot be read. It is not a text."
            raise TypeError(msg)
        else:
            if bool_log == 1:
                print("Text = " + str(textorbinaryLine))
        # Row 3 : Comment line
        commentLine = bfile.readline()
        if bool_log == 1:
            print("Comment = " + str(commentLine))
        # Row 4 : Number of characters to read for the measurement description. Several lines are allowed
        nbmeasurementLine = bfile.readline()
        if bool_log == 1:
            print("nbmeasurementLine = " + str(nbmeasurementLine))
        # nbmeasurement = nbmeasurementLine[:-1].split("\t")
        # Row 5 : Measurement description (cannot be edited from the viewer).
        measurementdescriptionLine = bfile.readline()
        if bool_log == 1:
            print("measurement description = " + str(measurementdescriptionLine))
        # Row 6: Contains two boolean values (0=false and 1=true) - reflection / transmission data
        reflectionortransmissionLine = bfile.readline()
        reflectionortransmissionString = reflectionortransmissionLine[:-1].split("\t")
        reflectionortransmission = [int(i) for i in reflectionortransmissionString]
        # Reflection: false or true
        scatterType = []
        if reflectionortransmission[0] == 1:
            scatterType.append("BRDF")
        if reflectionortransmission[1] == 1:
            scatterType.append("BTDF")
        # Row 7: Contains a boolean value describing the type of value stored in the file: 1 bsdf / 0 intensity
        typeLine = bfile.readline()
        intensity_or_bsdf = float(typeLine.strip())
        if bool_log == 1:
            print("BSDF(1) or Intensity(1) values = " + str(intensity_or_bsdf))
        # Row 8: Number of incident angles and number of wavelength samples (in nanometer).
        nbAngleIncidenceWavelengthLine = bfile.readline()
        nbAngleIncidenceWavelength = nbAngleIncidenceWavelengthLine[:-1].split("\t")
        nbAngleIncidence = int(nbAngleIncidenceWavelength[0])
        nbWavelength = int(nbAngleIncidenceWavelength[1])
        # Row 9: List of the incident angles.
        angleIncidenceLine = bfile.readline()
        angleIncidenceString = angleIncidenceLine[:-1].split()
        angleIncidence = [float(i) for i in angleIncidenceString]
        # Row 10: List of the wavelength samples.
        wavelengthLine = bfile.readline()
        wavelengthString = wavelengthLine[:-1].split("\t")
        wavelength = [float(i) for i in wavelengthString]

        if bool_log == 1:
            print(".....Header was correctly read\n")
        # tempVariable = input('Press Enter to continue\n')

        if bool_log == 1:
            print("Reading BSDF content.....")

        # Row 11: Reflection (or transmission) percentage for BRDF wavelength data normalization, for the first table.
        # NormalizationLine = bfile.readline()
        # Row 12: Number of angles measured for Theta and Phi
        # for the incident angle N°1 and the wavelength N°1 of the incident angle N°1.

        nb_reflection_transmission = len(scatterType)
        # tisData = np.zeros((nb_reflection_transmission * nbAngleIncidence, nbWavelength))
        tisdata_temp_list = []
        scatterRadial_temp_list = []
        scatterAzimuth_temp_list = []
        bsdfData_temp_list = []

        for i in range(nb_reflection_transmission * nbAngleIncidence):
            for j in range(nbWavelength):
                tisdata_temp_list.append(float(bfile.readline()))
                nbthetaphiLine = bfile.readline()
                nbthetaphi = nbthetaphiLine[:-1].split()
                nbScatterRadial = int(nbthetaphi[0])
                nbScatterAzimuth = int(nbthetaphi[1])
                # nbScatterRadial_list.append(nbScatterRadial)
                # nbScatterAzimuth_list.append(nbScatterAzimuth)

                scatterAzimuthLine = bfile.readline()
                scatterAzimuthLineString = (scatterAzimuthLine[:-1].strip()).split("\t")
                scatterAzimuth = [float(i) for i in scatterAzimuthLineString]
                scatterAzimuth_temp_list.append(scatterAzimuth)

                bsdfDataBlock = np.zeros((nbScatterRadial, nbScatterAzimuth))
                # scatterRadial = np.zeros(nbScatterRadial)
                scatterRadial = []

                for k in range(nbScatterRadial):
                    dataLine = bfile.readline()
                    data = dataLine.split()
                    # scatterRadial[k] = float(data[0])
                    scatterRadial.append(float(data[0]))
                    bsdfDataBlock[k] = data[1:]

                # If transmission data
                if scatterRadial[0] >= 90:
                    # change line theta from 90--> 180 to 0-->90
                    temp = scatterRadial
                    temp_180 = [180 - temp[index_temp] for index_temp in range(len(temp))]
                    scatterRadial = temp_180[::-1]
                    # swap the radial / theta of the bsdf_block
                    bsdfDataBlock = swap_rows(bsdfDataBlock)

                scatterRadial_temp_list.append(scatterRadial)
                bsdfData_temp_list.append(bsdfDataBlock)

        # Need to reorder
        # BRDF: RT --> incidence --> wavelength
        # Format: RT --> wavelength --> incidence
        tisdata_list = []
        scatterRadial_list = []
        scatterAzimuth_list = []
        bsdfData_list = []
        incidence_list = []
        wavelength_list = []
        scatterType_list = []
        samplerotation = []
        samplerotation.append(0)
        samplerotation_list = []

        for index_RT in range(nb_reflection_transmission):
            for index_wavelength in range(nbWavelength):
                for index_incidence in range(nbAngleIncidence):
                    index_block = ((index_incidence * nbWavelength) + index_wavelength) + (
                        index_RT * nbWavelength * nbAngleIncidence
                    )
                    scatterType_list.append(scatterType[index_RT])
                    wavelength_list.append(wavelength[index_wavelength])
                    samplerotation_list.append(0)
                    incidence_list.append(angleIncidence[index_incidence])
                    tisdata_list.append(tisdata_temp_list[index_block] / 100)
                    scatterRadial_list.append(scatterRadial_temp_list[index_block])
                    scatterAzimuth_list.append(scatterAzimuth_temp_list[index_block])
                    bsdfData_list.append(bsdfData_temp_list[index_block])

        if bool_log == 1:
            print(".....BSDF data was correctly read\n")

        #    return scatterType, BSDFType, nbSampleRotation, nbAngleIncidence, nbScatterAzimuth, nbScatterRadial, \
        #           angleIncidence, wavelength, scatterRadial, scatterAzimuth, tisData, bsdfData
        bfile.close()

        self.scattertype = scatterType
        self.symmetry = symmetry
        self.wavelength = wavelength
        self.samplerotation = samplerotation
        self.incidence = angleIncidence
        self.bsdfdata_scattertype = scatterType_list
        self.bsdfdata_wavelength = wavelength_list
        self.bsdfdata_samplerotation = samplerotation_list
        self.bsdfdata_incidence = incidence_list
        self.bsdfdata_tisdata = tisdata_list
        self.bsdfdata_theta = scatterRadial_list
        self.bsdfdata_phi = scatterAzimuth_list
        self.bsdfdata = bsdfData_list

        # Convert intensity values to BSDF values
        if intensity_or_bsdf == 0:
            self.intensity_to_bsdf_data()

    def read_speos_anisotropicbsdf(self, bool_log):
        """
        That function reads a Speos anisotropicbsdf file

        Parameters
        ----------
        bool_log : boolean
            0 no report
            1 report values
        """
        samplerotation_list = []
        angleIncidence_list = []
        wavelength_list = []
        RT_list = []
        tisdata_list = []
        nbWavelength = 0

        # Reading file
        print("Reading Speos anisotropicbsdf file: " + str(self.filename_input) + "...\n")

        bfile = open(self.filename_input, "r")

        input_file_extension = os.path.splitext(self.filename_input)[1].lower()[0:]
        if "anisotropicbsdf" in input_file_extension:
            symmetry = "Asymmetrical4D"
        # Read the header
        if bool_log == 1:
            print("Reading header of Speos BSDF.....")
        # Row 1 : header
        headerLine = bfile.readline()
        header = headerLine[:-1].split()
        version = header[len(header) - 1]
        if float(version[1:]) < 8.0:
            msg = "The format is not supported. Open and save the file with the BSDF viewer to update the format."
            raise TypeError(msg)
        if bool_log == 1:
            print("Header = " + str(headerLine))
        # Row 2 : text 0 or binary 1
        textorbinaryLine = bfile.readline()
        textorbinary = textorbinaryLine[:-1].split()
        if textorbinary[0] == 0:
            msg = "The BSDF data cannot be read. It is not a text."
            raise TypeError(msg)
        else:
            if bool_log == 1:
                print("Text = " + str(textorbinaryLine))
        # Row 3 : Comment line
        commentLine = bfile.readline()
        if bool_log == 1:
            print("Comment = " + str(commentLine))
        # Row 4 : Number of characters to read for the measurement description. Several lines are allowed
        nbmeasurementLine = bfile.readline()
        if bool_log == 1:
            print("nbmeasurementLine = " + str(nbmeasurementLine))
        # nbmeasurement = nbmeasurementLine[:-1].split("\t")
        # Row 5 : Measurement description (cannot be edited from the viewer).
        measurementdescriptionLine = bfile.readline()
        if bool_log == 1:
            print("measurement description = " + str(measurementdescriptionLine))
        # Row 6: Contains the anisotropy vector in the global coordinates system
        anisotropyvectorLine = bfile.readline()
        anisotropyvectorString = anisotropyvectorLine[:-1].split()
        anisotropyvector = [int(i) for i in anisotropyvectorString]

        if bool_log == 1:
            print("The anisotropy vector is = " + str(anisotropyvector))

        # if not (anisotropyvector == [0, 1, 0]):
        #    msg = "Only the (0,1,0) anisotropy vector is supported for now"
        #    raise TypeError(msg)

        # Row 7: Contains two boolean values (0=false and 1=true) - reflection / transmission data
        reflectionortransmissionLine = bfile.readline()
        reflectionortransmissionString = reflectionortransmissionLine[:-1].split()
        reflectionortransmission = [int(i) for i in reflectionortransmissionString]
        # Reflection: false or true
        scatterType = []
        if reflectionortransmission[0] == 1:
            scatterType.append("BRDF")
        if reflectionortransmission[1] == 1:
            scatterType.append("BTDF")
        # Row 8: Contains a boolean value describing the type of value stored in the file: 1 bsdf / 0 intensity
        typeLine = bfile.readline()
        intensity_or_bsdf = float(typeLine.strip())
        if bool_log == 1:
            print("BSDF(1) or Intensity(1) values = " + str(intensity_or_bsdf))
        # scattertype_nb_list = []

        # Reflection
        if reflectionortransmission[0] == 1:
            # Row 9: Number of anisotropy angles in reflection.
            nbsamplerotationLine = bfile.readline()
            nbsamplerotation_reflection = int(nbsamplerotationLine.strip())
            # Row 10: List of anisotropy angles in reflection.
            samplerotationLine = bfile.readline()
            samplerotationString = samplerotationLine[:-1].split()
            samplerotation = [float(i) for i in samplerotationString]
            # samplerotation_list.append(samplerotation_reflection)
            for index_samplerotation in range(nbsamplerotation_reflection):
                # Row 11: Number of incident angles in reflection, for anisotropy angle N°1
                nbAngleIncidenceLine = bfile.readline()
                nbAngleIncidence = int(nbAngleIncidenceLine.strip())
                for index_incidence in range(nbAngleIncidence):
                    samplerotation_list.append(samplerotation[index_samplerotation])
                    RT_list.append("BRDF")
                # Row 12: List of incident angles in reflection, for anisotropy angle N°1.
                angleIncidenceLine = bfile.readline()
                angleIncidenceString = angleIncidenceLine[:-1].split()
                angleIncidence = [float(i) for i in angleIncidenceString]
                angleIncidence_list.extend(angleIncidence)
                # Check that the angle of incidences are identical
                if index_samplerotation > 0:
                    if not angleIncidence == save_angleIncidence:
                        msg = "The angle of incidences must be identical for all the sample rotations."
                        raise TypeError(msg)
                save_angleIncidence = angleIncidence

        # Transmission
        if reflectionortransmission[1] == 1:
            # Row 13: Number of anisotropy angles in transmission
            nbsamplerotationLine = bfile.readline()
            nbsamplerotation_transmission = int(nbsamplerotationLine.strip())
            if reflectionortransmission[0] == 1:
                if not nbsamplerotation_reflection == nbsamplerotation_transmission:
                    msg = "The number of sample rotation in transmission and reflection have to be equal."
                    raise TypeError(msg)
            # Row 14: List of anisotropy angles in reflection.
            samplerotationLine = bfile.readline()
            samplerotationString = samplerotationLine[:-1].split()
            samplerotation = [float(i) for i in samplerotationString]
            # samplerotation_list.append(samplerotation_transmission)
            for index_samplerotation in range(nbsamplerotation_transmission):
                # Row 15: Number of incident angles in reflection, for anisotropy angle N°1
                nbAngleIncidenceLine = bfile.readline()
                nbAngleIncidence = int(nbAngleIncidenceLine.strip())
                for index_incidence in range(nbAngleIncidence):
                    samplerotation_list.append(samplerotation[index_samplerotation])
                    RT_list.append("BTDF")
                # Row 16: List of incident angles in reflection, for anisotropy angle N°1.
                angleIncidenceLine = bfile.readline()
                angleIncidenceString = angleIncidenceLine[:-1].split()
                angleIncidence = [float(i) for i in angleIncidenceString]
                angleIncidence_list.extend(angleIncidence)
                # Check that the angle of incidences are identical
                if index_samplerotation > 0 or reflectionortransmission[0] == 1:
                    if not angleIncidence == save_angleIncidence:
                        msg = "The angle of incidences must be identical for all the sample rotations."
                        raise TypeError(msg)
                save_angleIncidence = angleIncidence

        wavelength = []

        # Reflection
        if reflectionortransmission[0] == 1:
            # Row 17: Theta angle and a Phi angle for each spectrum measurement in reflection.
            theta_phi_reflection_reference_Line = bfile.readline()
            if bool_log == 1:
                print("Theta and Phi angles in reflection. = " + str(theta_phi_reflection_reference_Line))
            # Row 18: Reflective Spectrum description: wavelength (nm), coefficient (%)
            theta_phi_reflection_comment_Line = bfile.readline()
            if bool_log == 1:
                print("Reflection: wavelength (nm), coefficient (%) = " + str(theta_phi_reflection_comment_Line))
            # Row 19: Number of wavelength measurements in reflection
            nbWavelength_reflection_Line = bfile.readline()
            nbWavelength_reflection = int(nbWavelength_reflection_Line.strip())
            nbWavelength = nbWavelength_reflection
            # Row 20: Wavelength measurements in reflection (in nm). One wavelength takes one line.
            wavelength_reflection_list = []
            for index_wavelength in range(nbWavelength_reflection):
                Wavelength_reflection_Line = bfile.readline()
                Wavelength_reflection_String = Wavelength_reflection_Line[:-1].split()
                Wavelength_reflection = [float(i) for i in Wavelength_reflection_String]
                wavelength_reflection_list.append(Wavelength_reflection)
            index_middle_wavelength = int(len(wavelength_reflection_list) / 2)
            wavelength.append(wavelength_reflection_list[index_middle_wavelength][0])
            tisdata_list.append((wavelength_reflection_list[index_middle_wavelength][1]) / 100)
        # Transmission
        if reflectionortransmission[1] == 1:
            # Row 21: Theta angle and a Phi angle for each spectrum measurement in transmission.
            theta_phi_transmission_reference_Line = bfile.readline()
            if bool_log == 1:
                print("Theta and Phi angles in transmission. = " + str(theta_phi_transmission_reference_Line))
            # Row 22: Transmission Spectrum description: wavelength (nm), coefficient (%)
            theta_phi_transmission_comment_Line = bfile.readline()
            if bool_log == 1:
                print("Transmission: wavelength (nm), coefficient (%) = " + str(theta_phi_transmission_comment_Line))
            # Row 23: Number of wavelength measurements in transmission.
            nbWavelength_transmission_Line = bfile.readline()
            nbWavelength_transmission = int(nbWavelength_transmission_Line.strip())
            nbWavelength = nbWavelength + nbWavelength_transmission
            # Row 24: Wavelength measurements in transmission (in nm).
            wavelength_transmission_list = []
            for index_wavelength in range(nbWavelength_transmission):
                Wavelength_transmission_Line = bfile.readline()
                Wavelength_transmission_String = Wavelength_transmission_Line[:-1].split()
                Wavelength_transmission = [float(i) for i in Wavelength_transmission_String]
                wavelength_transmission_list.append(Wavelength_transmission)
            index_middle_wavelength = int(len(wavelength_transmission_list) / 2)
            if reflectionortransmission[0] == 0:
                wavelength.append(wavelength_transmission_list[index_middle_wavelength][0])
            tisdata_list.append((wavelength_transmission_list[index_middle_wavelength][1]) / 100)

        if bool_log == 1:
            print(".....Header was correctly read\n")
        # tempVariable = input('Press Enter to continue\n')

        if bool_log == 1:
            print("Reading BSDF content.....")

        # tisData = np.zeros((nb_reflection_transmission * nbAngleIncidence, nbWavelength))
        scatterRadial_temp_list = []
        scatterAzimuth_temp_list = []
        bsdfData_temp_list = []

        # reflection
        for index_block in range(len(angleIncidence_list)):
            nbthetaphiLine = bfile.readline()
            nbthetaphi = nbthetaphiLine[:-1].split()
            nbScatterRadial = int(nbthetaphi[0])
            nbScatterAzimuth = int(nbthetaphi[1])

            scatterAzimuthLine = bfile.readline()
            scatterAzimuthLineString = (scatterAzimuthLine[:-1].strip()).split()
            scatterAzimuth = [float(i) for i in scatterAzimuthLineString]
            scatterAzimuth_temp_list.append(scatterAzimuth)

            bsdfDataBlock = np.zeros((nbScatterRadial, nbScatterAzimuth))
            scatterRadial = []

            for k in range(nbScatterRadial):
                dataLine = bfile.readline()
                data = dataLine.split()
                scatterRadial.append(float(data[0]))
                bsdfDataBlock[k] = data[1:]

            # If transmission data
            if scatterRadial[0] >= 90:
                # change line theta from 90--> 180 to 0-->90
                temp = scatterRadial
                temp_180 = [180 - temp[index_temp] for index_temp in range(len(temp))]
                scatterRadial = temp_180[::-1]
                # swap the radial / theta of the bsdf_block
                bsdfDataBlock = swap_rows(bsdfDataBlock)

            scatterRadial_temp_list.append(scatterRadial)
            bsdfData_temp_list.append(bsdfDataBlock)

        # Need to reorder
        # BRDF: RT --> incidence --> wavelength
        # Format: RT --> wavelength --> incidence
        scatterRadial_list = []
        scatterAzimuth_list = []
        bsdfData_list = []

        for index_block in range(len(angleIncidence_list)):
            # tisdata_list.append(tisdata_temp_list[index_block]/100)
            wavelength_list.append(wavelength[0])
            scatterRadial_list.append(scatterRadial_temp_list[index_block])
            scatterAzimuth_list.append(scatterAzimuth_temp_list[index_block])
            bsdfData_list.append(bsdfData_temp_list[index_block])

        if bool_log == 1:
            print(".....BSDF data was correctly read\n")

        self.scattertype = scatterType
        self.symmetry = symmetry
        self.wavelength = wavelength
        self.samplerotation = samplerotation
        self.incidence = angleIncidence
        self.bsdfdata_scattertype = RT_list
        self.bsdfdata_wavelength = wavelength_list
        self.bsdfdata_samplerotation = samplerotation_list
        self.bsdfdata_incidence = angleIncidence_list
        self.bsdfdata_tisdata = tisdata_list
        self.bsdfdata_theta = scatterRadial_list
        self.bsdfdata_phi = scatterAzimuth_list
        self.bsdfdata = bsdfData_list

        # Convert intensity values to BSDF values
        if intensity_or_bsdf == 0:
            self.intensity_to_bsdf_data()

    def read_zemax_bsdf(self, bool_log):
        """
        That function reads a Zemax bsdf file

        Parameters
        ----------
        bool_log : boolean
            0 no report
            1 report values
        """

        # Reading file
        print("Reading Zemax BSDF file: " + str(self.filename_input) + "...\n")
        bfile = open(self.filename_input, "r")

        # Read the header
        if bool_log == 1:
            print("Reading header of Zemax BSDF.....")
        # Source type
        sourceLine = bfile.readline()
        while sourceLine[0] == "#" or len(sourceLine) < 6:
            sourceLine = bfile.readline()
        # source = sourceLine[8:-1]
        source = (sourceLine.split())[1]
        source = source.strip()
        if bool_log == 1:
            print("Source = " + str(source))
        # Symmetry type
        symmetryLine = bfile.readline()
        while symmetryLine[0] == "#":
            symmetryLine = bfile.readline()
        # symmetry = symmetryLine[10:-1]
        # symmetry = symmetryLine[8:-1]
        symmetry = (symmetryLine.split())[1]
        symmetry = symmetry.strip()
        if bool_log == 1:
            print("Symmetry = " + str(symmetry))
        # Spectral content type
        spectralContentLine = bfile.readline()
        while spectralContentLine[0] == "#":
            spectralContentLine = bfile.readline()
        # spectralContent = spectralContentLine[17:-1]
        # spectralContent = spectralContentLine[15:-1]
        spectralContent = (spectralContentLine.split())[1]
        spectralContent = spectralContent.strip()
        if bool_log == 1:
            print("Spectral content = " + str(spectralContent))
        # Scatter type
        scatterTypeLine = bfile.readline()
        while scatterTypeLine[0] == "#":
            scatterTypeLine = bfile.readline()
        # scatterType = scatterTypeLine[13:-1]
        # scatterType = str(scatterTypeLine[11:-1])
        scatterType = str(scatterTypeLine.split()[1])
        scatterType = scatterType.strip()
        if bool_log == 1:
            print("Scatter type = " + str(scatterType))
        # Number sample rotation
        sampleRotationLine = bfile.readline()
        while sampleRotationLine[0] == "#":
            sampleRotationLine = bfile.readline()
        # nbSampleRotation = int(sampleRotationLine[16:-1])
        # nbSampleRotation = int(sampleRotationLine[14:-1])
        sampleRotationLine = (sampleRotationLine.split())[1]
        nbSampleRotation = int(sampleRotationLine.strip())
        if bool_log == 1:
            print("Nb sample rotation = " + str(nbSampleRotation))
        # Sample rotation values
        sampleRotationLine = bfile.readline()
        while sampleRotationLine[0] == "#":
            sampleRotationLine = bfile.readline()
        # sampleRotation = sampleRotationLine[:-1].split('\t')
        sampleRotationString = sampleRotationLine[:-1].split()
        while sampleRotationString[-1] == "":
            sampleRotationString = sampleRotationString[:-1]
        if len(sampleRotationString) != nbSampleRotation:
            msg = "Wrong data for sample rotation values"
            raise TypeError(msg)
        else:
            sampleRotation = [float(i) for i in sampleRotationString]
            if bool_log == 1:
                print("Sample rotation angle values : " + str(sampleRotationString))
        # Number angle incidence
        angleIncidenceLine = bfile.readline()
        while angleIncidenceLine[0] == "#":
            angleIncidenceLine = bfile.readline()
        # nbAngleIncidence = int(angleIncidenceLine[18:-1])
        # nbAngleIncidence = int(angleIncidenceLine[16:-1])
        angleIncidenceLine = (angleIncidenceLine.split())[1]
        nbAngleIncidence = int(angleIncidenceLine.strip())
        if bool_log == 1:
            print("Nb angle incidence = " + str(nbAngleIncidence))
        # Angle incidence values
        angleIncidenceLine = bfile.readline()
        while angleIncidenceLine[0] == "#":
            angleIncidenceLine = bfile.readline()
        # Split can be tabular or white spaces
        # angleIncidence = angleIncidenceLine[:-1].split('\t')
        angleIncidenceString = angleIncidenceLine[:-1].split()
        while angleIncidenceString[-1] == "":
            angleIncidenceString = angleIncidenceString[:-1]
        if len(angleIncidenceString) != nbAngleIncidence:
            msg = "Wrong data for angle incidence values"
            raise TypeError(msg)
        else:
            angleIncidence = [float(i) for i in angleIncidenceString]
            if bool_log == 1:
                print("Angle incidence angle values : " + str(angleIncidenceString))
        # Number scatter azimuth
        scatterNbAzimuthLine = bfile.readline()
        while scatterNbAzimuthLine[0] == "#":
            scatterNbAzimuthLine = bfile.readline()
        # nbScatterAzimuth = int(scatterAzimuthLine[15:-1])
        # nbScatterAzimuth = int(scatterAzimuthLine[14:-1])
        nbScatterAzimuth = int((scatterNbAzimuthLine.split())[1])
        if bool_log == 1:
            print("Nb scatter azimuth = " + str(nbScatterAzimuth))
        # Scatter azimuth values
        scatterAzimuthLine = bfile.readline()
        while scatterAzimuthLine[0] == "#":
            scatterAzimuthLine = bfile.readline()
        # scatterAzimuth = scatterAzimuthLine[:-1].split('\t')
        scatterAzimuthString = scatterAzimuthLine[:-1].split()
        while scatterAzimuthString[-1] == "":
            scatterAzimuthString = scatterAzimuthString[:-1]
        if len(scatterAzimuthString) != nbScatterAzimuth:
            msg = "Wrong data for scatter azimuth values"
            raise TypeError(msg)
            # tempVariable = input(".....Press Enter to continue")
        else:
            scatterAzimuth = [float(i) for i in scatterAzimuthString]
            if bool_log == 1:
                print("Scatter azimuth angle values : " + str(scatterAzimuthString))
        # Number scatter radial
        scatterRadialLine = bfile.readline()
        while scatterRadialLine[0] == "#":
            scatterRadialLine = bfile.readline()
        # nbScatterRadial = int(scatterRadialLine[14:-1])
        # nbScatterRadial = int(scatterRadialLine[13:-1])
        scatterRadialLine = (scatterRadialLine.split())[1]
        nbScatterRadial = int(scatterRadialLine)
        if bool_log == 1:
            print("Nb scatter radial = " + str(nbScatterRadial))
        # Scatter radial values
        scatterRadialLine = bfile.readline()
        while scatterRadialLine[0] == "#":
            scatterRadialLine = bfile.readline()
        # scatterRadial = scatterRadialLine[:-1].split('\t')
        scatterRadialString = scatterRadialLine[:-1].split()
        while scatterRadialString[-1] == "":
            scatterRadialString = scatterRadialString[:-1]
        if len(scatterRadialString) != nbScatterRadial:
            msg = "WARNING: Wrong data for scatter radial values"
            raise TypeError(msg)
            # tempVariable = input(".....Press Enter to continue")
        else:
            scatterRadial = [float(i) for i in scatterRadialString]
            if bool_log == 1:
                print("Scatter radial angle values : " + str(scatterRadialString))
        if bool_log == 1:
            print(".....Header was correctly read\n")
        # tempVariable = input('Press Enter to continue\n')

        if bool_log == 1:
            print("Reading BSDF content.....")
        dataLine = bfile.readline()
        while dataLine[0:9] != "DataBegin":
            dataLine = bfile.readline()
        # Initialization of a bsdfData list
        # Initialization of a vector tisData to save the TIS at each sample rotation and angle of incidence

        bsdfData_list = []
        theta_list = []
        phi_list = []
        wavelength_list = []
        # tisData = np.zeros((nbSampleRotation, nbAngleIncidence))
        tisData_list = []
        scattertype_list = []
        scattertype_data_list = []
        sampleRotation_list = []
        angleIncidence_list = []

        scattertype_list.append(scatterType)

        for index_samplerotation in range(nbSampleRotation):
            for index_incidence in range(nbAngleIncidence):
                # Reading TIS (Total Integrated Scatter) value
                tisLine = bfile.readline()
                # tisData[index_samplerotation][index_incidence] = float(tisLine[4:-1])
                tisData_list.append(float(tisLine[4:-1]))
                wavelength_list.append(0.55)
                sampleRotation_list.append(sampleRotation[index_samplerotation])
                angleIncidence_list.append(angleIncidence[index_incidence])
                scattertype_data_list.append(scatterType)
                bsdfData_block = np.zeros((nbScatterAzimuth, nbScatterRadial))
                for index_phi in range(nbScatterAzimuth):
                    dataLine = bfile.readline()
                    bsdfData_block[index_phi] = dataLine.split()
                bsdfData_list.append(bsdfData_block.transpose())
                theta_list.append(scatterRadial)
                phi_list.append(scatterAzimuth)

        if bool_log == 1:
            print(".....BSDF data was correctly read\n")

        self.scattertype = scattertype_list
        self.symmetry = symmetry
        self.wavelength = [0.55]
        self.samplerotation = sampleRotation
        self.incidence = angleIncidence
        self.bsdfdata_wavelength = wavelength_list
        self.bsdfdata_scattertype = scattertype_data_list
        self.bsdfdata_samplerotation = sampleRotation_list
        self.bsdfdata_incidence = angleIncidence_list
        self.bsdfdata_tisdata = tisData_list
        self.bsdfdata_theta = theta_list
        self.bsdfdata_phi = phi_list
        self.bsdfdata = bsdfData_list

    def converter_coordinate_system_bsdf(self, bool_normal_1, bool_log):
        """
        That function converts the coordinate system of the bsdf data
        On import, the data is converted to the local surface coordinate system
        On export, the data is converted to the exported file coordinate system
        For Zemax, specular and for Speos, local surface coordinate system

        Parameters
        ----------
        bool_normal_1 : boolean
            0 to convert to normal BSDF data to specular
            1 to convert specular BSDF data to normal
        bool_log : boolean
            0 no report
            1 report values

        Returns
        -------


        """

        print("Converting data...\n")

        line_theta_output_list, line_phi_output_list = phi_theta_output(
            self.bsdfdata_theta, self.bsdfdata_phi, self.zemax_or_speos
        )
        line_theta_output = line_theta_output_list[0]
        line_phi_output = line_phi_output_list[0]

        # nb_wavelength = len(self.wavelength)
        # nb_samplerotation = len(self.samplerotation)
        # nb_angleofincidence = len(self.incidence)
        # nb_reflection_transmission = len(self.scattertype)
        # bsdf_output = self.bsdf

        # index_block = 0

        for index_block in range(len(self.bsdfdata_incidence)):
            current_angleofincidence = self.bsdfdata_incidence[index_block]
            if len(self.bsdfdata_theta) == 1:
                line_theta_input = self.bsdfdata_theta[0]
                line_phi_input = self.bsdfdata_phi[0]
            else:
                line_theta_input = self.bsdfdata_theta[index_block]
                line_phi_input = self.bsdfdata_phi[index_block]
            bsdfData_output_block = np.zeros((len(line_theta_output), len(line_phi_output)))

            for index_theta in range(len(line_theta_output)):
                currentTheta = line_theta_output[index_theta]
                for index_phi in range(len(line_phi_output)):
                    currentPhi = line_phi_output[index_phi]

                    if bool_normal_1 == 1:
                        # Convert the angles to the "specular" definition
                        newTheta, newPhi = convert_normal_to_specular_using_cartesian(
                            currentTheta, currentPhi, current_angleofincidence
                        )
                        # Added the case where symmetry == PlaneSymmetrical
                        if self.symmetry == "PlaneSymmetrical" and newPhi > 180:
                            newPhi = 360 - newPhi
                    else:
                        # Convert the angles to the "normal" definition
                        newTheta, newPhi = convert_specular_to_normal_using_cartesian(
                            currentTheta, currentPhi, current_angleofincidence
                        )

                    bsdfData_output_block[index_theta][index_phi] = compute_new_value_matrix(
                        self.bsdfdata[index_block], line_theta_input, line_phi_input, newTheta, newPhi
                    )
            self.bsdfdata[index_block] = bsdfData_output_block
            index_block = index_block + 1

        self.bsdfdata_theta = line_theta_output_list
        self.bsdfdata_phi = line_phi_output_list

    def normalize_bsdf_data(self, bool_log):
        """
        That function normalizes the BSDF data vs the TIS values

        Parameters
        ----------
        bool_log : boolean
            0 no report
             1 report values

        Returns
        -------


        """

        if bool_log == 1:
            print("Computing normalization...")
            print("nbSampleRotation nbAngleIncidence IntegralValue IntegralError Zemax_TIS_value NormalizationFactor")

        # Initialization
        normalizationBsdf = []

        for index_block in range(len(self.bsdfdata_incidence)):
            block_data = np.transpose(self.bsdfdata[index_block])

            theta_rad, phi_rad = np.radians(self.bsdfdata_theta[0]), np.radians(
                self.bsdfdata_phi[0]
            )  # samples on which integrande is known
            integrande = (
                (1 / math.pi) * block_data * np.sin(theta_rad) * np.cos(theta_rad)
            )  # *theta for polar integration
            # Linear interpolation of the values
            # interp2d is apparently deprecated
            # Look for alternatives f = interpolate.bisplrep(theta_rad, phi_rad, integrande)
            f = interpolate.RectBivariateSpline(phi_rad, theta_rad, integrande, kx=1, ky=1)
            # calculation of the integral
            # r = nquad(f, [[0, math.pi / 2], [0, 2 * math.pi]], opts=[{"epsabs": 0.1}, {"epsabs": 0.1}])
            r = nquad(
                f,
                [[min(theta_rad), max(theta_rad)], [min(phi_rad), max(phi_rad)]],
                opts=[{"epsabs": 0.1}, {"epsabs": 0.1}],
            )
            IntegralValue = abs(r[0])
            IntegralError = r[1]

            # Normalization of the data
            if IntegralValue > 0:
                normalizationBsdf.append(self.bsdfdata_tisdata[index_block] / (IntegralValue))
            else:
                normalizationBsdf.append(1)
                print("Integral <= 0!!!!")
            if bool_log == 1:
                print(
                    self.bsdfdata_samplerotation[index_block],
                    " ",
                    self.bsdfdata_incidence[index_block],
                    " ",
                    round(IntegralValue, 3),
                    " ",
                    round(IntegralError, 3),
                    " ",
                    self.bsdfdata_tisdata[index_block],
                    " ",
                    round(normalizationBsdf[index_block], 3),
                )
            self.bsdfdata[index_block] = self.bsdfdata[index_block] * normalizationBsdf[index_block]
            index_block = index_block + 1

    def calculate_tis_data(self, bool_log):
        """
        That function computes the TIS values from the BSDF data

        Parameters
        ----------
        bool_log : boolean
            0 no report
            1 to report values

        """

        if bool_log == 1:
            print("Computing normalization...")
            print("nbSampleRotation nbAngleIncidence IntegralValue IntegralError Zemax_TIS_value")

        for index_block in range(len(self.bsdfdata_incidence)):
            block_data = np.transpose(self.bsdfdata[index_block])

            theta_rad, phi_rad = np.radians(self.bsdfdata_theta[index_block]), np.radians(
                self.bsdfdata_phi[index_block]
            )  # samples on which integrande is known
            integrande = (
                (1 / math.pi) * block_data * np.sin(theta_rad) * np.cos(theta_rad)
            )  # *theta for polar integration
            # Linear interpolation of the values
            # interp2d is apparently deprecated
            # Look for alternatives f = interpolate.bisplrep(theta_rad, phi_rad, integrande)
            f = interpolate.RectBivariateSpline(phi_rad, theta_rad, integrande, kx=1, ky=1)
            # calculation of the integral
            # r = nquad(f, [[0, math.pi / 2], [0, 2 * math.pi]], opts=[{"epsabs": 0.1}, {"epsabs": 0.1}])
            r = nquad(
                f,
                [[min(theta_rad), max(theta_rad)], [min(phi_rad), max(phi_rad)]],
                opts=[{"epsabs": 0.1}, {"epsabs": 0.1}],
            )
            IntegralValue = abs(r[0])
            IntegralError = r[1]

            if index_block == 0:
                tis_value = self.bsdfdata_tisdata[0]
                normalization = self.bsdfdata_tisdata[0] / IntegralValue
            else:
                tis_value = IntegralValue * normalization
                self.bsdfdata_tisdata.append(tis_value)
            if bool_log == 1:
                print(
                    self.bsdfdata_samplerotation[index_block],
                    " ",
                    self.bsdfdata_incidence[index_block],
                    " ",
                    round(IntegralValue, 3),
                    " ",
                    round(IntegralError, 3),
                    " ",
                    self.bsdfdata_tisdata[index_block],
                )
            index_block = index_block + 1

    def write_zemax_file(self, bool_log):
        """
        Writes Zemax bsdf files
        That function will write one Zemax file per wavelength and scatter type (BTDF or BRDF)

        Parameters
        ----------
        bool_log : boolean
            0 no report
            1 report values

        """
        # Writing a Zemax file for each wavelength
        self.converter_coordinate_system_bsdf(0, bool_log)
        self.bsdfdata_theta = self.bsdfdata_theta[0]
        self.bsdfdata_phi = self.bsdfdata_phi[0]

        # Writing a Zemax file for each wavelength
        print("Writing Zemax data\n")

        for index_RT in range(len(self.scattertype)):
            if self.scattertype[index_RT] == "BRDF":
                for index_wavelength in range(len(self.wavelength)):
                    nLines_header = self.write_zemax_header_bsdf(index_RT, index_wavelength)
                    nLines_data = self.write_zemax_data_bsdf(index_RT, index_wavelength)

                    # Writing Zemax file content (nLines) in a file
                    outputFilepath = (
                        os.path.splitext(self.filename_input)[0].lower()
                        + "_"
                        + str(self.wavelength[index_wavelength])
                        + "_"
                        + str(self.scattertype[index_RT])
                        + ".bsdf"
                    )
                    write_file(outputFilepath, nLines_header + nLines_data)

    def write_zemax_header_bsdf(self, index_RT, index_wavelength):
        """
        That function writes the header of a Zemax BSDF file

        Parameters
        ----------
        index_RT : integer
            integer that gives the scatter type
            0 for BRDF
            1 for BTDF
        index_wavelength : integer
            index that gives the wavelength

        """

        # Header
        nLines = ["#Data converted from Speos data\n"]
        # Wavelength
        comment = "#Wavelength (nm) = " + str(self.wavelength[index_wavelength])
        nLines.append(str(comment) + "\n")
        # Source
        comment = "Source  Measured"
        nLines.append(str(comment) + "\n")
        # Symmetry
        nLines.append("Symmetry  " + str(self.symmetry) + "\n")
        # SpectralContent
        spectralcontent = "SpectralContent  Monochrome"
        nLines.append(str(spectralcontent) + "\n")
        # ScatterType
        ScatterType = "ScatterType  " + str(self.scattertype[index_RT])
        nLines.append(ScatterType + "\n")
        # SampleRotation
        nLines.append("SampleRotation  " + str(len(self.samplerotation)) + "\n")
        # List of SampleRotation
        for i in range(len(self.samplerotation)):
            nLines.append(str(self.samplerotation[i]) + "\t")
        nLines.append("\n")
        # AngleOfIncidence
        nLines.append("AngleOfIncidence  " + str(len(self.incidence)) + "\n")
        # List of AngleOfIncidence
        for i in range(len(self.incidence)):
            nLines.append(str(self.incidence[i]) + "\t")
        nLines.append("\n")
        # List of ScatterAzimuth
        nLines.append("ScatterAzimuth " + str(len(self.bsdfdata_phi)) + "\n")
        for i in range(len(self.bsdfdata_phi)):
            nLines.append(str(self.bsdfdata_phi[i]) + "\t")
        nLines.append("\n")
        # List of ScatterRadial
        nLines.append("ScatterRadial " + str(len(self.bsdfdata_theta)) + "\n")
        for i in range(len(self.bsdfdata_theta)):
            nLines.append(str(self.bsdfdata_theta[i]) + "\t")
        nLines.append("\n")
        # A few more lines
        nLines.append("\n")
        nLines.append("Monochrome\n")
        nLines.append("DataBegin\n")

        return nLines

    def write_zemax_data_bsdf(self, index_RT, index_wavelength):
        """
        That function writes the main data of Zemax BSDF file

        Parameters
        ----------
        index_RT : integer
            integer that gives the scatter type
            0 for BRDF
            1 for BTDF
        index_wavelength : integer
            index that gives the wavelength

        """

        nLines = []
        nb_angleofincidence = len(self.incidence)
        nb_wavelength = len(self.wavelength)
        nb_samplerotation = len(self.samplerotation)

        for index_samplerotation in range(len(self.samplerotation)):
            for index_angleofincidence in range(len(self.incidence)):
                index_data = (
                    index_RT * nb_wavelength * nb_samplerotation
                    + index_wavelength * nb_samplerotation
                    + index_samplerotation
                ) * nb_angleofincidence + index_angleofincidence
                nLines.append("TIS " + str(round(self.bsdfdata_tisdata[index_data], 3)) + "\n")
                for index_phi in range(len(self.bsdfdata_phi)):
                    for index_theta in range(len(self.bsdfdata_theta) - 1):
                        scientific_notation = "{:.3e}".format(self.bsdfdata[index_data][index_theta][index_phi])
                        nLines.append(str(scientific_notation) + "\t")
                    index_theta = len(self.bsdfdata_theta) - 1
                    scientific_notation = "{:.3e}".format(self.bsdfdata[index_data][index_theta][index_phi])
                    nLines.append(str(scientific_notation) + "\n")
        nLines.append("DataEnd\n")

        return nLines

    def write_speos_anisotropicbsdf_file(self):
        """
        That function writes a Speos anisotropicbsdf file

        Returns
        -------


        """
        # Writing a Speos file
        print("Writing Speos data\n")
        nLines = self.write_speos_header_anisotropicbsdf()
        nLines = self.write_speos_data_anisotropicbsdf(nLines)
        outputFilepath = os.path.splitext(self.filename_input)[0].lower() + ".anisotropicbsdf"
        write_file(outputFilepath, nLines)

    def write_speos_header_anisotropicbsdf(self):
        """
        That function writes the header of a Speos anisotropicbsdf file

        Returns
        -------
        nLines: string
            string containing the header of the Speos anisotropicbsdf file
        """

        nbSampleRotation = len(self.samplerotation)
        nbAngleIncidence = len(self.incidence)
        binaryMode = 0
        anisotropyVector = [0, 1, 0]

        measurementDescription = "Measurement description"
        comment = "Comment"

        # Header
        nLines = ["OPTIS - Anisotropic BSDF surface file v8.0\n"]
        # Binary mode
        nLines.append(str(binaryMode) + "\n")
        # Comment
        nLines.append(comment + "\n")
        # Measurement description
        nLines.append(str(len(measurementDescription)) + "\n")
        nLines.append(measurementDescription + "\n")
        # Anisotropy vector
        nLines.append(
            str(anisotropyVector[0]) + "\t" + str(anisotropyVector[1]) + "\t" + str(anisotropyVector[2]) + "\n"
        )
        # Scatter type (BRDF/BTDF)
        # Type of values
        # 1 means the data is proportional to the BSDF data
        # 0 means the data is proportional to the measured intensity
        # For BTDF: valuesType = 0 because of a bug
        if self.scattertype[0] == "BRDF":
            nLines.append("1" + "\t" + "0" + "\n")
            valuesType = 1
            nLines.append(str(valuesType) + "\n")
        elif self.scattertype[0] == "BTDF":
            nLines.append("0" + "\t" + "1" + "\n")
            valuesType = 0
            nLines.append(str(valuesType) + "\n")
        else:
            print(".....WARNING: Original data file has no valid ScatterType")
            # tempVariable = input(".....Press Enter to continue")
        # Anisotropy angles (SampleRotations)
        nLines.append(str(nbSampleRotation) + "\n")
        for i in range(nbSampleRotation):
            nLines.append(str(self.samplerotation[i]) + "\t")
        if nbSampleRotation != 0:
            nLines.append("\n")
        # Incident angles (AngleIncidence)
        for k in range(nbSampleRotation):
            nLines.append(str(nbAngleIncidence) + "\n")
            for i in range(nbAngleIncidence):
                nLines.append(str(self.bsdfdata_incidence[i]) + "\t")
            if nbAngleIncidence != 0:
                nLines.append("\n")
        # theta and phi for measurement
        nLines.append(str(self.bsdfdata_incidence[0]) + "\t" + "0\n")
        # Spectrum description
        nLines.append("\n")
        # Number of wavelength
        nLines.append("2" + "\n")
        # Wavelength measurements
        nLines.append("350" + "\t" + str(100 * self.bsdfdata_tisdata[0]) + "\n")
        nLines.append("850" + "\t" + str(100 * self.bsdfdata_tisdata[0]) + "\n")

        return nLines

    def write_speos_data_anisotropicbsdf(self, nLines):
        """
        That function writes the main data of a Speos anisotropicbsdf file
        Parameters
        ----------
        nLines : string
            string containing the header of the Speos anisotropicbsdf file
        Returns
        -------
        nLines : string
            string containing the text of the Speos anisotropicbsdf file

        """

        self.bsdfdata_theta = self.bsdfdata_theta[0]
        self.bsdfdata_phi = self.bsdfdata_phi[0]

        nbtheta = len(self.bsdfdata_theta)
        nbphi = len(self.bsdfdata_phi)
        index_block = 0

        # If transmission data
        if self.scattertype[0] == "BTDF":
            # change line theta from 90--> 180 to 0-->90
            temp = self.bsdfdata_theta
            temp_180 = [180 - temp[index_theta] for index_theta in range(len(temp))]
            self.bsdfdata_theta = temp_180[::-1]

        for index_samplerotation in range(len(self.samplerotation)):
            for index_incidence in range(len(self.incidence)):
                nLines.append(str(int(nbtheta)) + " " + str(int(nbphi)) + "\n")

                # Write the 1st line of the block with the Phi values
                for index_phi in range(nbphi):
                    currentPhi = self.bsdfdata_phi[index_phi]
                    nLines.append("\t" + str(currentPhi))
                nLines.append("\n")

                if self.scattertype[0] == "BTDF":
                    self.bsdfdata[index_block] = swap_rows(self.bsdfdata[index_block])

                for index_theta in range(nbtheta):
                    currentTheta = self.bsdfdata_theta[index_theta]
                    nLines.append(str(currentTheta))
                    for index_phi in range(nbphi):
                        if self.scattertype[0] == "BRDF":
                            nLines.append("\t" + str(self.bsdfdata[index_block][index_theta][index_phi]))
                        elif self.scattertype[0] == "BTDF":
                            thetas_cosine = math.cos((180 - currentTheta) * math.pi / 180)
                            nLines.append(
                                "\t" + str(thetas_cosine * self.bsdfdata[index_block][index_theta][index_phi])
                            )
                    nLines.append("\n")
                index_block = index_block + 1
        nLines.append("End of file")
        nLines.append("\n")

        return nLines

    def convert_rgb_to_spectrum_value(self, rgb_tuple, wavelength):
        """
        function to convert an RGB tuple to a spectrum
        Parameters
        ----------
        wavelength: float
            wavelength of conversion
        rgb_tuple: tuple
            3 floats of RGB
        Returns
        -------
        spectrumvalue at wavelength: floats
        """

        r, b, g = rgb_tuple
        red_spectral_representation = [
            1.28,
            1.28,
            1.28,
            1.28,
            1.28,
            1.28,
            1.28,
            1.28,
            1.28,
            1.28,
            1.28,
            1.28,
            1.28,
            1.28,
            1.29,
            1.3,
            1.34,
            1.44,
            1.7,
            2.27,
            3.48,
            5.81,
            9.93,
            16.6,
            26.4,
            39.4,
            55,
            71.4,
            86.1,
            96.3,
            100,
            96.3,
            86.1,
            71.4,
            55,
            39.4,
            26.4,
            16.6,
            9.93,
            5.81,
            3.48,
            2.27,
            1.7,
            1.44,
            1.34,
            1.3,
            1.29,
            1.28,
        ]
        green_spectral_representation = [
            4.13245e-05,
            0.000203619,
            0.000915526,
            0.00375632,
            0.0140636,
            0.0480473,
            0.14979,
            0.426124,
            1.10619,
            2.62039,
            5.66423,
            11.1727,
            20.11,
            33.0301,
            49.5047,
            67.7056,
            84.4972,
            96.2279,
            100,
            94.8286,
            82.0577,
            64.7947,
            46.6875,
            30.6974,
            18.418,
            10.0838,
            5.03789,
            2.29674,
            0.955466,
            0.36271,
            0.125645,
            0.0397163,
            0.011456,
            0.00301537,
            0.000724246,
            0.000158735,
            3.17468e-05,
            5.79386e-06,
            9.64886e-07,
            1.46631e-07,
            2.03336e-08,
            2.57302e-09,
            2.97107e-10,
            3.13057e-11,
            3.01006e-12,
            2.64099e-13,
            2.11445e-14,
            1.54479e-15,
        ]
        blue_spectral_representation = [
            1.36,
            2.27,
            4.57,
            9.61,
            19,
            34.1,
            54.1,
            75.6,
            92.8,
            100,
            94.5,
            78.4,
            57.1,
            36.6,
            20.8,
            10.6,
            5.07,
            2.48,
            1.44,
            1.08,
            0.97,
            0.942,
            0.935,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
            0.934,
        ]
        return (
            (
                r * self.get_srgb_spectrum_at_wavelength(red_spectral_representation, 360.0, 830.0, wavelength)
                + g * self.get_srgb_spectrum_at_wavelength(green_spectral_representation, 360.0, 830.0, wavelength)
                + b * self.get_srgb_spectrum_at_wavelength(blue_spectral_representation, 360.0, 830.0, wavelength)
            )
            / 100.0
            @ staticmethod
        )

    @staticmethod
    def get_srgb_spectrum_at_wavelength(conversion_spectrum, wl_start, wl_end, wl):
        """
        Method to extrapolar
        Parameters
        ----------
        conversion_spectrum: list
            Spectrum data in % values 0-100
        wl_start: float
            start wavelength in nm
        wl_end: float
            end wavelength in nm
        Returns
        -------
        spectrum value in % 0-100
        """

        interval_items = len(conversion_spectrum) - 1
        lambda_increment = (wl_end - wl_start) / interval_items
        if wl <= wl_start:
            return conversion_spectrum[0]
        elif wl >= wl_end:
            return conversion_spectrum[interval_items]
        pos = (wl - wl_start) / lambda_increment
        pos_integer = int(pos)
        pos_fractional = int(pos) - pos
        slope = conversion_spectrum[pos_integer + 1] - conversion_spectrum[pos_integer]
        return conversion_spectrum[pos_integer] + pos_fractional * slope

    def intensity_to_bsdf_data(self):
        """
        That function converts intensity values into BSDF values

        """
        bsdf_block = []
        for index_block in range(len(self.bsdfdata)):
            bsdf_block = self.bsdfdata[index_block]
            bsdf_block_theta = self.bsdfdata_theta[index_block]

            for index_theta in range(len(bsdf_block_theta)):
                currentTheta = bsdf_block_theta[index_theta]
                thetas_cosine = math.cos((currentTheta) * math.pi / 180)
                if thetas_cosine != 0.0:
                    bsdf_block[index_theta] = bsdf_block[index_theta] / thetas_cosine

            self.bsdfdata[index_block] = bsdf_block


def convert_normal_to_specular_using_cartesian(theta_i, phi_i, angle_inc):
    """
    That function converts from normal to specular reference using cartesian coordinates
    phi_i = 0 in the normal reference = phi_o = 180 in the specular reference

    Parameters
    ----------
    theta_i : float
        Scattered polar angle in the normal reference
    phi_i : float
        Scattered azimuthal angle in the normal reference
    angle_inc : float
        Angle of incidence

    Returns
    -------
    theta_o : float
        Scattered polar angle in the specular reference
    phi_o : float
        Scattered azimuthal angle in the specular reference
    """

    # spherical coordinates in normal reference
    theta_i *= math.pi / 180
    phi_i *= math.pi / 180
    # Conversion to cartesian coordinates
    x_i = math.sin(theta_i) * math.cos(phi_i)
    y_i = math.sin(theta_i) * math.sin(phi_i)
    z_i = math.cos(theta_i)
    # Conversion to new specular cartesian coordinates
    x_o = x_i * math.cos(angle_inc * math.pi / 180) - z_i * math.sin(angle_inc * math.pi / 180)
    y_o = y_i
    z_o = x_i * math.sin(angle_inc * math.pi / 180) + z_i * math.cos(angle_inc * math.pi / 180)
    # Normalization
    norm = math.sqrt(x_o * x_o + y_o * y_o + z_o * z_o)
    x_o *= 1 / norm
    y_o *= 1 / norm
    z_o *= 1 / norm
    # Conversion to new spherical coordinates
    theta_o = math.acos(z_o) * (180 / math.pi)

    if x_o == 0:
        if y_o == 0:
            phi_o = 0
        if y_o > 0:
            phi_o = 90
        if y_o < 0:
            phi_o = 270
    else:
        phi_o = math.atan(y_o / x_o) * (180 / math.pi)
        if x_o < 0:
            phi_o = 180 + phi_o
        if x_o > 0 and y_o < 0:
            phi_o = 360 + phi_o

    # added lines to change phi ref
    if phi_o < 180:
        phi_o = phi_o + 180
    else:
        phi_o = phi_o - 180

    return (theta_o, phi_o)


def convert_specular_to_normal_using_cartesian(theta_i, phi_i, angle_inc):
    """
    That function converts from specular to normal reference using cartesian coordinates
    Specular reference: phi = 0 top of the plot
    Normal reference: phi = 0 bottom of the plot

    Parameters
    ----------
    theta_i : float
        Scattered polar angle in the specular reference
    phi_i : float
        Scattered azimuthal angle in the specular reference
    angle_inc : float
        Angle of incidence

    Returns
    -------
    theta_o : float
        Scattered polar angle in the normal reference
    phi_o : float
        Scattered azimuthal angle in the normal reference

    """

    # spherical coordinates in normal reference
    theta_i *= math.pi / 180
    phi_i *= math.pi / 180
    # Conversion to cartesian coordinates
    x_i = math.sin(theta_i) * math.cos(phi_i)
    y_i = math.sin(theta_i) * math.sin(phi_i)
    z_i = math.cos(theta_i)
    # Conversion to new normal cartesian coordinates
    x_o = -x_i * math.cos(angle_inc * math.pi / 180) + z_i * math.sin(angle_inc * math.pi / 180)  # to check
    y_o = y_i
    z_o = x_i * math.sin(angle_inc * math.pi / 180) + z_i * math.cos(angle_inc * math.pi / 180)  # to check
    # Normalization
    norm = math.sqrt(x_o * x_o + y_o * y_o + z_o * z_o)
    x_o *= 1 / norm
    y_o *= 1 / norm
    z_o *= 1 / norm
    # Conversion to new spherical coordinates
    theta_o = math.acos(z_o) * (180 / math.pi)

    if round(x_o, 2) == 0:
        if round(y_o, 0) == 0:
            phi_o = phi_i * (180 / math.pi)
        if y_o > 0:
            phi_o = 270
        if y_o < 0:
            phi_o = 90
    else:
        phi_o = abs(math.atan2(y_o, x_o) * (180 / math.pi))
        if round(y_o, 3) > 0:
            phi_o = 360 - phi_o

    theta_o = round(theta_o, 2)
    phi_o = round(phi_o, 2)

    return (theta_o, phi_o)


def compute_new_value_matrix(matrix_z, line_x, line_y, new_x, new_y):
    """
    That function takes (x,y) as an argument and returns a new interpolated value from a matrix[x,y]

    Parameters
    ----------
    matrix_z : matrix of z values
        matrix giving a z value for a set of x,y values Z(x,y)
    line_x : list
        List of x
    line_y : list
        List of y
    new_x : flaot
        New x value
    new_y : flaot
        New y value

    Returns
    -------
    newValue: float
        newValue = Z(new_x,new_y)
    """

    index_x = bisect.bisect_left(line_x, new_x)
    if index_x == 0:
        indexInf_x = index_x
        indexSup_x = index_x
        coeff_x = 0
    elif index_x <= (len(line_x) - 1):
        # Sandrine: added +1
        indexInf_x = index_x - 1
        indexSup_x = index_x
        x_Inf = line_x[indexInf_x]
        x_Sup = line_x[indexSup_x]
        coeff_x = (new_x - x_Inf) / (x_Sup - x_Inf)
    else:
        newValue = 0
        return newValue

    index_y = bisect.bisect_left(line_y, new_y)
    if index_y == 0:
        indexInf_y = index_y
        indexSup_y = index_y
        coeff_y = 0
    elif index_y <= (len(line_y) - 1):
        indexInf_y = index_y - 1
        indexSup_y = index_y
        y_Inf = line_y[indexInf_y]
        y_Sup = line_y[indexSup_y]
        coeff_y = (new_y - y_Inf) / (y_Sup - y_Inf)
    else:
        newValue = 0
        return newValue

    # Linear interpolation
    value_Inf_x = matrix_z[indexInf_x][indexInf_y] * (1 - coeff_y) + matrix_z[indexInf_x][indexSup_y] * coeff_y
    value_Sup_x = matrix_z[indexSup_x][indexInf_y] * (1 - coeff_y) + matrix_z[indexSup_x][indexSup_y] * coeff_y
    newValue = value_Inf_x * (1 - coeff_x) + value_Sup_x * coeff_x
    return newValue


def swap_columns(arr):
    """
    That function swap columns of an array
    If the columns go from 1 to N, after swapping they go from N to 1

    Parameters
    ----------
    arr : array
        original array

    """
    arr_temp = np.zeros((arr.shape[0], arr.shape[1]))
    nb_columns = arr.shape[1]

    for index_column in range(nb_columns):
        arr_temp[:, index_column] = arr[:, nb_columns - 1 - index_column]

    return arr_temp


def swap_rows(arr):
    """
    That function swap rows of an array
    If the rows go from 1 to N, after swapping they go from N to 1

    Parameters
    ----------
    arr : array
        original array

    """
    arr_temp = np.zeros((arr.shape[0], arr.shape[1]))
    nb_rows = arr.shape[0]

    for index_row in range(nb_rows):
        arr_temp[index_row, :] = arr[nb_rows - 1 - index_row, :]

    return arr_temp


def write_file(outputFilepath, nLines):
    """
    That function writes the text nLines in the file

    Parameters
    ----------
    outputFilepath : filename
        file to write
    nLines : string
        text containing the content of the file

    """

    nFile = open(outputFilepath, "w")
    nFile.writelines(nLines)
    nFile.close()
    print("The file " + str(outputFilepath) + " is ready!")


def phi_theta_output(theta_input, phi_input, zemax_or_speos):
    """
    That function gives a unique theta list and a phi list for all the BSDF block

    Parameters
    ----------
    theta_input : list
        list of all the theta inputs per BSDF block
    phi_input : list
        list of all the phi inputs per BSDF block
    zemax_or_speos : string
        zemax or speos imported data

    Returns
    -------
    theta_output: list
        list of the theta output angles
    phi_output : list
        list of the phi output angles

    """

    theta_output = []
    phi_output = []

    # Limitation
    nbTheta_max = 1000
    nbPhi_max = 1000
    if zemax_or_speos == "speos":
        theta_max = 180
    else:
        theta_max = 90
    phi_max = 360

    # Default values
    precisionTheta = theta_input[0][1] - theta_input[0][0]
    precisionPhi = phi_input[0][1] - phi_input[0][0]

    nbTheta = int(theta_max / precisionTheta) + 1
    nbPhi = int(phi_max / precisionPhi) + 1

    if nbTheta > nbTheta_max:
        precisionTheta = 0.1
        nbTheta = int(theta_max / precisionTheta) + 1
    if nbPhi > nbPhi_max:
        precisionPhi = 0.5
        nbPhi = int(phi_max / precisionPhi) + 1

    print(
        "Phi and Theta spacings are uniform in the converted format.\n"
        "It may result in a loss of accuracy in some cases."
    )
    print("Precision Theta = ", precisionTheta)
    print("Precision Phi = ", precisionPhi)

    theta_output.append([(precisionTheta * k) for k in range(nbTheta)])
    phi_output.append([(precisionPhi * x) for x in range(nbPhi)])

    return theta_output, phi_output
