import math
import os
from pyoptics.post_process.dpf_base import DataProcessingFramework


class dpf_HDRIViewer(DataProcessingFramework):
    def __init__(self):
        DataProcessingFramework.__init__(self)
        self.souce_list = []

    def Get_SourceList(self, SpeosVRObject):
        if SpeosVRObject is not None:
            total_sources = SpeosVRObject.GetNbSources
            for layer in range(total_sources):
                self.souce_list.append(SpeosVRObject.GetSourceName(layer))
            return (self.souce_list)
        else:
            print("Not valid SpeosVRObject")

    def __valid_dir(self, dir):
        if not os.path.isdir(dir):
            os.makedirs(dir)

    def __export_VRview(self, SpeosVRObject, expo_path, phi_angles=None, theta_angles=None):
        if phi_angles == None and theta_angles == None:
            ## Export all angle combinations
            SpeosVRObject.Show(True)
            SpeosVRObject.ExportAllObserverImages(expo_path + "\\", 0)
        else:
            ## Export angle combinations provided
            for count in range(len(phi_angles)):
                try:
                    SpeosVRObject.SetSightDirection(phi_angles[count], theta_angles[count])
                    SpeosVRObject.Show(True)
                    SpeosVRObject.ExportObserverImage(expo_path + str(math.degrees([phi_angles[count]])) + str(
                        math.degrees([theta_angles[count]])) + ".JPG")
                except Exception as e:
                    print(e)

    def Export_VRViews(self, SpeosVRObject, expo_path, phi_angles=None, theta_angles=None, config_IDs=None):
        self.__valid_dir(expo_path)
        expo_path += "\\"

        if config_IDs == None:
            ## Expor all configurations
            config_IDs = SpeosVRObject.GetNbConfigurations
            for config in range(config_IDs):
                SpeosVRObject.SetConfigurationById(config)
                self.__export_VRview(SpeosVRObject, expo_path, phi_angles, theta_angles)

        elif isinstance(config_IDs, int):
            try:
                SpeosVRObject.SetConfigurationById(config_IDs)
                self.__export_VRview(SpeosVRObject, expo_path, phi_angles, theta_angles)
            except Exception as e:
                print(e)

        elif isinstance(config_IDs, str):
            try:
                SpeosVRObject.SetConfigurationByName(config_IDs)
                self.__export_VRview(SpeosVRObject, expo_path, phi_angles, theta_angles)
            except Exception as e:
                print(e)

        elif isinstance(config_IDs, list):
            for item in config_IDs:
                if isinstance(config_IDs[0], int):
                    try:
                        SpeosVRObject.SetConfigurationById(item)
                        self.__export_VRview(SpeosVRObject, expo_path, phi_angles, theta_angles)
                    except Exception as e:
                        print(e)
                else:
                    try:
                        SpeosVRObject.SetConfigurationByName(item)
                        self.__export_VRview(SpeosVRObject, expo_path, phi_angles, theta_angles)
                    except Exception as e:
                        print(e)

# dpf = dpf_HDRIViewer()
# VR = dpf.OpenFile(r"C:\Users\plu\ANSYS, Inc\EMEA-FES-E - SpeosConverter\Prio B projects\B_19_hrubja2_VOLVO_V317_RCL\Results_PLU\Product1 - TAIL_P1_hor_1.3.SPEOS_CATPART_16.6.2020.TAIL_P1_hor_1.3.LAMPA-TAIL.speos360")
# SouceList = dpf.Get_SourceList(VR)
# export_dir = r"D:\\TTest"
# dpf.Export_VRViews(SpeosVRObject = VR, expo_path = export_dir, config_IDs = 0)