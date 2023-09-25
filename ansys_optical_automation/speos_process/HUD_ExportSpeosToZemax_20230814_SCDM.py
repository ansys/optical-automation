# Copyright <2023> <ANSYS, INC>
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Python Script, API Version = V232
# Original Code : MGE
# Change Note 8/14/23 HYI

#Speos Script Limitation:
#Global Axis : X should be car direction, and Z is zenith direcion.
#HUD Design feature should have 1 Freeform, 1 Fold and 1 PGU.
#User needs to edit the bat file to get results.
#(Path for files, and the name of the HUD design feature)

import os
import math
import ctypes

#Acticave Root
result = ComponentHelper.SetRootActive(None)

#Get UI Selection Input
ctypes.windll.user32.MessageBoxW(0, "Please select a HUD Optical Design feature, then Click [Ok]", "HUD Optical Design selection", 0x00001000L)
if len(Selection.GetActive().Items) != 1: sys.exit('Canceled')
if len(Selection.GetActive().Items) == 1:    
    selectedHODFeature = Selection.GetActive().Items[0]                
    selectedHODFeatureName = selectedHODFeature.GetName()
    
hud_OpticalDesign = SpeosDes.HUDOD.Find(selectedHODFeatureName)
#Get File path
Dir = DocumentHelper.GetActiveDocument().Path
Output_Dir = Dir[:Dir.rfind("\\")]+ "\\SPEOS output files\\" + Dir[Dir.rfind("\\")+1:Dir.rfind(".")] + "\\"

#List for txt output
hUDOpticalDesign = SpeosDes.HUDOD.Find(selectedHODFeatureName)
lines = [str (hUDOpticalDesign.EyeboxOrientationType), str (hUDOpticalDesign.EBHorizontalSize), str (hUDOpticalDesign.EBHorizontalSampling), 
str (hUDOpticalDesign.EBVerticalSize), str (hUDOpticalDesign.EBVerticalSampling), str (hUDOpticalDesign.EyeboxConfigPositionDirectionType), 
str (hUDOpticalDesign.TIVirtualImageDistance), str (hUDOpticalDesign.TILookOverAngle), str(hUDOpticalDesign.TILookDownAngle), 
str (hUDOpticalDesign.TargetImageModeType), str (hUDOpticalDesign.TIHorizontalFOV), str (hUDOpticalDesign.TIVerticalFOV), 
str (hUDOpticalDesign.PGUHorizontalSampling), str (hUDOpticalDesign.PGUVerticalSampling), 
str (hUDOpticalDesign.PGUHorizontalSize), str (hUDOpticalDesign.PGUVerticalSize), str (hUDOpticalDesign.PGUHorizontalResolution), 
str (hUDOpticalDesign.PGUVerticalResolution), str (hUDOpticalDesign.ManufacturingX), str (hUDOpticalDesign.ManufacturingY)]

#Choose Surface/Lines based on the Input
#SurfaceBodies[0]=Freeform
#SurfaceBodies[1]=Fold
#SurfaceBodies[2]=PGU
#PolyLines[0]=Optical Axis_0
#PolyLines[1]=Optical Axis_1
#PolyLines[2]=Optical Axis_2
#PolyLines[3]=Optical Axis_3
Inputchecks=0
Inputcheckl=0
SurfaceBodies = []
for body in GetActivePart().Bodies:    
        if body.GetName().__contains__(selectedHODFeatureName) and body.GetName().__contains__("Freeform"):
            SurfaceBodies.append(body)
            Inputchecks += 1
            break
for body in GetActivePart().Bodies:    
        if body.GetName().__contains__(selectedHODFeatureName) and body.GetName().__contains__("Fold"):
            SurfaceBodies.append(body)
            Inputchecks += 1
            break
for body in GetActivePart().Bodies:    
        if body.GetName().__contains__(selectedHODFeatureName) and body.GetName().__contains__("PGU"):
            SurfaceBodies.append(body)
            Inputchecks += 1
            break
