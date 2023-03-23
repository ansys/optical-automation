import clr, os, winreg
from itertools import islice

# This boilerplate requires the 'pythonnet' module.
# The following instructions are for installing the 'pythonnet' module via pip:
#    1. Ensure you are running a Python version compatible with PythonNET. Check the article "ZOS-API using Python.NET" or
#    "Getting started with Python" in our knowledge base for more details.
#    2. Install 'pythonnet' from pip via a command prompt (type 'cmd' from the start menu or press Windows + R and type 'cmd' then enter)
#
#        python -m pip install pythonnet

class PythonStandaloneApplication4(object):
    class LicenseException(Exception):
        pass
    class ConnectionException(Exception):
        pass
    class InitializationException(Exception):
        pass
    class SystemNotPresentException(Exception):
        pass

    def __init__(self, path=None):
        # determine location of ZOSAPI_NetHelper.dll & add as reference
        aKey = winreg.OpenKey(winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER), r"Software\Zemax", 0, winreg.KEY_READ)
        zemaxData = winreg.QueryValueEx(aKey, 'ZemaxRoot')
        NetHelper = os.path.join(os.sep, zemaxData[0], r'ZOS-API\Libraries\ZOSAPI_NetHelper.dll')
        winreg.CloseKey(aKey)
        clr.AddReference(NetHelper)
        import ZOSAPI_NetHelper
        
        # Find the installed version of OpticStudio
        #if len(path) == 0:
        if path is None:
            isInitialized = ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize()
        else:
            # Note -- uncomment the following line to use a custom initialization path
            isInitialized = ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize(path)
        
        # determine the ZOS root directory
        if isInitialized:
            dir = ZOSAPI_NetHelper.ZOSAPI_Initializer.GetZemaxDirectory()
        else:
            raise PythonStandaloneApplication4.InitializationException("Unable to locate Zemax OpticStudio.  Try using a hard-coded path.")

        # add ZOS-API referencecs
        clr.AddReference(os.path.join(os.sep, dir, "ZOSAPI.dll"))
        clr.AddReference(os.path.join(os.sep, dir, "ZOSAPI_Interfaces.dll"))
        import ZOSAPI

        # create a reference to the API namespace
        self.ZOSAPI = ZOSAPI

        # create a reference to the API namespace
        self.ZOSAPI = ZOSAPI

        # Create the initial connection class
        self.TheConnection = ZOSAPI.ZOSAPI_Connection()

        if self.TheConnection is None:
            raise PythonStandaloneApplication4.ConnectionException("Unable to initialize .NET connection to ZOSAPI")

        self.TheApplication = self.TheConnection.CreateNewApplication()
        if self.TheApplication is None:
            raise PythonStandaloneApplication4.InitializationException("Unable to acquire ZOSAPI application")

        if self.TheApplication.IsValidLicenseForAPI == False:
            raise PythonStandaloneApplication4.LicenseException("License is not valid for ZOSAPI use")

        self.TheSystem = self.TheApplication.PrimarySystem
        if self.TheSystem is None:
            raise PythonStandaloneApplication4.SystemNotPresentException("Unable to acquire Primary system")

    def __del__(self):
        if self.TheApplication is not None:
            self.TheApplication.CloseApplication()
            self.TheApplication = None
        
        self.TheConnection = None
    
    def OpenFile(self, filepath, saveIfNeeded):
        if self.TheSystem is None:
            raise PythonStandaloneApplication4.SystemNotPresentException("Unable to acquire Primary system")
        self.TheSystem.LoadFile(filepath, saveIfNeeded)

    def CloseFile(self, save):
        if self.TheSystem is None:
            raise PythonStandaloneApplication4.SystemNotPresentException("Unable to acquire Primary system")
        self.TheSystem.Close(save)

    def SamplesDir(self):
        if self.TheApplication is None:
            raise PythonStandaloneApplication4.InitializationException("Unable to acquire ZOSAPI application")

        return self.TheApplication.SamplesDir

    def ExampleConstants(self):
        if self.TheApplication.LicenseStatus == self.ZOSAPI.LicenseStatusType.PremiumEdition:
            return "Premium"
        elif self.TheApplication.LicenseStatus == self.ZOSAPI.LicenseStatusType.EnterpriseEdition:
            return "Enterprise"
        elif self.TheApplication.LicenseStatus == self.ZOSAPI.LicenseStatusType.ProfessionalEdition:
            return "Professional"
        elif self.TheApplication.LicenseStatus == self.ZOSAPI.LicenseStatusType.StandardEdition:
            return "Standard"
        elif self.TheApplication.LicenseStatus == self.ZOSAPI.LicenseStatusType.OpticStudioHPCEdition:
            return "HPC"
        else:
            return "Invalid"
    
    def reshape(self, data, x, y, transpose = False):
        """Converts a System.Double[,] to a 2D list for plotting or post processing
        
        Parameters
        ----------
        data      : System.Double[,] data directly from ZOS-API 
        x         : x width of new 2D list [use var.GetLength(0) for dimension]
        y         : y width of new 2D list [use var.GetLength(1) for dimension]
        transpose : transposes data; needed for some multi-dimensional line series data
        
        Returns
        -------
        res       : 2D list; can be directly used with Matplotlib or converted to
                    a numpy array using numpy.asarray(res)
        """
        if type(data) is not list:
            data = list(data)
        var_lst = [y] * x;
        it = iter(data)
        res = [list(islice(it, i)) for i in var_lst]
        if transpose:
            return self.transpose(res);
        return res
    
    def transpose(self, data):
        """Transposes a 2D list (Python3.x or greater).  
        
        Useful for converting mutli-dimensional line series (i.e. FFT PSF)
        
        Parameters
        ----------
        data      : Python native list (if using System.Data[,] object reshape first)    
        
        Returns
        -------
        res       : transposed 2D list
        """
        if type(data) is not list:
            data = list(data)
        return list(map(list, zip(*data)))

