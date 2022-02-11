import win32com.client as win32
import os


class DataProcessingFramework:
    def __init__(self):
        print("init dpf class")

    def OpenFile(self, str_path):
        if os.path.isfile(str_path):
            if str_path.lower().endswith(('.optisvr', '.speos360')):
                VR = win32.Dispatch("HDRIViewer.Application")
                if VR.OpenFile(str_path):
                    return VR
                print("no such speos360 file found")
                return None
            elif str_path.lower().endswith('.xmp'):
                XMP = win32.Dispatch("HDRIViewer.Application")
                if XMP.OpenFile(str_path):
                    return XMP
                print("no such xmp file found")
                return None
        else:
            print("no such file found")


