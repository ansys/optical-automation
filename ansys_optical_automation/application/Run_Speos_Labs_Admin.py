"""
Requirements: administrative privileges.
-----------------------------------------------------------------------
This module launches with administrator privileges all executables in:
`C:\\Program Files\\ANSYS Inc\\vXXX\\Optical Products\\Viewers`

Many users lack administrative rights, so this module can be executed right after the installation
while the user still has admin rights.

Upon launching each application, the module registers the associated COM server used to call each application, 
with the path to each executable appropriately registered.

Classes and Main Methods
-----------------------------------------------------------------------
1. **SpeosPathFinder**
   - This class provides two methods to locate the Speos application path:
      - A method to search for a specific Speos version Path.
      - A default method that identifies and returns the latest installed version of Speos.

2. **LabsAdmin**
   - This class offers methods to open or close one or multiple applications simultaneously.
   - By default, if no specific applications are specified, it will launch all applications found.

"""

import subprocess, os, time, sys

# If pygetwindow is not installed, do it
third_party_package = "pygetwindow"
try: 
    gw =  __import__(third_party_package)
    print(f"{third_party_package} is already installed.")
except ImportError:
    print(f"{third_party_package} not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", third_party_package])
    import pygetwindow as gw

class SpeosPathFinder:
    '''
    Class to find the environmental variable to Speos installation.
    There are two methds:
    - find_latest_awp_root --> Finds the environmental variable for
    last version of Speos.
    - get_custom_awp_root --> Finds the environmental variable for
    a specific version of Speos.
    '''
    def __init__(self):
        self.last_version = "000"
        self.version = "000"
    def find_latest_awp_root(self):
        # Find the last version of AWP_ROOT in the environmental variables
        for key, value in os.environ.items():
            if "AWP_ROOT" in key and key.split("AWP_ROOT")[1] > self.last_version:
                self.last_version = key.split("AWP_ROOT")[1]
        # Build environmental variable
        ThreeDigitCode = self.last_version
        return ThreeDigitCode

class LabsAdmin:
    '''
    Class with methods to:
    - Run one specific application.
    - Kill one specific application.
    - Run all applications as admin.
    - Kill all applications.
    - Run and Kill one application.
    - Run and Kill all applications.
    '''
    def __init__(self, ThreeDigitCode = SpeosPathFinder().find_latest_awp_root()):
        self.ThreeDigitCode = ThreeDigitCode
        self.Path_Installation_Root = os.environ.get("AWP_ROOT" + self.ThreeDigitCode,"")
    def RunSingleApp(self, exe_name):
        # Execute only one application
        exe_path = os.path.join(self.Path_Installation_Root, 'Optical Products', 'Viewers', exe_name)
        print("Application Executed: " + exe_path)
        subprocess.Popen(["powershell", "-Command", f"Start-Process '{exe_path}' -Verb RunAs"])
    def RunAll(self):
        # Run as Admin All Apps
        print("\n\n#### Run all Viewer as admin STARTED: \n")
        Dictionary_Labs = self.Applications()
        PathToViewers = os.path.join(self.ThreeDigitCode, 'Optical Products', 'Viewers')
        for App in Dictionary_Labs.keys():
            self.RunSingleApp(os.path.join(self.Path_Installation_Root, 'Optical Products', 'Viewers', App))
    def Applications(self):
        # Check if Speos_Root has enough characters
        if len(self.ThreeDigitCode) != 3:
            raise ValueError("\n\nThe code must be of 3 characters long to derive the version.")
        self.Version = "20" + self.ThreeDigitCode[0] + self.ThreeDigitCode[1] + " R" + self.ThreeDigitCode[2]
        self.Version = "20" + self.ThreeDigitCode[0] + self.ThreeDigitCode[1] + " R" + self.ThreeDigitCode[2]
        # Dictonary with the name of the file and the title once opened
        self.Labs_Applications = {
            "XmpViewer.exe": "Speos " + self.Version + " - Extended map [No Name]",
            "VRLab.exe": "Speos " + self.Version + " - Empty view",
            "Xm3Viewer.exe": "Speos " + self.Version + " - Virtual 3D Photometric Lab [No file loaded]",
            "VisionLabViewer.exe": "Speos " + self.Version + " - Spectral map [No Name]",
            "TextureMappingViewer.exe": "Texture Mapping Viewer",
            "VMPViewer.exe": "Speos " + self.Version + " - 3D Energy Density Lab [No Name]",
            "SimpleScatteringViewer.exe": "Speos " + self.Version + " - Scattering surface [No Name]",
            "VPLab.exe": "Speos " + self.Version + " - Photometric Calc",
            "SPEOSCore.exe": "Speos Core " + self.Version,
            "SpectrumViewer.exe": "Speos " + self.Version + " - Spectrum [No Name]",
            "RoughMirrorViewer.exe": "Speos " + self.Version + " - Mirror surface [No Name]",
            "FluorescentSurfaceViewer.exe": "Speos " + self.Version + " - Fluorescent surface [No Name]",
            "BSDF_BRDF_Anisotropic_Viewer.exe": "Speos " + self.Version + " - Bsdf surface [No Name]",
            "PolarizerSurfaceEditor.exe": "Speos " + self.Version + " - Polarizer surface [No Name]",
            "RetroReflectingSurfaceViewer.exe": "Speos " + self.Version + " - Retro-reflecting surface [No Name]",
            "IESViewer.exe": "Speos " + self.Version + " - Iesna LM-63 []",
            "CoatedSurfaceViewer.exe": "Speos " + self.Version + " - Coated surface [No Name]",
            "EulumdatViewer.exe": "Speos " + self.Version + " - Eulumdat [No Name]",
            "VirtualLightingAnimation.exe": "Virtual Lighting Animation [BETA] " + self.Version,
            "AdvancedScatteringViewer.exe": "Speos " + self.Version + " - Scattering surface (Advanced model) [No Name]",
            "DoeSurfaceViewer.exe": "Speos " + self.Version + " - Thin lens surface [No Name]",
            "GratingSurfaceViewer.exe": "Speos " + self.Version + " - Grating surface [No Name]",
            "RayEditor.exe": "Speos " + self.Version + " -  [No Name]",
            "UserMaterialViewer.exe": "Speos " + self.Version + " - User Material (Advanced Model) [No Name]"
        }
        return self.Labs_Applications
    def KillApp(self, exe_name):
        Dictionary_Labs = self.Applications()
        open_windows = gw.getAllTitles()
        app_opened = False
        Expected_title = Dictionary_Labs[exe_name]
        while not app_opened:
            # List all open applications
            open_windows = gw.getAllTitles()
            # print(open_windows)
            Expected_title = Dictionary_Labs[exe_name]
            for title in open_windows:
                if Expected_title in title:
                    app_opened = True
                    print("Trying to find: " + exe_name)
                    subprocess.run(["taskkill", "/f", "/im", exe_name])
                    break
            time.sleep(0.2)
    def KillAll(self):
        # Kill all Labs App
        Dictionary_Labs = self.Applications()
        print("\n\n#### Kill all process: \n")
        for App in Dictionary_Labs.keys():
            self.KillApp(App)
    def RunAndKillApp(self, exe_name):
        self.RunSingleApp(exe_name)
        self.KillApp(exe_name)
    def RunAndKillAll(self):
        self.RunAll()
        self.KillAll()

try:
    LabsAdmin().RunAndKillAll()
except Exception as err:
    print("Unexpected "+str(err)+", "+str(type(err)))