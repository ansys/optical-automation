import os
import win32com.client
import numpy as np

from ansys_optical_automation.zemax_process.base import BaseZOS

# ===============================
# 2022-10-12 Etienne Lesage - Creating the code.
# 2022-12-23 Sandrine Auriol - Reading detector data using zos-api
# ===============================

def Convert_ZemaxtxtDetector_to_Speosxmptxt(DetectorFileName):
    """
    function that converts the Zemax text detector data to speos xmp text

    Parameters
    ----------
    DetectorFileName : string
        Full path filename of the detector data
    Returns
    -------
    xmpTextFilePath : string
        Path of a text file representing the xmp data of the detector
    """

    # Open Zemax text detector
    tfile = open(DetectorFileName, 'r')
    fileContent = tfile.readlines()
    tfile.close()
    # Reformat the content
    fileContent = [s.replace("\n", "") for s in fileContent]
    fileContent = [s.replace("\x00", "") for s in fileContent]
    fileContent[:] = [x for x in fileContent if x]
    # SensorName = fileContent[4] # name of the sensor
    # SensorName = ''.join([i for i in SensorName if (i.isalnum() or i.isspace())])
    lineInformation = fileContent[5]
    lineInformation = lineInformation.split(",")
    SizeInformation = lineInformation[0]
    SizeInformation = SizeInformation.replace("Size", "")
    SizeInformation = SizeInformation.replace("W X", ",")
    SizeInformation = SizeInformation.replace("H", ",")
    SizeInformation = SizeInformation.split(",")
    SensorSizeW = float(SizeInformation[0]) # Width of the sensor
    SensorSizeH = float(SizeInformation[1]) # Height of the sensor
    PixelsInformation = lineInformation[1]
    PixelsInformation = PixelsInformation.replace("Pixels", "")
    PixelsInformation = PixelsInformation.replace("W X", ",")
    PixelsInformation = PixelsInformation.replace("H", ",")
    PixelsInformation = PixelsInformation.replace("H", ",")
    PixelsInformation = PixelsInformation.split(",")
    SensorPixelsW = int(PixelsInformation[0]) # Horizontal resolution of the sensor
    SensorPixelsH = int(PixelsInformation[1]) # Vertical resolution of the sensor
    lineInformation = fileContent[7]
    lineInformation = lineInformation.split(": ")
    lineInformation = lineInformation[1].split(" ")
    TotalPower = float(lineInformation[0]) # Received power

    # Speos xmp header
    xmpTextDescription = ""
    xmpTextDescription += "3\n"
    xmpTextDescription += "0\n"
    xmpTextDescription += "0\n"
    xmpTextDescription += "1\n"
    xmpTextDescription += str(-SensorSizeW / 2) + "\t" + str(SensorSizeW / 2) + "\t" + str(-SensorSizeH / 2) + "\t" + str(SensorSizeH / 2) + "\n"
    xmpTextDescription += str(SensorPixelsW) + "\t" + str(SensorPixelsH) + "\n"
    xmpTextDescription += "-1\t1\t" + str(TotalPower) + "\n"
    xmpTextDescription += "1\n"

    # Speos xmp data
    for lineIndex in range(19, len(fileContent), 1):
        lineInformation = fileContent[lineIndex]
        xmpTextDescription += lineInformation.split("\t", 1)[1] + "\n"

    # Write the Speos text xmp data
    length_no_extension = len(DetectorFileName) - 4
    # xmpFileName = os.path.join(workingDir, DetectorFileName[:length_no_extension] + ".xmp")
    # xmpFilePath = os.path.join(workingDir, xmpFileName)
    # length_no_extension = len(xmpFileName)-4
    xmpTextFilePath = os.path.join(DetectorFileName[:length_no_extension] + "_speos_xmp.txt")
    tfile = open(xmpTextFilePath, 'w')
    tfile.writelines(xmpTextDescription)
    tfile.close()
    print("The file has been created!", xmpTextFilePath)

    return xmpTextFilePath

