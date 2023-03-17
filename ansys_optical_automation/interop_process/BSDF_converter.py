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
        self.filename_input = None
        self.bool_success = 0
        self.zemax_or_speos = None
        self.scattertype = None
        self.symmetry = None
        self.wavelength = None
        self.samplerotation = None
        self.incidence = None
        self.tisdata = {"wavelength","sample_rotation","angleofincidence"}
        self.theta_input = {"wavelength", "sample_rotation", "angleofincidence"}
        self.phi_input = {"wavelength", "sample_rotation", "angleofincidence"}
        self.theta = {"wavelength", "sample_rotation", "angleofincidence"}
        self.phi = {"wavelength", "sample_rotation", "angleofincidence"}
        self.bsdf_input = {"wavelength", "sample_rotation", "angleofincidence", "theta", "phi"}
        self.bsdf = {"transmission_reflection",
                     "wavelength",
                     "sample_rotation",
                     "angleofincidence",
                     "theta",
                     "phi"}

    def import_data(self,inputFilepath,bool_log=True):
        self.filename_input = inputFilepath
        input_file_extension = os.path.splitext(inputFilepath)[1].lower()[0:]
        if not ("bsdf" in input_file_extension or "brdf" in input_file_extension):
            msg = "Nonsupported file selected"
            raise TypeError(msg)
        if "bsdf" in input_file_extension:
            self.zemax_or_speos = "zemax"
            self.read_zemax_bsdf(bool_log)
            self.phi_theta_output()
            self.converter_coordinate_system_bsdf(bool_log)
            self.normalize_bsdf_data(bool_log)

        if "brdf" in input_file_extension:
            self.zemax_or_speos = "speos"
            self.read_speos_brdf(bool_log)
            self.phi_theta_output()
            self.converter_coordinate_system_bsdf(bool_log)

    def read_speos_brdf(self, bool_log):
        """
        That function reads Speos BSDF file

        Parameters
        ----------
        inputFilepath : string
            BSDF filename
        bool_log : boolean
            0 --> no report / 1 --> reports values

        """

        # Reading file
        print("Reading Speos BSDF file: " + str(self.filename_input) + "...\n")
        self.bool_success = 1

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
            bool_success = 0
            print(".....WARNING: The format is not supported.")
            print(".....Open and save the file with the BSDF viewer to update the format.")
            input(".....Press Enter to continue")
            exit()
        if bool_log == 1:
            print("Header = " + str(headerLine))
        # Row 2 : text 0 or binary 1
        textorbinaryLine = bfile.readline()
        textorbinary = textorbinaryLine[:-1].split("\t")
        if textorbinary[0] == 0:
            bool_success = 0
            print(".....WARNING: The BSDF data cannot be read. It is not a text.")
            input(".....Press Enter to continue")
            exit()
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
        if bool_log == 1:
            print("BSDF(1) or Intensity(1) values = " + str(typeLine))
        # Row 8: Number of incident angles and number of wavelength samples (in nanometer).
        nbAngleIncidenceWavelengthLine = bfile.readline()
        nbAngleIncidenceWavelength = nbAngleIncidenceWavelengthLine[:-1].split("\t")
        nbAngleIncidence = int(nbAngleIncidenceWavelength[0])
        nbWavelength = int(nbAngleIncidenceWavelength[1])
        # Row 9: List of the incident angles.
        angleIncidenceLine = bfile.readline()
        angleIncidenceString = angleIncidenceLine[:-1].split("\t")
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

        scatterRadial_list = []
        scatterAzimuth_list = []
        nbScatterRadial_list = []
        nbScatterAzimuth_list = []
        nb_reflection_transmission = len(scatterType)
        #tisData = np.zeros((nb_reflection_transmission * nbAngleIncidence, nbWavelength))
        tisdata_list = []

        # tisData[0][0] = float(NormalizationLine)

        bsdfData_list = []

        for i in range(nb_reflection_transmission * nbAngleIncidence):
            for j in range(nbWavelength):
                tisdata_list.append(float(bfile.readline()))
                nbthetaphiLine = bfile.readline()
                nbthetaphi = nbthetaphiLine[:-1].split(" ")
                nbScatterRadial = int(nbthetaphi[0])
                nbScatterAzimuth = int(nbthetaphi[1])
                nbScatterRadial_list.append(nbScatterRadial)
                nbScatterAzimuth_list.append(nbScatterAzimuth)

                scatterAzimuthLine = bfile.readline()
                scatterAzimuthLineString = (scatterAzimuthLine[:-1].strip()).split("\t")
                scatterAzimuth = [float(i) for i in scatterAzimuthLineString]
                scatterAzimuth_list.append(scatterAzimuth)

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

                scatterRadial_list.append(scatterRadial)
                bsdfData_list.append(bsdfDataBlock)

        if bool_log == 1:
            print(".....BSDF data was correctly read\n")

        #    return scatterType, BSDFType, nbSampleRotation, nbAngleIncidence, nbScatterAzimuth, nbScatterRadial, \
        #           angleIncidence, wavelength, scatterRadial, scatterAzimuth, tisData, bsdfData
        samplerotation_list = []
        samplerotation_list.append(0)

        self.scattertype = scatterType
        self.symmetry = "Asymmetrical"
        self.wavelength = wavelength
        self.samplerotation = samplerotation_list
        self.incidence = angleIncidence
        self.tisdata = tisdata_list
        self.theta_input = scatterRadial_list
        self.phi_input = scatterAzimuth_list
        self.bsdf_input = bsdfData_list

    def read_zemax_bsdf(self, bool_log):
        """
        That function reads Zemax BSDF file

        Parameters
        ----------
        inputFilepath : string
            BSDF filename
        bool_log : boolean
            0 --> no report / 1 --> reports values
        """

        # Reading file
        print("Reading Zemax BSDF file: " + str(self.filename_input) + "...\n")
        self.bool_success = 1
        bfile = open(self.filename_input, "r")

        # Read the header
        if bool_log == 1:
            print("Reading header of Zemax BSDF.....")
        # Source type
        sourceLine = bfile.readline()
        while sourceLine[0] == "#" or len(sourceLine) < 6:
            sourceLine = bfile.readline()
        # source = sourceLine[8:-1]
        source = sourceLine[6:-1]
        source = source.strip()
        if bool_log == 1:
            print("Source = " + str(source))
        # Symmetry type
        symmetryLine = bfile.readline()
        while symmetryLine[0] == "#":
            symmetryLine = bfile.readline()
        # symmetry = symmetryLine[10:-1]
        symmetry = symmetryLine[8:-1]
        symmetry = symmetry.strip()
        if bool_log == 1:
            print("Symmetry = " + str(symmetry))
        # Spectral content type
        spectralContentLine = bfile.readline()
        while spectralContentLine[0] == "#":
            spectralContentLine = bfile.readline()
        # spectralContent = spectralContentLine[17:-1]
        spectralContent = spectralContentLine[15:-1]
        spectralContent = spectralContent.strip()
        if bool_log == 1:
            print("Spectral content = " + str(spectralContent))
        # Scatter type
        scatterTypeLine = bfile.readline()
        while scatterTypeLine[0] == "#":
            scatterTypeLine = bfile.readline()
        # scatterType = scatterTypeLine[13:-1]
        scatterType = str(scatterTypeLine[11:-1])
        scatterType = scatterType.strip()
        if bool_log == 1:
            print("Scatter type = " + str(scatterType))
        # Number sample rotation
        sampleRotationLine = bfile.readline()
        while sampleRotationLine[0] == "#":
            sampleRotationLine = bfile.readline()
        # nbSampleRotation = int(sampleRotationLine[16:-1])
        nbSampleRotation = int(sampleRotationLine[14:-1])
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
            print(".....WARNING: Wrong data for sample rotation values")
            self.bool_success = 0
        else:
            sampleRotation = [float(i) for i in sampleRotationString]
            if bool_log == 1:
                print("Sample rotation angle values : " + str(sampleRotationString))
        # Number angle incidence
        angleIncidenceLine = bfile.readline()
        while angleIncidenceLine[0] == "#":
            angleIncidenceLine = bfile.readline()
        # nbAngleIncidence = int(angleIncidenceLine[18:-1])
        nbAngleIncidence = int(angleIncidenceLine[16:-1])
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
            print(".....WARNING: Wrong data for angle incidence values")
            self.bool_success = 0
        else:
            angleIncidence = [float(i) for i in angleIncidenceString]
            if bool_log == 1:
                print("Angle incidence angle values : " + str(angleIncidenceString))
        # Number scatter azimuth
        scatterAzimuthLine = bfile.readline()
        while scatterAzimuthLine[0] == "#":
            scatterAzimuthLine = bfile.readline()
        # nbScatterAzimuth = int(scatterAzimuthLine[15:-1])
        nbScatterAzimuth = int(scatterAzimuthLine[14:-1])
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
            print(".....WARNING: Wrong data for scatter azimuth values")
            self.bool_success = 0
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
        nbScatterRadial = int(scatterRadialLine[13:-1])
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
            print(".....WARNING: Wrong data for scatter radial values")
            self.bool_success = 0
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
        theta_list=[]
        phi_list=[]
        wavelength_list = []
        wavelength_list.append(0.55)
        #tisData = np.zeros((nbSampleRotation, nbAngleIncidence))
        tisData_list = []
        scattertype_list = []

        for index_samplerotation in range(nbSampleRotation):
            for index_incidence in range(nbAngleIncidence):
                # Reading TIS (Total Integrated Scatter) value
                tisLine = bfile.readline()
                #tisData[index_samplerotation][index_incidence] = float(tisLine[4:-1])
                tisData_list.append(float(tisLine[4:-1]))
                bsdfData_block = np.zeros((nbScatterAzimuth, nbScatterRadial))
                for index_phi in range(nbScatterAzimuth):
                    dataLine = bfile.readline()
                    bsdfData_block[index_phi] = dataLine.split()
                bsdfData_list.append(bsdfData_block.transpose())
        theta_list.append(scatterRadial)
        phi_list.append(scatterAzimuth)
        scattertype_list.append(scatterType)

        if bool_log == 1:
            print(".....BSDF data was correctly read\n")

        self.scattertype = scattertype_list
        self.symmetry = symmetry
        self.wavelength = wavelength_list
        self.samplerotation = sampleRotation
        self.incidence = angleIncidence
        self.tisdata = tisData_list
        self.theta_input = theta_list
        self.phi_input = phi_list
        self.bsdf_input = bsdfData_list

    def phi_theta_output(self):
        """
        That function writes the text nLines in the file

        Parameters
        ----------
        self : object of the class BsdfStructure
            bsdf
        """

        # Limitation
        nbTheta_max = 1000
        nbPhi_max = 1000
        if self.zemax_or_speos == 'speos':
            theta_max = 180
        else:
            theta_max = 90
        phi_max = 360
        #if bsdfstructure_input.symmetry == "PlaneSymmetrical":
        #    phi_max = 180
        #    nbPhi_max = 500

        # Default values
        precisionTheta = self.theta_input[0][1] - self.theta_input[0][0]
        precisionPhi = self.phi_input[0][1] - self.phi_input[0][0]

        nbTheta = int(theta_max / precisionTheta) + 1
        nbPhi = int(phi_max / precisionPhi) + 1

        if nbTheta > nbTheta_max:
            precisionTheta = 0.1
            nbTheta = int(theta_max / precisionTheta + 1)
        if nbPhi > nbPhi_max:
            precisionPhi = 0.5
            nbPhi = int(nbPhi_max / precisionPhi + 1)

        print("Precision Theta = ", precisionTheta)
        print("Precision Phi = ", precisionPhi)

        self.theta = [(precisionTheta * k) for k in range(nbTheta)]
        self.phi = [(precisionPhi * x) for x in range(nbPhi)]

    def converter_coordinate_system_bsdf(self, bool_log):
        """
        That function converts the bsdf data

        """

        print("Converting data...\n")

        nb_wavelength = len(self.wavelength)
        nb_samplerotation = len(self.samplerotation)
        nb_angleofincidence = len(self.incidence)
        nb_reflection_transmission = len(self.scattertype)
        self.bsdf = []

        index_block = 0

        for index_reflection_transmission in range(nb_reflection_transmission):
            for index_wavelength in range(nb_wavelength):
                for index_samplerotation in range(nb_samplerotation):
                    for index_angleofincidence in range(nb_angleofincidence):

                        current_angleofincidence = self.incidence[index_angleofincidence]

                        if self.zemax_or_speos == 'speos':
                            line_theta_input = self.theta_input[index_block]
                            line_phi_input = self.phi_input[index_block]
                        if self.zemax_or_speos == 'zemax':
                            line_theta_input = self.theta_input[0]
                            line_phi_input = self.phi_input[0]
                        line_theta_output = self.theta
                        line_phi_output = self.phi

                        nb_theta_output = len(line_theta_output)
                        nb_phi_output = len(line_phi_output)
                        bsdfData_output_block = np.zeros((nb_theta_output, nb_phi_output))

                        for index_theta in range(nb_theta_output):
                            currentTheta = line_theta_output[index_theta]
                            for index_phi in range(nb_phi_output):
                                currentPhi = line_phi_output[index_phi]

                                if self.zemax_or_speos == 'speos':
                                    # Convert the angles to the "normal" definition
                                    newTheta, newPhi = convert_specular_to_normal_using_cartesian(
                                        currentTheta, currentPhi, current_angleofincidence
                                    )
                                if self.zemax_or_speos == 'zemax':
                                    # Convert the angles to the "specular" definition
                                    newTheta, newPhi = convert_normal_to_specular_using_cartesian(
                                        currentTheta, currentPhi, current_angleofincidence
                                    )
                                    # Added the case where symmetry == PlaneSymmetrical
                                    if self.symmetry == "PlaneSymmetrical" and newPhi > 180:
                                        newPhi = 360 - newPhi

                                if newTheta > 90 or newTheta < 0:
                                    bsdfData_output_block[index_theta][index_phi] = 0

                                bsdfData_output_block[index_theta][index_phi] = compute_new_value_matrix(
                                    self.bsdf_input[index_block], line_theta_input, line_phi_input, newTheta, newPhi
                                )
                        index_block = index_block + 1

                        self.bsdf.append(bsdfData_output_block)

    def normalize_bsdf_data(self, bool_log):
        """
        That function normalizes the BSDF data vs the TIS values
        """

        # BRDF: theta goes from 0 to 90
        # BTDF: theta goes from 90 to 180

        if bool_log == 1:
            print("Computing normalization...")
            print("nbSampleRotation nbAngleIncidence IntegralValue IntegralError Zemax_TIS_value NormalizationFactor")

        # Initialization
        nbSampleRotation=len(self.samplerotation)
        nbAngleIncidence=len(self.incidence)
        normalizationBsdf = []

        index_block = 0
        for index_samplerotation in range(nbSampleRotation):
            for index_incidence in range(nbAngleIncidence):
                block_data = np.transpose(self.bsdf[index_block])

                theta_rad, phi_rad = np.radians(self.theta), np.radians(self.phi)  # samples on which integrande is known
                integrande = ((1 / math.pi) * block_data * np.sin(theta_rad) * np.cos(theta_rad))  # *theta for polar integration
                # Linear interpolation of the values
                # interp2d is apparently deprecated
                # Look for alternatives f = interpolate.bisplrep(theta_rad, phi_rad, integrande)
                f = interpolate.interp2d(theta_rad, phi_rad, integrande, kind="linear", bounds_error=False,
                                         fill_value=0)
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
                    normalizationBsdf.append(self.tisdata[index_block] / (IntegralValue))
                else:
                    normalizationBsdf.append(1)
                    print("Integral <= 0!!!!")
                if bool_log == 1:
                    print(
                        index_samplerotation,
                        " ",
                        index_incidence,
                        " ",
                        round(IntegralValue, 3),
                        " ",
                        round(IntegralError, 3),
                        " ",
                        self.tisdata[index_block],
                        " ",
                        round(normalizationBsdf[index_block], 3),
                    )
                self.bsdf[index_block] = self.bsdf[index_block] * normalizationBsdf[index_block]
                index_block = index_block + 1

    def write_zemax_file(self):

        # Writing a Zemax file for each wavelength
        print("Writing Zemax data\n")

        for index_wavelength in range(len(self.wavelength)):
            # nbSampleRotation = 1
            # sampleRotation = [0]

            for index_RT in range(len(self.scattertype)):
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
        That function writes the header of Zemax BSDF file

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
        nLines.append("ScatterAzimuth " + str(len(self.phi)) + "\n")
        for i in range(len(self.phi)):
            nLines.append(str(self.phi[i]) + "\t")
        nLines.append("\n")
        # List of ScatterRadial
        nLines.append("ScatterRadial " + str(len(self.theta)) + "\n")
        for i in range(len(self.theta)):
            nLines.append(str(self.theta[i]) + "\t")
        nLines.append("\n")
        # A few more lines
        nLines.append("\n")
        nLines.append("Monochrome\n")
        nLines.append("DataBegin\n")

        return nLines

    def write_zemax_data_bsdf(self, index_RT, index_wavelength):
        """
        That function writes the main data of Zemax BSDF file

        """
        nLines = []
        nb_angleofincidence = len(self.incidence)
        nb_wavelength = len(self.wavelength)
        nb_samplerotation = len(self.samplerotation)

        for index_samplerotation in range(len(self.samplerotation)):
            for index_angleofincidence in range(nb_angleofincidence):
                index_data = (index_RT * nb_wavelength * nb_samplerotation +
                              index_wavelength * nb_samplerotation +
                              index_samplerotation) * nb_angleofincidence + index_angleofincidence
                nLines.append("TIS " + str(round(self.tisdata[index_data] / 100, 3)) + "\n")
                for index_phi in range(len(self.phi)):
                    for index_theta in range(len(self.theta) - 1):
                        scientific_notation = "{:.3e}".format(self.bsdf[index_data][index_theta][index_phi])
                        nLines.append(str(scientific_notation) + "\t")
                    index_theta = len(self.theta) - 1
                    scientific_notation = "{:.3e}".format(self.bsdf[index_data][index_theta][index_phi])
                    nLines.append(str(scientific_notation) + "\n")
            nLines.append("DataEnd\n")

        return nLines

    def write_speos_file(self):

        # Writing a Speos file
        print("Writing Speos data\n")
        nLines = self.write_speos_header_bsdf()
        nLines = self.write_speos_data_bsdf(nLines)
        outputFilepath = (os.path.splitext(self.filename_input)[0].lower() + ".anisotropicbsdf")
        write_file(outputFilepath, nLines)

    def write_speos_header_bsdf(self):
        """
        That function writes the header of Speos BSDF file

        Parameters
        ----------

        """

        nbSampleRotation = len(self.samplerotation)
        nbAngleIncidence = len(self.incidence)
        binaryMode = 0
        anisotropyVector = [0, 1, 0]

        measurementDescription = "Measurement description"
        comment = "Comment"

        # Header
        nLines = ["OPTIS - Anisotropic BSDF surface file v7.0\n"]
        # Binary mode
        nLines.append(str(binaryMode) + "\n")
        # Comment
        nLines.append(comment + "\n")
        # Measurement description
        nLines.append(str(len(measurementDescription)) + "\n")
        nLines.append(measurementDescription + "\n")
        # Anisotropy vector
        nLines.append(
            str(anisotropyVector[0]) + "\t" + str(anisotropyVector[1]) + "\t" + str(anisotropyVector[2]) + "\n")
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
                nLines.append(str(self.incidence[i]) + "\t")
            if nbAngleIncidence != 0:
                nLines.append("\n")
        # theta and phi for measurement
        nLines.append(str(self.incidence[0]) + "\t" + "0\n")
        # Spectrum description
        nLines.append("\n")
        # Number of wavelength
        nLines.append("2" + "\n")
        # Wavelength measurements
        nLines.append("350" + "\t" + str(100 * self.tisdata[0]) + "\n")
        nLines.append("850" + "\t" + str(100 * self.tisdata[0]) + "\n")

        return nLines

    def write_speos_data_bsdf(self,nLines):
        """
        That function writes the main data of Speos BSDF file

        """
        nbtheta = len(self.theta)
        nbphi = len(self.phi)
        index_block = 0

        # If transmission data
        if self.scattertype[0] == "BTDF":
            # change line theta from 90--> 180 to 0-->90
            temp = self.theta
            temp_180 = [180 - temp[index_theta] for index_theta in range(len(temp))]
            self.theta = temp_180[::-1]

        #if self.scattertype[0] == "BTDF":
        # bsdfData_output = bsdfData_output_temp
        # else:
        #    for i in range(nblistDimension1):
        #        for j in range(nblistDimension2):
        #            for k in range(len(line_theta_output)):
        #                bsdfData_output[i][j][k] = bsdfData_output_temp[i][j][len(line_theta_output) - 1 - k]

        for index_samplerotation in range(len(self.samplerotation)):
            for index_incidence in range(len(self.incidence)):
                nLines.append(str(int(nbtheta)) + " " + str(int(nbphi)) + "\n")

                # Write the 1st line of the block with the Phi values
                for index_phi in range(nbphi):
                    currentPhi = self.phi[index_phi]
                    nLines.append("\t" + str(currentPhi))
                nLines.append("\n")

                if self.scattertype[0] == "BTDF":
                    self.bsdf[index_block] = swap_rows(self.bsdf[index_block])

                for index_theta in range(nbtheta):
                    currentTheta = self.theta[index_theta]
                    nLines.append(str(currentTheta))
                    for index_phi in range(nbphi):
                        if self.scattertype[0] == "BRDF":
                            nLines.append("\t" + str(self.bsdf[index_block][index_theta][index_phi]))
                        elif self.scattertype[0] == "BTDF":
                            thetas_cosine = math.cos((180 - currentTheta) * math.pi / 180)
                            nLines.append("\t" + str(thetas_cosine * self.bsdf[index_block][index_theta][index_phi]))
                    nLines.append("\n")
                index_block = index_block + 1
        nLines.append("End of file")
        nLines.append("\n")

        return nLines


