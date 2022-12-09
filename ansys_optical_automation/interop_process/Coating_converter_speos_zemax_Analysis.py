import math

import clr, os, winreg
from itertools import islice
import shutil
import numpy as np
import io

from ansys_optical_automation.zemax_process.base import BaseZOS
from comtypes.client import CreateObject

def main():

    zos = BaseZOS()
    
    # load local variables
    ZOSAPI = zos.zosapi
    TheApplication = zos.the_application
    TheSystem = zos.the_system
    
    # Insert Code Here
 
    
    #-------------------------------------------------------------------------------------------------
    # USER INPUT
    Coatingfilename = "Meopta_CoatingFileExample.dat"
    Coatingfolder = r"C:\Data\PROJECTS\MEOPTA_COATING\COATINGS"
    User_Wavelength_min = 0.31
    User_Wavelength_max = 0.9
    Nb_Wavelength = 5
    # Wavelength unit in Speos in um
    Speos_Wavelength_units_um = 1000
    # AngleOfIncidence_min = 0
    # AngleOfIncidence_max = 90
    # Nb_AngleOfIncidence = 91

    #Coating substrates
    #We could also read a Zemax file and extract coatings directly with the substrates
    #Here we extract two coatings per substrates: Substrate -> AIR and AIR -> SubstrateN-SK16
    SubstrateCatalog = "SCHOTT"
    SubstrateName = ("N-SK16", "N-SF56", "SF4")
    #SubstrateName = ("N-SK16")

    #Number of digits
    Nb_digits = 6
    skip_lines = 4
    
    #-------------------------------------------------------------------------------------------------

    myformat = '{:.'+str(Nb_digits)+'f}'
    Coatingfullfilename = Coatingfolder+'\\'+ Coatingfilename
    print(Coatingfullfilename)

    # Set up primary optical system
    TheSystem = TheApplication.PrimarySystem;
    sampleDir = TheApplication.SamplesDir;    
    coatingDir = TheApplication.CoatingDir;  
    DestinationFile=coatingDir+'\\'+Coatingfilename
    #print(DestinationFile)
    shutil.copy(Coatingfullfilename,DestinationFile)
    # Check the material catalog
    if not TheSystem.SystemData.MaterialCatalogs.IsCatalogInUse(SubstrateCatalog):
        TheSystem.SystemData.MaterialCatalogs.AddCatalog(SubstrateCatalog)
    # Make new file
    testFile = sampleDir+ '\coating.zos'
    #print(testFile)
    TheSystem.New(False)
    TheSystem.SaveAs(testFile)   
    # Coating catalog
    TheSystem.SystemData.Files.CoatingFile = Coatingfilename
    # Aperture
    TheSystemData = TheSystem.SystemData
    TheSystemData.Aperture.ApertureValue = 1
    TheLDE = TheSystem.LDE
    Surface_0 = TheLDE.GetSurfaceAt(0)
    Surface_1 = TheLDE.GetSurfaceAt(1)
    CoatingList = Surface_1.CoatingData.GetAvailableCoatings()
    CoatingList_Length = CoatingList.Length
    wave = 1
    TheSystem.Save()
    
    # % TABLE coating? Can be checked with number of layers
    # % TestSurface.CoatingData.NumberOfLayers = 0 --> TABLE
    # % TestSurface.CoatingData.NumberOfLayers <> 0 --> COAT
    # % If it is a TABLE coating --> direct conversion
    # % If it is a COAT coating --> need to use a method to convert

    for j in range(len(SubstrateName)):
        Material_1 = SubstrateName[j]
        Material_2_name = "AIR"
        Material_2 = ''

        # Open the material catalog and check the wavelength ranges
        My_Material_Catalog = TheSystem.Tools.OpenMaterialsCatalog()
        My_Material_Catalog.SelectedCatalog = SubstrateCatalog
        My_Material_Catalog.SelectedMaterial = Material_1
        Material_1_minwave = My_Material_Catalog.MinimumWavelength
        Material_1_maxwave = My_Material_Catalog.MaximumWavelength
        My_Material_Catalog.Close()

        if Material_1_minwave > User_Wavelength_min:
            Wavelength_min = Material_1_minwave
        else:
            Wavelength_min = User_Wavelength_min
        if User_Wavelength_max > Material_1_maxwave:
            Wavelength_max = Material_1_maxwave
        else:
            Wavelength_max = User_Wavelength_max
        Wavelength_delta = (Wavelength_max - Wavelength_min) / (Nb_Wavelength - 1)

        for i in range(CoatingList_Length):
            # print(CoatingList[i])
            coating_name = CoatingList[i]
            if not coating_name == 'None':
                Name1 = str(coating_name) + '_' + str(Material_2_name) + '_' + str(Material_1)
                Name2 = str(coating_name) + '_' + str(Material_1) + '_' + str(Material_2_name)
                Coatingfilename1 = Name1 + '.coated'
                Coatingfilename2 = Name2 + '.coated'
                Coatingfullfilename1 = Coatingfolder + '\\' + Coatingfilename1
                Coatingfullfilename2 = Coatingfolder + '\\' + Coatingfilename2
                # Errorfullfilename1 = Coatingfolder+'\\'+ Name1 + '_error.txt'
                fileID1 = open(Coatingfullfilename1,'w')
                fileID2 = open(Coatingfullfilename2, 'w')
                # fileErrorID = open(Errorfullfilename1,'w')
                coatingData = list()

                # From AIR TO SUBSTRATE
                Surface_0.Material = Material_2  # AIR
                Surface_1.Material = Material_1
                Surface_1.Coating = coating_name

                # Need to loop for all wavelength
                for wavelength_index in range(Nb_Wavelength):
                    wavelength = round(Wavelength_min + wavelength_index * (Wavelength_max - Wavelength_min) / (
                            Nb_Wavelength - 1), 3)
                    TheSystem.SystemData.Wavelengths.GetWavelength(wave).Wavelength = wavelength
                    #--------------------------------------------------------------------------------------------------
                    # Reading from the analysis
                    # No access to the settings so:
                    # - the incident angles should be set by default from 0 to 90
                    # - the surface should be set to 1
                    # --------------------------------------------------------------------------------------------------
                    # TheSystem.Save()

                    My_Transmission_vs_angle = TheSystem.Analyses.New_Analysis(
                        ZOSAPI.Analysis.AnalysisIDM.TransmissionvsAngle)
                    My_Transmission_vs_angle.ApplyAndWaitForCompletion()
                    My_Transmission_vs_angle_results = My_Transmission_vs_angle.GetResults()
                    Resultfullfilename = Coatingfolder + '\\My_Transmission_vs_angle_' + Name1 + '.txt'
                    bool_result = My_Transmission_vs_angle_results.GetTextFile(Resultfullfilename)
                    # if bool_result == False:
                        # print("The result file was not created!")
                    My_Transmission_vs_angle.Close()

                    # Reading the transmission file
                    bfile = io.open(Resultfullfilename, 'r', encoding='utf-16-le')
                    header_line = bfile.readline()
                    while header_line[1:10].strip() != 'Angle':
                        header_line = bfile.readline()
                    # Now reading the content
                    # Angle S - Reflect P - Reflect S - Transmit    P - Transmit
                    index_AngleOfIncidence = 0
                    dataLine = 'start'
                    while not len(dataLine) == 1:
                        dataLine = bfile.readline()
                        dataLine = dataLine.split('\t')
                        dataLine = dataLine[0:5] #only keeping the first 5 values
                        #Miss 3 lines
                        for index_line in range(skip_lines):
                            bfile.readline()
                        coatingData.append(dataLine)
                        index_AngleOfIncidence = index_AngleOfIncidence + 1
                        # print(index_AngleOfIncidence)
                        # Nb_AngleOfIncidence = len(coatingData)
                    Nb_AngleOfIncidence = index_AngleOfIncidence - 1
                    bfile.close()

                # Writing the file
                fileID1.write('OPTIS - Coated surface file v1.0\n')
                fileID1.write(Name1 + "\n")
                fileID1.write(str(Nb_AngleOfIncidence) + " " + str(Nb_Wavelength) + "\n")

                #1st line
                for wavelength_index in range(Nb_Wavelength):
                    wavelength = round(Wavelength_min + wavelength_index * (Wavelength_max - Wavelength_min) / (
                            Nb_Wavelength - 1), 3)
                    fileID1.write("\t" + " " + myformat.format(Speos_Wavelength_units_um * wavelength) + " " + "\t")
                fileID1.write("\n")
                #Loop to read the data
                for angle_index in range(Nb_AngleOfIncidence):
                    #1st column: angle of incidence
                    angleofincidence = float(coatingData[angle_index][0])
                    fileID1.write(myformat.format(angleofincidence) + ' \t')
                    for wavelength_index in range(Nb_Wavelength):
                        offset = angle_index+wavelength_index*(Nb_AngleOfIncidence+1)
                        Reflectance_Ppol_1 = float(coatingData[offset][2])
                        Transmittance_Ppol_1 = float(coatingData[offset][4])
                        fileID1.write(myformat.format(100 * Reflectance_Ppol_1) + '\t' + myformat.format(
                            100 * Transmittance_Ppol_1) + '\t')
                    fileID1.write("\n\t")
                    for wavelength_index in range(Nb_Wavelength):
                        offset = angle_index+wavelength_index*(Nb_AngleOfIncidence+1)
                        Reflectance_Spol_1 = float(coatingData[offset][1])
                        Transmittance_Spol_1 = float(coatingData[offset][3])
                        fileID1.write(myformat.format(100 * Reflectance_Spol_1) + "\t" + myformat.format(
                            100 * Transmittance_Spol_1) + "\t")
                    fileID1.write("\n")
                fileID1.close()
                print("File " + Coatingfilename1 + " created")
                coatingData.clear()
                os.remove(Resultfullfilename)

                # from SUBSTRATE to AIR
                Surface_0.Material = Material_1
                Surface_1.Material = Material_2 #AIR
                Surface_1.Coating = coating_name

                for wavelength_index in range(Nb_Wavelength):
                    wavelength = round(Wavelength_min + wavelength_index * (Wavelength_max - Wavelength_min) / (
                            Nb_Wavelength - 1), 3)
                    TheSystem.SystemData.Wavelengths.GetWavelength(wave).Wavelength = wavelength
                    # --------------------------------------------------------------------------------------------------
                    # Reading from the analysis
                    # No access to the settings so:
                    # - the incident angles should be set by default from 0 to 90
                    # - the surface should be set to 1
                    # --------------------------------------------------------------------------------------------------
                    # From AIR TO SUBSTRATE
                    # Need to loop for all wavelength
                    My_Transmission_vs_angle = TheSystem.Analyses.New_Analysis(
                        ZOSAPI.Analysis.AnalysisIDM.TransmissionvsAngle)
                    My_Transmission_vs_angle.ApplyAndWaitForCompletion()
                    My_Transmission_vs_angle_results = My_Transmission_vs_angle.GetResults()
                    Resultfullfilename2 = Coatingfolder + '\\My_Transmission_vs_angle_' + Name2 + '.txt'
                    bool_result = My_Transmission_vs_angle_results.GetTextFile(Resultfullfilename2)
                    # if bool_result == False:
                    #    print("The result file was not created!")
                    My_Transmission_vs_angle.Close()

                    # Reading the transmission file
                    # bfile = open(Resultfullfilename, 'r')
                    bfile = io.open(Resultfullfilename2, 'r', encoding='utf-16-le')
                    header_line = bfile.readline()
                    while header_line[1:10].strip() != 'Angle':
                        header_line = bfile.readline()
                    # Now reading the content
                    # Angle S - Reflect P - Reflect S - Transmit    P - Transmit
                    index_AngleOfIncidence = 0
                    dataLine = 'start'
                    while not len(dataLine) == 1:
                        dataLine = bfile.readline()
                        dataLine = dataLine.split('\t')
                        dataLine = dataLine[0:5]  # only keeping the first 5 values
                        # Miss 3 lines
                        for index_line in range(skip_lines):
                            bfile.readline()
                        coatingData.append(dataLine)
                        index_AngleOfIncidence = index_AngleOfIncidence + 1
                    Nb_AngleOfIncidence = index_AngleOfIncidence - 1
                    bfile.close()

                # Writing the file
                fileID2.write('OPTIS - Coated surface file v1.0\n')
                fileID2.write(Name2 + "\n")
                fileID2.write(str(Nb_AngleOfIncidence) + " " + str(Nb_Wavelength) + "\n")
                for wavelength_index in range(Nb_Wavelength):
                    wavelength = round(Wavelength_min + wavelength_index * (Wavelength_max - Wavelength_min) / (
                            Nb_Wavelength - 1), 3)
                    fileID2.write("\t" + " " + myformat.format(Speos_Wavelength_units_um * wavelength) + " " + "\t")
                fileID2.write("\n")

                for angle_index in range(Nb_AngleOfIncidence):
                    # 1st column: angle of incidence
                    angleofincidence = float(coatingData[angle_index][0])
                    fileID2.write(myformat.format(angleofincidence) + ' \t')
                    for wavelength_index in range(Nb_Wavelength):
                        offset = angle_index + wavelength_index * (Nb_AngleOfIncidence + 1)
                        Reflectance_Ppol_1 = float(coatingData[offset][2])
                        Transmittance_Ppol_1 = float(coatingData[offset][4])
                        fileID2.write(myformat.format(100 * Reflectance_Ppol_1) + '\t' + myformat.format(
                            100 * Transmittance_Ppol_1) + '\t')
                    fileID2.write("\n\t")
                    for wavelength_index in range(Nb_Wavelength):
                        offset = angle_index + wavelength_index * (Nb_AngleOfIncidence + 1)
                        Reflectance_Spol_1 = float(coatingData[offset][1])
                        Transmittance_Spol_1 = float(coatingData[offset][3])
                        fileID2.write(myformat.format(100 * Reflectance_Spol_1) + "\t" + myformat.format(
                            100 * Transmittance_Spol_1) + "\t")
                    fileID2.write("\n")
                fileID2.close()
                print("File " + Coatingfilename2 + " created")
                coatingData.clear()
                os.remove(Resultfullfilename2)

                # Create the BSDF180 that combines the two coatings
                BSDFViewer = CreateObject("SimpleBSDFSurfaceViewer.Application")
                # Builds BSDF 180
                BSDFViewer.BuildBSDF180(Coatingfullfilename1, Coatingfullfilename2)
                BSDF180filename = str(coating_name) + '_' + str(Material_2_name) + '_' + str(Material_1) + '.bsdf180'
                BSDF180fullfilename = Coatingfolder + '\\' + BSDF180filename
                # Save BSDF180
                BSDFViewer.SaveFile(BSDF180fullfilename)
                print("File " + BSDF180filename + " created\n")


    os.remove(DestinationFile)
    os.remove(testFile)
    # This will clean up the connection to OpticStudio.
    # Note that it closes down the server instance of OpticStudio, so you for maximum performance do not do
    # this until you need to.
    del zos
    zos = None


main()