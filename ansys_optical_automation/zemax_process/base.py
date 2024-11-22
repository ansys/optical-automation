import os
from itertools import islice


class BaseZOS:
    """
    Basic Class structure to start Zemax Opticstudio
    """

    class LicenseException(Exception):
        pass

    class ConnectionException(Exception):
        pass

    class InitializationException(Exception):
        pass

    class SystemNotPresentException(Exception):
        pass

    def __init__(self, path=None):
        """
        function that initializes the connection to OpticStudio

        Parameters
        ----------
        path

        Returns
        -------
        None

        """
        # determine location of ZOSAPI_NetHelper.dll & add as reference
        import clr

        program_data = os.environ["Programdata"]
        net_helper = os.path.join(program_data, "Zemax", r"ZOS-API\Libraries\ZOSAPI_NetHelper.dll")
        clr.AddReference(net_helper)
        import ZOSAPI_NetHelper

        # Find the installed version of OpticStudio
        # path = "C:\Program Files\Ansys Zemax OpticStudio 2023 R2.01"
        if path is None:
            is_initialized = ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize()
        else:
            # Note -- uncomment the following line to use a custom initialization path
            is_initialized = ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize(path)

        # determine the ZOS root directory
        if is_initialized:
            zemax_directory = ZOSAPI_NetHelper.ZOSAPI_Initializer.GetZemaxDirectory()
        else:
            raise BaseZOS.InitializationException("Unable to locate Zemax OpticStudio.  Try using a hard-coded path.")

        # add ZOS-API referencecs
        clr.AddReference(os.path.join(os.sep, zemax_directory, "ZOSAPI.dll"))
        clr.AddReference(os.path.join(os.sep, zemax_directory, "ZOSAPI_Interfaces.dll"))
        import ZOSAPI

        # create a reference to the API namespace
        self.zosapi = ZOSAPI

        # Create the initial connection class
        self.the_connection = ZOSAPI.ZOSAPI_Connection()

        if self.the_connection is None:
            raise BaseZOS.ConnectionException("Unable to initialize .NET connection to ZOSAPI")

        self.the_application = self.the_connection.CreateNewApplication()
        if self.the_application is None:
            raise BaseZOS.InitializationException("Unable to acquire ZOSAPI application")

        if not self.the_application.IsValidLicenseForAPI:
            raise BaseZOS.LicenseException("License is not valid for ZOSAPI use")

        self.the_system = self.the_application.PrimarySystem
        if self.the_system is None:
            raise BaseZOS.SystemNotPresentException("Unable to acquire Primary system")

    def __del__(self):
        """
        function to shut down the OpticStudio process
        It cleans up the connection to OpticStudio.

        Returns
        -------
        None
        """
        if self.the_application is not None:
            self.the_application.CloseApplication()
            self.the_application = None

        self.the_connection = None

    def open_file(self, file_path, save_if_needed):
        """
        function to open a file

        Parameters
        ----------
        file_path : str
            String to the zemax zos file
        save_if_needed : boolean
            distinguish if to save already opened file before open a new one

        Returns
        -------


        """
        if self.the_system is None:
            raise BaseZOS.SystemNotPresentException("Unable to acquire Primary system")
        self.the_system.LoadFile(file_path, save_if_needed)

    def close_file(self, save):
        """
        close open file
        Parameters
        ----------
        save : bool
        defines if to save already open file

        Returns
        -------
        None
        """
        if self.the_system is None:
            raise BaseZOS.SystemNotPresentException("Unable to acquire Primary system")
        self.the_system.Close(save)

    def samples_dir(self):
        """
        gets the full path for the current user's samples directory
        by default: in the "My Documents\\Zemax\\Samples\\folder"

        Parameters
        ----------
        None

        Returns
        -------
        The user's samples files directory

        """
        if self.the_application is None:
            raise BaseZOS.InitializationException("Unable to acquire ZOSAPI application")

        return self.the_application.SamplesDir

    def example_constants(self):
        """
        gets the license status type

        Returns
        -------
        the license type
        It can be premium, professional, standard or invalid.

        """
        if self.the_application.LicenseStatus == self.zosapi.LicenseStatusType.PremiumEdition:
            return "Premium"
        elif self.the_application.LicenseStatus == self.zosapi.LicenseStatusTypeProfessionalEdition:
            return "Professional"
        elif self.the_application.LicenseStatus == self.zosapi.LicenseStatusTypeStandardEdition:
            return "Standard"
        else:
            return "Invalid"

    def reshape(self, data, x, y, transpose=False):
        """Converts a System.Double[,] to a 2D list for plotting or post processing

        Parameters
        ----------
        data : System.Double[,] data directly from ZOS-API
        x : x width of new 2D list [use var.GetLength(0) for dimension]
        y : y width of new 2D list [use var.GetLength(1) for dimension]
        transpose : transposes data; needed for some multi-dimensional line series data

        Returns
        -------
        res : 2D list; can be directly used with Matplotlib or converted to
            a numpy array using numpy.asarray(res)
        """
        if type(data) is not list:
            data = list(data)
        var_lst = [y] * x
        it = iter(data)
        res = [list(islice(it, i)) for i in var_lst]
        if transpose:
            return self.transpose(res)
        return res

    def transpose(self, data):
        """Transposes a 2D list (Python3.x or greater).

        Useful for converting mutli-dimensional line series (i.e. FFT PSF)

        Parameters
        ----------
        data : Python native list (if using System.Data[,] object reshape first)

        Returns
        -------
        res : transposed 2D list
        """
        if type(data) is not list:
            data = list(data)
        return list(map(list, zip(*data)))
