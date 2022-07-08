import os
import sys


class DataProcessingFramework:
    """Provides the basic data processing framework.

    The class contains mainly opening and saving functionalities to allow interacting with any result file.

    """

    def __init__(self, application=None, extension=""):
        """Initialize general properties of the data postprocessing framework.

        Parameters
        ----------
        application : str, optional
            Application object started in the framework. The default is ``None``.
        extension : tuple, optional
            Extensions accepted by the application object. The default is ``""``.
        """
        self.application = application
        self.accepted_extensions = extension
        if self.application is not None:
            if "Iron" in sys.version:
                instance_type = System.Type.GetTypeFromProgID(self.application)
                self.dpf_instance = System.Activator.CreateInstance(instance_type)
            else:
                import win32com.client as win32

                self.dpf_instance = win32.Dispatch(self.application)
        else:
            raise ImportError("Application is not defined.")

    def open_file(self, str_path):
        """Opens a file in DPF based on a path.

        Parameters
        ----------
        str_path : str
            Path for the file to open. For example, ``r"C:\\temp\\Test.speos360"``.
        """
        if os.path.isfile(str_path):
            if not str_path.lower().endswith(self.accepted_extensions):
                raise TypeError(
                    str_path.lower().split(".")[len(str_path.lower().split(".")) - 1]
                    + " is not an"
                    + "accepted extension"
                )
            if not self.dpf_instance.OpenFile(str_path):
                raise ImportError("File could not be opened.")
        else:
            raise FileNotFoundError("File is not found.")

    def valid_dir(self, str_path):
        """Check if a folder is present and, if not, create it.

        Parameters
        ----------
        str_path : str
            Path for the folder to validate. For example, ``r"C:\\temp\"``.
        """
        if not os.path.isdir(str_path):
            os.makedirs(str_path)
