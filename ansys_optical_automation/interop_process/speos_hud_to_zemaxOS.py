import shutil  # Used to copy file to Zemax Objects directory

from ansys_optical_automation.zemax_process.base import BaseZOS


class SpeosHUDToZemax:
    """
    This class contains functions for parsing input files and applying them to Zemax OpticStudio
    This script contains the following assumptions:
    1. We have three files exported from Speos:
        a. HUD_SpeosToZemax
        b. HUD surface export
        c. Windshield.STP
    2. Assuming the comment "#Point coordinates start from Eyebox and go to PGU. These are vertices of 4 polylines,
        so there are 8 vertices, 4 are duplicates" is always used directly preceding the point-by-point data
    3. Assuming three objects + one step file are being imported. Nothing more
    4. Assuming the points and tilt angles are all preceded by "n Point:" or "Z:" or "Y':" or "X'':"
    5. Assuming point-by-point data is duplicated such that lines 6, 4, and 2 may be removed
    6. Assuming object size data is directly preceded by "#Surface dimensions start from freeform and go to PGU.
        There are 4 edge dimensions per surface"
    7. Assuming sizing data directly precedes the position data, and is duplicated
    8. Assumption: We are using MM units and received m units from Speos
    9. Assume eyebox data is given in the first lines, separate from other position/tilt data
    10. Assume gut ray strikes all objects except windshield at local axis (center)
    11. BIG assumption: We do not need the Horizontal/Vertical angle reports with the X, Y, Z data now
    12. Assume gut ray leaving PGU is at a 180 degree X Tilt wrt the PGU position
    13. Assume gut ray leaving PGU may not be "normal to" the PGU itself.
        Will allow for some minor optimization of position
        a. Assume gut ray leaving PGU is at object 3
    """

    def __init__(self, fullFile, freeformFile, freeformFileName, windshieldStart, windshieldFile):
        """
        Description
        ----------
        This function will be used to connect to the ZOS-API and to bring in all external files

        Parameters
        ----------
        fullFile : str
            This file provides the full positional/angle information for each object in the HUD system
        freeformFile : str
            This file provides the full freeform mirror profile as an Extended Polynomial
        freeformFileName : str
            This is the name of the freeformFile input without the path
        windshieldStart : str
            This file represents the windshield as a CAD object. Will be used for direct import into OS
        windshieldFile : str
            The name of the windshield CAD file

        Returns
        -------
        None
        """
        self.fullFile = fullFile
        self.freeformFile = freeformFile
        self.freeformFileName = freeformFileName
        windshieldStart = windshieldStart
        self.windshieldFile = windshieldFile

        # Make some connections to the base ZOS
        self.zos = BaseZOS()
        self.TheSystem = self.zos.the_application.PrimarySystem

        # Begin by creating a new system in Zemax OpticStudio's Non-Sequential Mode
        self.TheSystem.New(False)
        self.TheSystem.MakeNonSequential()

        # Convert the system units to MM as that is what we received from Speos
        self.TheSystem.SystemData.Units.LensUnits = self.zos.zosapi.SystemData.ZemaxSystemUnits.Millimeters

        # Give the file a new name
        self.osFilename = self.fullFile[:-4] + "_OSOutput.zmx"
        self.TheSystem.SaveAs(self.osFilename)

        # Identify the location of the Objects Directory and move the windshield file there
        objectsDir = self.zos.the_application.ObjectsDir
        newPath = objectsDir + "\\CAD Files\\" + windshieldFile
        shutil.copyfile(windshieldStart, newPath)

        # Update the CAD libraries.
        # This is required to import the windshield due to restrictions on sizing using the Parasolid libraries
        self.TheSystem.TheApplication.Preferences.General.SetUseParasolid(False)

        # Move into the NSC file editing stage
        self.NSCFileCreation(self.TheSystem, objectsDir)

        # TO-DO: Create a method to confirm successful conversion

    def HUDfileParser(self, filePath):
        """
        This function will be used to parse through the HUD_SpeosToZemax text file
        This function pulls the relevant components
        ----------
        Parameters
        ----------
        filePath : str
            Defining the location of the HUD_SpeosToZemax text file

        Returns
        -------
        A set of arrays containing the object-specific position and tilt data
        Arrays include:
            eyebox
            windshield
            freeform
            fold
            pgu
        """
        # Begin by creating arrays for each object
        fileData = []
        eyebox = []
        # Windshield data is largely unused and is only made available for further optimization of position
        windshield = []
        freeform = []
        fold = []
        pgu = []

        # Parse file line-by-line into an array
        with open(filePath) as the_file:
            for the_line in the_file:
                # Pull the data from text into an array. Remove the new line character at the end
                fileData.append(the_line[:-1])

        # Store location data to a new array
        positionData = []
        tiltData = []
        sizeData = []

        # Note: We are assuming the standard 3-objects.
        # If more objects w/ data provided, the following line numbers will fail

        # Search for the point-by-point data. Nominally, this is stored at line 43
        # However, it may be the case that we update the output
        # So let's search for the comment directly preceding the point data
        for line in range(len(fileData)):
            if (
                fileData[line]
                == "#Surface dimensions start from freeform and go to PGU. There are 4 edge dimensions per surface"
            ):
                startPosition = line + 1

        # Grab the point-by-point position data AND the tilt data
        for i in range(startPosition, len(fileData)):
            # Start with point data. All the point data have a value at the front that is a number
            # TO-DO: Update the method for checking the first character
            if fileData[i][0] == "1" or fileData[i][0] == "2" or fileData[i][0] == "3" or fileData[i][0] == "4":
                trimVal = fileData[i].find("(") + 1
                endTrimVal = fileData[i].find(")")
                fileData[i] = fileData[i][trimVal:endTrimVal]
                dummy = fileData[i].replace(" ", "").split(",")
                # Convert to numbers instead of string and convert to mm
                for n in range(len(dummy)):
                    dummy[n] = float(dummy[n]) * 1000
                positionData.append(dummy)
            if fileData[i][0] == "Z" or fileData[i][0] == "Y" or fileData[i][0] == "X":
                trimVal = fileData[i].find(":") + 1
                endTrimVal = len(fileData[i])
                fileData[i] = float(fileData[i][trimVal:endTrimVal])
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
        # Setting up an array to hold the dummy data, and then it will replace tiltData
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
            msg = (
                "#Point coordinates start from Eyepoint and go to PGU. "
                "These are vertices of 4 polylines,so there are 8 vertices, 4 are duplicates"
            )
            if fileData[line] == msg:
                # if fileData[line] == "#Point coordinates start from Eyepoint and go to PGU.
                # These are vertices of 4 polylines, so there are 8 vertices, 4 are duplicates":
                startSizing = line + 1

        # The sizing data directly precedes the position data, so that will be our range
        # The sizing data is also duplicated, so we will skip some lines in the loop
        for i in range(startPosition + 1, startSizing - 1, 4):
            # Store the X, Y size to a dummy array and convert to mm
            dummy = [float(fileData[i]) * 1000, float(fileData[i + 1]) * 1000]
            dummy.sort()
            sizeData.append(dummy)

        # Eyebox data
        # Eyebox X size (Speos Vertical output)
        eyebox.append(float(fileData[3]))
        # Eyebox Y size (Speos Horizontal data)
        eyebox.append(float(fileData[1]))
        eyebox.append(0)
        for i in range(3):
            eyebox.append(positionData[0][i])
        eyebox.append(0)
        eyebox.append(fileData[8])
        eyebox.append(fileData[7])

        # Windshield data
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

        # Freeform data
        for i in range(2):
            freeform.append(sizeData[0][i])
        # Distance from freeform to fold mirror
        freeform.append(float(fileData[23]))
        for i in range(3):
            freeform.append(positionData[2][i])
        for i in range(3):
            freeform.append(tiltData[0][i])

        # Fold mirror data
        for i in range(2):
            fold.append(sizeData[1][i])
        # Distance from fold mirror to PGU
        fold.append(float(fileData[26]))
        for i in range(3):
            fold.append(positionData[3][i])
        for i in range(3):
            fold.append(tiltData[1][i])

        # PGU data
        for i in range(2):
            pgu.append(sizeData[2][i])
        pgu.append(0)
        for i in range(3):
            pgu.append(positionData[4][i])
        for i in range(3):
            pgu.append(tiltData[2][i])

        return eyebox, windshield, freeform, fold, pgu

    def NSCFreeformConversion(self, freeformProfile, obj, objData):
        """
        Parameters
        ----------
        freeformProfile : str
            Defining the location of the file containing the freeform profile information
        obj : zosapi.Editors.NCE.INCERow
            The object in the NSCE representing the freeform mirror
        objData : zosapi.Editors.NCE.IObject
            The parameter data for the given Zemax OpticStudio object

        Returns
        -------
        None
        """

        file = freeformProfile
        # Define arrays to hold the data
        dataArray = []
        # Define arrays to hold the multi-dimensional data
        # positionData = []
        # paramData = []
        # Parse the file #
        # Open the file and analyze
        with open(file) as the_file:
            for the_line in the_file:
                # Pull the data from text into an array. Remove the new line character at the end
                dataArray.append(the_line[:-1])
        # Line 1
        # Skip this line. This is handled in the full file

        # Line 2
        # Vector data. Ignore for now

        # Line 5
        # Pull the radius data
        dummy = dataArray[5].replace(" ", "").split("=")
        radius = float(dummy[1])

        # Line 6
        # Pull the conic data
        dummy = dataArray[6].replace(" ", "").split("=")
        conic = float(dummy[1])

        # Line 7 #
        # Pull the normalization data
        # TO DO: make sure this norm value is a radius. If not, convert
        dummy = dataArray[7].replace(" ", "").split("=")
        normRad = float(dummy[1])

        # Line 8 #
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
                findY = dummy[0].find("Y") + 1
                xVal = int(dummy[0][1:findY-1])
                yVal = int(dummy[0][findY:])
                # Max X calculation
                if xVal > maxX:
                    maxX = xVal
                # Max Y calculation
                if yVal > maxY:
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
                if osParam.Header == paramData[test][0]:
                    osParam.DoubleValue = paramData[test][1]

    def newObj(self, NSCE):
        """
        Description
        ----------
        I will be calling the InsertNewObject command a lot to add items, so a function is created to handle that call

        Parameters
        ----------
        NSCE : zosapi.Editors.NCE
            Zemax OpticStudio Non-Sequential Component Editor object

        Returns
        -------
        new : zosapi.Editors.NCE.INCERow
            A new object in the NSCE
        """

        new = NSCE.InsertNewObjectAt(NSCE.NumberOfObjects + 1)
        return new

    def newType(self, objectIn, enumVal, file):
        """
        Description
        ----------
        This will be used to change the type of a new object

        Parameters
        ----------
        objectIn : zosapi.Editors.NCE.INCERow
            The INSCRow object containing the newly-created Non-Sequential object
        enumVal : enum zosapi.Editors.NCE.ObjectType
            Used to determine the settings for the object type we are modifying
        file : str
            If needed, a file may be required to change the object type

        Returns
        -------
        None

        """

        typeSet = objectIn.GetObjectTypeSettings(enumVal)
        typeSet.FileName1 = file
        objectIn.ChangeType(typeSet)

    def NSCFileCreation(self, ZOSSystem, objectsDir):
        """
        Parameters
        ----------
        ZOSSystem : zosapi.IOpticalSystem
            This is the lens file we are working with
        objectsDir : str
            The location of the Objects directory within the home Zemax folder

        Returns
        -------
        None
        """
        # Send for the eyebox, windshield, freeform, fold mirror, and PGU coordinates
        componentCoordinateData = self.HUDfileParser(self.fullFile)
        eyebox = componentCoordinateData[0]
        # windshield = componentCoordinateData[1]
        freeform = componentCoordinateData[2]
        fold = componentCoordinateData[3]
        pgu = componentCoordinateData[4]

        # Access the Non-Sequential Component Editor to begin writing to the Zemax OS file
        TheNCE = ZOSSystem.NCE

        # Begin writing to the NCE
        # Set a Null Object to move into the Speos +X coordinate system
        globalRef = TheNCE.GetObjectAt(1)
        globalRef.Comment = "Move to Speos axis"
        globalRef.TiltAboutY = -90

        # PGU Setup
        obj = self.newObj(TheNCE)
        self.newType(obj, self.zos.zosapi.Editors.NCE.ObjectType.Rectangle, "")
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

        # Gut ray. Used to confirm the tilts are correct
        obj = self.newObj(TheNCE)
        self.newType(obj, self.zos.zosapi.Editors.NCE.ObjectType.SourceRay, "")
        obj.Comment = "Gut Ray from PGU"
        obj.RefObject = -1
        obj.TiltAboutX = 180
        # Access parameter values for object type
        param = obj.ObjectData
        param.NumberOfLayoutRays = 1
        param.NumberOfAnalysisRays = 1

        # Optimize the angular position of the gut ray leaving the PGU
        # This assumes the gut ray from the PGU is at object 3
        TheMFE = ZOSSystem.MFE
        for i in range(1, 4):
            op = TheMFE.AddOperand()
            op.ChangeType(self.zos.zosapi.Editors.MFE.MeritOperandType.NSRA)
            op.GetOperandCell(self.zos.zosapi.Editors.MFE.MeritColumn.Param2).IntegerValue = 3
            op.GetOperandCell(self.zos.zosapi.Editors.MFE.MeritColumn.Param5).IntegerValue = 1
            op.GetOperandCell(self.zos.zosapi.Editors.MFE.MeritColumn.Param6).IntegerValue = i
            op.Target = fold[i + 2]
            op.Weight = 1.0
        # Set gut ray tilts variable
        obj.TiltAboutXCell.MakeSolveVariable()
        obj.TiltAboutYCell.MakeSolveVariable()
        # Optimize for a couple of cycles. It should not take long to converge to near 0
        localOpt = ZOSSystem.Tools.OpenLocalOptimization()
        localOpt.Algorithm = self.zos.zosapi.Tools.Optimization.OptimizationAlgorithm.DampedLeastSquares
        localOpt.Cycles = self.zos.zosapi.Tools.Optimization.OptimizationCycles.Fixed_5_Cycles
        localOpt.RunAndWaitForCompletion()
        localOpt.Close()
        # Remove variables
        ZOSSystem.Tools.RemoveAllVariables()

        # Fold mirror setup
        obj = self.newObj(TheNCE)
        self.newType(obj, self.zos.zosapi.Editors.NCE.ObjectType.Rectangle, "")
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

        # Freeform setup
        obj = self.newObj(TheNCE)
        self.newType(obj, self.zos.zosapi.Editors.NCE.ObjectType.ExtendedPolynomialSurface, "")
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
        file = self.freeformFileName[:-3] + "UDA"
        udaFile = objectsDir + "\\Apertures\\" + file
        toFile = "REC 0 0 " + str(freeform[1] / 2) + " " + str(freeform[0] / 2)
        with open(udaFile, "w") as f:
            f.write(toFile)
        # Apply the UDA to the freeform
        obj.TypeData.UserDefinedAperture = True
        obj.TypeData.UDAFile = file
        # Access parameter values for the object type
        param = obj.ObjectData
        param.RadialHeight = freeform[1] / 2
        # Access a function which parses the polynomial terms
        self.NSCFreeformConversion(self.freeformFile, obj, param)

        # Windshield setup
        # For now, we are simply loading in a CAD with the position data already applied
        # TO-DO: Make into a native object
        obj = self.newObj(TheNCE)
        self.newType(obj, self.zos.zosapi.Editors.NCE.ObjectType.CADPartSTEPIGESSAT, self.windshieldFile)
        obj.Material = "MIRROR"

        # Eyebox setup
        obj = self.newObj(TheNCE)
        self.newType(obj, self.zos.zosapi.Editors.NCE.ObjectType.DetectorRectangle, "")
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

        # Opposing gut ray setup
        # Gut ray from the Eyebox to ensure proper alignment/tilt angles are applied
        obj = self.newObj(TheNCE)
        self.newType(obj, self.zos.zosapi.Editors.NCE.ObjectType.SourceRay, "")
        obj.Comment = "Opposing Gut Ray"
        obj.RefObject = -1
        # Access parameter values for the object type
        param = obj.ObjectData
        param.NumberOfLayoutRays = 1
        param.NumberOfAnalysisRays = 1

        # Save the file
        ZOSSystem.Save()
