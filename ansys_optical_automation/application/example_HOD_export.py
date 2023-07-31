# Python Script, API Version = V21
# import sys
# repo_path=r"your repository location"
# sys.path.append(repo_path
import os

from ansys_optical_automation.speos_process.speos_hod import HOD

input_data = InputHelper.CreateTextBox("HUD A", "Name of HUD Design:", "Type name of HUD Design")
InputHelper.PauseAndGetInput("Enter the HUD design name", input_data)
export_file_name = os.path.split(GetActivePart().Document.Path)[0]
hod_name = input_data.Value
current_HOD_system = HOD(hod_name, SpeosDes, SpaceClaim)
current_HOD_system.export_to_zemax(export_file_name, True)
