# Python Script, API Version = V241
# # (c) 2024 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited. ANSYS Confidential Information
#
# '''
# THIS ANSYS SOFTWARE PRODUCT AND PROGRAM DOCUMENTATION INCLUDE TRADE SECRETS AND ARE CONFIDENTIAL AND
# PROPRIETARY PRODUCTS OF ANSYS, INC., ITS SUBSIDIARIES, OR LICENSORS.  The software products and documentation
# are furnished by ANSYS, Inc., its subsidiaries, or affiliates under a software license agreement that contains
# provisions concerning non-disclosure, copying, length and nature of use, compliance with exporting laws, warranties,
# disclaimers, limitations of liability, and remedies, and other provisions.  The software products and documentation
# may be used, disclosed, transferred, or copied only in accordance with the terms and conditions of that software
# license agreement.
# '''
import os
import signal
import time

from System import Activator
from System import Type

# import sys


yml_path = args[0]


def extract_parameters_from_yml(yml_path):
    param = {}  # Dictionary to store parameter chains
    try:
        with open(yml_path, "r") as file:
            for line in file:
                if ":" in line:  # Checking if the line contains ":"
                    key, value = line.split(":", 1)  # Splitting line into key and value
                    key = key.strip()  # Removing leading and trailing whitespace from key
                    value = value.strip()  # Removing leading and trailing whitespace from value
                    if key in param:  # Check if the key already exists in the dictionary
                        if isinstance(param[key], list):  # If the value is already a list
                            param[key].append(value)  # Append value to the list
                        else:  # If the value is not a list, convert it to a list
                            param[key] = [parameters[key], value]
                    else:  # If the key doesn't exist, create a new key-value pair
                        param[key] = value
    except IOError:
        print("Error: File not found or could not be opened.")
    return param


def import_project(param):
    # Open Speos project
    Ansys_SPEOS_file = r"" + str(param.get("Scdocx Path"))
    print(Ansys_SPEOS_file)
    importOptions = ImportOptions.Create()
    DocumentOpen.Execute(Ansys_SPEOS_file, importOptions)


def XMP_processing(param, index):
    # Parameters extraction
    sensor_name = param.get("Sensor Name")
    sim_name = param.get("Simulation Name")
    xml = param.get("XMP Template Path")

    DirectoryPath = param.get("Working Directory")
    OutputFolderPath = SpeosSim.Command.GetOutputFolder()  # Path to SPEOS Output Files folder
    # repertorypath = os.path.dirname(GetRootPart().Document.Path)  # Get document path
    docname = os.path.basename(GetRootPart().Document.Path)  # get document's name with extension
    docname = os.path.splitext(docname)[0]  # Document's name without extension

    xmpViewerType = Type.GetTypeFromProgID("XMPViewer.Application")  # Start COM communication
    XMPViewer = Activator.CreateInstance(xmpViewerType)  # Start XmpViewer.exe instance in background

    XMPPath = OutputFolderPath + "\\" + docname + "\\" + sim_name + "." + sensor_name + ".Exposure.xmp"
    XMPViewer.OpenFile(r"" + str(XMPPath))  # open irradiance map
    TemplateFile = r"" + xml
    XMPViewer.ImportTemplate(TemplateFile, 1, 1, 0)

    keep_XMP = param.get("Keep XMP")
    keep_PNG = param.get("Keep PNG")
    if keep_XMP.lower() == "yes":
        ExportedXMPPath = DirectoryPath + "\\" + str(index) + ".xmp"
        XMPViewer.SaveFile(ExportedXMPPath)
    else:
        pass
    if keep_PNG.lower() == "yes":
        ExportedImagePath = DirectoryPath + "\\" + str(index) + ".png"
        XMPViewer.ExportXMPImage(ExportedImagePath, 1)  # Export PNG image
    else:
        pass
    RetVal = XMPViewer.GetPID()  # get process id
    os.kill(RetVal, signal.SIGBREAK)  # kill process


def Simloop(param):
    start_time = float(param.get("Start Time (in s)"))
    index = 0
    end_time = float(param.get("End Time (in s)"))
    fps = float(param.get("Frame Per Second"))
    SimName = str(param.get("Simulation Name"))
    SimMode = str(param.get("Computation Mode"))
    if SimMode.lower() == "cpu":
        while start_time <= end_time:
            Sim = SpeosSim.SimulationInverse.Find(SimName)
            Sim.TimelineStart = float(start_time)
            Sim.Compute()
            time.sleep(3)
            XMP_processing(param, index)
            index += 1
            start_time += 1 / fps
            print(start_time)
    elif SimMode.lower() == "gpu":
        while start_time <= end_time:
            Sim = SpeosSim.SimulationInverse.Find(SimName)
            Sim.TimelineStart = float(start_time)
            Sim.GpuCompute()
            time.sleep(3)
            XMP_processing(param, index)
            index += 1
            start_time += 1 / fps
            print(start_time)
    else:
        while start_time <= end_time:
            Sim = SpeosSim.SimulationInverse.Find(SimName)
            Sim.TimelineStart = float(start_time)
            Sim.Compute()
            time.sleep(3)
            XMP_processing(param, index)
            index += 1
            start_time += 1 / fps
            print(start_time)


def Done(param):
    Donefile = param.get("Working Directory") + "Done.txt"
    with open(Donefile, "w") as f:
        f.write("Animation_Maker_yml process done.")


# Get Animation parameters from yaml file
param = extract_parameters_from_yml(yml_path)
import_project(param)
Simloop(param)
Done(param)
