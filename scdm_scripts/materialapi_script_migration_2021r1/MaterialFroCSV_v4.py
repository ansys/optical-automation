# Python Script, API Version = V20 Beta
########## !!!!!!!!!!!!!!!!!!!!!! ############
#### pleace start your folder with a "0" #####


import SPEOS_SC.SIM.Automation as SpeosAutomation
import csv

def GetRealOrigianl(item):
    result = item
    while result.GetOriginal():
        result = result.GetOriginal()
    return result


def Create_Dictionary():
    Dic = {}
    All_body = GetRootPart().GetAllBodies()
    for ibody in All_body:
        body = GetRealOrigianl(ibody)
        try: 
            if body.Material.Name not in Dic:
                Dic.update({body.Material.Name:List[IDesignBody]()})
            Dic[body.Material.Name].Add(ibody)
        except:
            "Do nothing"
    return Dic


def Apply_Geo_to_Material():
    OP_List = {}
    All_OP = GetRootPart().CustomObjects
    for item in All_OP:
        OP_List.update({item.GetName():List[IDesignBody]()})
    
    Dic = Create_Dictionary()
    for item in Dic:
        if item in OP_List:
            OP = Selection.CreateByNames(item).Items[0]
            try:
                OP = clr.Convert(OP, SpeosAutomation.OpticalProperties)
                mysel = Selection.Create(Dic[item])
                OP.SelectGeometries(mysel)
            except:
                "Wrong"
        else:
            OP_Created=SpeosAutomation.OpticalProperties.Create(None)
            OP_Created.OpticalPropertyName=item
            sel = Selection.Create(Dic[item])
            OP_Created.SelectGeometries(sel)
    
def Get_Total_Layers():
    Layer_List = []
    ActiveDoc = DocumentHelper.GetActiveDocument()
    Total_Layer = ActiveDoc.Layers
    for layer in Total_Layer:
        Layer_List.append(layer.GetName())
    return Layer_List


def Apply_Geo_to_Layer(): 
    Layer_List = Get_Total_Layers()
    Geo_Dic = Create_Dictionary()
    
    for item in Geo_Dic:
        sel = Selection.Create(Geo_Dic[item])
        if item in Layer_List:
            Layers.MoveTo(sel, item)
        else:
            CreateLayer(item)
            Layer_List.append(item)
            Layers.MoveTo(sel, item)
            

def CreateLayer(OP_Name):
    ActiveDoc = DocumentHelper.GetActiveDocument()
    nb_layer = ActiveDoc.Layers.Count
    ActiveDoc.Layers[nb_layer-1].Create(ActiveDoc, OP_Name, Color.Empty)

def create_SPEOSMaterial(CSV, work_directory):
    # work_directory  = "D:\#ANSYS SPEOS_Concept Proof\API Scripts\ASP_MaterialFromCsv"
    with open(CSV) as myfile:
        reader = csv.reader(myfile)
        for line in reader:
            if ("End" not in line) and ("Materialname" not in line):
                OP_Name = line[0].rstrip()
                FOP_Name = line[1]
                VOP_Name = line[2]
                SOP_Name = line[3]
                CreateLayer(OP_Name)
                
                
                if FOP_Name == "True": #check only SOP
                    OP_Created=SpeosAutomation.OpticalProperties.Create(None)
                    OP_Created.OpticalPropertyName= OP_Name
        
                    if "Mirror" in SOP_Name: 
                        Start = SOP_Name.find("Mirror")+6
                        Value = SOP_Name[Start:]
                        print Value
                        Value = int(Value)
                        OP_Created.SetMirrorFaceOpticalProperties(Value)
                    elif "Optical Polished" in SOP_Name:
                        OP_Created.SetOpticalPolishedFaceOpticalProperties()
                    else:
                        OP_Created.SetLibraryFaceOpticalProperties(work_directory + "SPEOS input files\\" + SOP_Name)
                
                else:
                    if "Opaque" in VOP_Name:
                        OP_Created=SpeosAutomation.OpticalProperties.Create(None)
                        OP_Created.OpticalPropertyName= OP_Name
            
                        if "Mirror" in SOP_Name: 
                            Start = SOP_Name.find("Mirror")+6
                            Value = SOP_Name[Start:]
                            print Value
                            Value = int(Value)
                            OP_Created.SetMirrorFaceOpticalProperties(Value)
                            OP_Created.SetOpaqueVolumeOpticalProperties()
                        elif "Optical Polished" in SOP_Name:
                            OP_Created.SetOpticalPolishedFaceOpticalProperties()
                            OP_Created.SetOpaqueVolumeOpticalProperties()
                        else:
                            OP_Created.SetLibraryFaceOpticalProperties(work_directory + "SPEOS input files\\" + SOP_Name)
                            OP_Created.SetOpaqueVolumeOpticalProperties()
                            
                    elif "Optic" in VOP_Name:
                        OP_Created=SpeosAutomation.OpticalProperties.Create(None)
                        OP_Created.OpticalPropertyName= OP_Name
                        HasContringence=False
            
                        if "Mirror" in SOP_Name: 
                            Start = SOP_Name.find("Mirror")+6
                            Value = SOP_Name[Start:]
                            print Value
                            Value = int(Value)
                            OP_Created.SetMirrorFaceOpticalProperties(Value)
                            OP_Created.SetOpticVolumeOpticalProperties(1.5,0,HasContringence,0)
                        elif "Optical Polished" in SOP_Name:
                            OP_Created.SetOpticalPolishedFaceOpticalProperties()
                            OP_Created.SetOpticVolumeOpticalProperties(1.5,0,HasContringence,0)
                        else:
                            OP_Created.SetLibraryFaceOpticalProperties(work_directory + "SPEOS input files\\" + SOP_Name)
                            OP_Created.SetOpticVolumeOpticalProperties(1.5,0,HasContringence,0)
        
                    else:
                        OP_Created=SpeosAutomation.OpticalProperties.Create(None)
                        OP_Created.OpticalPropertyName= OP_Name
            
                        if "Mirror" in SOP_Name: 
                            Start = SOP_Name.find("Mirror")+6
                            Value = SOP_Name[Start:]
                            print Value
                            Value = int(Value)
                            OP_Created.SetMirrorFaceOpticalProperties(Value)
                            OP_Created.SetLibraryVolumeOpticalProperties(work_directory + "SPEOS input files\\" + VOP_Name)
                        elif "Optical Polished" in SOP_Name:
                            OP_Created.SetOpticalPolishedFaceOpticalProperties()
                            OP_Created.SetLibraryVolumeOpticalProperties(work_directory + "SPEOS input files\\" + VOP_Name)
                        else:
                            OP_Created.SetLibraryFaceOpticalProperties(SOP_Name)
                            OP_Created.SetLibraryVolumeOpticalProperties(work_directory + "SPEOS input files\\" + VOP_Name)


create_SPEOSMaterial("D:\#ANSYS SPEOS_Concept Proof\API Scripts\ASP_MaterialFromCsv\Materials.csv", "D:\#ANSYS SPEOS_Concept Proof\API Scripts\ASP_MaterialFromCsv")
#Apply_Geo_to_Material()
#Apply_Geo_to_Layer()