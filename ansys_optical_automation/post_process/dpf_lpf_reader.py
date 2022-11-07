import os
import sys

from ansys_optical_automation.post_process.dpf_base import DataProcessingFramework

# better versioning to be done later
speosInstallationPath = os.path.join(os.environ.get("AWP_ROOT231"), r"Optical Products\Speos\bin")
sys.path.append(speosInstallationPath)

import IllumineCore_pywrap
import IllumineSpeos_pywrap


class DpfLpfReader(DataProcessingFramework):
    def __init__(self):
        DataProcessingFramework.__init__(self, extension=".lpf")
        self.dpf_instance = IllumineSpeos_pywrap.CLpfFileReader()
        self.traces = []
        self.trace_count = 0
        self.sequence_faces = []
        self.sequence_impacts = []
        self.sequences = []

    def open_file(self, str_path):
        """
        Parameters
        ----------
        str_path : str
            path to file to be opened by LPF reader

        Returns
        -------


        """
        lpf_file = IllumineCore_pywrap.Path(str_path)
        error = self.dpf_instance.InitLpfFileName(lpf_file)
        self.error_manager(error)

    def error_manager(self, error):
        """
        function to retrieve errors from LPF reader
         if no error found returns none
        Parameters
        ----------
        error :  IllumineSpeos error object
            error Object produced by LPF reader

        Returns
        -------
        None

        """
        if error.Ptr() is not None:
            # Retrieve and print error message
            error_message = IllumineSpeos_pywrap.COptString()
            error.Ptr().GetErrorMessage(error_message)
            error_message = error_message.ToOptisString().Ptr()
            raise ChildProcessError(error_message)
        else:
            return None

    def retrieve_traces(self):
        """
        function to retrieve all traces to a list of traces
        Returns
        -------

        """
        self.trace_count = self.dpf_instance.GetNbOfTraces()
        ray_path_vector = IllumineSpeos_pywrap.Vector_COptRayPath()
        ray_path_vector.Resize(self.trace_count)
        error = self.dpf_instance.GetRayPathBundle(ray_path_vector.ToSpan())
        self.error_manager(error)
        self.traces = ray_path_vector
        for ray in self.traces:
            if ray.vUniqueFaceIds in self.sequence_faces:
                self.sequences[self.sequence_faces.index(ray.vUniqueFaceIds)].append(ray)
            else:
                self.sequence_faces.append(ray.vUniqueFaceIds)
                self.sequence_impacts.append(ray.vImpacts.Size())
                self.sequences.append([ray])
