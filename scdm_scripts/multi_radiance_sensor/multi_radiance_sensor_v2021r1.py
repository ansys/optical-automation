##################################################################
# multi_radiance_sensor  - Copyright ANSYS. All Rights Reserved.
# ##################################################################
# CREATION:      2021.08.17
# VERSION:       1.0.0
#
# OVERVIEW
# ========
# This script is generated for showing scripting capabilities purpose.
# It contains functions to create multiple Speos Radiance sensors.
#
#
# ##################################################################
# https://opensource.org/licenses/MIT
#
# Copyright 2021 Ansys, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# The user agrees to this disclaimer and user agreement with the download or usage
# of the provided files.
#
# ##################################################################

# Python Script, API Version = V20 Beta


import sys
sys.path += [R"C:\Program Files\ANSYS Inc\v202\Optical Products\SPEOS\Bin"]
import clr


class Struct:
    pass

def MultiRadianceSensor():
    selection = getSelectionedElements()
    if selection is None:
        return
    openFileDialog = OpenFileDialog()
    openFileDialog.Filter = "Excel Files (*.xlsx)|*.xlsx|All Files (*.*)|*.*"
    if not openFileDialog.Show():
        return
    inputs = ReadValuesFromExcel(openFileDialog.FileName)

    radianceSensorSelection = Selection.Empty()
    for hAngle, vAngle in zip(inputs.hAngles, inputs.vAngles):
        info = getRadianceSensorInfo(hAngle, vAngle, inputs, selection)
        iScSensor = createNewRadianceSensor(info, inputs)
        radianceSensorSelection += Selection.CreateByObjects(iScSensor)
    NamedSelection.Create(radianceSensorSelection, Selection.Empty())

def ReadValuesFromExcel(filename):
    clr.AddReference("Microsoft.Office.Interop.Excel")
    import Microsoft.Office.Interop.Excel as Excel

    result = Struct()
    excel = Excel.ApplicationClass()
    workbook = excel.Workbooks.Open(filename)
    sheet = workbook.ActiveSheet
    result.hAngles = _getListOfData(sheet, 3, 2)
    result.vAngles = _getListOfData(sheet, 3, 3)
    result.distance = sheet.Cells[3, 5].Value2
    result.focal = sheet.Cells[9, 5].Value2
    result.offset = sheet.Cells[6, 5].Value2
    result.resolutionMode = sheet.Cells[2,8].Value2
    result.resolutionX = sheet.Cells[5, 7].Value2
    result.resolutionY = sheet.Cells[5, 8].Value2
    result.type = sheet.Cells[3,10].Value2
    result.layer = sheet.Cells[6,10].Value2
    workbook.Close()
    return result

def _getListOfData(sheet, iRow, iCol, dataType=float, orientation="vertical"):
    """Collect the list of data that start in coordinate ("iRow", "iCol") of the "sheet" """

    checkType = None
    if dataType == float:
        checkType = lambda value : type(value) in [int, float]
    elif dataType == int:
        checkType = lambda value : type(value) == int or (type(value) == float and value.is_integer()) 
    
    curValue = sheet.Cells[iRow, iCol].Value2
    result = []

    while checkType(curValue):
        result += [curValue]
        if orientation == "vertical":
            iRow += 1
        else:
            iCol += 1
        curValue = sheet.Cells[iRow, iCol].Value2

    return result

def getSelectionedElements():
    result = Struct()
    primarySelection = Selection.GetActive()
    secondarySelection = Selection.GetActiveSecondary()
    if len(primarySelection.GetItems[IDesignBody]()) == 0:
        MessageBox.Show("Please select the object(s) to look at using the primary selection")
        return
    if len(secondarySelection.GetItems[ICoordinateSystem]()) == 0:
        MessageBox.Show("Please select the coordinate system to use as reference for the sensors position using the secondary selection")
        return
    result.coordinateSystem = getRealOriginal(secondarySelection.GetItems[ICoordinateSystem]()[0])
    bodyList = [getRealOriginal(iItem) for iItem in primarySelection.GetItems[IDesignBody]()]
    bodyListCopy = List[Body]()
    [bodyListCopy.Add(iItem.Shape.Copy()) for iItem in bodyList]
    result.body = bodyListCopy[0]
    result.body.CombinePieces(bodyListCopy)
    return result