def convert_normal_to_specular_using_cartesian(theta_i, phi_i, angle_inc):
    """
    That function converts from normal to specular reference using cartesian coordinates
    phi = 0 top of the plot

    Parameters
    ----------
    theta_i : float
        Scattered polar angle in the normal reference
    phi_i : float
        Scattered azimuthal angle in the normal reference
    angle_inc : float
        Angle of incidence
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

    Parameters
    ----------
    theta_i : float
        Scattered polar angle in the specular reference
    phi_i : float
        Scattered azimuthal angle in the specular reference
    angle_inc : float
        Angle of incidence
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


def convert_normal_to_specular_using_cylindrical(theta_i, phi_i, angle_inc):
    """
    That function converts from normal to specular reference using cylindrical cartesian conversion
    phi = 0 top of the plot

    Parameters
    ----------
    theta_i : float
        Scattered polar angle in the normal reference
    phi_i : float
        Scattered azimuthal angle in the normal reference
    angle_inc : float
        Angle of incidence
    """

    # cylindrical coordinates
    # theta_i*=math.pi/180
    phi_i *= math.pi / 180
    # Conversion to cartesian coordinates
    x_i = (theta_i) * math.cos(phi_i)
    y_i = (theta_i) * math.sin(phi_i)
    # Conversion to new cartesian coordinates
    x_o = x_i - angle_inc
    y_o = y_i
    # Conversion to new cylindrical coordinates
    theta_o = math.sqrt(x_o * x_o + y_o * y_o)

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

    return (theta_o, phi_o)


def convert_normal_to_specular_using_cylindrical_phiref(theta_i, phi_i, angle_inc):
    """
    That function converts from normal to specular reference using cylindrical cartesian conversion
    phi=0 for OpticStudio is phi=180 for speos
    phi = 0 top of the plot

    Parameters
    ----------
    theta_i : float
        Scattered polar angle in the normal reference
    phi_i : float
        Scattered azimuthal angle in the normal reference
    angle_inc : float
        Angle of incidence
    """

    # cylindrical coordinates
    # theta_i*=math.pi/180
    phi_i *= math.pi / 180
    # Conversion to cartesian coordinates
    x_i = (theta_i) * math.cos(phi_i)
    y_i = (theta_i) * math.sin(phi_i)
    # Conversion to new cartesian coordinates
    x_o = x_i - angle_inc
    y_o = y_i
    # Conversion to new cylindrical coordinates
    theta_o = math.sqrt(x_o * x_o + y_o * y_o)

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


def obsolete_read_zemax_bsdf(inputFilepath, bool_log):
    """
    That function reads Zemax BSDF file

    Parameters
    ----------
    inputFilepath : string
        BSDF filename
    bool_log : boolean
        0 --> no report / 1 --> reports values
    """

    bfile = open(inputFilepath, "r")

    # Read the header
    if bool_log == 1:
        print("Reading header of Zemax BSDF.....")
    # Source type
    sourceLine = bfile.readline()
    while sourceLine[0] == "#" or len(sourceLine) < 6:
        sourceLine = bfile.readline()
    # source = sourceLine[8:-1]
    source = sourceLine[6:-1]
    source = source.strip()
    if bool_log == 1:
        print("Source = " + str(source))
    # Symmetry type
    symmetryLine = bfile.readline()
    while symmetryLine[0] == "#":
        symmetryLine = bfile.readline()
    # symmetry = symmetryLine[10:-1]
    symmetry = symmetryLine[8:-1]
    symmetry = symmetry.strip()
    if bool_log == 1:
        print("Symmetry = " + str(symmetry))
    # Spectral content type
    spectralContentLine = bfile.readline()
    while spectralContentLine[0] == "#":
        spectralContentLine = bfile.readline()
    # spectralContent = spectralContentLine[17:-1]
    spectralContent = spectralContentLine[15:-1]
    spectralContent = spectralContent.strip()
    if bool_log == 1:
        print("Spectral content = " + str(spectralContent))
    # Scatter type
    scatterTypeLine = bfile.readline()
    while scatterTypeLine[0] == "#":
        scatterTypeLine = bfile.readline()
    # scatterType = scatterTypeLine[13:-1]
    scatterType = str(scatterTypeLine[11:-1])
    scatterType = scatterType.strip()
    if bool_log == 1:
        print("Scatter type = " + str(scatterType))
    # Number sample rotation
    sampleRotationLine = bfile.readline()
    while sampleRotationLine[0] == "#":
        sampleRotationLine = bfile.readline()
    # nbSampleRotation = int(sampleRotationLine[16:-1])
    nbSampleRotation = int(sampleRotationLine[14:-1])
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
        print(".....WARNING: Wrong data for sample rotation values")
        # tempVariable = input(".....Press Enter to continue")
    else:
        sampleRotation = [float(i) for i in sampleRotationString]
        if bool_log == 1:
            print("Sample rotation angle values : " + str(sampleRotationString))
    # Number angle incidence
    angleIncidenceLine = bfile.readline()
    while angleIncidenceLine[0] == "#":
        angleIncidenceLine = bfile.readline()
    # nbAngleIncidence = int(angleIncidenceLine[18:-1])
    nbAngleIncidence = int(angleIncidenceLine[16:-1])
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
        print(".....WARNING: Wrong data for angle incidence values")
        # tempVariable = input(".....Press Enter to continue")
    else:
        angleIncidence = [float(i) for i in angleIncidenceString]
        if bool_log == 1:
            print("Angle incidence angle values : " + str(angleIncidenceString))
    # Number scatter azimuth
    scatterAzimuthLine = bfile.readline()
    while scatterAzimuthLine[0] == "#":
        scatterAzimuthLine = bfile.readline()
    # nbScatterAzimuth = int(scatterAzimuthLine[15:-1])
    nbScatterAzimuth = int(scatterAzimuthLine[14:-1])
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
        print(".....WARNING: Wrong data for scatter azimuth values")
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
    nbScatterRadial = int(scatterRadialLine[13:-1])
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
        print(".....WARNING: Wrong data for scatter radial values")
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
    # Initialization of a matrix bsdfData
    # Initialization of a vector tisData to save the TIS at each sample rotation and angle of incidence
    # Initialization of a vector normalizationBsdf to normalize the BSDF block
    # The normalization is done vs the BSDF data from the first angle of incidence
    # TIS = integral(BSDF x cos(theta)sin(theta) dtheta dphi)

    bsdfData = np.zeros((nbSampleRotation, nbAngleIncidence, nbScatterAzimuth, nbScatterRadial))
    tisData = np.zeros((nbSampleRotation, nbAngleIncidence))

    for i in range(nbSampleRotation):
        for j in range(nbAngleIncidence):
            # Reading TIS (Total Integrated Scatter) value
            tisLine = bfile.readline()
            tisData[i][j] = float(tisLine[4:-1])
            for k in range(nbScatterAzimuth):
                dataLine = bfile.readline()
                bsdfData[i][j][k] = dataLine.split()
    if bool_log == 1:
        print(".....BSDF data was correctly read\n")

    return (
        scatterType,
        symmetry,
        angleIncidence,
        sampleRotation,
        scatterRadial,
        scatterAzimuth,
        tisData,
        bsdfData,
    )


def obsolete_read_speos_bsdf(inputFilepath, bsdf_data, bool_log):
    """
    That function reads Speos BSDF file

    Parameters
    ----------
    inputFilepath : string
        BSDF filename
    bool_log : boolean
        0 --> no report / 1 --> reports values

    """

    bsdf_data.bool_success = 1
    bool_success = 1

    bfile = open(inputFilepath, "r")
    # filesize = os.fstat(bfile.fileno()).st_size

    input_file_extension = os.path.splitext(inputFilepath)[1].lower()[0:]
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
        bool_success = 0
        print(".....WARNING: The format is not supported.")
        print(".....Open and save the file with the BSDF viewer to update the format.")
        input(".....Press Enter to continue")
        exit()
    if bool_log == 1:
        print("Header = " + str(headerLine))
    # Row 2 : text 0 or binary 1
    textorbinaryLine = bfile.readline()
    textorbinary = textorbinaryLine[:-1].split("\t")
    if textorbinary[0] == 0:
        bool_success = 0
        print(".....WARNING: The BSDF data cannot be read. It is not a text.")
        input(".....Press Enter to continue")
        exit()
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
    if bool_log == 1:
        print("BSDF(1) or Intensity(1) values = " + str(typeLine))
    # Row 8: Number of incident angles and number of wavelength samples (in nanometer).
    nbAngleIncidenceWavelengthLine = bfile.readline()
    nbAngleIncidenceWavelength = nbAngleIncidenceWavelengthLine[:-1].split("\t")
    nbAngleIncidence = int(nbAngleIncidenceWavelength[0])
    nbWavelength = int(nbAngleIncidenceWavelength[1])
    # Row 9: List of the incident angles.
    angleIncidenceLine = bfile.readline()
    angleIncidenceString = angleIncidenceLine[:-1].split("\t")
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

    scatterRadial_list = []
    scatterAzimuth_list = []
    nbScatterRadial_list = []
    nbScatterAzimuth_list = []
    nb_reflection_transmission = len(scatterType)
    tisData = np.zeros((nb_reflection_transmission * nbAngleIncidence, nbWavelength))

    # tisData[0][0] = float(NormalizationLine)

    bsdfData_list = []

    for i in range(nb_reflection_transmission * nbAngleIncidence):
        for j in range(nbWavelength):
            tisData[i][j] = float(bfile.readline())
            nbthetaphiLine = bfile.readline()
            nbthetaphi = nbthetaphiLine[:-1].split(" ")
            nbScatterRadial = int(nbthetaphi[0])
            nbScatterAzimuth = int(nbthetaphi[1])
            nbScatterRadial_list.append(nbScatterRadial)
            nbScatterAzimuth_list.append(nbScatterAzimuth)

            scatterAzimuthLine = bfile.readline()
            scatterAzimuthLineString = (scatterAzimuthLine[:-1].strip()).split("\t")
            scatterAzimuth = [float(i) for i in scatterAzimuthLineString]
            scatterAzimuth_list.append(scatterAzimuth)

            bsdfDataBlock = np.zeros((nbScatterRadial, nbScatterAzimuth))
            # scatterRadial = np.zeros(nbScatterRadial)
            scatterRadial = []

            for k in range(nbScatterRadial):
                dataLine = bfile.readline()
                data = dataLine.split()
                # scatterRadial[k] = float(data[0])
                scatterRadial.append(float(data[0]))
                bsdfDataBlock[k] = data[1:]
            scatterRadial_list.append(scatterRadial)
            bsdfData_list.append(np.transpose(bsdfDataBlock))

    if bool_log == 1:
        print(".....BSDF data was correctly read\n")

    #    return scatterType, BSDFType, nbSampleRotation, nbAngleIncidence, nbScatterAzimuth, nbScatterRadial, \
    #           angleIncidence, wavelength, scatterRadial, scatterAzimuth, tisData, bsdfData
    samplerotation_list = []
    samplerotation_list.append(0)

    bsdf_data.scattertype = scatterType
    bsdf_data.symmetry = "Asymmetrical"
    bsdf_data.wavelength = wavelength
    bsdf_data.samplerotation = samplerotation_list
    bsdf_data.incidence = angleIncidence
    bsdf_data.tisdata = tisData
    bsdf_data.theta_input = scatterRadial_list
    bsdf_data.phi_input = scatterAzimuth_list
    bsdf_data.bsdf_input = bsdfData_list


    #return (
    #    bool_success,
    #    nb_reflection_transmission,
    #    scatterType,
    #    symmetry,
    #    nbSampleRotation,
    #    nbAngleIncidence,
    #    angleIncidence,
    #    wavelength,
    #    scatterRadial_list,
    #    scatterAzimuth_list,
    #    tisData,
    #    bsdfData_list,
    #)

    return bsdf_data


def obsolete_write_speos_header_bsdf(
    binaryMode,
    anisotropyVector,
    scatterType,
    sampleRotation,
    angleIncidence,
    tisData,
):
    """
    That function writes the header of Speos BSDF file

    Parameters
    ----------
    binaryMode : boolean
        Text or binary mode - only text for now
    anisotropyVector : vector
        Anisotropy vector
    scatterType : string
        BRDF or BTDF
    sampleRotation : list
        list of sample rotations
    angleIncidence : float
        list of angles of incidences
    tisData : float
        list of tis values
    """

    nbSampleRotation = len(sampleRotation)
    nbAngleIncidence = len(angleIncidence)

    measurementDescription = "Measurement description"
    comment = "Comment"

    # Header
    nLines = ["OPTIS - Anisotropic BSDF surface file v7.0\n"]
    # Binary mode
    nLines.append(str(binaryMode) + "\n")
    # Comment
    nLines.append(comment + "\n")
    # Measurement description
    nLines.append(str(len(measurementDescription)) + "\n")
    nLines.append(measurementDescription + "\n")
    # Anisotropy vector
    nLines.append(str(anisotropyVector[0]) + "\t" + str(anisotropyVector[1]) + "\t" + str(anisotropyVector[2]) + "\n")
    # Scatter type (BRDF/BTDF)
    # Type of values
    # 1 means the data is proportional to the BSDF data
    # 0 means the data is proportional to the measured intensity
    # For BTDF: valuesType = 0 because of a bug
    if scatterType == "BRDF":
        nLines.append("1" + "\t" + "0" + "\n")
        valuesType = 1
        nLines.append(str(valuesType) + "\n")
    elif scatterType == "BTDF":
        nLines.append("0" + "\t" + "1" + "\n")
        valuesType = 0
        nLines.append(str(valuesType) + "\n")
    else:
        print(".....WARNING: Original data file has no valid ScatterType")
        # tempVariable = input(".....Press Enter to continue")
    # Anisotropy angles (SampleRotations)
    nLines.append(str(nbSampleRotation) + "\n")
    for i in range(nbSampleRotation):
        nLines.append(str(sampleRotation[i]) + "\t")
    if nbSampleRotation != 0:
        nLines.append("\n")
    # Incident angles (AngleIncidence)
    for k in range(nbSampleRotation):
        nLines.append(str(nbAngleIncidence) + "\n")
        for i in range(nbAngleIncidence):
            nLines.append(str(angleIncidence[i]) + "\t")
        if nbAngleIncidence != 0:
            nLines.append("\n")
    # theta and phi for measurement
    nLines.append(str(angleIncidence[0]) + "\t" + "0\n")
    # Spectrum description
    nLines.append("\n")
    # Number of wavelength
    nLines.append("2" + "\n")
    # Wavelength measurements
    nLines.append("350" + "\t" + str(100 * tisData[0][0]) + "\n")
    nLines.append("850" + "\t" + str(100 * tisData[0][0]) + "\n")

    return nLines


def obsolete_write_zemax_header_bsdf(bsdf_data,index_RT,index_wavelength):
    """
    That function writes the header of Zemax BSDF file

    Parameters
    ----------
    scatterType : string
        BRDF or BTDF
    symmetry : string
        Asymmetrical or Asymmetrical4D
    currentwavelength : float
        Current wavelength
    nbSampleRotation : integer
        Number of sample rotations
    nbAngleIncidence : integer
        Number of angle of incidence
    sampleRotation : list
        list of sample rotations
    angleIncidence : float
        list of angles of incidences
    line_theta : list
        list of theta / radial angles
    line_phi : list
        list of phi / azimuthal angles
    """

    # Header
    nLines = ["#Data converted from Speos data\n"]
    # Wavelength
    comment = "#Wavelength (nm) = " + str(bsdf_data.wavelength[index_wavelength])
    nLines.append(str(comment) + "\n")
    # Source
    comment = "Source  Measured"
    nLines.append(str(comment) + "\n")
    # Symmetry
    nLines.append("Symmetry  " + str(bsdf_data.symmetry) + "\n")
    # SpectralContent
    spectralcontent = "SpectralContent  Monochrome"
    nLines.append(str(spectralcontent) + "\n")
    # ScatterType
    ScatterType = "ScatterType  " + str(bsdf_data.scattertype[index_RT])
    nLines.append(ScatterType + "\n")
    # SampleRotation
    nLines.append("SampleRotation  " + str(len(bsdf_data.samplerotation)) + "\n")
    # List of SampleRotation
    for i in range(len(bsdf_data.samplerotation)):
        nLines.append(str(bsdf_data.samplerotation[i]) + "\t")
    nLines.append("\n")
    # AngleOfIncidence
    nLines.append("AngleOfIncidence  " + str(len(bsdf_data.incidence)) + "\n")
    # List of AngleOfIncidence
    for i in range(len(bsdf_data.incidence)):
        nLines.append(str(bsdf_data.incidence[i]) + "\t")
    nLines.append("\n")
    # List of ScatterAzimuth
    nLines.append("ScatterAzimuth " + str(len(bsdf_data.phi_input)) + "\n")
    for i in range(len(bsdf_data.phi_input)):
        nLines.append(str(bsdf_data.phi_input[i]) + "\t")
    nLines.append("\n")
    # List of ScatterRadial
    nLines.append("ScatterRadial " + str(len(bsdf_data.theta_input)) + "\n")
    for i in range(len(bsdf_data.theta_input)):
        nLines.append(str(bsdf_data.theta_input[i]) + "\t")
    nLines.append("\n")
    # A few more lines
    nLines.append("\n")
    nLines.append("Monochrome\n")
    nLines.append("DataBegin\n")

    return nLines


def compute_new_value_matrix(matrix_z, line_x, line_y, new_x, new_y):
    """
    That function takes (x,y) as an argument and returns a new interpolated value from a matrix[x,y]

    Parameters
    ----------
    matrix_z : matrix of z values
        matrix giving a z value for a set of x,y values
    line_x : list
        List of x
    line_y : list
        List of y
    new_x : flaot
        New value of theta
    new_y : flaot
        New value of phi
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
        index_x = len(line_x) - 1
        indexInf_x = index_x - 1
        indexSup_x = index_x
        coeff_x = 0

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
        index_y = len(line_y) - 1
        indexInf_y = index_y - 1
        indexSup_y = index_y
        coeff_y = 0

    # Linear interpolation
    value_Inf_x = matrix_z[indexInf_x][indexInf_y] * (1 - coeff_y) + matrix_z[indexInf_x][indexSup_y] * coeff_y
    value_Sup_x = matrix_z[indexSup_x][indexInf_y] * (1 - coeff_y) + matrix_z[indexSup_x][indexSup_y] * coeff_y
    newValue = value_Inf_x * (1 - coeff_x) + value_Sup_x * coeff_x
    return newValue