PolyLines = []
for curve in GetActivePart().Curves:
    if curve.GetName().__contains__("Optical Axis_0") and curve.GetName().__contains__(selectedHODFeatureName):
        PolyLines.append(curve)
        Inputcheckl += 1
        break
for curve in GetActivePart().Curves:
    if curve.GetName().__contains__("Optical Axis_1") and curve.GetName().__contains__(selectedHODFeatureName):
        PolyLines.append(curve)
        Inputcheckl += 1
        break
for curve in GetActivePart().Curves:
    if curve.GetName().__contains__("Optical Axis_2") and curve.GetName().__contains__(selectedHODFeatureName):
        PolyLines.append(curve)
        Inputcheckl += 1
        break
for curve in GetActivePart().Curves:
    if curve.GetName().__contains__("Optical Axis_3") and curve.GetName().__contains__(selectedHODFeatureName):
        PolyLines.append(curve)
        Inputcheckl += 1
        break
if (Inputchecks != 3): sys.exit('Canceled')
if (Inputcheckl != 4): sys.exit('Canceled')

#Extract Optical Axis coordinates and Mirror boundaries
Edgesprev = Selection.CreateByObjects(SurfaceBodies).ConvertToEdges()
Curvesprev = Selection.CreateByObjects(PolyLines).ConvertToCurves()
Edges = Selection.CreateByObjects(SurfaceBodies).ConvertToEdges()
Curves = Selection.CreateByObjects(PolyLines).ConvertToCurves()
n=0
o=0

# Create New Part for Visual Check
result = ComponentHelper.SetRootActive(None)
selection = PartSelection.Create(GetRootPart())
result = ComponentHelper.CreateNewComponent(selection, None)

# Refence Math Functions
def length_squared(u):
    return sum([a ** 2 for a in u])

def length(u):
    return math.sqrt(length_squared(u))

def add(u, v):    
    return [a + b for a, b in zip(u, v)]

#Select 3 points for 1 Surface#
#ExtPtsST=Start Point of Edge
#ExtPtsEND=End Point of Edge
#ExtPts3for1 = (3 points from one surface) * (3 surfaces)
ExtPtsST=[]
ExtPtsEND=[]
number_Exp_PT=0
for i in Edges:
    ExtPtsST.append(i.StartPoint.Position)
    ExtPtsEND.append(i.EndPoint.Position)
    number_Exp_PT += 1
facecount = 0
pointcount =0
totalfindcount=0
ExtPts3for1=[]
while facecount < 3:
    pointcount=0
    findcount=0
    while pointcount <= 3:
        numberinExtPT=pointcount + facecount * 4
        if pointcount == 0:
            ExtPts3for1.append(ExtPtsST[numberinExtPT])
            findcount += 1
            totalfindcount += 1
            pointcount += 1
        if ExtPts3for1[totalfindcount-1] == ExtPtsST[numberinExtPT+1]:
            ExtPts3for1.append(ExtPtsEND[numberinExtPT+1])
            findcount += 1
            totalfindcount += 1
            pointcount += 1
        elif ExtPts3for1[totalfindcount-1] == ExtPtsEND[numberinExtPT+1]:
            ExtPts3for1.append(ExtPtsST[numberinExtPT+1])
            findcount += 1
            totalfindcount += 1
            pointcount += 1
        if ExtPts3for1[totalfindcount-1] != ExtPtsEND[numberinExtPT+1] and ExtPts3for1[totalfindcount-1] != ExtPtsST[numberinExtPT+1]:
            if findcount < 3:
                ExtPts3for1.append(ExtPtsST[numberinExtPT+1])
                findcount += 1
                totalfindcount += 1
            if findcount < 3:
                ExtPts3for1.append(ExtPtsEND[numberinExtPT+1])
                findcount += 1
                totalfindcount += 1
            pointcount += 1
        if findcount>=3:
            break
    facecount += 1
     
