# Python Script, API Version = V232
"""
Recreate an HOA simulation from an HUD Design
"""

# Limits :
# Works only if the HOD feature is located in the main assembly
# Script only runs from Speos
# Tilt angle function works from 26R1 (request the display of Tilt Angle in the HOD feature)

# Asking user to select the HOD feature
result = InputHelper.PauseAndGetInput("Choose HOD element")
current_sel = result.PrimarySelection

# Check if the selected object has a type (no type if geometry selected for example)
if "Type" in dir(current_sel.Items[0]):
    # check if there is a selection and only one object
    if current_sel.Count == 1:
        # check the type of object, error if not HOD
        if current_sel.Items[0].Type == "SPEOS_SC.OSD.SpeosWrapperOSDHUDOD":
            hod_name = current_sel.Items[0].Name
            hodObject = SpeosDes.HUDOD.Find(hod_name)
            hodStatus = False
            hodStatus = hodObject.IsUpToDate
            if not hodStatus:
                ApplicationHelper.ReportWarning(
                    "The HOD feature selected is not up to date, please verify the simulation inputs"
                )

            # Creation of HOA simulation
            hoaSim = SpeosSim.SimulationHoa.Create()

            # Affecting HOD axis and reverse direction to HOA feature
            Veh_axis = hodObject.VehicleAxis.LinkedObject
            if Veh_axis is not None:
                hoaSim.VehicleAxis.Set(Veh_axis)
            Top_axis = hodObject.TopAxis.LinkedObject
            if Top_axis is not None:
                hoaSim.TopAxis.Set(Top_axis)
            Reverse_veh = hodObject.ReverseVehiculeAxisDirection
            Reverse_Top = hodObject.ReverseTopAxisDirection
            hoaSim.ReverseVehiculeAxisDirection = Reverse_veh
            hoaSim.ReverseTopAxisDirection = Reverse_Top

            # Eyebox definition
            eyeBoxPoint = hodObject.EyeboxCenter.LinkedObject
            hoaSim.Eyebox.EyeboxCenter.Set(eyeBoxPoint)
            hoaSim.Eyebox.EyeboxOrientationTypeIndex = hodObject.EyeboxOrientationTypeIndex
            hoaSim.Eyebox.EBBinocularHorizontalSize = hodObject.EBHorizontalSize
            hoaSim.Eyebox.EBVerticalSize = hodObject.EBVerticalSize
            hoaSim.Eyebox.EBMonocularHorizontalSampling = hodObject.EBHorizontalSampling
            hoaSim.Eyebox.EBVerticalSampling = hodObject.EBVerticalSampling
            eyebox_number = hodObject.EBConfigurations.Count
            # Monoeyebox or MultiEyebox
            if eyebox_number > 1:
                hoaSim.Eyebox.EBMultiEyebox = 1
                hoaSim.Eyebox.EyeboxConfigPositionDirectionTypeIndex = (
                    hodObject.EyeboxConfigPositionDirectionTypeIndex
                )  # Finding Position direction
                hoaSim.Eyebox.EBConfigurations.Clear()

                i = 0
                j = 0
                eyebox_item = []
                while j < eyebox_number:
                    eyebox_item.append(hodObject.EBConfigurations.Item[j])
                    j = j + 1

                while i < eyebox_number:
                    eyebox_item = hodObject.EBConfigurations.Item[i]
                    if i > 0:
                        hoaSim.Eyebox.EBConfigurations.AddNew(i)
                    hoaSim.Eyebox.EBConfigurations[i].EBConfigName = hodObject.EBConfigurations[i].EBConfigName
                    # Test to avoid changing the Central Eyebox offset, which provoques an error
                    if float(hodObject.EBConfigurations[i].Offset) != 0.0:
                        hoaSim.Eyebox.EBConfigurations[i].OffsetText = str(hodObject.EBConfigurations[i].Offset) + " mm"
                    i = i + 1

            # Target Image definition
            # Set of TI parameters, TID, LOA, LDA
            if hoaSim.TargetImage.TIVirtualImageDistance != hodObject.TIVirtualImageDistance:
                hoaSim.TargetImage.TIVirtualImageDistance = hodObject.TIVirtualImageDistance
            if hoaSim.TargetImage.TILookOverAngle != hodObject.TILookOverAngle:
                hoaSim.TargetImage.TILookOverAngle = hodObject.TILookOverAngle
            if hoaSim.TargetImage.TILookDownAngle != hodObject.TILookDownAngle:
                hoaSim.TargetImage.TILookDownAngle = hodObject.TILookDownAngle
            # Test on the TI mode, 0 if size, 1 if FOV
            hoaSim.TargetImage.TargetImageModeTypeIndex = hodObject.TargetImageModeTypeIndex
            if hoaSim.TargetImage.TargetImageModeTypeIndex == 0:
                if hoaSim.TargetImage.TIHorizontalSize != hodObject.TIHorizontalSize:
                    hoaSim.TargetImage.TIHorizontalSize = hodObject.TIHorizontalSize
                if hoaSim.TargetImage.TIVerticalSize != hodObject.TIVerticalSize:
                    hoaSim.TargetImage.TIVerticalSize = hodObject.TIVerticalSize
            else:
                if hoaSim.TargetImage.TIHorizontalFOV != hodObject.TIHorizontalFOV:
                    hoaSim.TargetImage.TIHorizontalFOV = hodObject.TIHorizontalFOV
                if hoaSim.TargetImage.TIVerticalFOV != hodObject.TIVerticalFOV:
                    hoaSim.TargetImage.TIVerticalFOV = hodObject.TIVerticalFOV

            # Windshield definition
            windshieldInnerSurface = hodObject.WindshieldInnerSurface.LinkedObject
            hoaSim.Windshield.WindshieldInnerSurface.Set(windshieldInnerSurface)

            # mirrors
            # Selecting mirrors
            NbProjectorHOD = 0
            k = 0
            ProjectorsName = []
            ProjectorIsMulti = []
            ProjectorMultiID = 0
            MultiTicked = False

            while str(hodObject.Projectors[k].ProjectorType) != "PGU":
                ProjectorsName.append(hodObject.Projectors[k].Name)
                ProjectorIsMulti.append(hodObject.Projectors[k].MultiConfig)
                if hodObject.Projectors[k].MultiConfig:
                    ProjectorMultiID = k
                    MultiTicked = True
                k += 1
                NbProjectorHOD += 1

            bodies = GetRootPart().Bodies
            selection = []
            Number_of_mirrors_selected = 0
            m = 0

            while m < NbProjectorHOD:
                i = 0
                MirrorNameToSearch = "[" + hod_name + "]_" + ProjectorsName[m]
                for i in range(len(bodies)):
                    if bodies[i].GetName().Contains(MirrorNameToSearch):
                        selection.append(GetRootPart().Bodies[i].Faces[0])
                        Number_of_mirrors_selected += 1
                        break
                m += 1
            if Number_of_mirrors_selected != NbProjectorHOD:
                Display = MessageBox.Show("Some mirrors can't be found, please select the mirrors manually")
                ApplicationHelper.ReportWarning("Some mirrors can't be found, please select the mirrors manually")
            else:
                hoaSim.Mirrors.MirrorFaces.Set(selection)
                if MultiTicked:
                    PossibleMirrors = []
                    PossibleMirrors = hoaSim.Mirrors.GetMultiEyeBoxMirrorPossibleValues()
                    hoaSim.Mirrors.MultiEyeBoxMirror = PossibleMirrors[ProjectorMultiID + 1]
                    TiltAxisToSearch = "[" + hod_name + "]_Tilt Axis"
                    TiltAxisFound = False
                    TiltAxisCurves = GetRootPart().Curves
                    for curve in TiltAxisCurves:
                        if curve.GetName() == TiltAxisToSearch:
                            hoaSim.Mirrors.TiltRotationAxis.Set(curve)
                            TiltAxisFound = True
                            break
                    if not TiltAxisFound:
                        Display = MessageBox.Show("Tilt axis can't be found, please select it manually")
                        ApplicationHelper.ReportWarning("Tilt axis can't be found, please select it manually")

                    version = int(dir(SpaceClaim.Api)[0][1:])
                    if not version >= 261:
                        Display = MessageBox.Show(
                            "Speos version is older than 2026R1, Tilt angles can't be retrieved,"
                            " please add them manually"
                        )
                        ApplicationHelper.ReportWarning(
                            "Speos version is older than 2026R1, Tilt angles can't be "
                            "retrieved, please add them manually"
                        )
                    else:
                        n = 0
                        while n < eyebox_number:
                            AdvancedParameterName = (
                                "[" + hod_name + "]" + "_Tilt Angle " + hodObject.EBConfigurations[n].EBConfigName
                            )
                            hoaSim.Eyebox.EBConfigurations[n].TiltAngle = hodObject.AdvancedParameters[
                                AdvancedParameterName
                            ]
                            n = n + 1

            # PGU
            # PGU Center
            activePartPoints = GetActivePart().DatumPoints
            CenterToSearch = "[" + hod_name + "]_PGU Center"
            PGU_center_found = False

            for point in activePartPoints:
                if point.GetName().Contains(CenterToSearch):
                    hoaSim.PGU.OriginPoint.Set(point)
                    PGU_center_found = True
                    break

            if not PGU_center_found:
                Display = MessageBox.Show("PGU center can't be found, please select it manually")
                ApplicationHelper.ReportWarning("PGU center can't be found, please select it manually")

            # PGU Axis
            curves = GetRootPart().Curves
            AxisHToSearch = "[" + hod_name + "]_PGU Horizontal Axis"
            AxisVToSearch = "[" + hod_name + "]_PGU Vertical Axis"
            PGU_AxisHFound = False
            PGU_AxisVFound = False

            for curve in curves:
                if curve.GetName() == AxisHToSearch:
                    hoaSim.PGU.XDirection.Set(curve)
                    PGU_AxisHFound = True
                elif curve.GetName() == AxisVToSearch:
                    hoaSim.PGU.YDirection.Set(curve)
                    PGU_AxisVFound = True

            if not PGU_AxisHFound:
                Display = MessageBox.Show("PGU Horizontal axis can't be found, please select it manually")
                ApplicationHelper.ReportWarning("PGU Horizontal axis can't be found, please select it manually")
            if not PGU_AxisVFound:
                Display = MessageBox.Show("PGU Vertical axis can't be found, please select it manually")
                ApplicationHelper.ReportWarning("PGU Vertical axis can't be found, please select it manually")
            # PGU parameters
            hoaSim.PGU.PGUCharacteristicsTypeIndex = hodObject.PGUCharacteristicsTypeIndex
            # PGU user define case
            if hoaSim.PGU.PGUCharacteristicsTypeIndex == 6:
                hoaSim.PGU.PGUHorizontalResolution = hodObject.PGUHorizontalResolution
                hoaSim.PGU.PGUVerticalResolution = hodObject.PGUVerticalResolution
                hoaSim.PGU.PGUHorizontalSize = hodObject.PGUHorizontalSize
                hoaSim.PGU.PGUVerticalSize = hodObject.PGUVerticalSize

            # Warping, report and windshield outer face doesn't exist in HOD feature so can't be retrieve
            Display = MessageBox.Show(
                "HOA simulation created, do not forget to add warping, report and windshield outer face if needed"
            )
            ApplicationHelper.ReportInformation(
                "HOA simulation created, do not forget to add warping, report and windshield outer face if needed"
            )
        else:
            Display = MessageBox.Show("Please select a HOD feature")
            ApplicationHelper.ReportError("Please select a HOD feature")

    elif current_sel.Count > 1:
        Display = MessageBox.Show("Please select only one HOD feature")
        ApplicationHelper.ReportError("Please select only one HOD feature")
    else:
        Display = MessageBox.Show("Please select a HOD feature")
        ApplicationHelper.ReportError("Please select a HOD feature")
else:
    Display = MessageBox.Show("Please select a HOD feature")
    ApplicationHelper.ReportError("Please select a HOD feature")