def obsolete_convert_zemax_speos_bsdf_data(
    nb_reflection_transmission,
    symmetry,
    scatterType,
    listDimension1,
    listDimension2,
    line_theta_input,
    line_phi_input,
    line_theta_output,
    line_phi_output,
    bsdfData_input,
    bool_speos_brdf,
):
    """
    That function converts the block data from Zemax to Speos

    Parameters
    ----------
    nb_reflection_transmission : integer
        1 if data=BRDF or BTDF and 2 if both
    symmetry : string
        PlaneSymmetric or ASymmetrical4D
    scatterType : string
        BTDF or BRDF
    listDimension1 sampleRotation : list
        If converting a BRDF file (bool_speos_brdf = True): list of angles of incidence
        If converting a Zemax file (bool_speos_brdf = False): list of Sample Rotations
    listDimension2 angleIncidence : list
        If converting a BRDF file (bool_speos_brdf = True): list of wavelengths
        If converting a Zemax file (bool_speos_brdf = False): list of angles of incidence
    line_theta_input : list
        List of radial / theta input angles
    line_phi_input : list
        List of azimuthal / phi input angles
    line_theta_output : list
        List of radial / theta output angles
    line_phi_output : list
        List of azimuthal / phi output angles
    bsdfData_input : Array
        Array with input BSDF data
    bool_speos_brdf : boolean
        bool = 1 if speos BRDF data to convert, 0 otherwise
    """

    nblistDimension1 = len(listDimension1)
    nblistDimension2 = len(listDimension2)

    # Initialization
    bsdfData_output_temp = np.zeros(
        (nb_reflection_transmission * nblistDimension1, nblistDimension2, len(line_theta_output), len(line_phi_output))
    )
    bsdfData_output = np.zeros(
        (nb_reflection_transmission * nblistDimension1, nblistDimension2, len(line_theta_output), len(line_phi_output))
    )

    index_block = 0
    # if speos BRDF dimension_1 =  data i --> angle of incidence
    # if zemax data i --> Sample rotation
    for i in range(nb_reflection_transmission * nblistDimension1):

        # if speos BRDF data j --> wavelength
        # if zemax data i --> angleofincidence
        for j in range(nblistDimension2):
            for k in range(len(line_theta_output)):
                currentTheta = line_theta_output[k]
                for l_index in range(len(line_phi_output)):
                    currentPhi = line_phi_output[l_index]

                    if bool_speos_brdf == 1:
                        currentAngleInc = listDimension1[i % nblistDimension1]
                        # Convert the angles to the "normal" definition
                        newTheta, newPhi = convert_specular_to_normal_using_cartesian(
                            currentTheta, currentPhi, currentAngleInc
                        )
                    else:
                        # Convert the angles to the "specular" definition
                        currentAngleInc = listDimension2[j]
                        newTheta, newPhi = convert_normal_to_specular_using_cartesian(
                            currentTheta, currentPhi, currentAngleInc
                        )
                    # newTheta, newPhi = convert_cylindrical(currentTheta, currentPhi, currentAngleInc)
                    # newTheta, newPhi = convert_cylindrical_phiref(currentTheta, currentPhi, currentAngleInc)
                    if newTheta > 90 or newTheta < 0:
                        bsdfData_output[i][j][k][l_index] = 0
                    else:
                        # Added the case where symmetry == PlaneSymmetrical
                        if symmetry == "PlaneSymmetrical" and newPhi > 180:
                            newPhi = 360 - newPhi
                        # Look in scatterRadial to find scatterRadial[indexInfTheta] = newTheta

                        # Defining the BSDF values
                        if bool_speos_brdf == 0:
                            bsdf_block = bsdfData_input[i][j]
                            bsdfData_output_temp[i][j][k][l_index] = compute_new_value_matrix(
                                bsdf_block, line_theta_input, line_phi_input, newTheta, newPhi
                            )
                        else:
                            bsdf_block = bsdfData_input[index_block]
                            # If Speos transmission data
                            if line_theta_input[index_block][0] >=90:
                                temp = line_theta_input[index_block]
                                temp_180 = [180-temp[index_theta] for index_theta in range(len(temp))]

                                #sawp columns of the bsdf_block
                                bsdf_block = swap_columns(bsdf_block)
                                line_theta_input[index_block] = temp_180[::-1]

                            bsdfData_output_temp[i][j][k][l_index] = compute_new_value_matrix(
                                bsdf_block, line_theta_input[index_block], line_phi_input[index_block], newTheta, newPhi
                            )

            index_block = index_block + 1

    if bool_speos_brdf == 1 or scatterType == "BRDF":
        bsdfData_output = bsdfData_output_temp
    else:
        for i in range(nblistDimension1):
            for j in range(nblistDimension2):
                for k in range(len(line_theta_output)):
                    bsdfData_output[i][j][k] = bsdfData_output_temp[i][j][len(line_theta_output) - 1 - k]

    bsdfData_output_temp = []

    return bsdfData_output


