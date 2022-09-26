import csv
import os
import sys

from comtypes import automation
from comtypes import pointer

from ansys_optical_automation.post_process.dpf_base import DataProcessingFramework


class DpfXmpViewer(DataProcessingFramework):
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
            self.source_list = []
            if self.dpf_instance.MapType == 2 or self.dpf_instance.MapType == 3:
                self.get_source_list()
        else:
            raise ImportError("Opening the file failed.")

    def export(self, format="txt"):
        """
        function to export an XMP map to another format

        Parameters
        ----------
        format : str
            export format allowed values
            ["txt", "png", "bmp", "jpg", "tiff", "pf", "ies", "ldt"]
        """
        allowed_exports = ["txt", "png", "bmp", "jpg", "tiff", "pf", "ies", "ldt"]
        if format in allowed_exports:
            export_path = self.file_path + "export." + format
            if format == "txt":
                if not self.dpf_instance.ExportTXT(export_path):
                    msg = format + " export failed"
                    raise Exception(msg)
            elif format == "pf":
                if not self.dpf_instance.ExportPF(export_path):
                    msg = format + " export failed"
                    raise Exception(msg)
            elif format == "pf":
                if not self.dpf_instance.ExportPF(export_path):
                    msg = format + " export failed"
                    raise Exception(msg)
            elif format in ["ies", "ldt"]:
                if not self.dpf_instance.ExportXMPtoIntensity(export_path):
                    msg = format + " export failed"
                    raise Exception(msg)
            elif format in ["png", "bmp", "jpg", "tiff"]:
                if not self.dpf_instance.ExportXMPImage(export_path):
                    msg = format + " export failed"
                    raise Exception(msg)
        else:
            msg = "cannot export data to: " + format
            raise ValueError(msg)

        return export_path

    def read_txt_export(self, txt_path, inc_data=False):
        """
        Parameters
        ----------
        txt_path : str
            string pointing to the textfile
        inc_data : bool
            Boolean to determine if to include data matrix as list
            currently not working correctly

        Returns
        -------
        for inc_data True: data matrix[wavelength[layer[x[y]]]]
        """
        if not inc_data:
            self.dpf_instance.ImportTXT(txt_path)
        else:
            self.dpf_instance.ImportTXT(txt_path)
            variant = automation.VARIANT(5)
            if self.dpf_instance.Maptype == 2 and self.dpf_instance.GetSampleCRI(0, 0, 2, pointer(variant)):
                "account for spectral maps"
                matrix = []
                with open(txt_path, "r") as file:
                    my_data = csv.reader(file, delimiter="\t")
                    for i in range(9):
                        next(my_data)
                    for w in range(self.dpf_instance.WNb - 1):
                        matrix.append([])
                        for k in range(int(self.dpf_instance.YHeight / self.dpf_instance.YSampleHeight)):
                            line = next(my_data)
                            matrix[w].append(line)
                            # print(line)
                return matrix
            elif self.dpf_instance.Maptype == 3:
                matrix = []
                with open(txt_path, "r") as file:
                    my_data = csv.reader(file, delimiter="\t")
                    for i in range(8):
                        next(my_data)
                    for k in range(int(self.dpf_instance.YHeight / self.dpf_instance.YSampleHeight)):
                        line = next(my_data)
                        matrix.append(line)
                return matrix
            elif self.dpf_instance.Maptype == 2 and not self.dpf_instance.GetSampleCRI(0, 0, 2, pointer(variant)):
                matrix = []
                with open(txt_path, "r") as file:
                    my_data = csv.reader(file, delimiter="\t")
                    for i in range(9):
                        next(my_data)
                    for k in range(int(self.dpf_instance.YHeight / self.dpf_instance.YSampleHeight)):
                        line = next(my_data)
                        matrix.append(line)
                return matrix
            else:
                return False

    def get_source_list(self):
        """
        Get the source list stored in the simulation result.

        Returns
        -------
        list
            List of sources available in the postprocessing file.
        """
        if "Iron" in sys.version:
            raise Exception("IronPython not supported")
        else:
            if self.dpf_instance.MapType == 2 or self.dpf_instance.MapType == 3:
                total_sources = self.dpf_instance.ExtendedGetNbSource
                for layer in range(total_sources):
                    name = automation.VARIANT()
                    self.dpf_instance.ExtendedGetSourceName(layer, pointer(name))
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
            raise ImportError("Template import failed")
        else:
            if not self.dpf_instance.MeasuresExportTXT(export_path):
                raise ValueError("Measurement export failed")

    def rect_export_spectrum(self, x_pos, y_pos, width, height):
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