import struct

from ansys_optical_automation.post_process.dpf_rayfile import DpfRayfile


class RayfileConverter(DpfRayfile):
    """
    This class contains the methods to convert rayfile between speos and zemax
    """

    def __init__(self, file_path):
        DpfRayfile.__init__(self, file_path)

    def __export_to_zemax(self):
        """
        this method convert the rayfile from speos into zemax format

        Returns
        -------
        None

        """
        outfile = self.export_file(convert=True)
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
        )  # ray_format_type is color since the SPES ray file always contains wavelength
        zemax_spectrum_file.write(struct.pack("<I", 0))  # flux_type is Watss
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

    def __export_to_speos(self):
        """
        this method convert the zemax rayfile into speos format

        Returns
        -------
        None

        """
        outfile = self.export_file(convert=True)
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
            speos_ray_file.write(struct.pack("f", ray.wavelength))
            speos_ray_file.write(struct.pack("f", ray.energy))
        speos_ray_file.close()

    def speos_to_zemax(self):
        """
        this method will read the speos rayfile content and convert it to zemax format
        Parameters
        ----------
        rayfile_path: str
            speos rayfile path

        Returns
        -------
        None

        """

        self.__export_to_zemax()

    def zemax_to_speos(self):
        """
        this method convert the zemax rayfile into speos format
        Parameters
        ----------
        rayfile_path: str
            zemax rayfile

        Returns
        -------
        None

        """
        self.__export_to_speos()