#Select 2 PTS(for Horzontal Vector) for 1 Surface
#Assumption : Horizotal lenght is longer than vertical lengh.
#H(Smaller y) is hpoints[0], H(Larger y) is hpoints[1] for Freeform
#H(Smaller y) is hpoints[2], H(Larger y) is hpoints[3] for Fold
#H(Smaller y) is hpoints[4], H(Larger y) is hpoints[5] for PGU
lengthcheck=0
hpoints=[]
while lengthcheck<3:
    lengthindex=lengthcheck*3
    length01=length(ExtPts3for1[lengthindex]-ExtPts3for1[lengthindex+1])
    length12=length(ExtPts3for1[lengthindex+1]-ExtPts3for1[lengthindex+2])
    length20=length(ExtPts3for1[lengthindex+2]-ExtPts3for1[lengthindex])
    lenggthset=[length01,length12,length20]
    lengsetsort=sorted(lenggthset)
    if lengsetsort[1]==length01:
        if (ExtPts3for1[lengthindex])[1] < (ExtPts3for1[lengthindex+1])[1]:
            hpoints.append(ExtPts3for1[lengthindex])
            hpoints.append(ExtPts3for1[lengthindex+1])
        else:
            hpoints.append(ExtPts3for1[lengthindex+1])
            hpoints.append(ExtPts3for1[lengthindex])
    elif lengsetsort[1]==length12:
        if (ExtPts3for1[lengthindex+1])[1] < (ExtPts3for1[lengthindex+2])[1]:
            hpoints.append(ExtPts3for1[lengthindex+1])
            hpoints.append(ExtPts3for1[lengthindex+2])
        else:
            hpoints.append(ExtPts3for1[lengthindex+2])
            hpoints.append(ExtPts3for1[lengthindex+1])
    elif lengsetsort[1]==length20:
        if (ExtPts3for1[lengthindex+2])[1] < (ExtPts3for1[lengthindex])[1]:
            hpoints.append(ExtPts3for1[lengthindex+2])
            hpoints.append(ExtPts3for1[lengthindex])
        else:
            hpoints.append(ExtPts3for1[lengthindex])
            hpoints.append(ExtPts3for1[lengthindex+2])
    lengthcheck += 1
    
#Get Normals from edge points of surfaces
#Only NVS[2](Normal for PGU) will be used
#NVS[0], NVS[1] will be ignored, and normals for those will be calculated based on polyline(optical axes).
NVS=[]
if (Vector.Cross(ExtPts3for1[1]-ExtPts3for1[0], ExtPts3for1[2]-ExtPts3for1[0]))[0] >= 0:
    NVS.append(Vector.Cross(ExtPts3for1[1]-ExtPts3for1[0], ExtPts3for1[2]-ExtPts3for1[0]))
else:
    NVS.append(-Vector.Cross(ExtPts3for1[1]-ExtPts3for1[0], ExtPts3for1[2]-ExtPts3for1[0]))
if (Vector.Cross(ExtPts3for1[4]-ExtPts3for1[3], ExtPts3for1[5]-ExtPts3for1[3]))[0] < 0:
    NVS.append(Vector.Cross(ExtPts3for1[4]-ExtPts3for1[3], ExtPts3for1[5]-ExtPts3for1[3]))
else:
    NVS.append(-Vector.Cross(ExtPts3for1[4]-ExtPts3for1[3], ExtPts3for1[5]-ExtPts3for1[3]))
if (Vector.Cross(ExtPts3for1[7]-ExtPts3for1[6], ExtPts3for1[8]-ExtPts3for1[6]))[0] >= 0:
    NVS.append(Vector.Cross(ExtPts3for1[7]-ExtPts3for1[6], ExtPts3for1[8]-ExtPts3for1[6]))
else:
    NVS.append(-Vector.Cross(ExtPts3for1[7]-ExtPts3for1[6], ExtPts3for1[8]-ExtPts3for1[6]))

#Get Normals(Unit) from polyline(optical axes) wirh PGU from the Surface
#NVP[0](Normal for Freefrom) from Polyline
#NVP[1](Normal for Freefrom) from Polyline
#NVP[2] from NVS[2](Normal for PGU)
clinecount=0
PtsfromPoly=[]
for i in Curves:
    PtsfromPoly.append(i.EndPoint.Position)
    clinecount += 1
