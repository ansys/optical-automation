import os

import comtypes

from ansys_optical_automation.post_process.dpf_base import DataProcessingFramework


class XmpViewer(DataProcessingFramework):
    """
    Provides for launching Speos postprocessing software, Virtual reality lab.

    This framework is used to interact with the software and automatically perform
    analysis and postprocessing on the simulation results
    """

    def __init__(self):
        """Initialize DPF as HDRIViewer."""
        DataProcessingFramework.__init__(self, extension=".xmp", application="XMPViewer.Application")
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
            print(self.dpf_instance.MapType)
            total_sources = self.dpf_instance.ExtendedGetNbSource
            for layer in range(total_sources):
                name = comtypes.automation.VARIANT()
                self.dpf_instance.ExtendedGetSourceName(layer, comtypes.pointer(name))
                self.source_list.append(name.value[0])
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

    def rect_export_spectrum(self, x_pos, y_pos, width, height, normalize=True):
        """
        Parameters
        ----------
        x_pos : float
            x position of rectangle
        y_pos : float
            y position of rectangle
        width : float
            width or rectangle
        height : float
            height of rectangle

        Returns
        -------
        return list of wavelength and list of energy values
        """
        if self.dpf_instance.MapType == 2:
            w_nb = self.dpf_instance.SpectralGetNbWavelength
            w_min = self.dpf_instance.WMin
            w_max = self.dpf_instance.WMax
            wavelength = []
            energy = []
            signal = [wavelength, energy]
            for i, WL in enumerate(range(int(w_min), int(w_max), int((w_max - w_min) / (w_nb - 1)))):
                signal[0].append(WL)
                self.dpf_instance.SpectralSetActiveWavelength(i)
                signal[1].append(self.dpf_instance.SurfaceRectangleCalculation(x_pos, y_pos, width, height)[6])
            return signal
        else:
            msg = "NonSupportedMap"
            raise Exception(msg)
