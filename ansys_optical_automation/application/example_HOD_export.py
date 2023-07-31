# Python Script, API Version = V21
import sys

repo_path = r"D:\Work\Gitdir\Optical-automation"
sys.path.append(repo_path)
from ansys_optical_automation.speos_process.speos_hod import HOD

hod_name = "HUD A"
export_file_name = r"C:\temp"

current_HOD_system = HOD(hod_name, SpeosDes, SpaceClaim)
current_HOD_system.export_to_zemax(export_file_name, True)