nPoly01=(PtsfromPoly[0]-PtsfromPoly[1])/length(PtsfromPoly[0]-PtsfromPoly[1])
nPoly12=(PtsfromPoly[1]-PtsfromPoly[2])/length(PtsfromPoly[1]-PtsfromPoly[2])
nPoly23=(PtsfromPoly[2]-PtsfromPoly[3])/length(PtsfromPoly[2]-PtsfromPoly[3])
NVP1=add(nPoly01, -nPoly12)
NVP2=add(nPoly12, -nPoly23)
NVP1length= math.sqrt(NVP1[0]*NVP1[0]+NVP1[1]*NVP1[1]+NVP1[2]*NVP1[2])
NVP2length= math.sqrt(NVP2[0]*NVP2[0]+NVP2[1]*NVP2[1]+NVP2[2]*NVP2[2])
NVS2length= math.sqrt((NVS[2])[0]*(NVS[2])[0]+(NVS[2])[1]*(NVS[2])[1]+(NVS[2])[2]*(NVS[2])[2])
NVP=[]
NVP.append(Vector.Create(NVP1[0]/NVP1length,NVP1[1]/NVP1length,NVP1[2]/NVP1length))
NVP.append(Vector.Create(NVP2[0]/NVP2length,NVP2[1]/NVP2length,NVP2[2]/NVP2length))
NVP.append(NVS[2]/NVS2length)

# Center Point of Surfaces
#NP[0] Center of FreeForm
#NP[1] Center of Fold
#NP[2] Center of PGU

NP=[]
NP.append(PtsfromPoly[1])
NP.append(PtsfromPoly[2])
NP.append(PtsfromPoly[3])

# HorV-Rotated
# Horizon Vector for Surfaced based on facing direction
# HVR[0]=Horizontal Vector of Freeform
# HVR[0]=Horizontal Vector of Fold(Flipped:Facing Reverse Car Direction)
# HVR[0]=Horizontal Vector of PGU
HVR=[]
HVR.append(Vector.Create((hpoints[1])[0]-(hpoints[0])[0],(hpoints[1])[1]-(hpoints[0])[1],(hpoints[1])[2]-(hpoints[0])[2]))
HVR.append(Vector.Create((hpoints[2])[0]-(hpoints[3])[0],(hpoints[2])[1]-(hpoints[3])[1],(hpoints[2])[2]-(hpoints[3])[2]))
HVR.append(Vector.Create((hpoints[5])[0]-(hpoints[4])[0],(hpoints[5])[1]-(hpoints[4])[1],(hpoints[5])[2]-(hpoints[4])[2]))

#Calculate/Draw Horiziontal line before rotation (X'') for Freeform
#HV[0] :Freeform Horizontal vector before rotation (X'') 
HV=[]
x1=(hpoints[0])[0]
y1=(hpoints[0])[1]
z1=(hpoints[0])[2]
aa=(NVP[0])[1]/(NVP[0])[0]
bb=(NP[0])[1]-aa*(NP[0])[0]
axa = aa * aa
nn = 1 / (axa +1)
mm = 1 - axa
x2 = nn *((mm*x1)+(2*aa*y1)-(2*aa*bb))
y2 = nn *((2*aa*x1)-(mm*y1)+(2*bb))
HV.append(Vector.Create(x2-x1,y2-y1,0))
pointO = Point.Create(M(x1), M(y1), M(z1))
pointOri = Point.Create(M(x2), M(y2), M(z1))
result = DesignCurve.Create(GetActivePart(),CurveSegment.Create(pointO, pointOri),True)

#Get/Draw Horiziontal line before rotation (X'') for Fold
#HV[1] :Fold Horizontal vector before rotation (X'') 
x1=(hpoints[3])[0]
y1=(hpoints[3])[1]
z1=(hpoints[3])[2]
aa=(NVP[1])[1]/(NVP[1])[0]
bb=(NP[1])[1]-aa*(NP[1])[0]
axa = aa * aa
nn = 1 / (axa +1)
mm = 1 - axa
x2 = nn *((mm*x1)+(2*aa*y1)-(2*aa*bb))
y2 = nn *((2*aa*x1)-(mm*y1)+(2*bb))
HV.append(Vector.Create(x2-x1,y2-y1,0))
pointO = Point.Create(M(x1), M(y1), M(z1))
pointOri = Point.Create(M(x2), M(y2), M(z1))
result = DesignCurve.Create(GetActivePart(),CurveSegment.Create(pointO, pointOri),True)

