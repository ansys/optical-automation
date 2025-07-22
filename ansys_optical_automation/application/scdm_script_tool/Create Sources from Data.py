# ----------------------------------------------------------------------------------------
# Script Description:
#
# This script automates the creation of surface light sources in Speos based on 
# geometry names that match predefined custom LED identifiers.
#
# A dictionary named `leds_invented` stores reference LEDs where:
#   • Each key corresponds to an expected geometry name (e.g., "LED_Invented_1")
#   • Each value contains:
#       - "Flux" (luminous flux in lumens)
#       - "Spectrum" (path to a .spectrum file for spectral power distribution)
#
# Steps:
# 1. Iterate over all bodies in the root part of the model.
# 2. Check if each body's name contains any of the keys from the LED dictionary.
# 3. If a match is found:
#       - Create a new surface light source in Speos.
#       - Assign the specified flux and spectrum values.
#       - Use the face of the body as the emissive surface.
#       - Set a default ray length (e.g., 5 mm).
# ----------------------------------------------------------------------------------------
import os

# Base path
path = r"C:\Users\amarin\OneDrive - ANSYS, Inc\Things\Usefull scripts\Simulation setups from Catia\Materials"

# Dictionary of custom LEDs
leds_invented = {
    "LED_Invented_1": {
        "Flux": 50,
        "Spectrum": os.path.join(path, "CREE XLamp Color Blue -DominantWavelength457nm.spectrum")
    },
    "LED_Invented_2": {
        "Flux": 70,
        "Spectrum": os.path.join(path, "CREE XR-C Amber.spectrum")
    }
}

# Loop over all bodies in the root part
for body in GetRootPart().GetAllBodies():
    body_name = body.GetName()
    
    # Check if the body's name contains any of the LED dictionary keys
    for key in leds_invented:
        if key in body_name:
            flux = leds_invented[key]["Flux"]
            spectrum = leds_invented[key]["Spectrum"]

            # Create a new surface light source
            surface = SpeosSim.SourceSurface.Create()
            surface.Name = body_name
            surface.FluxValueLuminous = flux
            surface.SpectrumType = SpeosSim.SourceSurface.EnumSpectrumType.Library
            surface.SpectrumValueLibrary = spectrum
            surface.RayLength = 5

            # Assign the first face of the body as the emissive surface
            emissive_face = FaceSelection.Create(body.Faces[0])
            surface.EmissiveFaces.Set(emissive_face.Items)

            print("✓ Created light source: " + body_name + " | Flux: " + str(flux) + " | Spectrum: " + spectrum)