def swap_columns(arr):
    arr_temp = np.zeros((arr.shape[0],arr.shape[1]))
    nb_columns = arr.shape[1]

    for index_column in range(nb_columns):
        arr_temp[:, index_column] = arr[:, nb_columns - 1 - index_column]

    return arr_temp

def swap_rows(arr):
    arr_temp = np.zeros((arr.shape[0],arr.shape[1]))
    nb_rows = arr.shape[0]

    for index_row in range(nb_rows):
        arr_temp[index_row,:] = arr[nb_rows - 1 - index_row,:]

    return arr_temp


def obsolete_normalize_bsdf_data(
    nbSampleRotation, nbAngleIncidence, line_theta, line_phi, tisData, bsdfData, bool_zemax0_speos1, bool_log
):
    """
    That function normalizes the BSDF data vs the TIS values

    Parameters
    ----------
    nbSampleRotation : integer
        Number of sample rotations
    nbAngleIncidence : integer
        Number of angle of incidences
    line_theta : list
        List of theta angles
    line_phi : list
        List of phi angles
    tisData : list
        List of TIS values
    bsdfData : matrix
        Raw BSDF data matrix - values to be normalized
    bool_log : boolean
        0 --> no report / 1 --> reports values
    Returns
    -------
    normalizationBsdf : list of values
        List of the normalization values for each angle of incidence / sample rotation
    """

    # BRDF: theta goes from 0 to 90
    # BTDF: theta goes from 90 to 180

    if bool_log == 1:
        print("Computing normalization...")
        print("nbSampleRotation nbAngleIncidence IntegralValue IntegralError Zemax_TIS_value NormalizationFactor")

    # Initialization
    normalizationBsdf = np.zeros((nbSampleRotation, nbAngleIncidence))

    for i in range(nbSampleRotation):
        for j in range(nbAngleIncidence):
            block_data = bsdfData[i, j, :, :]
            if bool_zemax0_speos1 == 1:
                block_data = block_data.transpose()

            theta_rad, phi_rad = np.radians(line_theta), np.radians(line_phi)  # samples on which integrande is known
            integrande = (
                (1 / math.pi) * block_data * np.sin(theta_rad) * np.cos(theta_rad)
            )  # *theta for polar integration
            # Linear interpolation of the values
            # interp2d is apparently deprecated
            # Look for alternatives f = interpolate.bisplrep(theta_rad, phi_rad, integrande)
            f = interpolate.interp2d(theta_rad, phi_rad, integrande, kind="linear", bounds_error=False, fill_value=0)

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
                normalizationBsdf[i][j] = tisData[i][j] / (IntegralValue)
            else:
                normalizationBsdf[i][j] == 1
                print("Integral = 0!!!!")

            if bool_log == 1:
                print(
                    i,
                    " ",
                    j,
                    " ",
                    round(IntegralValue, 3),
                    " ",
                    round(IntegralError, 3),
                    " ",
                    tisData[i][j],
                    " ",
                    round(normalizationBsdf[i][j], 3),
                )

            bsdfData[i][j][:][:] = bsdfData[i, j, :, :] * normalizationBsdf[i][j]

    return normalizationBsdf, bsdfData


