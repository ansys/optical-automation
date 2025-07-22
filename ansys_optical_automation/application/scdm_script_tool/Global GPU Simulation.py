# ----------------------------------------------------------------------------------------
# Script Description:
#
# This script creates and configures a Speos Direct Simulation automatically importing
# all elements and enabling GPU-based computation.
#
# Main Objectives:
#   • Create a new Direct Simulation.
#   • Assign it a default name ("Complete_Simulation") or a timestamped fallback if the 
#     default name is already in use or causes a conflict.
#   • Automatically select all geometries, light sources, and sensors present in the model.
#   • Set a predefined number of rays (1e7) for the simulation.
#   • Launch the simulation using **GPU Compute** to accelerate performance.
# ----------------------------------------------------------------------------------------

import clr
import System
from System import DateTime
# Create a new Speos Direct Simulation
direct = SpeosSim.SimulationDirect.Create()
try:
    direct.Name = "Complete_Simulation"
except Exception as e:
    print(e)  # Print the actual exception
    # Get current date and time
    now = DateTime.Now
    timestamp = now.ToString("yyyyMMdd_HHmmss")  # Format: 20250527_141530
    # Assign a unique name using timestamp
    direct.Name = "Complete_Simulation_" + timestamp
# Select all available geometries, sources, and sensors
direct.Geometries.SelectAll()
direct.Sources.SelectAll()
direct.Sensors.SelectAll()
# Set simulation parameters
direct.NbRays = 1e7
direct.GpuCompute()