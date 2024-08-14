# © 2012-2024 ANSYS, Inc. All rights reserved. Unauthorized use, distribution, or duplication is prohibited.
# THIS ANSYS SOFTWARE PRODUCT AND PROGRAM DOCUMENTATION INCLUDE TRADE SECRETS AND ARE CONFIDENTIAL AND
# PROPRIETARY PRODUCTS OF ANSYS, INC., ITS SUBSIDIARIES, OR LICENSORS.
# The software products and documentation are furnished by ANSYS, Inc., its subsidiaries, or affiliates under a software
# license agreement that contains provisions concerning non-disclosure, copying, length and nature of use, compliance
# with exporting laws, warranties, disclaimers, limitations of liability, and remedies, and other provisions.
# The software products and documentation may be used, disclosed, transferred, or copied only in accordance with the
# terms and conditions of that software license agreement.

import sys
from os import path

import clr

sys.path += [R"C:\Program Files\ANSYS Inc\v242\Optical Products\Speos\Bin"]

clr.AddReferenceToFile("Optis.Core_net.dll")
clr.AddReferenceToFile("Optis.Data_net.dll")

# References to Optis.Core and Optis.Data
import Optis.Core as OptisCore
import Optis.Data as OptisData


def GetAxisSystemData(iTime, iFrame):
    dAxisSystemData = OptisCore.DAxisSystemData()
    dAxisSystemData.Time = iTime
    dAxisSystemData.Origin.Init(1000 * iFrame.Origin.X, 1000 * iFrame.Origin.Y, 1000 * iFrame.Origin.Z)

    tmpVector = OptisCore.Vector3_double()
    tmpVector.Init(iFrame.DirX.X, iFrame.DirX.Y, iFrame.DirX.Z)
    tmpVector.Normalize()

    dAxisSystemData.Direction_X.Init(tmpVector.Get(0), tmpVector.Get(1), tmpVector.Get(2))

    tmpVector.Init(iFrame.DirY.X, iFrame.DirY.Y, iFrame.DirY.Z)
    tmpVector.Normalize()

    dAxisSystemData.Direction_Y.Init(tmpVector.Get(0), tmpVector.Get(1), tmpVector.Get(2))

    return dAxisSystemData


# Working directory
workingDirectory = path.dirname(GetRootPart().Document.Path.ToString())

# SpaceClaim InputHelper
ihTrajectoryName = InputHelper.CreateTextBox("Trajectory.1", "Trajectory name: ", "Enter the name of the trajectory")
ihFrameFrequency = InputHelper.CreateTextBox(
    30, "example_video_process_camera_timeline frame rate:", "Set timeline frame rate (FPS)", ValueType.PositiveInteger
)
ihReverseDirection = InputHelper.CreateCheckBox(False, "Reverse direction", "Reverse direction on trajectory")
ihObjectSpeed = InputHelper.CreateTextBox(
    50, "Object speed:", "Set the moving object speed (km/h)", ValueType.PositiveDouble
)

ihCoordinateSystem = InputHelper.CreateSelection(
    "Reference coordinate system", SelectionFilter.CoordinateSystem, 1, True
)
ihTrajectory = InputHelper.CreateSelection("Trajectory curve", SelectionFilter.Curve, 1, True)

InputHelper.PauseAndGetInput(
    "Trajectory parameters",
    ihTrajectoryName,
    ihFrameFrequency,
    ihObjectSpeed,
    ihReverseDirection,
    ihCoordinateSystem,
    ihTrajectory,
)

# Animation frame rate (s-1)
frameFrequency = float(ihFrameFrequency.Value)

# Object speed (km/h)
objectSpeed = float(ihObjectSpeed.Value)

# Trajectory file
trajectoryName = str(ihTrajectoryName.Value)
trajectoryAcquisitionFile = workingDirectory + "\\" + trajectoryName

# Reference coordinate system
coordSysSelection = ihCoordinateSystem.Value
trajectoryCoordSys = coordSysSelection.Items[0]

# Trajectory curve
trajCurveSelection = ihTrajectory.Value
trajectoryCurve = trajCurveSelection.Items[0]

# Reversed trajectory (Boolean)
isReversedTrajectory = ihReverseDirection.Value