def obsolete_write_speos_data_bsdf(nLines, scatterType, nbSampleRotation, nbAngleIncidence, line_theta, line_phi, bsdfDataSpeos):
    """
    That function writes the main data of Speos BSDF file

    Parameters
    ----------
    nLines : text
        Text containing the BSDF Speos header
    scatterType : string
        BRDF or BTDF
    nbSampleRotation : integer
        Number of sample rotations
    nbAngleIncidence : integer
        Number of angle of incidence
    line_theta : list
        list of theta angles
    line_phi : list
        list of phi angles
    bsdfDataSpeos : matrix of float
        BSDF data values
    """
    nbTheta = len(line_theta)
    nbPhi = len(line_phi)

    for i in range(nbSampleRotation):
        for j in range(nbAngleIncidence):
            nLines.append(str(int(nbTheta)) + " " + str(int(nbPhi)) + "\n")

            # Write the 1st line of the block with the Phi values
            for x in range(nbPhi):
                currentPhi = line_phi[x]
                nLines.append("\t" + str(currentPhi))
            nLines.append("\n")
            for k in range(nbTheta):
                currentTheta = line_theta[k]
                nLines.append(str(currentTheta))
                for phi_idx in range(nbPhi):
                    if scatterType == "BRDF":
                        nLines.append("\t" + str(bsdfDataSpeos[i][j][k][phi_idx]))
                    elif scatterType == "BTDF":
                        thetas_cosine = math.cos((180 - currentTheta) * math.pi / 180)
                        nLines.append("\t" + str(thetas_cosine * bsdfDataSpeos[i][j][k][phi_idx]))
                nLines.append("\n")
    nLines.append("End of file")
    nLines.append("\n")

    return nLines

