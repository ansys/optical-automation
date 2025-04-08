# Python Script, API Version = V232
"""
Recreate a direct simulation from an inverse or inverse from direct
"""
# Limits :
# Works only if the selected simulation is located in the main assembly
# specific options not set (i.e. Dispersion, FTG, automatic save frequency)
# FTG not set in geometries

if args.Count == 0:
    scdocfilepath = Window.ActiveWindow.Document.Path

# Asking user to select a simulation
result = InputHelper.PauseAndGetInput("Choose a simulation")
current_sel = result.PrimarySelection

# check if the Type propertie exist
if "Type" in dir(current_sel.Items[0]):
    current_sel_type = current_sel.Items[0].Type

    # check if there is a selection and only one object
    if current_sel.Count == 1:
        input_sim = current_sel.Items[0].Name
        # check simulation type
        if current_sel_type == "SPEOS_SC.SIM.SpeosWrapperSimulationDirect":
            InputSimObject = SpeosSim.SimulationDirect.Find(input_sim)
            # Create Inverse from direct
            inverse = SpeosSim.SimulationInverse.Create()
            # Set geometries/Sources/Sensors from selected simulation to new one
            inverse.Geometries.Set(InputSimObject.Geometries.LinkedObjects)
            inverse.Sources.Set(InputSimObject.Sources.LinkedObjects)
            inverse.Sensors.Set(InputSimObject.Sensors.LinkedObjects)
            # Set common properties (GDT, mesh)
            inverse.SetSimulationSettings(InputSimObject.GetSimulationSettings())
            # Set ambient material if existing
            if InputSimObject.AmbientMaterial:
                inverse.AmbientMaterial = InputSimObject.AmbientMaterial
        elif current_sel_type == "SPEOS_SC.SIM.SpeosWrapperSimulationInverse":
            InputSimObject = SpeosSim.SimulationInverse.Find(input_sim)
            # Create Direct from inverse
            direct = SpeosSim.SimulationDirect.Create()
            # Set geometries/Sources/Sensors from selected simulation to new one
            direct.Geometries.Set(InputSimObject.Geometries.LinkedObjects)
            direct.Sources.Set(InputSimObject.Sources.LinkedObjects)
            direct.Sensors.Set(InputSimObject.Sensors.LinkedObjects)
            # Set common properties (GDT, mesh)
            direct.SetSimulationSettings(InputSimObject.GetSimulationSettings())
            # Set ambient material if existing
            if InputSimObject.AmbientMaterial:
                direct.AmbientMaterial = InputSimObject.AmbientMaterial
        else:
            Display = MessageBox.Show("Please select a direct or inverse simulation.")
            ApplicationHelper.ReportError("Please select a direct or inverse simulation.")

    elif current_sel.Count > 1:
        Display = MessageBox.Show("Please select only one simulation.")
        ApplicationHelper.ReportError("Please select only one simulation.")
else:
    Display = MessageBox.Show("Please select a direct or inverse simulation.")
    ApplicationHelper.ReportError("Please select a direct or inverse simulation.")