#Get/Draw Horiziontal line before rotation (X'') for PGU
#HV[2] :PGU Horizontal vector before rotation (X'') 
x1=(hpoints[4])[0]
y1=(hpoints[4])[1]
z1=(hpoints[4])[2]
aa=(NVP[2])[1]/(NVP[2])[0]
bb=(NP[2])[1]-aa*(NP[2])[0]
axa = aa * aa
nn = 1 / (axa +1)
mm = 1 - axa
x2 = nn *((mm*x1)+(2*aa*y1)-(2*aa*bb))
y2 = nn *((2*aa*x1)-(mm*y1)+(2*bb))
HV.append(Vector.Create(x2-x1,y2-y1,0))
pointO = Point.Create(M(x1), M(y1), M(z1))
pointOri = Point.Create(M(x2), M(y2), M(z1))
result = DesignCurve.Create(GetActivePart(),CurveSegment.Create(pointO, pointOri),True)

#Draw Normal Direction Lines from Poilyline(Optical Axes)
drawtcount=0
while drawtcount < 3:
    pointstart = NP[drawtcount]
    pointCtrX = pointstart[0]
    pointCtrY = pointstart[1]
    pointCtrZ = pointstart[2]
    pointEnd = NVP[drawtcount]
    pointEndX= 0.1*pointEnd[0]+pointCtrX
    pointEndY= 0.1*pointEnd[1]+pointCtrY
    pointEndZ= 0.1*pointEnd[2]+pointCtrZ
    PointStart=Point.Create(M(pointCtrX),M(pointCtrY),M(pointCtrZ))
    PointEnd=Point.Create(M(pointEndX),M(pointEndY),M(pointEndZ))
    result = DesignCurve.Create(GetActivePart(),CurveSegment.Create(PointStart, PointEnd),True)
    drawtcount += 1
    
#Calculate Rotation Angles
dispcount = 0
theta=[0,0,0]
phi=[0,0,0]
rotate=[0,0,0]
while dispcount < 3:
    x= (NVP[dispcount])[0]
    y= (NVP[dispcount])[1]
    z =(NVP[dispcount])[2]
    r =  math.sqrt(x*x + y*y + z*z)
    theta[dispcount] = math.atan2(y,x)*180/ math.pi #to degrees
    phi[dispcount] =  math.acos(z/r)*180/ math.pi - 90
#    print("with Z: ", theta[dispcount])
#    print("with Y': ",phi[dispcount])
    HVlength= math.sqrt((HV[dispcount])[0]*(HV[dispcount])[0]+(HV[dispcount])[1]*(HV[dispcount])[1]+(HV[dispcount])[2]*(HV[dispcount])[2])
    HVRlength= math.sqrt((HVR[dispcount])[0]*(HVR[dispcount])[0]+(HVR[dispcount])[1]*(HVR[dispcount])[1]+(HVR[dispcount])[2]*(HVR[dispcount])[2])
    if (HVR[dispcount])[2] >= (HV[dispcount])[2]:
       rotate[dispcount]=math.acos(Vector.Dot(HV[dispcount],HVR[dispcount])/(HVlength*HVRlength))*180/ math.pi
    else: rotate[dispcount]=-math.acos(Vector.Dot(HV[dispcount],HVR[dispcount])/(HVlength*HVRlength))*180/ math.pi
#    print("with X'': ", rotate[dispcount])
    dispcount += 1
    
