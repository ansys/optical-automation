import math
import os
import struct

from ansys_optical_automation.post_process.dpf_base import DataProcessingFramework

Photopic_Conversion_wavelength = [
    380,
    390,
    400,
    410,
    420,
    430,
    440,
    450,
    460,
    470,
    480,
    490,
    500,
    507,
    510,
    520,
    530,
    540,
    550,
    555,
    560,
    570,
    580,
    590,
    600,
    610,
    620,
    630,
    640,
    650,
    660,
    670,
    680,
    690,
    700,
    710,
    720,
    730,
    740,
    750,
    760,
    770,
]
Photopic_Conversion_value = [
    0.027,
    0.082,
    0.27,
    0.826,
    2.732,
    7.923,
    15.709,
    25.954,
    40.98,
    62.139,
    94.951,
    142.078,
    220.609,
    303.464,
    303.464,
    484.93,
    588.746,
    651.582,
    679.551,
    683,
    679.585,
    650.216,
    594.21,
    517.031,
    430.973,
    343.549,
    260.223,
    180.995,
    119.525,
    73.081,
    41.663,
    21.856,
    11.611,
    5.607,
    2.802,
    1.428,
    0.715,
    0.355,
    0.17,
    0.082,
    0.041,
    0.02,
]


class DpfRay:
    """
    this class defines the ray property
    """

    def __init__(self, x, y, z, l_dir, m_dir, n_dir, wavelength, e):
        self.__cardinal_coordinate_x = x
        self.__cardinal_coordinate_y = y
        self.__cardinal_coordinate_Z = z
        self.__vector_radiation_l = l_dir
        self.__vector_radiation_m = m_dir
        self.__vector_radiation_n = n_dir
        self.__ray_wavelength = wavelength
        self.__ray_energy = e

    @property
    def coordinate_x(self) -> float:
        """
        return ray cardinal_coordinate_x
        Returns:
            cardinal_coordinate_x
        -------

        """
        return self.__cardinal_coordinate_x

    @property
    def coordinate_y(self) -> float:
        """
        return ray cardinal_coordinate_y
        Returns:
            cardinal_coordinate_y
        -------

        """
        return self.__cardinal_coordinate_y

    @property
    def coordinate_z(self) -> float:
        """
        return ray cardinal_coordinate_z
        Returns:
            cardinal_coordinate_z
        -------

        """
        return self.__cardinal_coordinate_Z

    @property
    def radiation_l(self) -> float:
        """
        return ray vector_radiation_l
        Returns:
            vector_radiation_l
        -------

        """
        return self.__vector_radiation_l

    @property
    def radiation_m(self) -> float:
        """
        return ray vector_radiation_m
        Returns:
            vector_radiation_m
        -------

        """
        return self.__vector_radiation_m

    @property
    def radiation_n(self) -> float:
        """
        return ray vector_radiation_n
        Returns:
            vector_radiation_n
        -------

        """
        return self.__vector_radiation_n

    @property
    def wavelength(self) -> float:
        """
        return ray wavelength
        Returns:
            wavelength
        -------

        """
        return self.__ray_wavelength

    @property
    def energy(self) -> float:
        """
        return ray energy
        Returns:
            energy
        -------

        """
        return self.__ray_energy


