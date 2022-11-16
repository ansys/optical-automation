import math
import os

import numpy as np
from scipy import interpolate
from scipy.integrate import nquad

EPSILON = 1e-6


class BrdfMeasurementPoint:
    """
    class of a single brdf point measure: brdf = f(wavelength, incidence, theta)
    no phi dependency for measured brdf
    """

    def __init__(self, input_incidence: float, input_wavelength: float, input_theta: float, input_brdf: float) -> None:
        self.incidence = input_incidence
        self.wavelength = input_wavelength
        self.theta = input_theta
        self.brdf = input_brdf


class BrdfStructure:
    """
    class of brdf
    """

    def __init__(self, wavelength_list):

        wavelength_list = sorted(set(wavelength_list))
        if not all(360 < item < 830 for item in wavelength_list):
            raise ValueError("Please provide correct wavelengths in range between 360 and 830nm ")
        self.__wavelengths = wavelength_list
        self.__incident_angles = []
        self.__theta_1d_ressampled = None
        self.__phi_1d_ressampled = None
        self.measurement_2d_brdf = []
        self.brdf = []
        self.reflectance = []
        self.file_name = "export_brdfstruct"

    def __valid_dir(self, str_path):
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

    def brdf_1d_function(self, wavelength, incident):
        """
        to provide a 1d linear fitting function for 2d measurement brdf points.

        Parameters
        ----------
        wavelength : float
            wavelength used to find the target brdf values.
        incident : float
            incident used to find the target brdf values.

        Returns
        -------


        """
        theta_brdf = [
            [MeasurePoint.theta, MeasurePoint.brdf]
            for MeasurePoint in self.measurement_2d_brdf
            if (MeasurePoint.incidence == incident and MeasurePoint.wavelength == wavelength)
        ]
        theta_brdf = np.array(theta_brdf).T
        return interpolate.interp1d(theta_brdf[0], theta_brdf[1], fill_value="extrapolate"), np.max(theta_brdf[0])

    def __brdf_reflectance(self, theta, phi, brdf):
        """
        function to calculate the reflectance of the brdf at one incident and wavelength

        Parameters
        ----------
        theta : np.array
        phi : np.array
        brdf : 2d brdf function

        Returns
        -------
        float
            brdf reflectance value.

        """
        theta_rad, phi_rad = np.radians(theta), np.radians(phi)  # samples on which integrande is known
        integrande = (1 / math.pi) * brdf * np.sin(theta_rad)  # *theta for polar integration
        f = interpolate.interp2d(theta_rad, phi_rad, integrande, kind="linear", bounds_error=False, fill_value=0)
        # calculation of integrande as from from samples
        r = nquad(f, [[0, math.pi / 2], [0, 2 * math.pi]], opts=[{"epsabs": 0.1}, {"epsabs": 0.1}])
        # reflectance calculaiton thanks to nquad lib
        return min(r[0] * 100, 100)  # return reflectance as percentage

    def convert(self, sampling=1):
        """
        convert the provided 2d measurement brdf data.

        Parameters
        ----------
        sampling : int
            sampling used for exported 4d brdf structure.

        Returns
        -------
        None

        """

        def brdf_2d_function(theta, phi):
            """
            an internal method to calculate the 2d brdf based on location theta and phi.

            Parameters
            ----------
            theta : float
                target point with theta value
            phi : float
                target point with phi value

            Returns
            -------
            float
                value of brdf value

            """
            # function that calculated 2d brdf from 1d using revolution assumption.
            angular_distance = np.sqrt(
                (incidence - theta * np.cos(np.radians(phi))) ** 2 + (theta * np.sin(np.radians(phi))) ** 2
            )
            # +4l for interpolation between measurement value on both side from specular direction
            angular_distance = np.where(angular_distance < EPSILON, 1, angular_distance)
            # special case for specular point (no interpolation due to null distance)
            weight = (incidence + angular_distance - theta * np.cos(np.radians(phi))) / (2 * angular_distance)
            weight = np.where(incidence + angular_distance > theta_max, 1, weight)
            # theta max : maximal reflected angle that is measured. for angle > theta_max we do not have values
            return weight * (brdf_1d(incidence - angular_distance)) + (1 - weight) * brdf_1d(
                incidence + angular_distance
            )

        if len(self.__incident_angles) == 0:
            for measurement in self.measurement_2d_brdf:
                if measurement.incidence not in self.__incident_angles:
                    self.__incident_angles.append(measurement.incidence)
        # mesh grid for direct 2d matrix calculation
        for incidence in self.__incident_angles:
            for wavelength in self.__wavelengths:
                brdf_1d, theta_max = self.brdf_1d_function(wavelength, incidence)
                self.__theta_1d_ressampled = np.linspace(0, 90, int(90 / sampling + 1))
                self.__phi_1d_ressampled = np.linspace(0, 360, int(360 / sampling + 1))
                theta_2d_ressampled, phi_2d_ressampled = np.meshgrid(
                    self.__theta_1d_ressampled, self.__phi_1d_ressampled
                )
                self.brdf.append(brdf_2d_function(theta_2d_ressampled, phi_2d_ressampled))
                self.reflectance.append(
                    self.__brdf_reflectance(self.__theta_1d_ressampled, self.__phi_1d_ressampled, self.brdf[-1])
                )
        self.brdf = np.reshape(
            self.brdf,
            (
                len(self.__incident_angles),
                len(self.__wavelengths),
                2 * int(180 / sampling + 1) - 1,
                int(90 / sampling + 1),
            ),
        )
        if np.all(self.brdf == 0):
            msg = "All NULL values at brdf structure, please provide valid inputs"
            raise ValueError(msg)
        self.brdf = np.moveaxis(self.brdf, 2, 3)
        self.reflectance = np.reshape(self.reflectance, (len(self.__incident_angles), len(self.__wavelengths)))

    def export_to_speos(self, export_dir):
        """
        save the 4d brdf structure into a brdf file.

        Parameters
        ----------
        export_dir : str
            directory to be exported

        Returns
        -------


        """
        self.__valid_dir(export_dir)
        file_name = os.path.join(export_dir, self.file_name + ".brdf")
        export = open(file_name, "w")
        export.write("OPTIS - brdf surface file v9.0\n")  # Header.
        export.write("0\n")  # Defines the mode: 0 for text mode, 1 for binary mode.
        export.write("Scattering surface\n")  # Comment line
        export.write("0\n\n")  # Number of characters to read for the measurement description.
        export.write("1\t0\n")  # Contains two boolean values (0=false and 1=true)
        # The first bReflection tells whether the surface has reflection data or not.
        # The second bTransmission tells whether the surface has transmission data or not.
        export.write("1\n")  # Contains a boolean value describing the type of value stored in the file:
        # 1 means the data is proportional to the BSDF.
        # 0 means the data is proportional to the measured intensity or to the probability density function.
        # Write BRDF sampling data
        export.write(
            "%d\t%d\n" % (self.brdf.shape[0], self.brdf.shape[1])
        )  # Number of incident angles and Number of wavelength samples (in nanometer)
        np.savetxt(
            export, [self.__incident_angles], format("%.3f"), footer="\n", newline="", delimiter="\t", comments=""
        )  # List of the incident angles.
        np.savetxt(
            export, [self.__wavelengths], format("%.1f"), footer="\n", newline="", delimiter="\t", comments=""
        )  # List of wavelength

        # Write BRDF tables
        for incidence in range(len(self.__incident_angles)):
            for wavelength in range(len(self.__wavelengths)):
                export.write("%f\n" % self.reflectance[incidence, wavelength])  # reflectance
                export.write("%d\t%d\n" % np.shape(self.brdf)[2:])
                np.savetxt(
                    export,
                    [self.__phi_1d_ressampled],
                    format("%.3f"),
                    footer="\n",
                    newline="",
                    delimiter="\t",
                    comments="",
                    header="\t",
                )  # phi header
                data_with_theta = np.concatenate(
                    (np.array([self.__theta_1d_ressampled]).T, self.brdf[incidence, wavelength, :, :]), axis=1
                )  # add theta header
                np.savetxt(
                    export, data_with_theta, format("%.3e"), delimiter="\t"
                )  # 2d matrix is directly save thnaks to np.savetxt lib
        export.close()