def Convert_ZemaxDDR_to_Speosxmptxt(DetectorFileName):
    """
    function that converts the Zemax DDR detector data to speos xmp text

    Parameters
    ----------
    DetectorFileName : string
        Full path filename of the detector data
    Returns
    -------
    xmpTextFilePath : string
        Path of a text file representing the xmp data of the detector
    """

    # To read the detector data we load them in a Zemax file
    zos = BaseZOS()
    # load local variables
    zosapi = zos.zosapi
    the_application = zos.the_application
    the_system = zos.the_system
    sample_dir = the_application.SamplesDir

    # Make new file
    test_file = sample_dir + '\\Non-sequential\\Sources\\detector.zos'
    # print(test_file)
    the_system.New(False)
    the_system.MakeNonSequential()
    the_system.SaveAs(test_file)
    detector_number = 1
    the_nce = the_system.NCE
    mydetector=the_nce.GetObjectAt(detector_number)
    mydetector.ChangeType(mydetector.GetObjectTypeSettings(zosapi.Editors.NCE.ObjectType.DetectorRectangle))

    #Need to create a system with a detector to be able to load the data
    #LoadDetector (int ObjectNumber, string fileName, bool appendData)
    the_system.Save()
    the_application.BeginMessageLogging()
    result_load_detector = the_nce.LoadDetector(detector_number, DetectorFileName, False)
    error = the_application.RetrieveLogMessages()
    print("Detector loaded successfully?", result_load_detector)
    if not error == "":
        print(error)
    the_application.ClearMessageLog()

    # Read the data of the detector
    hits_bool_return, total_hits = the_nce.GetDetectorData(detector_number, -3, 0, 0)  # Object Number, Pix -3 & Data=0 (total hits)
    flux_bool_return, total_flux = the_nce.GetDetectorData(detector_number, 0, 0, 0)  # Object Number, Pix=0 & Data=0 (total flux)
    # print(" total hits  = ", round(total_hits,0), "\n", "total flux =  ", round(total_flux,3))
    # get number of pixels in X, Y
    dims_bool_return, X_detectorDims, Y_detectorDims = the_nce.GetDetectorDimensions(detector_number, 0, 0)
    # GetAllDetectorDataSafe (int ObjectNumber, int Data)
    # Data = 0 --> Flux
    # Data = 1 --> Flux/area
    # Data = 2 --> Flux/solid angle pixel
    # detector_data = np.zeros((X_detectorDims,Y_detectorDims))
    detector_data = the_nce.GetAllDetectorDataSafe(detector_number,1)

    # Making data easier to assign in the header
    SensorPixelsW = X_detectorDims
    SensorPixelsH = Y_detectorDims
    XHalfWidth = mydetector.GetObjectCell(zosapi.Editors.NCE.ObjectColumn.Par1).DoubleValue
    YHalfWidth = mydetector.GetObjectCell(zosapi.Editors.NCE.ObjectColumn.Par2).DoubleValue
    SensorSizeW = 2 * XHalfWidth
    SensorSizeH = 2 * YHalfWidth
    TotalPower = total_flux

    # Header of the xmp file
    xmpTextDescription = ""
    xmpTextDescription += "3\n"
    xmpTextDescription += "0\n"
    xmpTextDescription += "0\n"
    xmpTextDescription += "1\n"
    xmpTextDescription += str(-SensorSizeW / 2) + "\t" + str(SensorSizeW / 2) + "\t" + str(-SensorSizeH / 2) + "\t" + str(SensorSizeH / 2) + "\n"
    xmpTextDescription += str(SensorPixelsW) + "\t" + str(SensorPixelsH) + "\n"
    xmpTextDescription += "-1\t1\t" + str(TotalPower) + "\n"
    xmpTextDescription += "1\n"

    # Block data of the xmp
    for x in range(X_detectorDims):
        for y in range(Y_detectorDims):
            xmpTextDescription += str(detector_data[x,y])+"\t"
        xmpTextDescription += "\n"

    # define the full path to the xmp file
    length_no_extension = len(DetectorFileName) - 4
    # xmpFileName = os.path.join(workingDir, DetectorFileName[:length_no_extension] + ".xmp")
    # xmpFilePath = os.path.join(workingDir, xmpFileName)
    # length_no_extension = len(xmpFileName)-4
    xmpTextFilePath = os.path.join(DetectorFileName[:length_no_extension] + ".txt")
    # write the text data into the xmp file
    tfile = open(xmpTextFilePath, 'w')
    tfile.writelines(xmpTextDescription)
    tfile.close()
    # clearing
    os.remove(test_file)

    return xmpTextFilePath

