import math
import os
import struct

from ansys_optical_automation.post_process.dpf_file import DpfFile

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


class DpfRayfile(DpfFile):
    """
    this class contains method to read extract ray data from given binary rayfile
    """

    def __init__(self, file_path):
        self.file_type = os.path.splitext(file_path)[1].lower()[1:]
        self.file_path = file_path
        DpfFile.__init__(self, self.file_type)
        self.__content = self.load(self.file_path)
        self.__ray_numb = 0
        self.__watt_value = 0
        self.__lumen_value = 0
        self.__rays = []
        self.identifier = 0
        self.description = "description"
        self.source_flux = 0
        self.load_content()

    def __photopic_conversion(self, wavelength):
        start = 0
        end = len(Photopic_Conversion_wavelength)
        pos = 0
        while start < end:
            mid = (start + end) // 2
            print(mid, Photopic_Conversion_wavelength[mid])
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

    def load_content(self):
        """
        this method load the information from rayfile provided

        Returns
        -------


        """

        if self.file_type == "ray":
            content_size = os.fstat(self.__content.fileno()).st_size - 28
            if content_size % 32 != 0:
                msg = "Provided rayfile is not generated from speos"
                raise ValueError(msg)
            self.__ray_numb = int(content_size / 32)

            self.__watt_value = struct.unpack("f", self.__content.read(4))[0]
            self.__content.read(4 * 5)
            self.__lumen_value = struct.unpack("f", self.__content.read(4))[0]
            for ray_idx in range(self.__ray_numb):
                x = struct.unpack("f", self.__content.read(4))[0]
                y = struct.unpack("f", self.__content.read(4))[0]
                z = struct.unpack("f", self.__content.read(4))[0]
                l_dir = struct.unpack("f", self.__content.read(4))[0]
                m_dir = struct.unpack("f", self.__content.read(4))[0]
                n_dir = struct.unpack("f", self.__content.read(4))[0]
                wav = struct.unpack("f", self.__content.read(4))[0] * 0.001
                e = struct.unpack("f", self.__content.read(4))[0]
                if e <= 0:
                    msg = "Error: ray power of ray of " + str(ray_idx) + " cannot be <= 0"
                    raise ValueError(msg)
                if wav <= 0:
                    msg = "Error: ray wavelength of ray of " + str(ray_idx) + "cannot be <= 0"
                    raise ValueError(msg)
                raylen = math.sqrt(l_dir * l_dir + m_dir * m_dir + n_dir * n_dir)
                if abs(raylen - 1) > 1e-3:
                    msg = "Error: Vector length of " + str(ray_idx) + "the ray is unusual (" + str(raylen) + ")"
                    raise ValueError(msg)
                self.__rays.append(DpfRay(x, y, z, l_dir, m_dir, n_dir, wav, e))
            self.__content.close()
        elif self.file_type == "dat" or self.file_type == "sdf":
            self.identifier = int.from_bytes(
                self.__content.read(4), byteorder="little"
            )  # Format version ID, current value is 1010
            self.__ray_numb = int.from_bytes(
                self.__content.read(4), byteorder="little"
            )  # The number of rays in the file
            self.description = self.__content.read(100).decode()  # A text description of the source
            self.source_flux = struct.unpack("f", self.__content.read(4))[0]  # The total flux in watts of this source
            ray_set_flux = struct.unpack("f", self.__content.read(4))[
                0
            ]  # The flux in watts represented by this Ray Set
            wavelength = 1000 * struct.unpack("f", self.__content.read(4))[0]
            # The wavelength in micrometers,
            # 0 if a composite,converted to nanometer since this is the speos' source file format.
            self.__content.read(18 * 4)
            # InclinationBeg = struct.unpack('f', self.__content.read(4))[0]  # Angular range for ray set (Degrees)
            # InclinationEnd = struct.unpack('f', self.__content.read(4))[0]  # Angular range for ray set (Degrees)
            # AzimuthBeg = struct.unpack('f', self.__content.read(4))[0]  # Angular range for ray set (Degrees)
            # AzimuthEnd = struct.unpack('f', self.__content.read(4))[0]  # Angular range for ray set (Degrees)
            # DimensionUnits = int.from_bytes(self.__content.read(4), byteorder='little')
            # METERS=0, IN=1, CM=2, FEET=3, MM=4
            # LocX = struct.unpack('f', self.__content.read(4))[0]  # Coordinate Translation of the source
            # LocY = struct.unpack('f', self.__content.read(4))[0]  # Coordinate Translation of the source
            # LocZ = struct.unpack('f', self.__content.read(4))[0]  # Coordinate Translation of the source
            # RotX = struct.unpack('f', self.__content.read(4))[0]  # Source rotation (Radians)
            # RotY = struct.unpack('f', self.__content.read(4))[0]  # Source rotation (Radians)
            # RotZ = struct.unpack('f', self.__content.read(4))[0]  # Source rotation (Radians)
            # ScaleX = struct.unpack('f', self.__content.read(4))[0]  # Currently unused
            # ScaleY = struct.unpack('f', self.__content.read(4))[0]  # Currently unused
            # ScaleZ = struct.unpack('f', self.__content.read(4))[0]  # Currently unused
            # self.__content.read(4 * 4)  # Unused data
            ray_format_type = int.from_bytes(self.__content.read(4), byteorder="little")
            # The ray_format_type must be either 0 for flux only format(.dat), or 2 for the spectral color format(.sdf).
            flux_type = int.from_bytes(
                self.__content.read(4), byteorder="little"
            )  # If and only if the ray_format_type is 0, then the flux_type is 0 for watts, and 1 for lumens.
            # For the spectral color format(.sdf), the flux must be in watts, and the wavelength in micrometers.
            self.__content.read(4 * 2)  # Unused data
            content_size = os.fstat(self.__content.fileno()).st_size - self.__content.tell()
            if ray_format_type == 0:
                if content_size % (7 * 4) != 0 or content_size // (7 * 4) != self.__ray_numb:
                    msg = "Warning: Zemax file may be wrong format. File size does not match ray numbers said in header"
                    raise ValueError(msg)
                wavelength = wavelength if wavelength != 0 else 550
                photopic_conversion = self.__photopic_conversion(wavelength)
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
            else:
                msg = "ray_format_type " + str(ray_format_type) + " is in wrong format"
                raise TypeError(msg)

            for ray_idx in range(self.__ray_numb):
                x = struct.unpack("f", self.__content.read(4))[0]
                y = struct.unpack("f", self.__content.read(4))[0]
                z = struct.unpack("f", self.__content.read(4))[0]
                l_dir = struct.unpack("f", self.__content.read(4))[0]
                m_dir = struct.unpack("f", self.__content.read(4))[0]
                n_dir = struct.unpack("f", self.__content.read(4))[0]
                wav = 550
                if ray_format_type == 2:
                    wav = struct.unpack("f", self.__content.read(4))[0]
                e = struct.unpack("f", self.__content.read(4))[0]
                if e <= 0:
                    msg = "Error: ray power of " + str(m_dir) + "th ray is <= 0"
                    raise ValueError(msg)
                if wav <= 0:
                    msg = "Error: ray wavelength cannot be <= 0"
                    raise ValueError(msg)
                raylen = math.sqrt(l_dir * l_dir + m_dir * m_dir + n_dir * n_dir)
                if abs(raylen - 1) > 1e-3:
                    msg = "Erorr: Vector length of " + str(m_dir) + "th ray is unusual (" + str(raylen) + ")"
                    raise ValueError(msg)
                self.__rays.append(DpfRay(x, y, z, l_dir, m_dir, n_dir, wav, e))
        else:
            msg = "Provided file type is not supported"
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
