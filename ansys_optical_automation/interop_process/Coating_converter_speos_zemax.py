import math

import clr, os, winreg
from itertools import islice
import shutil
import numpy as np

from ansys_optical_automation.zemax_process.base import BaseZOS

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
    AngleOfIncidence_min = 0
    AngleOfIncidence_max = 90
    Nb_AngleOfIncidence = 91

    #Coating substrates
    #We could also read a Zemax file and extract coatings directly with the substrates
    #Here we extract two coatings per substrates: Substrate -> AIR and AIR -> SubstrateN-SK16
    SubstrateCatalog = "SCHOTT"
    SubstrateName = ("N-SK16", "N-SF56", "SF4")

    #Number of digits
    Nb_digits = 6
    
    #-------------------------------------------------------------------------------------------------

    myformat = '{:.'+str(Nb_digits)+'f}'
    Coatingfullfilename = Coatingfolder+'\\'+ Coatingfilename
    print(Coatingfullfilename)
    #f=open(Coatingfullfilename,"r")
    #CoatingFile = f.readlines()

    # creates a new API directory
    # print(TheApplication.SamplesDir)
    # apiPath = TheApplication.SamplesDir+ '\API\Matlab'
    # if (os.path.exists(str(apiPath)) == 0):
    #    os.mkdir(str(apiPath))
        
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
    # Fields
    Field_1 = TheSystemData.Fields.GetField(1)
    NewField_2 = TheSystemData.Fields.AddField(0,0.0,1.0)
    # Lens data 
    TheLDE = TheSystem.LDE
    
    AngleOfIncidence_delta = (AngleOfIncidence_max - AngleOfIncidence_min)/(Nb_AngleOfIncidence-1)

    Surface_1 = TheLDE.GetSurfaceAt(1)
    Surface_2 = TheLDE.InsertNewSurfaceAt(2)
    CoatingList = Surface_1.CoatingData.GetAvailableCoatings()
    CoatingList_Length = CoatingList.Length

    # Build MF
    # % Build a merit function
    # Lines 1 to 4 for Surf 1 and Lines 4 to 8 for Surf 2
    # % Operand 1 = Reflectance_Ppol
    # % Operand 2 = Transmittance_Ppol
    # % Operand 3 = Reflectance_Spol
    # % Operand 4 = Transmittance_Spol
    # %Sets the wavelength

    TheMFE = TheSystem.MFE
    wave = 1
    # % Sets the field
    Field = 2
    CODA_data = [1, 2, -1, -2]  # Intensity R, T (S pol and then P pol)

    Surf = 1
    for line in range(4):
        MFE_Operand1 = TheMFE.InsertNewOperandAt(line+1)
        MFE_Operand1.ChangeType(ZOSAPI.Editors.MFE.MeritOperandType.CODA)
        MFE_Operand1.GetCellAt(2).IntegerValue = Surf
        MFE_Operand1.GetCellAt(3).IntegerValue = wave
        MFE_Operand1.GetCellAt(4).IntegerValue = Field
        MFE_Operand1.GetCellAt(5).Value = str(CODA_data[line])

    # Coating = TestSurface.Coating; #returns a string
    
    TheSystem.Save()
    
    # % TABLE coating? Can be checked with number of layers
    # % TestSurface.CoatingData.NumberOfLayers = 0 --> TABLE
    # % TestSurface.CoatingData.NumberOfLayers <> 0 --> COAT
    # % If it is a TABLE coating --> direct conversion
    # % If it is a COAT coating --> need to use a method to convert

    for j in range(len(SubstrateName)):
        Material_1 = SubstrateName[j]
        Surface_1.Material = Material_1
        Material_2 = 'AIR'

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

                    # Coating data contains S and P and reflection and transmission
                    # coatingData = np.zeros(2*Nb_Wavelength, 2*Nb_AngleOfIncidence)
                    # coatingData_reverse = np.zeros(2*Nb_Wavelength, 2*Nb_AngleOfIncidence)

                    # Defining coatings on Surfaces 1 and 2 to take into account both directions
                    Surface_1.Coating = coating_name
                    Surface_2.Coating = coating_name
                    # Coating_nb_layers = TestSurface.CoatingData.NumberOfLayers
                    Name1 = str(coating_name) + '_' + str(Material_2) + '_' + str(Material_1)
                    Name2 = str(coating_name) + '_' + str(Material_1) + '_' + str(Material_2)
                    Coatingfilename1 = Name1 + '.coated'
                    Coatingfilename2 = Name2 + '.coated'
                    Coatingfullfilename1 = Coatingfolder + '\\' + Coatingfilename1
                    Coatingfullfilename2 = Coatingfolder + '\\' + Coatingfilename2
                    Errorfullfilename1 = Coatingfolder+'\\'+ Name1 + '_error.txt'
                    fileID1 = open(Coatingfullfilename1,'w')
                    fileID2 = open(Coatingfullfilename2, 'w')
                    fileErrorID = open(Errorfullfilename1,'w')

                    fileID1.write('OPTIS - Coated surface file v1.0\n')
                    fileID1.write(Name1+"\n")
                    fileID1.write(str(Nb_AngleOfIncidence) + " " + str(Nb_Wavelength)+"\n")
                    fileID2.write('OPTIS - Coated surface file v1.0\n')
                    fileID2.write(Name2+"\n")
                    fileID2.write(str(Nb_AngleOfIncidence) + " " + str(Nb_Wavelength) + "\n")

                    # % if Coating_nb_layers == 0
                    #     % Direct conversion reading the TABLE coating in the text file
                    # I could just write one file in that case.
                    for wavelength_index in range(Nb_Wavelength):
                        wavelength = round(Wavelength_min + wavelength_index * (Wavelength_max - Wavelength_min) / (
                                    Nb_Wavelength - 1),3)
                        fileID1.write("\t" + " " + myformat.format(Speos_Wavelength_units_um * wavelength) + " " + "\t")
                        fileID2.write("\t" + " " + myformat.format(Speos_Wavelength_units_um * wavelength) + " " + "\t")

                    fileID1.write("\n")
                    fileID2.write("\n")

    #               % --------------------------------------------------------
    #               % Method 1 --> doesn't catch error messages
    #               % Using directly CODA operand without going through the
    #               % merit function
    #               % --------------------------------------------------------
    #               % --------------------------------------------------------
    #               % Method 2 --> catches error messages
    #               % Using directly CODA operand through the merit function
    #               % --------------------------------------------------------
                    #print(fileErrorID,'Wavelength Angle_Incidence Error_Message\n')

                    fileErrorID.write('Wavelength Angle_Incidence Error_Message\n')

                    #AngleOfIncidenceList=np.arange(AngleOfIncidence_min, AngleOfIncidence_max, AngleOfIncidence_delta)

                    nb_errors = 0
                    for angleofincidence_index in range(Nb_AngleOfIncidence):
                        angleofincidence = AngleOfIncidence_min + angleofincidence_index * (
                                    AngleOfIncidence_max - AngleOfIncidence_min) / (Nb_AngleOfIncidence-1)
                        fileID1.write(myformat.format(angleofincidence)+' \t')
                        fileID2.write(myformat.format(angleofincidence) + ' \t')
                        # % Catching error messages
                        TheApplication.BeginMessageLogging()

                        # % Parallel = P
                        for wavelength_index in range(Nb_Wavelength):
                             wavelength = round(Wavelength_min + wavelength_index * (Wavelength_max - Wavelength_min) / (
                                        Nb_Wavelength - 1), 3)
                             TheSystem.SystemData.Wavelengths.GetWavelength(wave).Wavelength = wavelength
                             TheMFE.CalculateMeritFunction()
                             # Retrieve error messages if any
                             error = TheApplication.RetrieveLogMessages()
                             Surf = 1
                             TheSystem.SystemData.Fields.GetField(Field).Y = angleofincidence
                             Reflectance_Ppol_1 = TheMFE.GetOperandValue(ZOSAPI.Editors.MFE.MeritOperandType.CODA, Surf, wave, Field, 1, 0, 0, 0, 0)
                             Transmittance_Ppol_1 = TheMFE.GetOperandValue(ZOSAPI.Editors.MFE.MeritOperandType.CODA, Surf, wave, Field, 2, 0, 0, 0, 0)

                             Refraction_index = TheMFE.GetOperandValue(ZOSAPI.Editors.MFE.MeritOperandType.INDX, Surf,
                                                                       wave, 0, 1, 0, 0, 0, 0)
                             # Reverse data
                             n2_sintheta2 = Refraction_index * math.sin(math.radians(angleofincidence))
                             if n2_sintheta2 > 1:
                                 angle_reverse = 90
                             else:
                                 angle_reverse = math.degrees(math.asin(n2_sintheta2))

                             TheSystem.SystemData.Fields.GetField(Field).Y = angle_reverse
                             Reflectance_Ppol_2 = TheMFE.GetOperandValue(ZOSAPI.Editors.MFE.MeritOperandType.CODA, Surf,
                                                                         wave, Field, 1, 0, 0, 0, 0)
                             Transmittance_Ppol_2 = TheMFE.GetOperandValue(ZOSAPI.Editors.MFE.MeritOperandType.CODA,
                                                                           Surf, wave, Field, 2, 0, 0, 0, 0)
                             #when error message the merit function is not updated correctly so we need to read the operand with GetOperandValue
                             if not error == "":
                                nb_errors = nb_errors + 1
                                fileErrorID.write(str(wavelength) + " " + str(angleofincidence) + " " + str(error) + "\n")
                             fileID1.write(myformat.format(100 * Reflectance_Ppol_1) + '\t' + myformat.format(
                                100 * Transmittance_Ppol_1) + '\t')
                             fileID2.write(myformat.format(100 * Reflectance_Ppol_2) + '\t' + myformat.format(
                                 100 * Transmittance_Ppol_2) + '\t')
                             TheApplication.ClearMessageLog()
                        fileID1.write('\n\t')
                        fileID2.write('\n\t')
                        # % Perpendicular = S
                        for wavelength_index in range(Nb_Wavelength):
                            wavelength = Wavelength_min + wavelength_index * (Wavelength_max - Wavelength_min) / (
                                        Nb_Wavelength - 1)
                            TheSystem.SystemData.Wavelengths.GetWavelength(wave).Wavelength = wavelength
                            Surf = 1
                            TheSystem.SystemData.Fields.GetField(Field).Y = angleofincidence
                            Reflectance_Spol_1 = TheMFE.GetOperandValue(ZOSAPI.Editors.MFE.MeritOperandType.CODA, Surf, wave, Field, -1, 0, 0, 0, 0)
                            Transmittance_Spol_1 = TheMFE.GetOperandValue(ZOSAPI.Editors.MFE.MeritOperandType.CODA, Surf, wave, Field, -2, 0, 0, 0, 0)

                            Refraction_index = TheMFE.GetOperandValue(ZOSAPI.Editors.MFE.MeritOperandType.INDX, Surf,
                                                                      wave, 0, 1, 0, 0, 0, 0)
                            # Reverse data
                            n2_sintheta2 = Refraction_index * math.sin(math.radians(angleofincidence))
                            if n2_sintheta2 > 1:
                                angle_reverse = 90
                            else:
                                angle_reverse = math.degrees(math.asin(n2_sintheta2))

                            TheSystem.SystemData.Fields.GetField(Field).Y = angle_reverse

                            Reflectance_Spol_2 = TheMFE.GetOperandValue(ZOSAPI.Editors.MFE.MeritOperandType.CODA, Surf,
                                                                        wave, Field, -1, 0, 0, 0, 0)
                            Transmittance_Spol_2 = TheMFE.GetOperandValue(ZOSAPI.Editors.MFE.MeritOperandType.CODA,
                                                                          Surf, wave, Field, -2, 0, 0, 0, 0)
                            fileID1.write(myformat.format(100 * Reflectance_Spol_1) + "\t" + myformat.format(
                                100 * Transmittance_Spol_1) + "\t")
                            fileID2.write(myformat.format(100 * Reflectance_Spol_2) + "\t" + myformat.format(
                                100 * Transmittance_Spol_2) + "\t")
                        fileID1.write("\n")
                        fileID2.write("\n")

                    fileID1.close()
                    fileID2.close()
                    fileErrorID.close()
                    if nb_errors == 0:
                       os.remove(Errorfullfilename)

    # Write the coating files





    os.remove(DestinationFile)
    os.remove(testFile);
    # This will clean up the connection to OpticStudio.
    # Note that it closes down the server instance of OpticStudio, so you for maximum performance do not do
    # this until you need to.
    del zos
    zos = None

main()