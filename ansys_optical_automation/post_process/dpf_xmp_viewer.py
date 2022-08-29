import os

from ansys_optical_automation.post_process.dpf_base import DataProcessingFramework


class XmpViewer(DataProcessingFramework):
    """
    Provides for launching Speos postprocessing software, Virtual reality lab.

    This framework is used to interact with the software and automatically perform
    analysis and postprocessing on the simulation results
    """

    def __init__(self):
        """Initialize DPF as HDRIViewer."""
        DataProcessingFramework.__init__(self, extension=(".xmp"), application="XMPViewer.Application")
        self.source_list = []

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
        if self.dpf_instance.OpenFile(str_path):
            if self.dpf_instance.MapType == 2 or self.dpf_instance.MapType == 3:
                self.get_source_list()
        else:
            raise ImportError("Opening the file failed.")

    def export(self, format="txt", layer=False):
        """
        function to export an XMP map to another format

        Parameters
        ----------
        format : str
            Format to export
        layer : bool
            False-> active configuration is exported
            True-> all layer are exported

        Returns
        -------
        str
            path to exported text file
        """
        self.dpf_instance.MapType
        export_path = self.file_path + "text_export.txt"

        return export_path

    def get_source_list(self):
        """
        Get the source list stored in the simulation result.

        Returns
        -------
        list
            List of sources available in the postprocessing file.
        """
        if self.dpf_instance.MapType == 2 or self.dpf_instance.MapType == 3:
            total_sources = self.dpf_instance.ExtendedGetNbSources
            for layer in range(total_sources):
                self.source_list.append(self.dpf_instance.ExtendedGetSourceName(layer))
            return self.source_list
        else:
            msg = "MapType=" + self.dpf_instance.MapType + " not support."
            raise TypeError(msg)

    def export_template_measures(self, template_path, export_path):
        """
        Function to import measurement tamplate and export measures as text
        Parameters
        ----------
        template_path : str
            path to XML template file
        export_path : str
            path to measurement text export

        Returns
        -------
        None
        """
        if not self.dpf_instance.ImportTemplate(template_path, 1, 1, 1):
            if not self.dpf_instance.MeasuresExportTXT(export_path):
                raise ValueError("Measurement export failed")
            raise ImportError("Template import failed")