# Acquisition of positions
def GetPositionOrientation(i_CoordSys, i_ReferenceCoordSys):
    # change base of current position
    newMatric = Matrix.CreateMapping(i_ReferenceCoordSys.Frame)

    currentPosition = newMatric.Inverse * i_CoordSys.Frame.Origin
    currentPosition = Point.Create(
        round(currentPosition.X, 6), round(currentPosition.Y, 6), round(currentPosition.Z, 6)
    )

    # change base of current iDirection
    iDirectionX = newMatric.Inverse * i_CoordSys.Frame.DirX

    # change base of current iDirection
    jDirectionX = newMatric.Inverse * i_CoordSys.Frame.DirY

    # Return new frame
    return Frame.Create(currentPosition, iDirectionX, jDirectionX)


def MoveAlongTrajectory(
    i_trajectoryCoordSys, i_trajectoryCurve, i_isReversedTrajectory, i_frameFrequency, i_objectSpeed
):
    selectedCoordSys = Selection.Create(i_trajectoryCoordSys)
    newselectedCoordSys = i_trajectoryCoordSys

    pathLength = i_trajectoryCurve.Shape.Length
    selectedCurve = Selection.Create(i_trajectoryCurve)

    # Convert speed in m/s
    convObjectSpeed = float(i_objectSpeed * 1000 / 3600)

    currentPosition = 0.0
    timeStamp = 0.0
    positionTable = []
    timeTable = []

    while currentPosition < 1:
        options = MoveOptions()

        if currentPosition == 0:
            options.Copy = True
        else:
            options.Copy = False

        if i_isReversedTrajectory:
            result = Move.AlongTrajectory(selectedCoordSys, selectedCurve, 1 - currentPosition, options)

            if currentPosition == 0:
                newselectedCoordSys = result.GetCreated[ICoordinateSystem]()[0]
                selectedCoordSys = Selection.Create(newselectedCoordSys)
                if newselectedCoordSys.Frame.Origin != i_trajectoryCoordSys.Frame.Origin:
                    options.Copy = False
                    result = Move.AlongTrajectory(selectedCoordSys, selectedCurve, currentPosition, options)
        else:
            result = Move.AlongTrajectory(selectedCoordSys, selectedCurve, currentPosition, options)

            if currentPosition == 0:
                newselectedCoordSys = result.GetCreated[ICoordinateSystem]()[0]
                selectedCoordSys = Selection.Create(newselectedCoordSys)
                if newselectedCoordSys.Frame.Origin != i_trajectoryCoordSys.Frame.Origin:
                    options.Copy = False
                    result = Move.AlongTrajectory(selectedCoordSys, selectedCurve, currentPosition, options)

        if result:
            movedFrame = GetPositionOrientation(newselectedCoordSys, i_trajectoryCoordSys)
            positionTable.append(movedFrame)
            timeTable.append(timeStamp)

        currentPosition += (convObjectSpeed / i_frameFrequency) / pathLength
        timeStamp += 1 / float(i_frameFrequency)

    result = Delete.Execute(selectedCoordSys)

    return timeTable, positionTable


# Length of path (m)
pathLength = trajectoryCurve.Shape.Length

# Get time stamps and relative coordinate systems
timeTable, positionTable = MoveAlongTrajectory(
    trajectoryCoordSys, trajectoryCurve, isReversedTrajectory, frameFrequency, objectSpeed
)

dAxisSystemData_Table = []
for time in timeTable:
    timeIndex = timeTable.index(time)
    fFrame = positionTable[timeIndex]

    dAxisSystemData = GetAxisSystemData(time, fFrame)
    dAxisSystemData_Table.append(dAxisSystemData)

if len(dAxisSystemData_Table) > 0:
    dmTrajectory = OptisCore.DAxisSystemTrajectory()
    dmTrajectory.Trajectory.Resize(len(dAxisSystemData_Table))

    for dAxisSystemData in dAxisSystemData_Table:
        dmTrajectory.Trajectory.Set(dAxisSystemData_Table.index(dAxisSystemData), dAxisSystemData)

    pathTrajectoryFile = str(workingDirectory + "\\" + str(ihTrajectoryName.Value) + ".json")
    strPathTrajectoryFile = OptisCore.String.From(pathTrajectoryFile)
    pathTrajectoryFile = OptisCore.Path(strPathTrajectoryFile)

    cAxisSystemTrajectoryWriter = OptisData.CAxisSystemTrajectoryWriter()
    cAxisSystemTrajectoryWriter.Open(pathTrajectoryFile)
    cAxisSystemTrajectoryWriter.Write(dmTrajectory)

    cAxisSystemTrajectoryWriter.Close()
