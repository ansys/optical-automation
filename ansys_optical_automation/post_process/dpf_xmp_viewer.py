import csv
import os
import sys

import numpy
from comtypes import automation
from comtypes import pointer

from ansys_optical_automation.post_process.dpf_base import DataProcessingFramework

supported_map_types = [2, 3]
supported_value_types = [0, 1, 2, 20]
supported_unit_types = [0, 1, 9]
axis_unit_types = [
    "default",
    "millimetre",
    "degree",
    "radian",
    "feet",
    "micrometer",
    "nanometer",
    "meter",
    "percent",
    "dB",
    "invert millimeter",
    "no unit",
    "wave",
    "centimeter",
    "inch",
    "milliradian",
    "arc minute",
    "arc second",
]


class MapStruct:
    """Provides a DPF to represent the data stored in an Ansys Speos XMP file"""

    def __init__(
        self,
        map_type,
        value_type,
        intensity_type,
        unit_type,
        axis_unit,
        size,
        resolution,
        layers=1,
        layer_name=None,
        wl_res=None,
    ):
        """
        Initialize the XMP MapStructure to create and edit XMP data.
        Currently only limited data is supported.

        Parameters
        ----------
        map_type : int
            2 for spectral, 3 for extended
        value_type : int
            0 for Irradiance, 1 for Intensity, 2 for Radiance, 20 for refractive Power
        unit_type : int
            0 for Radiometric, 1 for Photometric, 9 for Diopter
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
        layer_name : list
            list of str for the layer name
        """
        if map_type not in supported_map_types:
            msg = "Map type (value: " + str(map_type) + ") not supported"
            raise TypeError(msg)
        else:
            self.map_type = map_type
        if value_type not in supported_value_types:
            msg = "Value type (value: " + str(value_type) + ") not supported"
            raise TypeError(msg)
        else:
            self.value_type = value_type
        if unit_type not in supported_unit_types:
            msg = "Map type (value: " + str(unit_type) + ") not supported"
            raise TypeError(msg)
        else:
            self.unit_type = unit_type

        if len(size) != 4:
            msg = "Please provide correct input required"
            raise ValueError(msg)
        elif size[1] - size[0] <= 0:
            msg = "xMin (" + str(size[0]) + ") must be smaller then xMax (" + str(size[1]) + ")"
            raise ValueError(msg)
        elif size[3] - size[2] <= 0:
            msg = "yMin (" + str(size[0]) + ") must be smaller then yMax (" + str(size[1]) + ")"
            raise ValueError(msg)

        if not all(item > 0 for item in resolution):
            msg = "resolution must be a positive integer"
            raise ValueError(msg)

        if axis_unit not in range(13):
            msg = "Please provide a valid axis unit (value: " + str(axis_unit)
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
        self.wl_res = wl_res
        self.comment = ""
        self.intensity_type = intensity_type

        if layers <= 0 or layers != int(layers):
            msg = "Please provide a positive layer integer"
            raise ValueError(msg)
        else:
            print(
                "Warning power values for layers are set to 1 and need to be manually"
                "adjusted before export only 1 unit type is supported both will have the same value"
            )
            self.layers = layers
            self.layer_powers = numpy.ones(self.layers)
            if type(layer_name) is list:
                if len(layer_name) < self.layers:
                    self.layer_name = range(self.layers)
                    print("layername list to short is overwritten")
                else:
                    self.layer_name = layer_name
            else:
                self.layer_name = range(self.layers)
                print("Layernames not provided were overwritten")

        if self.map_type == 3:
            if wl_res is None:
                self.data = numpy.zeros((self.layers, self.xNb, self.yNb, 1))
            elif len(wl_res) != 3 or wl_res[1] - wl_res[0] <= 0:
                msg = "Please provide a valid wavelength range: \n" + str(wl_res) + "\n is not valid"
                raise ValueError(msg)
            else:
                self.wStart = wl_res[0]
                self.wEnd = wl_res[1]
                self.wNb = abs(int(wl_res[2]))
                self.data = numpy.zeros((self.layers, self.xNb, self.yNb, self.wNb))
        elif map_type == 2:
            if wl_res is None:
                self.data = numpy.zeros((self.layers, self.xNb, self.yNb, 4))
            elif len(wl_res) != 3 or wl_res[1] - wl_res[0] <= 0:
                msg = "Please provide a valid wavelength range: \n" + str(wl_res) + "\n is not valid"
                raise ValueError(msg)
            else:
                self.wStart = wl_res[0]
                self.wEnd = wl_res[1]
                self.wNb = abs(int(wl_res[2]))
                self.data = numpy.zeros((self.layers, self.xNb, self.yNb, self.wNb))
        self.export_name = "export_mapstruct"

    def valid_dir(self, str_path):
        """
        Check if a folder is present and, if not, create it.

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
        function to export current map struct to xmp TXT export.

        Parameters
        ----------
        export_path : export dir

        Returns
        -------
        None

        """
        self.valid_dir(export_path)
        file_name = os.path.join(export_path, self.export_name + ".txt")

        file_export = open(file_name, "w")
        file_export.writelines(str(self.map_type) + "\n")
        file_export.writelines(str(self.value_type) + "\t" + str(self.intensity_type) + "\n")
        file_export.writelines(str(self.unit_type) + "\n")
        file_export.writelines(str(self.axis_unit) + "\n")
        file_export.writelines(
            str(self.xMin) + "\t" + str(self.xMax) + "\t" + str(self.yMin) + "\t" + str(self.yMax) + "\n"
        )
        file_export.writelines(str(self.xNb) + "\t" + str(self.yNb) + "\n")

        if self.map_type == 2 and self.wl_res is not None:
            file_export.writelines(str(self.wStart) + "\t" + str(self.wEnd) + "\t" + str(self.wNb) + "\n")
            str_layer = "SeparatedByLayer" + "\t" + str(self.layers)
            for i in range(self.layers):
                str_layer += "\t" + str(self.layer_powers[i]) + "\t" + str(self.layer_powers[i])
            file_export.writelines(str_layer + "\n")
        elif self.map_type == 2 and self.wl_res is None:
            str_layer = "-1" + "\t" + "SeparatedByLayer" + "\t" + str(self.layers)
            for i in range(self.layers):
                str_layer += "\t" + str(self.layer_powers[i])
            file_export.writelines(str_layer + "\n")
        elif self.map_type == 3 and self.wl_res is not None:
            file_export.writelines(str(self.wStart) + "\t" + str(self.wEnd) + "\t" + str(self.wNb) + "\n")
            str_layer = str(self.layers)
            for i in range(self.layers):
                str_layer += "\t" + str(self.layer_powers[i]) + "\t" + str(self.layer_powers[i])
        elif self.map_type == 3 and self.wl_res is None:
            str_layer = str(self.layers)
            for i in range(self.layers):
                str_layer += "\t" + str(self.layer_powers[i])
            file_export.writelines(str_layer + "\n")

        if self.map_type == 2 and self.wl_res is not None:
            for i in range(self.layers):
                if type(self.layer_name[i]) == str:
                    file_export.writelines(self.layer_name[i] + "\n")
                else:
                    file_export.writelines("layer" + str(i) + "\n")
                for wl in range(self.wNb):
                    if wl != 0:
                        file_export.writelines("\n")
                    for y in range(self.yNb):
                        for x in range(self.xNb):
                            file_export.writelines(str(self.data[i, x, y, wl]) + "\t")
                        file_export.writelines("\n")
        elif self.map_type == 2 and self.wl_res is None:
            str_layer = ""
            for i in range(self.layers):
                str_layer += str(self.layer_powers[i]) + "\t"
            file_export.writelines(str_layer + "\n")
            for i in range(self.layers):
                if type(self.layer_name[i]) == str:
                    file_export.writelines(self.layer_name[i] + "\n")
                else:
                    file_export.writelines("layer" + str(i) + "\n")
                for y in range(self.yNb):
                    for x in range(self.xNb):
                        file_export.writelines(
                            str(self.data[i, x, y, 0])
                            + "\t"
                            + str(self.data[i, x, y, 1])
                            + "\t"
                            + str(self.data[i, x, y, 2])
                            + "\t"
                            + str(self.data[i, x, y, 3])
                            + "\t"
                        )
                    file_export.writelines("\n")
        elif self.map_type == 3 and self.wl_res is not None:
            for i in range(self.layers):
                if type(self.layer_name[i]) == str:
                    file_export.writelines(self.layer_name[i] + "\n")
                else:
                    file_export.writelines("layer" + str(i) + "\n")
                for wl in range(self.wNb):
                    if wl != 0:
                        file_export.writelines("\n")
                    for y in range(self.yNb):
                        for x in range(self.xNb):
                            file_export.writelines(str(self.data[i, x, y, wl]) + "\t")
                        file_export.writelines("\n")
        elif self.map_type == 3 and self.wl_res is None:
            for i in range(self.layers):
                if type(self.layer_name[i]) == str:
                    file_export.writelines(self.layer_name[i] + "\n")
                else:
                    file_export.writelines("layer" + str(i) + "\n")
                for y in range(self.yNb):
                    for x in range(self.xNb):
                        file_export.writelines(str(self.data[i, x, y, 0]) + "\t")
                    file_export.writelines("\n")
        file_export.close()

    def export_to_xmp(self, export_path=r"C:\temp"):
        """
        this function exports the current mapstruct in the dir defined as Mapstruct.xmp.
        Parameters
        ----------
        export_path: str
            path to be exported. Default at C:\temp

        Returns
        -------
        DpfXmpViewer object
        """
        xmp = DpfXmpViewer()
        txt_file = os.path.join(export_path, self.export_name + ".txt")
        xmp_file = os.path.join(export_path, self.export_name + ".xmp")
        self.__export_to_text(export_path)
        xmp.read_txt_export(txt_file)
        os.remove(txt_file)
        xmp.dpf_instance.SaveFile(xmp_file)
        return xmp


