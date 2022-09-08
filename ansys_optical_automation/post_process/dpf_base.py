import os
import sys


class DataProcessingFramework:
    """Provides DPF (Data Processing Framework).

    The class contains opening and saving functionalities to allow interacting with any results file.

    """

    application_list = ["HDRIViewer.Application", "XMPViewer.Application"]
    binary_format = {".ray", ".dat", ".sdf"}
    text_format = {".spectrum", ".spcd"}

    def __init__(self, extension, application=None):
        """Initialize general properties of DPF.

        Parameters
        ----------
        application : str
            Application object started in DPF. The default is ``None``.
        extension : tuple
            Extensions accepted by the application object.
        """
        self.file_path = None
        self.application = application
        self.accepted_extensions = extension
        if self.application is not None:
            if self.application in self.application_list:
                if "Iron" in sys.version:
                    instance_type = System.Type.GetTypeFromProgID(self.application)
                    self.dpf_instance = System.Activator.CreateInstance(instance_type)
                else:
                    import win32com.client as win32

                    self.dpf_instance = win32.Dispatch(self.application)
            else:
                raise ImportError("Application is not supported.")

    def open_file(self, str_path):
        """Open a file in DPF.

        Parameters
        ----------
        str_path : str
            Path for the file to open. For example, ``r"C:\\temp\\Test.speos360"``.

        Returns
        -------
        None

        """
        if not os.path.isfile(str_path):  # check if file is existing.
            raise FileNotFoundError("File is not found.")

        if not str_path.lower().endswith(tuple(self.accepted_extensions)):
            # check if accept extensions
            raise TypeError(
                str_path.lower().split(".")[len(str_path.lower().split(".")) - 1] + " is not an" + "accepted extension"
            )

        self.file_path = str_path
        if self.application is None:  # no application is required to open file, e.g. rayfile
            if str_path.lower().endswith(tuple(self.binary_format)):
                self.dpf_instance = open(str_path, "br")
            else:
                self.dpf_instance = open(str_path, "r")
        else:
            if not self.dpf_instance.OpenFile(str_path):
                raise ImportError("Opening the file failed.")

    def valid_dir(self, str_path):
        """Check if a folder is present and, if not, create it.

        Parameters
        ----------
        str_path : str
            Path for the folder to validate or create. For example, ``r"C:\\temp\"``.

        Returns
        -------
        None

        """
        if not os.path.isdir(str_path):
            os.makedirs(str_path)

    def close(self):
        """Function to close open files and applications

        Returns
        -------
        None

        """
        if self.application is None:  # no application is required to open file, e.g. rayfile
            self.dpf_instance.close()
        else:
            pid = self.dpf_instance.GetPID
            cmd = "taskkill /PID " + str(pid) + " /F"
            os.system(cmd)