#Display Axis for Freeform for Visual Check
origin=Point.Create(M((NP[0])[0]),M((NP[0])[1]),M((NP[0])[2]))
x_Direction = Direction.Create((NVP[0])[0],(NVP[0])[1],(NVP[0])[2])
y_Direction = Direction.Create((HV[0])[0],(HV[0])[1],(HV[0])[2])
result = DatumOriginCreator.Create(origin, x_Direction, y_Direction)
selection = Selection.Create(GetActivePart().CoordinateSystems[0])
axis = Move.GetAxis(selection, HandleAxis.X)
options = MoveOptions()
result = Move.Rotate(selection, axis, DEG(rotate[0]), options)
#Display Axis for Fold for Visual Check
origin=Point.Create(M((NP[1])[0]),M((NP[1])[1]),M((NP[1])[2]))
x_Direction = Direction.Create((NVP[1])[0],(NVP[1])[1],(NVP[1])[2])
y_Direction = Direction.Create((HV[1])[0],(HV[1])[1],(HV[1])[2])
result = DatumOriginCreator.Create(origin, x_Direction, y_Direction)
selection = Selection.Create(GetActivePart().CoordinateSystems[1])
axis = Move.GetAxis(selection, HandleAxis.X)
options = MoveOptions()
result = Move.Rotate(selection, axis, DEG(rotate[1]), options)
#Display Axis for PGU for Visual Check
origin=Point.Create(M((NP[2])[0]),M((NP[2])[1]),M((NP[2])[2]))
x_Direction = Direction.Create((NVP[2])[0],(NVP[2])[1],(NVP[2])[2])
y_Direction = Direction.Create((HV[2])[0],(HV[2])[1],(HV[2])[2])
result = DatumOriginCreator.Create(origin, x_Direction, y_Direction)
selection = Selection.Create(GetActivePart().CoordinateSystems[2])
axis = Move.GetAxis(selection, HandleAxis.X)
options = MoveOptions()
result = Move.Rotate(selection, axis, DEG(rotate[2]), options)

# Write HUD_SpeosToZemax.txt in the output folder.
with open(Output_Dir + 'HUD_SpeosToZemax.txt', 'w') as f:
    f.writelines('\n' .join(lines))
    f.write('\n')
    for index in range(0,3):
        list = hUDOpticalDesign.Projectors
        rowItem = list[index]
        projectors = [str (rowItem.Distance), str (rowItem.HorizontalAngle), str (rowItem.VerticalAngle)]
        f.writelines('\n' .join(projectors))
        f.writelines('\n')
        index += 1
    f.write('#Surface dimensions start from freeform and go to PGU. There are 4 edge dimensions per surface')
    for i in Edgesprev:
        f.write('\n')
        f.write(str(i.Length))
    f.write('\n')
    f.write('#Point coordinates start from Eyepoint and go to PGU. These are vertices of 4 polylines, so there are 8 vertices, 4 are duplicates')
    for i in Curvesprev:
        f.write('\n')
        n+=1
        f.write(str(n) + ' ')
        f.write(str(i.StartPoint.Position))
        f.write('\n')
        f.write(str(n) + ' ')
        f.write(str(i.EndPoint.Position))
    f.write('\n')
    f.write("#Rotation Angles(deg) for Z, Y', X'' (for 1st, 2nd and 3rd Surfaces)")
    for index in range(0,3):
        f.writelines("\nZ  : ")
        f.writelines(str(theta[index]))
        f.writelines("\nY' : ")
        f.writelines(str(phi[index]))
        f.writelines("\nX'': ")
        f.writelines(str(rotate[index]))
        index += 1

# Activate ROOT
result = ComponentHelper.SetRootActive(None)
#Exporting windshield geometry as CAD file
windshieldGeometry = Selection.Create(hud_OpticalDesign.WindshieldInnerSurface.LinkedObject)

# Create new design
Document.Create()
        
# Copy geometry
result = Copy.Execute(windshieldGeometry)
        
# Save as   
stepFilePath = os.path.join(Output_Dir, hud_OpticalDesign.Name + ".windshield.export.stp")    
options = ExportOptions.Create()
DocumentSave.Execute(stepFilePath, options)
DocumentHelper.CloseDocument()

#Open HUD_SpeosToZemax.txt
#b1 = Output_Dir + 'HUD_SpeosToZemax.txt'
#import subprocess
#subprocess.Popen('notepad.exe ' + b1)