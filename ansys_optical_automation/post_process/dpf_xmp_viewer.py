import csv
import os
import sys

import numpy
from comtypes import automation
from comtypes import pointer

from ansys_optical_automation.post_process.dpf_base import DataProcessingFramework

supported_map_types = [2, 3]
supported_value_types = [0, 2, 20]
supported_unit_types = [0, 1, 9]


class MapStruct:
    def __init__(self, map_type, value_type, unit_type, axis_unit, size, resolution, wl_res=None, layers=1):
        """
        Initialize the XMP Mapstructure to create and edit XMP data
        Currently only limited data is supported
        Parameters
        ----------
        map_type : int
            2 for spectral, 3 for extended
        value_type : int
            0 for Irradiance, 2 for Radiance, 20 for refractive Power
        unit_type : int
            0 fro Radiometric, 1 for Photometric, 9 for Diopter
        axis_unit : int
            0 = Default, 1 = Millimeter, 2 = Degree, 3 = Radian, 4 = Feet, 5 = Micrometer, 6 = Nanometer,
            7 = Meter, 8 = Percent, 9 = dB, 10 = Invert Millimeter, 11 = No Uni, 12 = Wave
        size : list of floats
            [XMin, XMax, YMin, YMax] map dimensions
        resolution : list of int
            resolution in [x,y]
        wl_res : list of int
            [Wstart, Wend, wNb] wstart and end wavlength and the resolution
        layers : int
            number of layers please not power values need to be defined later
        """
        if map_type not in supported_map_types:
            msg = "Map type (value: " + str(map_type) + ") not supported"
            raise TypeError(msg)
        else:
            self.map_type = map_type
        if value_type not in supported_value_types:
            msg = "Map type (value: " + str(map_type) + ") not supported"
            raise TypeError(msg)
        else:
            self.value_type = value_type
        if unit_type not in supported_unit_types:
            msg = "Map type (value: " + str(map_type) + ") not supported"
            raise TypeError(msg)
        else:
            self.unit_type = unit_type
        if size[1] - size[0] <= 0:
            msg = "xMin (" + str(size[0]) + ") must be smaller then xMax (" + str(size[1]) + ")"
            raise ValueError(msg)
        elif size[3] - size[2] <= 0:
            msg = "yMin (" + str(size[0]) + ") must be smaller then yMax (" + str(size[1]) + ")"
            raise ValueError(msg)
        elif not (int(abs(resolution[0])) > 0 or int(abs(resolution[1])) > 0):
            msg = "resolution must be a positive integer"
            raise ValueError(msg)
        if axis_unit not in range(13):
            msg = "Please provide a valid axis unit"
            raise ValueError(msg)
        else:
            self.axis_unit = axis_unit
        self.xMin = size[0]
        self.xMax = size[1]
        self.xNb = int(abs(resolution[0]))
        self.yMin = size[2]
        self.yMax = size[3]
        self.yNb = int(abs(resolution[1]))
        self.width = size[1] - size[0]
        self.height = size[3] - size[2]
        self.comment = ""
        self.intensity_type = 3  # not supported

        if layers <= 0 or layers != int(layers):
            msg = "Please provide a positive layer integer"
            raise ValueError(msg)
        else:
            self.layers = layers
            self.layer_powers = numpy.ones(self.layers)

        if self.value_type == 2:
            if wl_res is None:
                msg = "Please provide Wavelength start end and resolution values"
                raise ValueError(msg)
            elif wl_res[1] - wl_res[0] <= 0:
                msg = "Please provide a valid wavelength range: \n" + str(wl_res) + "\n is not valid"
                raise ValueError(msg)
            self.wStart = wl_res[0]
            self.wEnd = wl_res[1]
            self.wNb = wl_res[2]
            self.data = numpy.zeros((self.layers, self.xNb, self.yNb, self.wNb))
        else:
            self.data = numpy.zeros((self.layers, self.xNb, self.yNb, 1))

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

    def __export_to_text(self, export_path):
        """
        function to export current map struct to xmp TXT export
        Parameters
        ----------
        export_path : export dir

        Returns
        -------
        None

        """
        self.valid_dir(export_path)
        file_name = os.path.join(export_path, "export_mapstruct.txt")

        with open(file_name, "w") as file_export:
            file_export.writelines(str(self.map_type) + "\n")
            file_export.writelines(str(self.value_type) + "\t" + str(self.intensity_type) + "\n")
            file_export.writelines(str(self.unit_type) + "\n")
            file_export.writelines(str(self.axis_unit) + "\n")
            file_export.writelines(
                str(self.xMin) + "\t" + str(self.xMax) + "\t" + str(self.yMin) + "\t" + str(self.yMax) + "\n"
            )
            file_export.writelines(str(self.xNb) + "\t" + str(self.yNb) + "\n")
            if self.value_type == 2:
                file_export.writelines(str(self.wStart) + "\t" + str(self.wEnd) + "\t" + str(self.wNb) + "\n")
                str_layer = str(self.layers)
                for i in range(self.layers):
                    str_layer += "\t" + str(self.layer_powers[i]) + "\t" + str(self.layer_powers[i])
                    # do we need to do a radiometric conversion for it to work???
            else:
                str_layer = str(self.layers)
                for i in range(self.layers):
                    str_layer += "\t" + str(self.layer_powers[i])
            file_export.writelines(str_layer + "\n")
            if self.value_type == 2:
                for i in range(self.layers):
                    file_export.writelines("layer" + str(i) + "\n")
                    for wl in range(self.wNb):
                        for x in range(self.xNb):
                            for y in range(self.yNb):
                                file_export.writelines(str(self.data[i, x, y, wl]) + "\t")
                            file_export.writelines("\n")
            else:
                for i in range(self.layers):
                    file_export.writelines("layer" + str(i) + "\n")
                    for x in range(self.xNb):
                        for y in range(self.yNb):
                            file_export.writelines(str(self.data[i, x, y, 0]) + "\t")
                        file_export.writelines("\n")
            file_export.close()

    def export_to_xmp(self, export_path=None):
        """
        this function exports the current mapstruct in the define dir as Mapstruct.xmp
        Parameters
        ----------
        export_path :  export dir

        Returns
        -------
        DpfXmpViewer object of the
        """
        xmp = DpfXmpViewer()
        if export_path is None:
            export_path = r"C:\temp"
        file_name = os.path.join(export_path, "export_mapstruct.txt")
        self.__export_to_text(export_path)
        xmp.read_txt_export(file_name)
        os.remove(file_name)
        return xmp


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