def obsolete_write_zemax_data_bsdf(bsdf_data,index_RT, index_wavelength):
    """
    That function writes the main data of Zemax BSDF file

    Parameters
    ----------
    index_wavelength : integer
        Index of the wavelength
    index_RT : integer
    nbSampleRotation : integer
        Number of sample rotations
    nbAngleIncidence : integer
        Number of angle of incidence
    tisData : list
        TIS data values
    bsdfData : matrix of float
        BSDF data values

    Returns
    -------
    nLines = string
        Text containing the formatted header
    """
    nLines = []
    nb_angleofincidence = len(bsdf_data.incidence)

    #for i in range(len(bsdf_data.samplerotation)):
    #    for j in range(nb_angleofincidence):
    #        index_angle = j + nb_angleofincidence * index_RT
    #        nLines.append("TIS " + str(round(bsdf_data.tisdata[j][index_wavelength] / 100, 3)) + "\n")
    #        for k in range(bsdf_data.bsdf[index_angle].shape[1]):
    #            for l_index in range(bsdf_data.bsdf[index_angle].shape[1] - 1):
    #                scientific_notation = "{:.3e}".format(bsdf_data.bsdf[index_angle][index_wavelength][l_index][k])
    #                nLines.append(str(scientific_notation) + "\t")
    #            l_index = bsdfData.shape[2] - 1
    #            scientific_notation = "{:.3e}".format(bsdfData[index_angle][index_wavelength][l_index][k])
    #            nLines.append(str(scientific_notation) + "\n")
    #nLines.append("DataEnd\n")

    nb_wavelength = len(bsdf_data.wavelength)
    nb_samplerotation = len(bsdf_data.samplerotation)

    for index_samplerotation in range(len(bsdf_data.samplerotation)):
        for index_angleofincidence in range(nb_angleofincidence):

            index_data = (index_RT * nb_wavelength * nb_samplerotation +
                          index_wavelength * nb_samplerotation +
                          index_samplerotation) * nb_angleofincidence
            #index_tis = index_RT*nb_angleofincidence+index_angleofincidence
            nLines.append("TIS " + str(round(bsdf_data.tisdata[index_data] / 100, 3)) + "\n")
            for index_phi in range(len(bsdf_data.phi_input)):
                for index_theta in range(len(bsdf_data.theta_input) - 1):
                    scientific_notation = "{:.3e}".format(bsdf_data.bsdf_input[index_data][index_theta][index_phi])
                    nLines.append(str(scientific_notation) + "\t")
                index_theta = len(bsdf_data.theta_input) - 1
                scientific_notation = "{:.3e}".format(bsdf_data.bsdf_input[index_data][index_theta][index_phi])
                nLines.append(str(scientific_notation) + "\n")
        nLines.append("DataEnd\n")

    return nLines