def getRealOriginal(item):
    result = item
    while result.GetOriginal():
        result = result.GetOriginal()
    return result

def getRadianceSensorInfo(hAngle, vAngle, inputs, selection):
    result = Struct()
    hRotation = Matrix.CreateRotation(Line.Create(selection.coordinateSystem.Frame.Origin, selection.coordinateSystem.Frame.DirZ), DEG(hAngle))
    vRotation = Matrix.CreateRotation(Line.Create(selection.coordinateSystem.Frame.Origin, selection.coordinateSystem.Frame.DirY), DEG(vAngle))
    mRotation = hRotation*vRotation
    curFrame = mRotation*selection.coordinateSystem.Frame
    curFrameMatrix = Matrix.CreateMapping(curFrame)
    curFramePositionVector = curFrameMatrix.Translation
    curFramePosition = Point.Create(curFramePositionVector.X, curFramePositionVector.Y, curFramePositionVector.Z)
    bBox = curFrameMatrix*selection.body.GetBoundingBox(curFrameMatrix.Inverse, True)
    result.ori = curFramePosition
    result.lookAt = bBox.Center + inputs.distance*(-curFrame.DirX)
    result.dirX = -curFrame.DirY
    result.dirY = curFrame.DirZ
    offset = inputs.offset
    result.XEnd = inputs.focal * (bBox.Size.Y + offset)/2 / inputs.distance
    result.YEnd = inputs.focal * (bBox.Size.Z + offset)/2 / inputs.distance
    result.name = getRadianceSensorName(hAngle, vAngle)
    return result

def getRadianceSensorName(hAngle, vAngle):
    result = ""
    if hAngle == 0:
        result += 'H'
    else:
        if hAngle < 0:
            result += 'L'
        else:
            result += 'R'
        result += "{0}".format(round(abs(hAngle),2))
    result += ' '
    if vAngle == 0:
        result += 'V'
    else:
        if vAngle < 0:
            result += 'D'
        else:
            result += 'U'
        result += "{0}".format(round(abs(vAngle),2))
    return result

def createNewRadianceSensor(info, inputs):
    scSensor = SpeosSim.SensorRadiance.Create(None)
    scSensor.Name = info.name
    # Create Origin
    x_Direction = info.dirX
    y_Direction = info.dirY    
    result = DatumOriginCreator.Create(info.ori, x_Direction, y_Direction, Info1)
    sel =Selection.CreateByObjects(result.CreatedOrigin)
    direction =Direction.Create(result.CreatedOrigin.Axes[2].Shape.Geometry.Direction[0],result.CreatedOrigin.Axes[2].Shape.Geometry.Direction[1],result.CreatedOrigin.Axes[2].Shape.Geometry.Direction[2])
    options = MoveOptions()
    result = Move.Translate(sel,direction,inputs.distance,options, Info4)
    test=  result.GetModified[ICoordinateSystem]()
    #test= test[0].Axes[2].Shape.Geometry.Origin
    xdir = Selection.CreateByObjects(test[0].Axes[0])
    ydir = Selection.CreateByObjects(test[0].Axes[1])
    scSensor.XDirection.Set(xdir)
    scSensor.YDirection.Set(ydir)
    scSensor.OriginPoint.Set(Selection.CreateByObjects(test))
    #speSensor = SPEOS_SC.SIM.SpeosWrapperSensorRadiance.GetWrapper(scSensor)
    scSensor.Focal = inputs.focal
    scSensor.XIsMirrored = True
    scSensor.YIsMirrored =True
    scSensor.XEnd = info.XEnd
    scSensor.YEnd = info.YEnd
    scSensor.XNbSamples=inputs.resolutionX
    scSensor.YNbSamples=inputs.resolutionY

    return scSensor

MultiRadianceSensor()