def ApplyDisplaySettings(xmpViewer,scaleParameters):
    """
    function that applies scale values to the xmp viewer

    Parameters
    ----------
    xmpViewer : object
        Object representing the xmp viewer
    scaleParameters : list
        list of scale values containing the min and max of the irradiance [min, max]
    Returns
    -------
    nothing
    """
    retval = xmpViewer.SetLogScale(False)
    retval = xmpViewer.SetColorMode(4)
    retval = xmpViewer.SetMinMax(scaleParameters[0], scaleParameters[1])
    retval = xmpViewer.UpdateDisplayAndData
    retval = xmpViewer.ShowRuler(True)

def Measurements(xmpViewer):
    """
    function that measures the flux and maximum irradiance in the xmp viewer

    Parameters
    ----------
    xmpViewer : object
        Object representing the xmp viewer
    Returns
    -------
    max_xmp : float
        Maximum irradiance measured in the xmp viewer
    flux_xmp : float
        Total flux measured in the xmp viewer
    """
    retval = xmpViewer.SurfaceRectangleCalculation(0, 0, xmpViewer.XWidth, xmpViewer.YHeight)
    max_xmp = retval[3]
    flux_xmp = retval[6]
    # print("Max: ", round(max_xmp,3))
    # print("Flux: ", round(flux_xmp,3))

    return max_xmp, flux_xmp

def CreateXMPFile(xmpViewer, xmpTextFilePath):
    """
    function that imports the text file into the xmp viewer

    Parameters
    ----------
    xmpViewer : object
        Object representing the xmp viewer
    xmpTextFilePath : string
        Path of a text file representing the xmp data of the detector
    Returns
    -------
    Nothing
    """
    if os.path.exists(xmpTextFilePath):    
        retval = xmpViewer.ImportTXT(xmpTextFilePath)
        os.remove(xmpTextFilePath)

def OpenXMPFile(xmpViewer, xmpFilePath):
    """
    function that opens the xmp file

    Parameters
    ----------
    xmpViewer : object
        Object representing the xmp viewer
    xmpFilePath : string
        Filename of the xmp file
    Returns
    -------
    Nothing
    """
    if os.path.exists(xmpFilePath):    
        retval = xmpViewer.OpenFile(xmpFilePath)

def ExportData(xmpViewer, xmpTextFilePath, workingDir, zoomParameters, scaleParameters, SensorName = ""):

    xmpTextFileName = os.path.basename(xmpTextFilePath)
    
    xmpToSave = os.path.join(workingDir, os.path.splitext(xmpTextFileName)[0] + ".xmp")
    retval = xmpViewer.SaveFile(xmpToSave)
    
    imageFilePath = os.path.join(workingDir, os.path.splitext(xmpTextFileName)[0] + ".bmp")
    scaleImageFilePath = os.path.join(workingDir, os.path.splitext(xmpTextFileName)[0] + "_scale.bmp")    
    xmpZoomFilePath = os.path.join(workingDir, os.path.splitext(xmpTextFileName)[0] + "_zoom.xmp")
    imageFilePath2 = os.path.join(workingDir, os.path.splitext(xmpTextFileName)[0] + "_zoom.bmp")
    
    if SensorName != "":
        imageFilePath = os.path.join(workingDir, SensorName + ".bmp")
        scaleImageFilePath = os.path.join(workingDir, SensorName + "_scale.bmp")
        xmpZoomFilePath = os.path.join(workingDir, SensorName + "_zoom.xmp")
        imageFilePath2 = os.path.join(workingDir, SensorName + "_zoom.bmp")

    retval = xmpViewer.ExportXMPImage(imageFilePath)
    retval = xmpViewer.SaveScaleImage(scaleImageFilePath, 0, 174, 256)
    
    retval = xmpViewer.SurfaceRectangleExport(zoomParameters[0], zoomParameters[1], zoomParameters[2], zoomParameters[3], xmpZoomFilePath, 1)
    retval = xmpViewer.OpenFile(xmpZoomFilePath)
    
    # retval = xmpViewer.ExportXMPImage(imageFilePath)
    retval = xmpViewer.ExportXMPtoResizedImage(imageFilePath2, 10)

