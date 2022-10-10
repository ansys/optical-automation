import os
import sys

from ansys_optical_automation.lumerical_core.utils import get_lumerical_install_location


class DpfStack:
    """Provides DPF (Data Processing Framework).

    The class contains opening and saving functionalities to allow interacting between stack and speos and zemax.

    """

    def __init__(self, version):
        """Initialize general properties of DPF.

        Parameters
        ----------
        version : int
            version of lumerical in format of 222 or 231 to be used. For example, ``222`` for 2022 R2.
        """
        self.support_version = version
        self.stack_file_location = None
        self.stack = None
        self.rt_stack = None
        self.rt_theta = None
        self.rt_lambda = None
        self.R = None
        self.T = None

    def open_file(self, stack_file):
        """Open a stack file.

        Parameters
        ----------
        stack_file : str
            directory of stack file
        """

        if not stack_file.lower().endswith(("ldf", "fsp")):
            msg = "incorrect file provided"
            raise ImportError(msg)
        self.stack_file_location = stack_file

        if not self.stack_file_location.lower().endswith("fsp"):
            # TODO compute the stack project
            pass

        install_location = get_lumerical_install_location(self.support_version)
        lumapi_location = os.path.join(install_location, "api", "python")
        sys.path.append(lumapi_location)
        import lumapi

        self.stack = lumapi.FDTD(hide=True)
        self.stack.loaddata(self.stack_file_location)
        self.rt_stack = self.stack.getv("RTstack")

    def _save_stack_to_speos(self):
        """save the stack result into speos coated file formate."""
        output_file_location = os.path.splitext(self.stack_file_location)[0] + ".coated"
        # # write the file
        write_out = open(output_file_location, "w")
        write_out.write("OPTIS-Coated surface file v1.0\n")
        write_out.write("Coating surface\n")
        write_out.write(str(len(self.rt_theta)) + " " + str(len(self.rt_lambda)) + "\n\t")
        for wavelength in self.rt_lambda:
            write_out.write("%9.3f " % (wavelength[0] * 10e8))
        write_out.write("\n")

        for theta_idx, theta in enumerate(self.rt_theta):
            write_out.write("%3.2f " % theta[0])
            for lambda_idx, lambda_value in enumerate(self.rt_lambda):
                write_out.write("%3.2f " % self.R[lambda_idx, 0, theta_idx])
                write_out.write("%3.2f " % self.T[lambda_idx, 0, theta_idx])
            write_out.write("\n\t")
            for lambda_idx, lambda_value in enumerate(self.rt_lambda):
                write_out.write("%3.2f " % self.R[lambda_idx, 1, theta_idx])
                write_out.write("%3.2f " % self.T[lambda_idx, 1, theta_idx])
            write_out.write("\n")
        write_out.close()

    def _save_stack_to_zemax(self):
        """save the stack result into Zemax .dat file format."""
        output_file_location = os.path.splitext(self.stack_file_location)[0] + ".dat"
        # # write the file
        write_out = open(output_file_location, "w")
        write_out.write("! Lumerical stack coating data\n")
        write_out.write("TABLE LUMERICAL_STACK\n")

        for theta_idx, theta in enumerate(self.rt_theta):
            write_out.write("ANGL %3.2f\n" % theta[0])
            for lambda_idx, lambda_value in enumerate(self.rt_lambda):
                write_out.write(
                    "WAVE %8.6f %8.6f %8.6f %8.6f %8.6f\n"
                    % (
                        lambda_value[0] * 1e6,
                        self.R[lambda_idx, 1, theta_idx] / 100,  # Rs
                        self.R[lambda_idx, 0, theta_idx] / 100,  # Rp
                        self.T[lambda_idx, 1, theta_idx] / 100,  # Ts
                        self.T[lambda_idx, 0, theta_idx] / 100,  # Tp
                    )
                )
        write_out.write("\n")
        write_out.close()

    def _organize_data_for_output(self):
        """Retrieve data from stack result file."""
        import numpy as np

        Rp = None
        Tp = None
        Rs = None
        Ts = None
        try:
            self.rt_theta = self.rt_stack["theta"]
            self.rt_lambda = self.rt_stack["lambda"]
            Rp = self.rt_stack["Rp"] * 100  # switch to percent
            Tp = self.rt_stack["Tp"] * 100  # switch to percent
            Rs = self.rt_stack["Rs"] * 100  # switch to percent
            Ts = self.rt_stack["Ts"] * 100  # switch to percent
        except Exception as e:
            raise ValueError("provided data does not have all the theta, lambda, Rp, Rs, Tp, Ts values. Details:" + e)

        Ro = np.zeros((len(self.rt_lambda), 2, len(self.rt_theta)), dtype=float)
        To = np.zeros((len(self.rt_lambda), 2, len(self.rt_theta)), dtype=float)

        # resort by lambda to ensure increasing
        sorted_indices = np.argsort(self.rt_lambda[:, 0])
        self.rt_lambda = [rt_lambda_element for _, rt_lambda_element in sorted(zip(sorted_indices, self.rt_lambda))]
        Ro[:, 0, :] = [Rp_element for _, Rp_element in sorted(zip(sorted_indices, Rp))]
        Ro[:, 1, :] = [Rs_element for _, Rs_element in sorted(zip(sorted_indices, Rs))]
        To[:, 0, :] = [Tp_element for _, Tp_element in sorted(zip(sorted_indices, Tp))]
        To[:, 1, :] = [Ts_element for _, Ts_element in sorted(zip(sorted_indices, Ts))]

        # add the 90-degree angle with reflection 100 and transmission 0
        Ro[:, :, -1] = 100
        To[:, :, -1] = 0

        # # clamp R and T
        self.R = np.where((Ro > 100) | (Ro < 0), np.clip(Ro, 0, 100), Ro)
        self.T = np.where((To > 100) | (To < 0), np.clip(To, 0, 100), To)

    def convert_stack_to_speos(self):
        """conver the stack result into required information by speos coated file."""
        self._organize_data_for_output()
        self._save_stack_to_speos()

    def convert_stack_to_zemax(self):
        """conver the stack result into required information by Zemax .dat coating file."""
        self._organize_data_for_output()
        self._save_stack_to_zemax()