class DpfXmpViewer(DataProcessingFramework):
    """
    Provides for launching Speos postprocessing software, XMP Viewer.

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
                self.__get_source_list()
        else:
            raise ImportError("Opening the file failed.")

    def export(self, format="txt"):
        """
        function to export an XMP map to another format

        Parameters
        ----------
        format : str
            export format allowed values
            ["txt", "png", "bmp", "jpg", "tiff", "pf", "ies", "ldt", "extended.txt"]
        """
        allowed_exports = ["txt", "png", "bmp", "jpg", "tiff", "pf", "ies", "ldt", "extended.txt"]
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
            elif format in ["ies", "ldt"]:
                if not self.dpf_instance.ExportXMPtoIntensity(export_path):
                    msg = format + " export failed"
                    raise Exception(msg)
            elif format in ["png", "bmp", "jpg", "tiff"]:
                if not self.dpf_instance.ExportXMPImage(export_path):
                    msg = format + " export failed"
                    raise Exception(msg)
            if format == "extended.txt":
                if not self.dpf_instance.ExtendedExportTXT(export_path, 1):
                    msg = format + " export failed"
                    raise Exception(msg)
        else:
            msg = "cannot export data to: " + format
            raise ValueError(msg)

        return export_path

    def __read_txt_export(self, xmp_map_struct, txt_path):
        """
        function to load txt content into a XmpStruct.

        Parameters
        ----------
        xmp_map_struct : MapStruct
            class of MapStruct
        txt_path : str
            text file directory

        Returns
        -------
        MapStruct:
            a MapStruct whose values are filled with content from text file provided.

        """
        with open(txt_path, "r") as file:
            my_data = csv.reader(file, delimiter="\t")
            if self.dpf_instance.Maptype == 2 and xmp_map_struct.wl_res is not None:
                for i in range(8):
                    line = next(my_data)
                    if i == 6:
                        if line[0] == "-1" and len(line) == 1:
                            next(my_data)
                for layer_idx in range(xmp_map_struct.layers):
                    next(my_data)
                    for wavelength_idx in range(xmp_map_struct.wl_res[2]):
                        if wavelength_idx != 0:
                            next(my_data)
                        for xmp_value_idy in range(xmp_map_struct.yNb):
                            line = next(my_data)
                            for xmp_value_idx, xmp_value in enumerate(line):
                                if xmp_value != "":
                                    xmp_map_struct.data[
                                        layer_idx, xmp_value_idx, xmp_value_idy, wavelength_idx
                                    ] = xmp_value
            elif self.dpf_instance.Maptype == 3 and xmp_map_struct.wl_res is not None:
                for i in range(8):
                    line = next(my_data)
                    if i == 6:
                        if line[0] == "-1" and len(line) == 1:
                            next(my_data)
                for layer_idx in range(xmp_map_struct.layers):
                    next(my_data)
                    for wavelength_idx in range(xmp_map_struct.wl_res[2]):
                        if wavelength_idx != 0:
                            next(my_data)
                        for xmp_value_idy in range(xmp_map_struct.yNb):
                            line = next(my_data)
                            for xmp_value_idx, xmp_value in enumerate(line):
                                if xmp_value != "":
                                    xmp_map_struct.data[
                                        layer_idx, xmp_value_idx, xmp_value_idy, wavelength_idx
                                    ] = xmp_value
            elif self.dpf_instance.Maptype == 3 and xmp_map_struct.wl_res is None:
                for i in range(7):
                    line = next(my_data)
                    if i == 6:
                        if line[0] == "-1" and len(line) == 1:
                            next(my_data)
                for layer_idx in range(xmp_map_struct.layers):
                    line = next(my_data)
                    for xmp_value_idy in range(xmp_map_struct.yNb):
                        line = next(my_data)
                        for xmp_value_idx, xmp_value in enumerate(line):
                            if xmp_value != "":
                                xmp_map_struct.data[layer_idx, xmp_value_idx, xmp_value_idy, 0] = xmp_value
            elif self.dpf_instance.Maptype == 2 and xmp_map_struct.wl_res is None:
                for i in range(7):
                    line = next(my_data)
                    if i == 6:
                        if line[0] == "-1" and len(line) == 1:
                            next(my_data)
                for layer_idx in range(xmp_map_struct.layers):
                    line = next(my_data)
                    for xmp_value_idy in range(xmp_map_struct.yNb):
                        line = next(my_data)
                        for xmp_value_idx, xmp_value in enumerate(line):
                            if xmp_value != "":
                                xmp_map_struct.data[
                                    layer_idx, int(xmp_value_idx / 4), xmp_value_idy, xmp_value_idx % 4
                                ] = xmp_value
            else:
                msg = "Currently not supported"
                raise ImportError(msg)
        return xmp_map_struct

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
        MapStruct:
            MapStruct created according to the text file.

        """
        import_response = self.dpf_instance.ImportTXT(txt_path)
        self.source_list = []
        self.__get_source_list()
        if not import_response:
            msg = "Provided text file cannot be imported, Please check your text file content"
            raise ImportError(msg)
        if inc_data:
            variant = automation.VARIANT(5)
            xmp_maptype = self.dpf_instance.Maptype
            xmp_value_type = self.dpf_instance.ValueType
            xmp_intensity_type = self.dpf_instance.GetIntensityType
            xmp_unit_type = self.dpf_instance.UnitType
            xmp_axis_unit = axis_unit_types.index(self.dpf_instance.GetAxisUnitName)
            xmp_size = [self.dpf_instance.XMin, self.dpf_instance.XMax, self.dpf_instance.YMin, self.dpf_instance.YMax]
            xmp_resolution = [self.dpf_instance.XNb, self.dpf_instance.YNb]
            xmp_layer = len(self.source_list)
            if xmp_maptype in supported_map_types:
                if self.dpf_instance.GetSampleCRI(0, 0, 2, pointer(variant)):
                    # this is a spectral map
                    xmp_wl_res = [self.dpf_instance.WMin, self.dpf_instance.WMax, self.dpf_instance.WNb]
                    xmp_map_struct = MapStruct(
                        xmp_maptype,
                        xmp_value_type,
                        xmp_intensity_type,
                        xmp_unit_type,
                        xmp_axis_unit,
                        xmp_size,
                        xmp_resolution,
                        xmp_layer,
                        self.source_list,
                        xmp_wl_res,
                    )
                    return self.__read_txt_export(xmp_map_struct, txt_path)
                else:
                    xmp_map_struct = MapStruct(
                        xmp_maptype,
                        xmp_value_type,
                        xmp_intensity_type,
                        xmp_unit_type,
                        xmp_axis_unit,
                        xmp_size,
                        xmp_resolution,
                        xmp_layer,
                        layer_name=self.source_list,
                    )
                    return self.__read_txt_export(xmp_map_struct, txt_path)
            else:
                msg = "type of map are not supported currently"
                raise ImportError(msg)

    def __get_source_list(self):
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
                self.source_list = []
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
