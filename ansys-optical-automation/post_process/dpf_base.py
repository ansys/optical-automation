import os
import sys


class DataProcessingFramework:

    """
    basic data processing framework class
    the class will contain mainly opening and saving functionalities to allow interacting with any result file
    """

    def __init__(self, application=None, extension=""):
        """
        Initializes general properties of the data post-posprocessing framework
        the object

        Parameters
        ----------
        application:  application object started in the framework
        extension: extension used by the application
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
            raise ImportError("Application not defined")

    def open_file(self, str_path):
        """
        open file function allows to open a file based on a path
        Parameters
        ----------
        str_path: a string
            Path for file to open e.g. r"C:\\temp\\Test.speos360"

        Returns
        -------
        None
        """
        if os.path.isfile(str_path):
            if not str_path.lower().endswith(self.accepted_extensions):
                raise TypeError(
                    str_path.lower().split(".")[len(str_path.lower().split(".")) - 1]
                    + " is not an"
                    + "accepted extension"
                )
            if not self.dpf_instance.OpenFile(str_path):
                raise ImportError("File open failed")
        else:
            raise FileNotFoundError("File not found")

    def valid_dir(self, str_path):
        """
        check if a folder is there if not create it

        Parameters
        ----------
        str_path: a string
            Path for folder to validate e.g. r"C:\\temp\"

        Returns
        -------
        None
        """
        if not os.path.isdir(str_path):
            os.makedirs(str_path)
