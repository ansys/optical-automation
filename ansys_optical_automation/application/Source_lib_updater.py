# Python Script, API Version = V232
# IronPython Script version : V2.1.0
# Date: 17/06/2025
# © 2012-2023 ANSYS, Inc. All rights reserved. Unauthorized use, distribution, or duplication is prohibited.
# THIS ANSYS SOFTWARE PRODUCT AND PROGRAM DOCUMENTATION INCLUDE TRADE SECRETS AND ARE CONFIDENTIAL AND PROPRIETARY PRODUCTS OF ANSYS, INC., ITS SUBSIDIARIES, OR LICENSORS.
# The software products and documentation are furnished by ANSYS, Inc., its subsidiaries, or affiliates under a software license agreement that contains provisions concerning non-disclosure, copying, length and nature of use, compliance with exporting laws, warranties, disclaimers, limitations of liability, and remedies, and other provisions. 
# The software products and documentation may be used, disclosed, transferred, or copied only in accordance with the terms and conditions of that software license agreement.

import sys
import os
import shutil
from System.IO import Directory

### Inputs ###
path_name = r"D:\Temp\Test_Valeo_source_lib\2023R1"
        
def File_Finder(path_name):
    for dirpath, dirs, files in os.walk(path_name):
        for filename in files:
            fname = os.path.join(dirpath, filename)
            File_updater(fname)

def File_updater(fname):
    if fname.endswith('.scdocx'):
        DocumentOpen.Execute(fname)
        DocumentSave.Execute(fname) 

def Lightbox_inputs():
    rayfile_list = []
    geometry_list = []
    #Axis system
    selection_origin = Selection.Create(GetRootPart().CoordinateSystems[0])
    selection_X = Selection.Create(GetRootPart().CoordinateSystems[0].Axes[0])
    selection_Y = Selection.Create(GetRootPart().CoordinateSystems[0].Axes[1])
    
    # Append all bodies
#    component_list = GetRootPart().GetAllBodies()
#    for i, body_item in enumerate(component_list):
#        geometry_list.append(body_item)
#    selection_geometry = Selection.Create(geometry_list)
 
     # Append bodies under optical properties
    for item in GetRootPart().CustomObjects:
        if "node" in item.Type.ToLower():
            continue
        if "material" in item.Type.ToLower():
            print("material element found", item.GetName())
            obj_name = item.Type.ToString()[25:]
            name = item.GetName()
            global foundmaterial
            foundmaterial = getattr(SpeosSim, obj_name).Find(name)
            print(foundmaterial)
    #material = SpeosSim.Material.Find(foudmaterial)
    material = SpeosSim.Material.Find(name)
    geo_num = material.VolumeGeometries.Count
    selection_geometry = []
    for index in range(geo_num):
        selection_geometry.append(material.VolumeGeometries.Item[index])
     
    # Append all rayfiles
    all_speos = SpeosSim.Command.GetSpeosObjectsInActivePart() 
    for speos_item in all_speos:
        if SpeosSim.SourceRayFile.Find(speos_item.GetName()):
            rayfile_list.append(speos_item)
        if SpeosSim.Material.Find(speos_item.GetName()):
            Material_object = SpeosSim.Material.Find(speos_item.GetName())
            Material_geometries = Material_object.VolumeGeometries.LinkedObjects
    selection_rayfile = Selection.Create(rayfile_list)
    return selection_origin, selection_X, selection_Y, selection_rayfile, selection_geometry

def Lightbox_cleaner():
    for item in GetRootPart().CustomObjects:
        if "node" in item.Type.ToLower():
            continue
        if "component" in item.Type.ToLower():
            print("component element found", item.GetName())
            obj_name = item.Type.ToString()[25:]
            name = item.GetName()
            item.Delete()

def Log_Error_generator(N, filename, error):
    f.writelines(str(filename)+"\n"+str(error)+ "\n"*2)
         
def move_lightbox(project_name):
    OutputFolderPath = SpeosSim.Command.GetOutputFolder()
    LightboxPath = OutputFolderPath+"\\"+project_name+"\\"
    InputFolderPath = SpeosSim.Command.GetInputFolder()
    newPath = InputFolderPath+project_name+"\\"
    for  dirpath, dirs, files in os.walk(LightboxPath):
        for filename in files:
            fname = os.path.join(dirpath, filename)
            if fname.endswith('.SPEOSLightBox'):
                shutil.move(fname, InputFolderPath)
                
def remove_result(project_name):
    OutputFolderPath = SpeosSim.Command.GetOutputFolder()
    LightboxPath = OutputFolderPath+"\\"+project_name+"\\"
    if Directory.Exists(LightboxPath):
        Directory.Delete(LightboxPath, True)
        
### Main ###
myFilePath=os.path.join(path_name, "Log_Error.txt")
with open(myFilePath, "w") as f:
    for dirpath, dirs, files in os.walk(path_name):
        for filename in files:
            fname = os.path.join(dirpath, filename)
            #File_updater(fname)
            if fname.endswith('.scdocx'):
                DocumentOpen.Execute(fname)
                project_name = GetRootPart().GetName()                                ### Lightbox Export Creation ###
                print(project_name)
                #Lightbox_cleaner()
                lightBoxExport = SpeosSim.ComponentExport.Create()
                lightBoxExport.Name = project_name
                selection_origin, selection_X, selection_Y, selection_rayfile, selection_geometry = Lightbox_inputs()
                lightBoxExport.OriginPoint.Set(selection_origin.Items)
                lightBoxExport.XDirection.Set(selection_X.Items)
                lightBoxExport.YDirection.Set(selection_Y.Items)
                lightBoxExport.Sources.Set(selection_rayfile.Items)
                lightBoxExport.Geometries.Set(selection_geometry)
                lightBoxExport.Compute()
                error = lightBoxExport.StatusInfo
                f.writelines(str("File Name: ")+str(filename)+"\n"+str("File Path: ")+str(fname)+"\n"+str(error)+ "\n"*2+"-"*80+"\n")
                DocumentSave.Execute(fname)
                move_lightbox(project_name)
                remove_result(project_name)
                DocumentHelper.CloseDocument()
                
                