def write_file(outputFilepath, nLines):
    """
    That function writes the text nLines in the file

    Parameters
    ----------
    nLines : text
        Text containing the data
    outputFilepath : filename
        file to write
    """
    nFile = open(outputFilepath, "w")
    nFile.writelines(nLines)
    nFile.close()
    print("The file " + str(outputFilepath) + " is ready!\n")

def obsolete_phi_theta_recommended_precision(scatterRadial, scatterAzimuth, symmetry, bool_zemax0_speos1):
    """
    That function writes the text nLines in the file

    Parameters
    ----------
    scatterRadial : list
        List of radial / theta angles
    scatterAzimuth : list
        List of azimuthal / phi angles
    symmetry : string
        PlaneSymmetrical, Asymmetrical, Asymmetrical4D
    bool_zemax0_speos1 : boolean
        if zemax data to convert == 0
    """

    # Limitation
    nbTheta_max = 1000
    nbPhi_max = 1000
    theta_max = 90
    phi_max = 360
    # multiple = 0.5
    if symmetry == "PlaneSymmetrical" and bool_zemax0_speos1 == 0:
        phi_max = 180
        nbPhi_max = 500

    # Default values
    precisionTheta = scatterRadial[1] - scatterRadial[0]
    precisionPhi = scatterAzimuth[1] - scatterAzimuth[0]

    nbTheta = int(theta_max / precisionTheta) + 1
    nbPhi = int(phi_max / precisionPhi) + 1

    if nbTheta > nbTheta_max:
        precisionTheta = 0.1
        nbTheta = int(theta_max / precisionTheta + 1)
    if nbPhi > nbPhi_max:
        precisionPhi = 0.5
        nbPhi = int(nbPhi_max / precisionPhi + 1)

    print("Precision Theta = ", precisionTheta)
    print("Precision Phi = ", precisionPhi)

    line_theta_output = [(precisionTheta * k) for k in range(nbTheta)]
    line_phi_output = [(precisionPhi * x) for x in range(nbPhi)]

    return line_theta_output, line_phi_output, precisionTheta, precisionPhi

