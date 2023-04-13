class SpeosHUDToZemax:
    """This class contains functions for parsing input files and applying them to Zemax OpticStudio"""

    def __init__(self, filePath):
        """

        Parameters
        ----------
        filePath : str
            Defining the location of the HUD_SpeosToZemax text file

        Returns
        ----------
        None
        """
        # Begin by creating arrays for each object
        self.fileData = []
        self.eyebox = []
        # Windshield data is largely unused and is only made available for further optimization of position
        self.windshield = []
        self.freeform = []
        self.fold = []
        self.pgu = []

        # Parse file line-by-line into an array
        with open(filePath) as the_file:
            for the_line in the_file:
                # Pull the data from text into an array. Remove the new line character at the end
                self.fileData.append(the_line[:-1])

        # Store location data to a new array
        self.positionData = []
        self.tiltData = []
        self.sizeData = []

        # Note: We are assuming the standard 3-objects.
        # If more objects w/ data provided, the following line numbers will fail

        # Search for the point-by-point data. Nominally, this is stored at line 43
        # However, it may be the case that we update the output
        # So let's search for the comment directly preceding the point data
        for line in range(len(self.fileData)):
            if self.fileData[line] == "#Point coordinates start from Eyebox and go to PGU. These are vertices of 4 polylines, so there are 8 vertices, 4 are duplicates":
                startPosition = line + 1

        # Grab the point-by-point position data AND the tilt data
        for i in range(startPosition, len(self.fileData)):
            # Start with point data. All the point data have a value at the front that is a number
            # TO-DO: Update the method for checking the first character
            if self.fileData[i][0] == "1" or self.fileData[i][0] == "2" or self.fileData[i][0] == "3" or self.fileData[i][0] == "4":
                trimVal = self.fileData[i].find("(")
                endTrimVal = self.fileData[i].find(")")
                self.fileData[i] = self.fileData[i][trimVal + 1:endTrimVal]
                dummy = self.fileData[i].replace(" ", "").split(",")
                # Convert to numbers instead of string and convert to mm
                for n in range(len(dummy)):
                    dummy[n] = float(dummy[n]) * 1000
                self.positionData.append(dummy)
            if self.fileData[i][0] == "Z" or self.fileData[i][0] == "Y" or self.fileData[i][0] == "X":
                trimVal = self.fileData[i].find(":")
                self.fileData[i] = float(self.fileData[i][trimVal + 1:len(self.fileData[i])])
                self.tiltData.append(self.fileData[i])
        # Get rid of the duplicate position data lines
        self.positionData.pop(6)
        self.positionData.pop(4)
        self.positionData.pop(2)

        # Organize and update the tilt data with the following knowledge
        # SPEOS Z -> OS X Tilt
        # SPEOS Y -> OS Y Tilt
        # SPEOS X -> (-1) * OS Z Tilt
        # TO-DO: Make this more efficient
        # Setting up an array to hold the dummy data, and then it will replace tiltData
        hold = []
        for i in range(0, len(self.tiltData), 3):
            dummy = []
            dummy.append(self.tiltData[i])
            dummy.append(self.tiltData[i + 1])
            dummy.append(-self.tiltData[i + 2])
            hold.append(dummy)

        # Replace tiltData with the cleaned up version of the tilt data
        tiltData = hold

        # Store size data to a new array. We have to do this bc it may be given to us out of order
        # The larger value should always be the Y-size of the object in OS. Use the array to sort
        # First, we must find where the size data begins (search for the comment)
        for line in range(len(self.fileData)):
            if self.fileData[line] == "#Surface dimensions start from freeform and go to PGU. There are 4 edge dimensions per surface":
                startSizing = line + 1

        # The sizing data directly precedes the position data, so that will be our range
        # The sizing data is also duplicated, so we will skip some lines in the loop
        for i in range(startSizing, startPosition - 1, 4):
            # Store the X, Y size to a dummy array and convert to mm
            dummy = [float(self.fileData[i]) * 1000, float(self.fileData[i + 1]) * 1000]
            dummy.sort()
            self.sizeData.append(dummy)

        ## Eyebox data
        # Eyebox X size (Speos Vertical output)
        self.eyebox.append(float(self.fileData[3]))
        # Eyebox Y size (Speos Horizontal data)
        self.eyebox.append(float(self.fileData[1]))
        self.eyebox.append(0)
        for i in range(3):
            self.eyebox.append(self.positionData[0][i])
        self.eyebox.append(0)
        self.eyebox.append(self.fileData[8])
        self.eyebox.append(self.fileData[7])

        ## Windshield data
        for i in range(2):
            self.windshield.append(0)
        # Distance from windshield to freeform
        self.windshield.append(float(self.fileData[20]))
        # The position data for the windshield is unique bc this is not the location of the local axis
        # Rather, this is the location where the ray is striking the windshield
        for i in range(3):
            self.windshield.append(self.positionData[1][i])
        for i in range(3):
            self.windshield.append(0)

        ## Freeform data
        for i in range(2):
            self.freeform.append(self.sizeData[0][i])
        # Distance from freeform to fold mirror
        self.freeform.append(float(self.fileData[23]))
        for i in range(3):
            self.freeform.append(self.positionData[2][i])
        for i in range(3):
            self.freeform.append(tiltData[0][i])

        ## Fold mirror data
        for i in range(2):
            self.fold.append(self.sizeData[1][i])
        # Distance from fold mirror to PGU
        self.fold.append(float(self.fileData[26]))
        for i in range(3):
            self.fold.append(self.positionData[3][i])
        for i in range(3):
            self.fold.append(tiltData[1][i])

        ## PGU data
        for i in range(2):
            self.pgu.append(self.sizeData[2][i])
        self.pgu.append(0)
        for i in range(3):
            self.pgu.append(self.positionData[4][i])
        for i in range(3):
            self.pgu.append(tiltData[2][i])


    def NSCFreeformConversion(self, filePath, dataArray, objData):
        """

        Parameters
        ----------
        filePath : str
            Defining the location of the file containing the freeform profile information
        dataArray: array
            An array to store freeform data. Assume empty array
        objData: ZOSAPI.Editors.NCE.IObject
            The parameter data for the given Zemax OpticStudio object

        Returns
        ----------
        None
        """

    def NSCFileCreation(self, ZOSSystem):
        """

        Parameters
        ----------
        ZOSSystem : ZOSAPI.IOpticalSystem

        Returns
        -------
        None
        """
        # Access the NCE
        TheNCE = ZOSSystem.NCE