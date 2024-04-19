# Python Script, API Version = V232
import os
import sys

repo_path = os.path.join(os.getenv("appdata"), "SpaceClaim", "Published Scripts")
sys.path.append(repo_path)

import ctypes
from ctypes import c_ulonglong

from ansys_optical_automation.speos_process.speos_hod import HOD

# Acticave Root
result = ComponentHelper.SetRootActive(None)
not_selected = True
# Get UI Selection Input
while not_selected:
    ctypes.windll.user32.MessageBoxW(
        0,
        "Please select a HUD Optical Design feature, then Click [Ok]",
        "HUD Optical Design selection",
        c_ulonglong(4096),
    )
    if len(Selection.GetActive().Items) != 1:
        sys.exit("Canceled")
    if len(Selection.GetActive().Items) == 1:
        selectedHODFeature = Selection.GetActive().Items[0]
        hod_name = selectedHODFeature.GetName()
    if SpeosDes.HUDOD.Find(hod_name) and SpeosDes.HUDOD.Find(hod_name).IsUpToDate:
        not_selected = False
    else:
        print("invalid Selection \nPlease CHeck that you have selected a HOD feature and the HOD feature is uptodate")

dir = os.path.split(GetActivePart().Document.Path)[0]
name = os.path.splitext(os.path.split(GetActivePart().Document.Path)[1])[0]
export_file_path = os.path.join(dir, r"SPEOS output files", name)
current_HOD_system = HOD(hod_name, SpeosDes, SpaceClaim)
current_HOD_system.export_to_zemax(export_file_path, False)
current_HOD_system.export_ws(export_file_path)
