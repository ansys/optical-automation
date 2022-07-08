import math

from ansys_optical_automation.post_process.dpf_base import DataProcessingFramework


class DpfHdriViewer(DataProcessingFramework):
    """
    Provides for launching Speos postprocessing software, Virtual reality lab.

    This framework is used to interact with the software and automatically perform
    analysis and postprocessing on the simulation results
    """

    def __init__(self):
        """Initialize DPF as HDRIViewer."""
        DataProcessingFramework.__init__(
            self, application="HDRIViewer.Application", extension=(".speos360", ".optisvr", ".xmp")
        )
        self.source_list = []

    def get_source_list(self):
        """
        Get the source list stored in the simulation result.

        Returns
        -------
        list
            List of sources available in the postprocessing file.
        """
        if self.dpf_instance is not None:
            total_sources = self.dpf_instance.GetNbSources
            for layer in range(total_sources):
                self.source_list.append(self.dpf_instance.GetSourceName(layer))
            return self.source_list
        else:
            raise ImportError("Object is not a valid SpeosVRObject.")

    def __export_vr_view(self, export_path, phi_angles=None, theta_angles=None):
        """
        Export VR results for defined angles or all angles as image (JPG) files.

        Parameters
        ----------
        export_path : string
            Path for exporting the set of JPG files. If this path does not exist,
            it is created.
        phi_angles : list of floats, optional
            List of phi angles to export. The default is ``None``, in which case
            all phi angles are exported.
        theta_angles : list of floats, optional
            List of theta angles to export. The default is ``None``, in which case
            all theta angles are exported.
        """
        if phi_angles is None and theta_angles is None:
            "Export all angle combinations"
            self.dpf_instance.Show(True)
            self.dpf_instance.ExportAllObserverImages(export_path + "\\", 0)
        else:
            "Export angle combinations provided"
            for count in range(len(phi_angles)):
                try:
                    self.dpf_instance.SetSightDirection(phi_angles[count], theta_angles[count])
                    self.dpf_instance.Show(True)
                    self.dpf_instance.ExportObserverImage(
                        export_path
                        + str(math.degrees([phi_angles[count]]))
                        + str(math.degrees([theta_angles[count]]))
                        + ".JPG"
                    )
                except Exception as e:
                    raise TypeError(
                        str(phi_angles) + str(theta_angles) + " are not existing iin the file \n Details: " + e
                    )

    def export_vr_views(self, export_path, phi_angles=None, theta_angles=None, config_ids=None):
        """
        Export VR results for all or specific configurations for defined angles or all angles as image (JPG) files.

        Parameters
        ----------
        export_path : string
            Path for exporting the JPG files. If this path does not exist,
            it is created.
        phi_angles : list of floats, optional
            List of phi angles to export. The default is ``None``, in which case
            all phi angles are exported.
        theta_angles : list of floats, optional
            List of theta angles to export. The default is ``None``, in which case
            all theta angles are exported.      
        config_ids : list of positive integers or list of strings or a string or an integer, optional
            List of configurations IDs to export. The default is ``None``, in which case all configuration
            IDs are exported.
        """
        self.valid_dir(export_path)
        export_path += "\\"

        if config_ids is None:
            "Export all configurations"
            config_ids = self.dpf_instance.GetNbConfigurations
            for config in range(config_ids):
                self.dpf_instance.SetConfigurationById(config)
                self.__export_vr_view(export_path, phi_angles, theta_angles)

        elif isinstance(config_ids, int):
            try:
                self.dpf_instance.SetConfigurationById(config_ids)
                self.__export_vr_view(export_path, phi_angles, theta_angles)
            except Exception as e:
                raise ValueError(str(config_ids) + " a non valid ID exists in the file \n Details: " + e)

        elif isinstance(config_ids, str):
            try:
                self.dpf_instance.SetConfigurationByName(config_ids)
                self.__export_vr_view(export_path, phi_angles, theta_angles)
            except Exception as e:
                raise ValueError(config_ids + " does not exist in the file \n Details: " + e)

        elif isinstance(config_ids, list):
            for item in config_ids:
                if isinstance(config_ids[0], int):
                    try:
                        self.dpf_instance.SetConfigurationById(item)
                        self.__export_vr_view(export_path, phi_angles, theta_angles)
                    except Exception as e:
                        raise ValueError(str(item) + " a non valid ID exists in the file \n Details: " + e)
                else:
                    try:
                        self.dpf_instance.SetConfigurationByName(item)
                        self.__export_vr_view(export_path, phi_angles, theta_angles)
                    except Exception as e:
                        raise ValueError(item + " does not exist in the file \n Details: " + e)
