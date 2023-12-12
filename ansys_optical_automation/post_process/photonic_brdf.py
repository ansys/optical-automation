import csv
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

    def __init__(self, input_incidence, input_wavelength, input_theta, input_brdf):
        self.incidence = input_incidence
        self.wavelength = input_wavelength
        self.theta = input_theta
        self.brdf = input_brdf


class BrdfStructure:
    """
    class of BRDF contains method to host and convert 2d reflectance brdf values into 3d brdf file.
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
        self.rt_list = []
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
        # calculation of integrande as from samples
        # current scipy method
        f = interpolate.RectBivariateSpline(phi_rad, theta_rad, integrande, kx=1, ky=1)
        r = nquad(f, [[0, 2 * math.pi], [0, math.pi / 2]], opts=[{"epsabs": 0.1}, {"epsabs": 0.1}])
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

        def brdf_2d_function(theta, phi, ratio=1):
            """
            an internal method to calculate the 2d brdf based on location theta and phi.

            Parameters
            ----------
            theta : float
                target point with theta value
            phi : float
                target point with phi value
            ratio : float
                value between 0 and 1: minor/major

            Returns
            -------
            float
                value of brdf value

            """
            # function that calculated 2d brdf from 1d using revolution assumption.
            angular_distance = np.sqrt(
                (theta * np.cos(np.radians(phi)) - incidence) ** 2 + ((theta * np.sin(np.radians(phi))) / ratio) ** 2
            )
            # +4l for interpolation between measurement value on both side from specular direction
            angular_distance = np.where(angular_distance < EPSILON, 1, angular_distance)
            # special case for specular point (no interpolation due to null distance)
            weight = (incidence + angular_distance - theta * np.cos(np.radians(phi))) / (2 * angular_distance)
            # theta max : maximal reflected angle that is measured. for angle > theta_max we do not have values
            brdf_left = np.where(
                brdf_1d(incidence - angular_distance) < 0.0, 0.0, brdf_1d(incidence - angular_distance)
            )
            brdf_right = np.where(
                brdf_1d(incidence + angular_distance) < 0.0, 0.0, brdf_1d(incidence + angular_distance)
            )
            return weight * brdf_left + (1 - weight) * brdf_right

        if len(self.__incident_angles) == 0:
            for measurement in self.measurement_2d_brdf:
                if measurement.incidence not in self.__incident_angles:
                    self.__incident_angles.append(measurement.incidence)
        # mesh grid for direct 2d matrix calculation
        normalized_scale = 1
        for incidence_id, incidence in enumerate(self.__incident_angles):
            for wavelength in self.__wavelengths:
                brdf_1d, theta_max = self.brdf_1d_function(wavelength, incidence)
                self.__theta_1d_ressampled = np.linspace(0, 90, int(90 / sampling + 1))
                self.__phi_1d_ressampled = np.linspace(0, 360, int(360 / sampling + 1))
                theta_2d_ressampled, phi_2d_ressampled = np.meshgrid(
                    self.__theta_1d_ressampled, self.__phi_1d_ressampled
                )
                self.brdf.append(brdf_2d_function(theta_2d_ressampled, phi_2d_ressampled, 1))
                if incidence_id == 0:
                    normalized_scale = self.rt_list[0] / self.__brdf_reflectance(
                        self.__theta_1d_ressampled, self.__phi_1d_ressampled, self.brdf[-1]
                    )
                self.brdf[-1] *= normalized_scale
                self.reflectance.append(
                    self.__brdf_reflectance(self.__theta_1d_ressampled, self.__phi_1d_ressampled, self.brdf[-1])
                )
                print(incidence, self.reflectance[-1])

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

    def export_to_speos(self, export_dir, rt):
        """
        save the 4d brdf structure into a brdf file.

        Parameters
        ----------
        export_dir : str
            directory to be exported
        rt : str
            type of bsdf: t for transmission, r for reflective material

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
        if rt.lower() == "t":
            export.write("0\t1\n")
        else:
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
                brdf_content = self.brdf[
                    incidence,
                    wavelength,
                    :,
                    :,
                ]
                data_with_theta = None
                if rt.lower() == "t":
                    brdf_content = np.flip(brdf_content, axis=0)
                    data_with_theta = np.concatenate(
                        ((np.array([self.__theta_1d_ressampled]) + 90).T, brdf_content), axis=1
                    )  # add theta header
                else:
                    data_with_theta = np.concatenate(
                        (np.array([self.__theta_1d_ressampled]).T, brdf_content), axis=1
                    )  # add theta header
                np.savetxt(
                    export, data_with_theta, format("%.3e"), delimiter="\t"
                )  # 2d matrix is directly save thnaks to np.savetxt lib
        export.close()


def convert_export(input_csv, rt, rt_type, output_path):
    """
    main function to convert 2d data into brdf and export.

    Parameters
    ----------
    input_csv : str
        path of csv file recording the 2d data.
    rt : str
        path for rt txt file.
    rt_type : str
        type for transmission, R for reflection, T for transmission
    output_path : str
        path for the brdf to be exported.

    Returns
    -------


    """
    wavelength_list = []
    brdf_data = None
    RT = []
    with open(rt) as myfile:
        for line in myfile:
            if "AOI" in line:
                RT_value = line.split()[2:]
                RT.append([float(value) * 100 for value in RT_value])
    with open(input_csv) as file:
        content = csv.reader(file, delimiter=",")
        FirstRow = True
        for row in content:
            if FirstRow:
                wavelength_list = [item.split("nm")[0] for item in row][2:]
                wavelength_list = [float(item) for item in wavelength_list]
                brdf_data = BrdfStructure(wavelength_list)
            else:
                for wavelength_idx, wavelength in enumerate(wavelength_list):
                    brdf_data.measurement_2d_brdf.append(
                        BrdfMeasurementPoint(float(row[0]), wavelength, float(row[1]), float(row[2 + wavelength_idx]))
                    )
            FirstRow = False
        if rt_type.lower() == "t":
            brdf_data.rt_list = [item[1] for item in RT]
        else:
            brdf_data.rt_list = [item[0] for item in RT]
        brdf_data.convert(sampling=1)
        brdf_data.export_to_speos(output_path, rt_type)


cwd = os.path.realpath(__file__)
repo = os.path.dirname(os.path.dirname(os.path.dirname(cwd)))
measurement_2d_file = r"D:\Customer\CP\infinite\MakrolonDQ5122_speos_transmissiononly_modified.csv"
rt_file = r"D:\Customer\CP\infinite\RTfile.txt"
convert_export(measurement_2d_file, rt_file, "T", r"D:\\")