if __name__ == '__main__':
    zos = PythonStandaloneApplication4()
    
    # load local variables
    ZOSAPI = zos.ZOSAPI
    TheApplication = zos.TheApplication
    TheSystem = zos.TheSystem
    
    # Insert Code Here

    ########################## Import additional modules ################################

    import math
    # Used to move STP file to Zemax Objects directory
    import shutil
    # Used to select files
    import tkinter as tk
    from tkinter import filedialog


    

    ########################## Pull file names ##########################################
    ##folder = input("Enter the working directory for this HUD model: ")
    #folder = r"C:\Users\Alexandra.Culler\Documents\Ansys Integrations\Steve_Speos_HUD\Sample2_Web_HUD"

    root = tk.Tk()
    root.withdraw()

    # Let's assume we have three files from SPEOS:
    # 1. HUD_SpeosToZemax
    # 2. HUD surface export. Let's assume the same naming scheme. If not, use the following:
    # for file in os.listdir(folder):
    #    if file.endswith(".txt") and file != "HUD_SpeosToZemax.txt":
    #        print(file)
    # <or use another input to ask for the freeform file>
    # <or or have it delivered at the top of the HUD_SpeosToZemax txt file>
    # 3. Windshield.STEP

    ######## Other dependencies:
    # Assuming the comment "#Point coordinates start from Eyepoint and go to PGU. These are vertices of 4 polylines, so there are 8 vertices, 4 are duplicates" is always used directly preceding the point-by-point data
    # Assuming three objects + one step file are being imported. Nothing more
    # Assuming the points and tilt angles are all preceded by "n Point:" or "Z:" or "Y':" or "X'':"
    # Assuming point-by-point data is duplicated such that lines 6, 4, and 2 may be removed
    # Assuming object size data is directly preceded by "#Surface dimensions start from freeform and go to PGU. There are 4 edge dimensions per surface"
    # Assuming sizing data directly precedes the position data, and is duplicated
    # Assumption: We are using MM units and received m units from Speos
    # Assume eyebox data is given in the first lines, separate from other position/tilt data
    # Assume gut ray strikes all objects except windshield at local axis (center)
    # BIG assumption: We do not need the Horizontal/Vertical angle reports with the X, Y, Z data now
    # Assume gut ray leaving PGU is at a 180 degree X Tilt wrt the PGU position
    # Assume gut ray leaving PGU may not be "normal to" the PGU itself. Will allow for some minor optimization of position
        # Assume gut ray leaving PGU is at object 3

    fullFile = filedialog.askopenfilename(
        title = "Select the HUD_SpeosToZemax text file...",
        filetypes = [('text files', '*.txt')]
        )
    freeformFile = filedialog.askopenfilename(
        title = "Select the freeform profile text file...",
        filetypes = [('text files', '*.txt')]
        )
    freeformFileName = os.path.basename(freeformFile)
    windshieldStart = filedialog.askopenfilename(
        title = "Select the windshield CAD file...",
        filetypes = [('CAD file', '*.stp')]
        )
    windshieldFile = os.path.basename(windshieldStart)

    # Select the three relevant files at once
    ##file1, file2, file3 = filedialog.askopenfilenames(
    ##    title = "Select Speos output files for input into OpticStudio..."
    ##    )
        

    # Copy the windshield file to the global directory
    objDir = TheApplication.ObjectsDir
    newPath = objDir + "\\CAD Files\\" + windshieldFile
    shutil.copyfile(windshieldStart, newPath)


    ########################## Pull in freeform data #############################
    ########################## Freeform function #################################
    ### This function will parse through the data from the text file and strip out the numeric data
    def surfaceDataExtract(file, dataArray, objData):

        # Define arrays to hold the multi-dimensional data
        positionData = []
        paramData = []

        ######## Parse the file ########
        # Open the file and analyze
        with open(file) as the_file:
            for the_line in the_file:
                # Pull the data from text into an array. Remove the new line character at the end
                dataArray.append(the_line[:-1])

        ######## Line 1 ########
        # Skip this line. This is handled in the full file

        ######## Line 2 ########
        # Vector data. Ignore for now

        ######## Line 5 ########
        # Pull the radius data
        dummy = dataArray[5].replace(" ", "").split("=")
        radius = float(dummy[1])

        ######## Line 6 ########
        # Pull the conic data
        dummy = dataArray[6].replace(" ", "").split("=")
        conic = float(dummy[1])

        ######## Line 7 ########
        # Pull the normalization data
        ###### TO DO: make sure this norm value is a radius. If not, convert
        dummy = dataArray[7].replace(" ", "").split("=")
        normRad = float(dummy[1])

        ######## Line 8 ########
        # Extract the surface parameter data
        # We need to store the coefficient title and the corresponding value
        # We also need to know how many X and Y coefficients. 
        paramData = []
        maxX = 0
        maxY = 0
        for i in range(8, len(dataArray)):
                if len(dataArray[i]):
                        trimVal = dataArray[i].find("X")
                        dataArray[i] = dataArray[i][trimVal:]
                        dummy = dataArray[i].replace(" ", "").split("=")
                        # X and Y analysis
                        # Use the left-hand side of the equals sign to find the max X and max Y
                        # First, strip out the values
                        # Then store against a max
                        findY = dummy[0].find("Y")
                        xVal = int(dummy[0][1:findY])
                        yVal = int(dummy[0][findY + 1:])
                        # Max X calculation
                        if (xVal > maxX):
                                maxX = xVal
                        # Max Y calculation
                        if (yVal > maxY):
                                maxY = yVal
                        paramData.append(dummy)

        # With the maxX and maxY, find the number of params required in OS.
        # OS defines parameters in a group where XNY0 is the left bound and X0YN is the right bound
        # Sum maxX and maxY to find N, then sum from 2 to N to find the # of Terms
        maxN = maxX + maxY
        termCount = 0
        # Sum the values from 2 (lowest number of polys in OS) to the max + 1 inclusive
        for val in range(2, maxN + 2):
                termCount = termCount + val

        objData.Radius = radius
        objData.Conic = conic
        objData.NormRad = normRad
        objData.NumberOfTerms = termCount

        # Begin filling in the next columns, beginning in with the column directly to the right of the #terms
        colStart = objData.NumberOfTermsCell.Col + 1
        colEnd = termCount + colStart - 1
        for col in range(colStart, colEnd):
            osParam = obj.GetCellAt(col)
            # For every column in OS, check if the column header is in use within our file
            for test in range(len(paramData)):
                if (osParam.Header == paramData[test][0]):
                    osParam.DoubleValue = paramData[test][1]




    #####################################################################################
    ########################## Begin parsing full file #############################

    # Begin by creating arrays for each object
    fileData = []
    eyebox = []
    # Windshield data is largely unused and is only made available for further optimization of position
    windshield = []
    freeform = []
    fold = []
    pgu = []

    # Parse file line-by-line into an array
    with open(fullFile) as the_file:
        for the_line in the_file:
            # Pull the data from text into an array. Remove the new line character at the end
            fileData.append(the_line[:-1])

    # Store location data to a new array
    positionData = []
    tiltData = []
    sizeData = []

    ######### Note: We are assuming the standard 3-objects.
    ######### If more objects w/ data provided, the following line numbers will fail

    # Search for the point-by-point data. Nominally, this is stored at line 43
    # However, it may be the case that we update the output
    # So let's search for the comment directly preceding the point data
    for line in range(len(fileData)):
        if fileData[line] == "#Point coordinates start from Eyepoint and go to PGU. These are vertices of 4 polylines, so there are 8 vertices, 4 are duplicates":
            startPosition = line + 1

    # Grab the point-by-point position data AND the tilt data
    for i in range(startPosition, len(fileData)):
        # Start with point data. All the point data have a value at the front that is a number
        # I'm gonna build this the inefficient way
        # TO-DO: Update the method for checking the first character
        if fileData[i][0] == "1" or fileData[i][0] == "2" or fileData[i][0] == "3" or fileData[i][0] == "4":
            trimVal = fileData[i].find("(")
            endTrimVal = fileData[i].find(")")
            fileData[i] = fileData[i][trimVal + 1:endTrimVal]
            dummy = fileData[i].replace(" ", "").split(",")
            # Convert to numbers instead of string and convert to mm
            for n in range(len(dummy)):
                dummy[n] = float(dummy[n]) * 1000
            positionData.append(dummy)
        if fileData[i][0] == "Z" or fileData[i][0] == "Y" or fileData[i][0] == "X":
            trimVal = fileData[i].find(":")
            fileData[i] = float(fileData[i][trimVal + 1:len(fileData[i])])
            tiltData.append(fileData[i])

    # Get rid of the duplicate position data lines
    positionData.pop(6)
    positionData.pop(4)
    positionData.pop(2)

    # Organize and update the tilt data with the following knowledge
    # SPEOS Z -> OS X Tilt
    # SPEOS Y -> OS Y Tilt
    # SPEOS X -> (-1) * OS Z Tilt
    # TO-DO: Make this more efficient
    # Setting up an array to hold the dummy data and then it will replace tiltData
    hold = []
    for i in range(0, len(tiltData), 3):
        dummy = []
        dummy.append(tiltData[i])
        dummy.append(tiltData[i + 1])
        dummy.append(-tiltData[i + 2])
        hold.append(dummy)

    # Replace tiltData with the cleaned up version of the tilt data
    tiltData = hold
        

    # Store size data to a new array. We have to do this bc it may be given to us out of order
    # The larger value should always be the Y-size of the object in OS. Use the array to sort
    # First, we must find where the size data begins (search for the comment)
    for line in range(len(fileData)):
        if fileData[line] == "#Surface dimensions start from freeform and go to PGU. There are 4 edge dimensions per surface":
            startSizing = line + 1

    # The sizing data directly precedes the position data, so that will be our range
    # The sizing data is also duplicated, so we will skip some lines in the loop
    for i in range(startSizing, startPosition - 1, 4):
        # Store the X, Y size to a dummy array and convert to mm
        dummy = [float(fileData[i]) * 1000, float(fileData[i+1]) * 1000]
        dummy.sort()
        sizeData.append(dummy)


    ########### Use the organized data above to populate arrays about each object type
    # The arrays will have the following info, in this order:
    # Horizontal size (2 * Y Half Width)
    # Vertical size (2 * X Half Width)
    # Distance travelled to next object (generally un-needed, but useful for comparison)
    # X position
    # Y position
    # Z position
    # X Tilt
    # Y Tilt
    # Z Tilt

    # If above values cannot be applied to object, they are set to -1 in the array

    ## Eyebox data
    # Eyebox X size (SPEOS Vertical output)
    eyebox.append(float(fileData[3]))
    # Eyebox Y size (SPEOS Horizontal data)
    eyebox.append(float(fileData[1]))
    eyebox.append(0)
    for i in range(3):
        eyebox.append(positionData[0][i])
    eyebox.append(0)
    eyebox.append(fileData[8])
    eyebox.append(fileData[7])

    ## Windshield data
    for i in range(2):
        windshield.append(0)
    # Distance from windshield to freeform
    windshield.append(float(fileData[20]))
    # The position data for the windshield is unique bc this is not the location of the local axis
    # Rather, this is the location where the ray is striking the windshield
    for i in range(3):
        windshield.append(positionData[1][i])
    for i in range(3):
        windshield.append(0)
    
    ## Freeform data
    for i in range(2):
        freeform.append(sizeData[0][i])
    # Distance from freeform to fold mirror
    freeform.append(float(fileData[23]))
    for i in range(3):
        freeform.append(positionData[2][i])
    for i in range(3):
        freeform.append(tiltData[0][i])

    ## Fold mirror data
    for i in range(2):
        fold.append(sizeData[1][i])
    # Distance from fold mirror to PGU
    fold.append(float(fileData[26]))
    for i in range(3):
        fold.append(positionData[3][i])
    for i in range(3):
        fold.append(tiltData[1][i])

    ## PGU data
    for i in range(2):
        pgu.append(sizeData[2][i])
    pgu.append(0)
    for i in range(3):
        pgu.append(positionData[4][i])
    for i in range(3):
        pgu.append(tiltData[2][i])



    ########################## Get started in OpticStudio #############################
    # Temporarily watch what's going on
    #TheSystem.UpdateMode = ZOSAPI.LensUpdateMode.AllWindows

    # Begin by making sure we are in NSC Mode
    TheSystem.New(False)
    TheSystem.MakeNonSequential()

    # Give the file a new name
    osFilename = fullFile[:-4] + "_OSOutput.zmx"
    TheSystem.SaveAs(osFilename)

    # Convert system units to MM as that is what we received from Speos
    TheSystem.SystemData.Units.LensUnits = ZOSAPI.SystemData.ZemaxSystemUnits.Millimeters

    # Access the NCE
    TheNCE = TheSystem.NCE

    ####### Begin adding items #######
    # Set a Null Object to move into the Speos +X coordinate system
    globalRef = TheNCE.GetObjectAt(1)
    globalRef.Comment = "Move to Speos axis"
    globalRef.TiltAboutY = -90

    # I will be calling the InsertNewObject command a lot, so let's make it a function
    def newObj(editor):
        new = editor.InsertNewObjectAt(editor.NumberOfObjects + 1)
        return new
    # Use a single function to change type
    def newType(objectIn, enumVal, file):
        typeSet = objectIn.GetObjectTypeSettings(enumVal)
        typeSet.FileName1 = file
        objectIn.ChangeType(typeSet)

    ### PGU Setup
    obj = newObj(TheNCE)
    newType(obj, ZOSAPI.Editors.NCE.ObjectType.Rectangle, "")
    obj.Comment = "SPEOS PGU"
    obj.RefObject = 1
    obj.XPosition = pgu[5]
    obj.YPosition = pgu[4]
    obj.ZPosition = (-1) * pgu[3]
    obj.TiltAboutX = pgu[6]
    obj.TiltAboutY = pgu[7]
    obj.TiltAboutZ = pgu[8]
    # Access parameter values for object type
    param = obj.ObjectData
    param.XHalfWidth = pgu[0] / 2
    param.YHalfWidth = pgu[1] / 2
    
    ### Gut ray. Used to confirm the tilts are correct
    obj = newObj(TheNCE)
    newType(obj, ZOSAPI.Editors.NCE.ObjectType.SourceRay, "")
    obj.Comment = "Gut Ray from PGU"
    obj.RefObject = -1
    obj.TiltAboutX = 180
    # Access parameter values for object type
    param = obj.ObjectData
    param.NumberOfLayoutRays = 1
    param.NumberOfAnalysisRays = 1

    ### Optimize the angular postition of the gut ray leaving the PGU
    # This assumes the gut ray from the PGU is at object 3
    TheMFE = TheSystem.MFE
    for i in range(1, 4):
        op = TheMFE.AddOperand()
        op.ChangeType(ZOSAPI.Editors.MFE.MeritOperandType.NSRA)
        op.GetOperandCell(ZOSAPI.Editors.MFE.MeritColumn.Param2).IntegerValue = 3
        op.GetOperandCell(ZOSAPI.Editors.MFE.MeritColumn.Param5).IntegerValue = 1
        op.GetOperandCell(ZOSAPI.Editors.MFE.MeritColumn.Param6).IntegerValue = i
        op.Target = fold[i + 2]
        op.Weight = 1.0
    # Set gut ray tilts variable
    obj.TiltAboutXCell.MakeSolveVariable()
    obj.TiltAboutYCell.MakeSolveVariable()
    # Optimize for a couple of cycles. It should not take long to converge to near 0
    localOpt = TheSystem.Tools.OpenLocalOptimization()
    localOpt.Algorithm = ZOSAPI.Tools.Optimization.OptimizationAlgorithm.DampedLeastSquares
    localOpt.Cycles = ZOSAPI.Tools.Optimization.OptimizationCycles.Fixed_5_Cycles
    localOpt.RunAndWaitForCompletion()
    localOpt.Close()
    # Remove variables
    TheSystem.Tools.RemoveAllVariables()

    ### Fold mirror setup
    obj = newObj(TheNCE)
    newType(obj, ZOSAPI.Editors.NCE.ObjectType.Rectangle, "")
    obj.Comment = "SPEOS Fold Mirror"
    obj.RefObject = 1
    obj.XPosition = fold[5]
    obj.YPosition = fold[4]
    obj.ZPosition = (-1) * fold[3]
    obj.TiltAboutX = fold[6]
    obj.TiltAboutY = fold[7]
    obj.TiltAboutZ = fold[8]
    obj.Material = "MIRROR"
    # Access parameter values for object type
    param = obj.ObjectData
    param.XHalfWidth = fold[0] / 2
    param.YHalfWidth = fold[1] / 2

    ### Freeform setup
    obj = newObj(TheNCE)
    newType(obj, ZOSAPI.Editors.NCE.ObjectType.ExtendedPolynomialSurface, "")
    obj.Comment = "SPEOS Freeform"
    obj.RefObject = 1
    obj.XPosition = freeform[5]
    obj.YPosition = freeform[4]
    obj.ZPosition = (-1) * freeform[3]
    obj.TiltAboutX = freeform[6]
    obj.TiltAboutY = freeform[7]
    obj.TiltAboutZ = freeform[8] + 90
    obj.Material = "MIRROR"
    # Create a UDA file to apply to the freeform
    # Flip X and Y dir to account for the new coordinate system. X0Y9 needs a 90 degree twist in OS to match
    file = freeformFileName[:-3] + "UDA"
    udaFile = objDir + "\\Apertures\\" + file
    toFile = "REC 0 0 " + str(freeform[1] / 2) + " " + str(freeform[0] / 2)
    with open(udaFile, 'w') as f:
        f.write(toFile)
    # Apply the UDA to the freeform
    obj.TypeData.UserDefinedAperture = True
    obj.TypeData.UDAFile = file
    # Access parameter values for the object type
    freeformData = []
    param = obj.ObjectData
    param.RadialHeight = freeform[1] / 2
    # Access a function which parses the polynomial terms
    surfaceDataExtract(freeformFile, freeformData, param)

    ### Windshield setup
    # For now, we are simply loading in a CAD with the position data already applied
    # TO-DO: Make into a native object
    obj = newObj(TheNCE)
    newType(obj, ZOSAPI.Editors.NCE.ObjectType.CADPartSTEPIGESSAT, windshieldFile)
    obj.Material = "MIRROR"

    ### Eyebox setup
    obj = newObj(TheNCE)
    newType(obj, ZOSAPI.Editors.NCE.ObjectType.DetectorRectangle, "")
    obj.Comment = "SPEOS Eyebox"
    obj.RefObject = 1
    obj.XPosition = eyebox[5]
    obj.YPosition = eyebox[4]
    obj.ZPosition = (-1) * eyebox[3]
    obj.TiltAboutX = eyebox[6]
    obj.TiltAboutY = eyebox[7]
    obj.TiltAboutZ = eyebox[8]
    obj.Material = "ABSORB"
    # Access parameter values for the object type
    param = obj.ObjectData
    param.XHalfWidth = eyebox[0] / 2
    param.YHalfWidth = eyebox[1] / 2

    ### Opposing gut ray setup
    # Gut ray from the Eyebox to ensure proper alignment/tilt angles are applied
    obj = newObj(TheNCE)
    newType(obj, ZOSAPI.Editors.NCE.ObjectType.SourceRay, "")
    obj.Comment = "Opposing Gut Ray"
    obj.RefObject = -1
    # Access parameter values for the object type
    param = obj.ObjectData
    param.NumberOfLayoutRays = 1
    param.NumberOfAnalysisRays = 1
     

    #################### Save the file ####################
    TheSystem.Save()
    
    
    # This will clean up the connection to OpticStudio.
    # Note that it closes down the server instance of OpticStudio, so you for maximum performance do not do
    # this until you need to.
    del zos
    zos = None
