import os
import sys


class DpfLpfReader:
    def __init__(self, speos_version):
        if speos_version not in [231, 232, 241, 242]:
            msg = "Speos API {} is not supported.".format(speos_version)
            raise ValueError(msg)
        speos_installation_path = os.path.join(
            os.environ.get("AWP_ROOT" + str(speos_version)), r"Optical Products\Speos\bin"
        )
        sys.path.append(speos_installation_path)

        import IllumineCore_pywrap
        import IllumineSpeos_pywrap

        self.pdf_core = IllumineCore_pywrap
        self.pdf_speos = IllumineSpeos_pywrap

        self.dpf_instance = self.pdf_speos.CLpfFileReader()
        self.traces = []
        self.trace_count = 0
        self.sequence_faces = []
        self.sequence_impacts = []
        self.sequences = []
        self.trace_boundary = [0, 0, 0]
        "@todo add min max for boundarie for non symetric usage"

    def open_file(self, str_path):
        """
        Parameters
        ----------
        str_path : str
            path to file to be opened by LPF reader

        Returns
        -------


        """
        lpf_file = self.pdf_core.Path(str_path)
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
            error_message = self.pdf_speos.COptString()
            error.Ptr().GetErrorMessage(error_message)
            error_message = error_message.ToOptisString().Ptr()
            raise ChildProcessError(error_message)
        else:
            return None

    def retrieve_traces(self, by_sequence=True):
        """
        function to retrieve all traces to a list of traces
        Returns
        -------

        """
        self.trace_count = self.dpf_instance.GetNbOfTraces()
        self.traces = self.pdf_speos.Vector_COptRayPath()
        self.traces.Resize(self.trace_count)
        error = self.dpf_instance.GetRayPathBundle(self.traces.ToSpan())
        self.error_manager(error)
        if by_sequence:
            for ray in self.traces:
                start_point = [ray.vImpacts.Get(0).Get(0), ray.vImpacts.Get(0).Get(1), ray.vImpacts.Get(0).Get(2)]
                self.trace_boundary[0] = max(self.trace_boundary[0], abs(start_point[0]))
                self.trace_boundary[1] = max(self.trace_boundary[1], abs(start_point[1]))
                self.trace_boundary[2] = max(self.trace_boundary[2], abs(start_point[2]))
                if ray.vUniqueFaceIds in self.sequence_faces:
                    self.sequences[self.sequence_faces.index(ray.vUniqueFaceIds)].append(ray)
                else:
                    self.sequence_faces.append(ray.vUniqueFaceIds)
                    self.sequence_impacts.append(ray.vImpacts.Size())
                    self.sequences.append([ray])