def Convert_detectordata_to_xmp(DetectorFileName,datatype, bool_image):
    """
    function that converts a DDR file into a xmp file

    Parameters
    ----------
    DetectorFileName : string
        Full path filename of the detector data
    datatype: string
        String that can be ".DDR" or ".TXT"
    bool_image : boolean
        Boolean = true to save a bmp of the xmp file
    Returns
    -------
    xmpFilePath : string
        Path of the xmp file representing the detector data
    """
    print("WARNING: the detector data has to be in Watts!")

    # Open xmp viewer
    xmpViewer = win32com.client.Dispatch("XMPViewer.Application")
    vpCalc = win32com.client.Dispatch("VPLab.Application")

    # Convert the data and write it into a text file in the xmp format
    if datatype.upper() == ".DDR":
        xmpTextFilePath = Convert_ZemaxDDR_to_Speosxmptxt(DetectorFileName)
    if datatype.upper() == ".TXT":
        xmpTextFilePath = Convert_ZemaxtxtDetector_to_Speosxmptxt(DetectorFileName)

    if os.path.exists(xmpTextFilePath):
        # Imports the text file into the xmp viewer
        CreateXMPFile(xmpViewer, xmpTextFilePath)
        # Make measurements in the xmp viewer
        Max_xmp, Flux_xmp = Measurements(xmpViewer)
        scaleParameters = [0,Max_xmp]
        ApplyDisplaySettings(xmpViewer,scaleParameters)

        # Define and create the xmp file
        length_no_extension = len(xmpTextFilePath)-4
        xmpFilePath = os.path.join(xmpTextFilePath[:length_no_extension] + ".xmp")
        xmpViewer.SaveFile(xmpFilePath)
        print("The file has been created!", xmpFilePath)

        # Check
        OpenXMPFile(xmpViewer, xmpFilePath) #not sure this line is needed except to check the xmp file?

        # Create an image if bool_image == true
        if bool_image:
            imageFilePath = os.path.splitext(xmpFilePath)[0] + ".bmp"
            xmpViewer.ExportXMPImage(imageFilePath)

        # xmpViewer.Show(1)
        # input("Press Enter to continue...")

        xmpViewer = None
        vpCalc = None

        return xmpFilePath

def DifferencePercentage(xmpFilePath1, xmpFilePath2,bool_image):
    """
    function that substracts two xmp files

    Parameters
    ----------
    xmpFilePath1 : string
        path to the 1st xmp file
    xmpFilePath2 : string
        path to the 2nd xmp file
    bool_image : boolean
        Boolean = true to save a bmp of the xmp file
    Returns
    -------
    xmpResult : string
        path to the percentage difference xmp file
    """

    # Define the xmp difference file
    xmpResult_temp = os.path.splitext(xmpFilePath1)[0] + "_temp.xmp"

    # Open xmp viewer
    xmpViewer = win32com.client.Dispatch("XMPViewer.Application")
    vpCalc = win32com.client.Dispatch("VPLab.Application")
    vpCalc.FileSource1(xmpFilePath1)
    vpCalc.FileSource2(xmpFilePath2)
    vpCalc.FileResult(xmpResult_temp)
    # Substract xmpFilePath1 - xmpFilePath2
    vpCalc.Operation("Subtraction")
    vpCalc.Process

    if os.path.exists(xmpResult_temp):
        xmpViewer.OpenFile(xmpResult_temp)
        # xmpViewer.SetLogScale(False)
        xmpResult_temp_2 = os.path.splitext(xmpFilePath1)[0] + "_temp2.xmp"
        vpCalc.FileSource1(xmpFilePath1)
        vpCalc.FileSource2(xmpResult_temp)
        vpCalc.FileResult(xmpResult_temp_2)
        # Substract (xmpFilePath1 - xmpFilePath2)/xmpFilePath1
        vpCalc.Operation("MapDivision")
        vpCalc.Process

        if os.path.exists(xmpResult_temp_2):
            xmpViewer.OpenFile(xmpResult_temp_2)
            # xmpViewer.SetLogScale(False)
            os.remove(xmpResult_temp)
            xmpResult = os.path.splitext(xmpFilePath1)[0] + "_difference.xmp"
            vpCalc.FileSource1(xmpResult_temp_2)
            vpCalc.AddParam(100.0)
            vpCalc.FileResult(xmpResult)
            vpCalc.Operation("ValueMultiplication")
            vpCalc.Process
            os.remove(xmpResult_temp_2)

            # retval = xmpViewer.SetLogScale(False)
            if bool_image:
                imageFilePath = os.path.splitext(xmpResult)[0] + "_difference.bmp"
                xmpViewer.ExportXMPImage(imageFilePath)
            # retval = xmpViewer.ExportXMPtoResizedImage(imageFilePath, 10)
            # retval = xmpViewer.SaveScaleImage(scaleImageFilePath, 0, 174, 256)

        print("The file has been created!", xmpResult)

        return xmpResult


print('This Python code converts OpticStudio detector viewer text output to Speos xmp format.')