class DpfRayfile(DataProcessingFramework):
    """
    this class contains method to read extract ray data from given binary rayfile
    """

    conversion_extension = {".ray": ".sdf", ".dat": ".ray", ".sdf": ".ray"}

    def __init__(self, file_path):
        DataProcessingFramework.__init__(self, extension=list(self.conversion_extension.keys()))
        self.__ray_numb = 0
        self.__watt_value = 0
        self.__lumen_value = 0
        self.__rays = []
        self.identifier = 0
        self.description = "description"
        self.source_flux = 0
        if file_path is not None:
            self.open_file(file_path)
            self.__binary = self.__is_binary()
            self.load_content()

    def __is_binary(self):
        """this method checks if a file is binary

        Returns
        -------
        Boolean
        """
        with open(self.file_path, "rb") as f:
            for block in f:
                if b"\0" in block:
                    f.close()
                    return True
            f.close()
        return False

    def __photopic_conversion(self, wavelength):
        """This method computes photopic to Radiometric conversion factor at the given wavelength

        Parameters
        ----------
        wavelength : int
            wavelength in nm
        """
        start = 0
        end = len(Photopic_Conversion_wavelength)
        pos = 0
        while start < end:
            mid = (start + end) // 2
            # print(mid, Photopic_Conversion_wavelength[mid])
            if Photopic_Conversion_wavelength[mid] == wavelength:
                pos = mid
                break
            if Photopic_Conversion_wavelength[mid] > wavelength:
                end = mid
            else:
                start = mid + 1
        pos = pos if pos != 0 else start

        start_wave = Photopic_Conversion_wavelength[pos]
        end_wave = Photopic_Conversion_wavelength[pos + 1]
        start_photopic = Photopic_Conversion_value[pos]
        end_photopic = Photopic_Conversion_value[pos + 1]
        return ((wavelength - start_wave) / (end_wave - start_wave)) * (end_photopic - start_photopic) + start_photopic

    def set_ray_count(self, raynumber):
        """
        redfine raynumber
        Parameters
        ----------
        raynumber : int

        Returns
        -------


        """
        self.__ray_numb = raynumber

    def load_content(self):
        """
        this method load the information from rayfile provided

        Returns
        -------


        """
        rayfile_type = self.file_path.split(".")[-1]
        if rayfile_type == "ray":
            content_size = os.fstat(self.dpf_instance.fileno()).st_size - 28
            if content_size % 32 != 0:
                msg = "Provided rayfile is not generated from speos"
                raise ValueError(msg)
            self.__ray_numb = int(content_size / 32)

            self.__watt_value = struct.unpack("f", self.dpf_instance.read(4))[0]
            self.dpf_instance.read(4 * 5)
            self.__lumen_value = struct.unpack("f", self.dpf_instance.read(4))[0]
            for ray_idx in range(self.__ray_numb):
                x = struct.unpack("f", self.dpf_instance.read(4))[0]
                y = struct.unpack("f", self.dpf_instance.read(4))[0]
                z = struct.unpack("f", self.dpf_instance.read(4))[0]
                l_dir = struct.unpack("f", self.dpf_instance.read(4))[0]
                m_dir = struct.unpack("f", self.dpf_instance.read(4))[0]
                n_dir = struct.unpack("f", self.dpf_instance.read(4))[0]
                wav = round(struct.unpack("f", self.dpf_instance.read(4))[0] * 0.001, 3)
                e = struct.unpack("f", self.dpf_instance.read(4))[0]
                if wav <= 0:
                    msg = "Error: ray wavelength of ray of " + str(ray_idx) + "cannot be <= 0"
                    raise ValueError(msg)
                raylen = math.sqrt(l_dir * l_dir + m_dir * m_dir + n_dir * n_dir)
                if abs(raylen - 1) > 1e-3:
                    msg = "Error: Vector length of " + str(ray_idx) + "the ray is unusual (" + str(raylen) + ")"
                    raise ValueError(msg)
                if e < 0:
                    msg = "Error: ray power of " + str(m_dir) + "th ray is < 0"
                    raise ValueError(msg)
                elif e == 0:
                    print('The ' + str(ray_idx) + ' th ray has 0 flux! \n Ray was removed from data')
                    self.__ray_numb -= 1
                else:
                    self.__rays.append(DpfRay(x, y, z, l_dir, m_dir, n_dir, wav, e))
            self.dpf_instance.close()
        elif (rayfile_type == "dat" or rayfile_type == "sdf") and self.__binary:
            self.identifier = int.from_bytes(
                self.dpf_instance.read(4), byteorder="little"
            )  # Format version ID, current value is 1010
            self.__ray_numb = int.from_bytes(
                self.dpf_instance.read(4), byteorder="little"
            )  # The number of rays in the file
            self.description = self.dpf_instance.read(100).decode()  # A text description of the source
            self.source_flux = struct.unpack("f", self.dpf_instance.read(4))[
                0
            ]  # The total flux in watts of this source
            ray_set_flux = struct.unpack("f", self.dpf_instance.read(4))[
                0
            ]  # The flux in watts represented by this Ray Set
            wavelength = round(struct.unpack("f", self.dpf_instance.read(4))[0], 3)
            # The wavelength in micrometers,
            # 0 if a composite,converted to nanometer since this is the speos' source file format.
            self.dpf_instance.read(18 * 4)  # Unused data
            ray_format_type = int.from_bytes(self.dpf_instance.read(4), byteorder="little")
            # The ray_format_type must be either 0 for flux only format(.dat), or 2 for the spectral color format(.sdf).
            flux_type = int.from_bytes(
                self.dpf_instance.read(4), byteorder="little"
            )  # If and only if the ray_format_type is 0, then the flux_type is 0 for watts, and 1 for lumens.
            # For the spectral color format(.sdf), the flux must be in watts, and the wavelength in micrometers.
            self.dpf_instance.read(4 * 2)  # Unused data
            content_size = os.fstat(self.dpf_instance.fileno()).st_size - self.dpf_instance.tell()
            if ray_format_type == 0:
                if content_size % (7 * 4) != 0 or content_size // (7 * 4) != self.__ray_numb:
                    msg = "Warning: Zemax file may be wrong format. File size does not match ray numbers said in header"
                    raise ValueError(msg)
                wavelength = wavelength if wavelength != 0 else 0.550
                photopic_conversion = self.__photopic_conversion(wavelength * 1000)
                # float(input(
                #     'You can find a luminous efficacy table here: '
                #     'http://hyperphysics.phy-astr.gsu.edu/hbase/vision/efficacy.html '
                #     'Please enter the Photopic Conversion value for this wavelength, 683 for wavelength at 550nm: '))
                if flux_type == 0:
                    self.__watt_value = ray_set_flux
                    self.__lumen_value = ray_set_flux * photopic_conversion
                elif flux_type == 2:
                    self.__watt_value = ray_set_flux / photopic_conversion
                    self.__lumen_value = ray_set_flux
                else:
                    msg = "flux_type is in wrong format"
                    raise TypeError(msg)
            elif ray_format_type == 2:
                if content_size % (8 * 4) != 0 or content_size // (8 * 4) != self.__ray_numb:
                    msg = "Zemax file may be wrong format. File size does not match ray numbers said in header."
                    raise TypeError(msg)
                self.__watt_value = ray_set_flux
            else:
                msg = "ray_format_type " + str(ray_format_type) + " is in wrong format"
                raise TypeError(msg)

            for ray_idx in range(self.__ray_numb):
                x = struct.unpack("f", self.dpf_instance.read(4))[0]
                y = struct.unpack("f", self.dpf_instance.read(4))[0]
                z = struct.unpack("f", self.dpf_instance.read(4))[0]
                l_dir = struct.unpack("f", self.dpf_instance.read(4))[0]
                m_dir = struct.unpack("f", self.dpf_instance.read(4))[0]
                n_dir = struct.unpack("f", self.dpf_instance.read(4))[0]
                wav = wavelength if wavelength != 0 else 550
                e = struct.unpack("f", self.dpf_instance.read(4))[0]
                if ray_format_type == 2:
                    wav = round(struct.unpack("f", self.dpf_instance.read(4))[0], 3)
                if wav <= 0:
                    msg = "Error: ray wavelength cannot be <= 0"
                    raise ValueError(msg)
                raylen = math.sqrt(l_dir * l_dir + m_dir * m_dir + n_dir * n_dir)
                if abs(raylen - 1) > 1e-3:
                    msg = "Erorr: Vector length of " + str(m_dir) + "th ray is unusual (" + str(raylen) + ")"
                    raise ValueError(msg)
                # Check ray energy:
                if e < 0:
                    msg = "Error: ray power of " + str(m_dir) + "th ray is < 0"
                    raise ValueError(msg)
                elif e == 0:
                    print('The ' + str(ray_idx) + ' th ray has 0 flux! \n Ray was removed from data')
                    self.__ray_number -= 1
                else:
                    self.__rays.append(DpfRay(x, y, z, l_dir, m_dir, n_dir, wav, e))

        else:
            if not self.__binary:
                msg = "Non binary files not supported \n Filepath:" + self.file_path
                raise TypeError(msg)
            else:
                msg = (
                    "Provided file type is not supported \n Filepath: "
                    + self.file_path
                    + "\n"
                    + "For Speos rayfile you can try to open the file with the RayfileEditor and save the file"
                )
                raise TypeError(msg)

    @property
    def radiometric_power(self) -> float:
        """
        this method return the Radiometric Power value
        Returns:
            Radiometric Power value
        -------

        """
        return self.__watt_value

    @property
    def photometric_power(self) -> float:
        """
        this method return Photometric Power value
        Returns:
            Photometric Power value
        -------

        """
        return self.__lumen_value

    @property
    def rays_number(self) -> int:
        """
        this method return the number of rays
        Returns:
            number of rays in rayfile
        -------

        """
        return self.__ray_numb

    @property
    def rays(self) -> [DpfRay]:
        """
        this method return a list of rays
        Returns:
            a list of rays
        -------

        """
        return self.__rays

    def export_to_zemax(self):
        """
        this method convert the rayfile into zemax format

        Returns
        -------
        None

        """
        outfile = self.export_file()
        zemax_spectrum_file = open(outfile, "wb")
        zemax_spectrum_file.write(struct.pack("<I", 1010))  # Identifier
        zemax_spectrum_file.write(struct.pack("<I", self.rays_number))  # NbrRays

        description = "Converted from SPEOS .ray file."
        # if len(description) > 100:
        #    description = description[:100]
        # else:
        #    description = description.ljust(100)
        description = description.ljust(100)
        zemax_spectrum_file.write(description.encode("ascii"))  # Description
        zemax_spectrum_file.write(struct.pack("f", self.radiometric_power))  # SourceFlux = radiometric flux in SPOES
        zemax_spectrum_file.write(struct.pack("f", self.radiometric_power))  # RaySetFlux = radiometric flux in SPOES
        zemax_spectrum_file.write(struct.pack("f", 0))  # Wavelength
        zemax_spectrum_file.write(struct.pack("f", 0))  # InclinationBeg
        zemax_spectrum_file.write(struct.pack("f", 0))  # InclinationEnd
        zemax_spectrum_file.write(struct.pack("f", 0))  # AzimuthBeg
        zemax_spectrum_file.write(struct.pack("f", 0))  # AzimuthEnd
        zemax_spectrum_file.write(struct.pack("<I", 4))  # DimensionUnits: M=0, IN=1, CM=2, FT=3, MM=4
        zemax_spectrum_file.write(struct.pack("f", 0))  # LocX
        zemax_spectrum_file.write(struct.pack("f", 0))  # LocY
        zemax_spectrum_file.write(struct.pack("f", 0))  # LocZ
        zemax_spectrum_file.write(struct.pack("f", 0))  # RotX
        zemax_spectrum_file.write(struct.pack("f", 0))  # RotY
        zemax_spectrum_file.write(struct.pack("f", 0))  # RotZ
        zemax_spectrum_file.write(struct.pack("f", 0))  # ScaleX
        zemax_spectrum_file.write(struct.pack("f", 0))  # ScaleY
        zemax_spectrum_file.write(struct.pack("f", 0))  # ScaleZ
        zemax_spectrum_file.write(struct.pack("f", 0))  # unused1 (float)
        zemax_spectrum_file.write(struct.pack("f", 0))  # unused2 (float)
        zemax_spectrum_file.write(struct.pack("f", 0))  # unused3 (float)
        zemax_spectrum_file.write(struct.pack("f", 0))  # unused4 (float)
        zemax_spectrum_file.write(
            struct.pack("<I", 2)
        )  # ray_format_type is color since the SPEOS ray file always contains wavelength
        zemax_spectrum_file.write(struct.pack("<I", 0))  # flux_type is Watts
        zemax_spectrum_file.write(struct.pack("<I", 0))  # reversed1 (int)
        zemax_spectrum_file.write(struct.pack("<I", 0))  # reversed2 (int)
        for ray in self.rays:
            zemax_spectrum_file.write(struct.pack("f", ray.coordinate_x))  # x
            zemax_spectrum_file.write(struct.pack("f", ray.coordinate_y))  # y
            zemax_spectrum_file.write(struct.pack("f", ray.coordinate_z))  # z
            zemax_spectrum_file.write(struct.pack("f", ray.radiation_l))  # l
            zemax_spectrum_file.write(struct.pack("f", ray.radiation_m))  # m
            zemax_spectrum_file.write(struct.pack("f", ray.radiation_n))  # n
            zemax_spectrum_file.write(struct.pack("f", ray.energy))  # flux (Watts)
            zemax_spectrum_file.write(struct.pack("f", ray.wavelength))  # wavelength
        zemax_spectrum_file.close()

    def export_to_speos(self):
        """
        this method convert the rayfile into speos format

        Returns
        -------
        None

        """
        outfile = self.export_file()
        speos_ray_file = open(outfile, "wb")
        speos_ray_file.write(struct.pack("f", self.radiometric_power))
        speos_ray_file.write(struct.pack("f", 2.0))
        speos_ray_file.write(struct.pack("f", 2.0))
        speos_ray_file.write(struct.pack("f", 2.0))
        speos_ray_file.write(struct.pack("f", 2.0))
        speos_ray_file.write(struct.pack("f", 2.0))
        speos_ray_file.write(struct.pack("f", self.photometric_power))
        for ray in self.rays:
            speos_ray_file.write(struct.pack("f", ray.coordinate_x))
            speos_ray_file.write(struct.pack("f", ray.coordinate_y))
            speos_ray_file.write(struct.pack("f", ray.coordinate_z))
            speos_ray_file.write(struct.pack("f", ray.radiation_l))
            speos_ray_file.write(struct.pack("f", ray.radiation_m))
            speos_ray_file.write(struct.pack("f", ray.radiation_n))
            speos_ray_file.write(struct.pack("f", ray.wavelength * 1000))
            speos_ray_file.write(struct.pack("f", ray.energy))
        speos_ray_file.close()

    def export_file(self, export_folder_dir=None, convert=False):
        """
        this method generates a file to be exported
        Parameters
        ----------

        export_folder_dir : str ,optional
            defines path where to export the rayfile
        convert : Boolean , optional
            defines if the export is a conversion, default value is False
        Returns
        -------
        outfile: str
            output file

        """
        input_file_folder = os.path.dirname(self.file_path)
        input_file_name = os.path.basename(self.file_path).split(".")[0]
        input_file_extension = os.path.splitext(self.file_path)[1].lower()[0:]
        output_file_path = ""
        if export_folder_dir is not None:
            self.valid_dir(export_folder_dir)
            output_file_path = os.path.join(export_folder_dir, input_file_name)
        else:
            output_file_path = os.path.join(input_file_folder, input_file_name)

        if convert:
            if input_file_extension in self.conversion_extension:
                exported_file_extension = self.conversion_extension[input_file_extension]
            else:
                exported_file_extension = input_file_extension
                msg = "Provided file extension " + exported_file_extension + " is not supported"
                raise TypeError(msg)

        else:
            if input_file_extension in self.conversion_extension:
                exported_file_extension = input_file_extension
            else:
                exported_file_extension = input_file_extension
                msg = "Provided file extension" + exported_file_extension + "is not supported"
                raise TypeError(msg)
        outfile = output_file_path + exported_file_extension
        outfile_num = 1
        while os.path.isfile(outfile):
            outfile = output_file_path + "_" + str(outfile_num) + exported_file_extension
            outfile_num += 1
        return outfile