def obsolete_phi_theta_output(bsdf_data_input, bsdf_data_output):
    """
    That function writes the text nLines in the file

    Parameters
    ----------
    scatterRadial : list
        List of radial / theta angles
    scatterAzimuth : list
        List of azimuthal / phi angles
    symmetry : string
        PlaneSymmetrical, Asymmetrical, Asymmetrical4D
    bool_zemax0_speos1 : boolean
        if zemax data to convert == 0
    """

    # Limitation
    nbTheta_max = 1000
    nbPhi_max = 1000
    theta_max = 90
    phi_max = 360
    # multiple = 0.5
    if bsdf_data_input.symmetry == "PlaneSymmetrical" and bsdf_data_input.zemax_or_speos == 0:
        phi_max = 180
        nbPhi_max = 500

    # Default values
    precisionTheta = bsdf_data_input.theta_input[0][1] - bsdf_data_input.theta_input[0][0]
    precisionPhi = bsdf_data_input.phi_input[0][1] - bsdf_data_input.phi_input[0][0]

    nbTheta = int(theta_max / precisionTheta) + 1
    nbPhi = int(phi_max / precisionPhi) + 1

    if nbTheta > nbTheta_max:
        precisionTheta = 0.1
        nbTheta = int(theta_max / precisionTheta + 1)
    if nbPhi > nbPhi_max:
        precisionPhi = 0.5
        nbPhi = int(nbPhi_max / precisionPhi + 1)

    print("Precision Theta = ", precisionTheta)
    print("Precision Phi = ", precisionPhi)

    bsdf_data_output.theta_input = [(precisionTheta * k) for k in range(nbTheta)]
    bsdf_data_output.phi_input = [(precisionPhi * x) for x in range(nbPhi)]

    return bsdf_data_output

def obsolete_convert_zemax_to_speos_bsdf(inputFilepath):
    """
    That function converts a Zemax BSDF file into a Speos BSDF file

    Parameters
    ----------
    inputFilepath : filename
        Zemax BSDF file to read
    """

    print("This Python code converts ZEMAX BSDF file to SPEOS BSDF format\n")

    # Reading Zemax file
    print("Reading Zemax BSDF file: " + str(inputFilepath) + "...\n")
    bool_log = 0

    (
        scatterType,
        symmetry,
        angleIncidence,
        sampleRotation,
        line_theta_zemax,
        line_phi_zemax,
        tisData,
        bsdfData_zemax,
    ) = obsolete_read_zemax_bsdf(inputFilepath, bool_log)

    # Recommended precisionTheta and precisionPhi
    bool_zemax0_speos1 = 1
    (
        line_theta_speos,
        line_phi_speos,
        dtheta_speos,
        dphi_speos,
    ) = obsolete_phi_theta_recommended_precision(line_theta_zemax, line_phi_zemax, symmetry, bool_zemax0_speos1)

    # Converting Zemax data to Speos data
    print("Converting Zemax data to Speos data...\n")
    binaryMode = 0
    anisotropyVector = [0, 1, 0]
    nb_reflection_transmission = 1
    bool_speos_brdf = 0
    bsdfDataSpeos = obsolete_convert_zemax_speos_bsdf_data(
        nb_reflection_transmission,
        symmetry,
        scatterType,
        sampleRotation,
        angleIncidence,
        line_theta_zemax,
        line_phi_zemax,
        line_theta_speos,
        line_phi_speos,
        bsdfData_zemax,
        bool_speos_brdf,
    )

    if scatterType == "BTDF":
        line_theta_speos = [(90 + dtheta_speos * k) for k in range(len(line_theta_speos))]

    # Normalization
    print("Computing Speos normalization...\n")
    bool_log = 1
    normalizationBsdf, bsdfDataSpeos = obsolete_normalize_bsdf_data(
        len(sampleRotation),
        len(angleIncidence),
        line_theta_speos,
        line_phi_speos,
        tisData,
        bsdfDataSpeos,
        bool_zemax0_speos1,
        bool_log,
    )

    # Writing Speos file content in nLines
    print("Writing Speos header data\n")
    nLines = obsolete_write_speos_header_bsdf(
        binaryMode,
        anisotropyVector,
        scatterType,
        sampleRotation,
        angleIncidence,
        tisData,
    )
    print("Writing Speos main data\n")
    nLines = obsolete_write_speos_data_bsdf(
        nLines, scatterType, len(sampleRotation), len(angleIncidence), line_theta_speos, line_phi_speos, bsdfDataSpeos
    )
    # Writing Speos file content (nLines) in a file
    print("Writing Speos BSDF file\n")
    # Speos output file
    outputFilepath = (
        os.path.splitext(inputFilepath)[0].lower()
        + "_"
        + str(dtheta_speos)
        + "_"
        + str(dphi_speos)
        + ".anisotropicbsdf"
    )
    write_file(outputFilepath, nLines)

    print(".....End of process\n")
