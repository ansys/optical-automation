import os

import ansys_optical_automation.post_process.dpf_base as dpf


class DpfFileBase(dpf.DataProcessingFramework):
    """
    this base class contains the base method for loading and generating export file optical property files
    """

    binary_format = {"ray": "sdf", "dat": "ray", "sdf": "ray"}
    text_format = {"spectrum": "spcd", "spcd": "spectrum"}

    def __init__(self, extension):
        ext_list = []
        for ext in list(self.binary_format.keys()):
            ext_list.append("." + ext)

        for ext in list(self.text_format.keys()):
            ext_list.append("." + ext)

        dpf.DataProcessingFramework.__init__(self, application="dpf", extension=tuple(ext_list))

        if extension.split(".")[0] == extension:
            self.extension = extension
        else:
            self.extension = extension.split(".")[1]

        if self.extension not in self.binary_format and self.extension not in self.text_format:
            msg = "Provided file has not been supported"
            raise TypeError(msg)

    def load(self, file_path):
        """
        this method load the provided file with corresponding method
        Parameters
        ----------
        file_path : str
            file path

        Returns
        -------
        open file object
        """
        if not os.path.isfile(file_path):
            msg = "Provided file cannot be found"
            raise ValueError(msg)

        if self.extension in self.binary_format:
            return open(file_path, "br")
        else:
            return open(file_path, "r")

    def export_file(self, file_path, convert=False):
        """
        this method generates a file to be exported
        Parameters
        ----------

        file_path: str
            input file
        convert : Boolean , optional
            defines if the export is a conversion, default value is False
        Returns
        -------
        outfile: str
            output file

        """
        exported_file_extension = ""

        input_file_name = os.path.splitext(file_path)[0]
        input_file_extension = os.path.splitext(file_path)[1].lower()[1:]

        if convert:
            if input_file_extension in self.binary_format:
                exported_file_extension = self.binary_format[input_file_extension]
            elif input_file_extension in self.text_format:
                exported_file_extension = self.text_format[input_file_extension]
            else:
                exported_file_extension = input_file_extension
                msg = "Provided file extension" + exported_file_extension + "is not supported"
                raise TypeError(msg)
        else:
            if input_file_extension in self.binary_format or input_file_extension in self.text_format:
                exported_file_extension = input_file_extension
            else:
                exported_file_extension = input_file_extension
                msg = "Provided file extension" + exported_file_extension + "is not supported"
                raise TypeError(msg)
            outfile = input_file_name + "." + exported_file_extension
        outfile_num = 1
        while os.path.isfile(outfile):
            outfile = input_file_name + "_" + str(outfile_num) + "." + exported_file_extension
            outfile_num += 1
        return outfile
