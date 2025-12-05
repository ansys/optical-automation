# ----------------------------------------------------------------------------------------
# Script Description:
#
# This script automates the creation of surface light sources in Speos based on
# geometry names that match predefined LED identifiers loaded from a JSON file.
#
# The JSON file `LED_Surface_Sources.json` must be located in:
#   C:\Program Files\ANSYS Inc\v252\Optical Products\OpticalLibraries
#
# Each key in the JSON:
#   - Key:   Substring expected to be found in the body name
#   - Value: {
#               "Flux": <float or null>,
#               "Spectrum": <relative or absolute path to .spectrum file>
#            }
# ----------------------------------------------------------------------------------------
import json
import os


def get_optical_lib_dir():
    ansys_dir = os.environ.get("ANSYS252_DIR")
    if not ansys_dir:
        raise EnvironmentError("Environment variable 'ANSYS252_DIR' is not defined.")
    v252_root = os.path.dirname(ansys_dir)  # ...\v252
    return os.path.join(v252_root, "Optical Products", "OpticalLibraries")


OPTICAL_LIB_DIR = get_optical_lib_dir()


def resolve_optical_path(path_str):
    """Return absolute path; if already absolute, return as is."""
    if not path_str:
        return None
    if os.path.isabs(path_str):
        return path_str
    return os.path.join(OPTICAL_LIB_DIR, path_str)


# Load LED definitions from JSON
led_json_path = os.path.join(OPTICAL_LIB_DIR, "LED_Surface_Sources.json")
if not os.path.isfile(led_json_path):
    raise IOError("LED definition file not found: " + led_json_path)

with open(led_json_path, "r") as f:
    leds_invented = json.load(f)

# Loop over all bodies in the root part
for body in GetRootPart().GetAllBodies():
    body_name = body.GetName()

    # Check if the body's name contains any of the LED dictionary keys
    for key, data in leds_invented.items():
        if key in body_name:
            flux = data.get("Flux")
            spectrum_rel = data.get("Spectrum")
            spectrum_full = resolve_optical_path(spectrum_rel)

            # Create a new surface light source
            surface = SpeosSim.SourceSurface.Create()
            surface.Name = body_name

            # If a flux is provided, use it; otherwise, keep default
            if flux is not None:
                surface.FluxValueLuminous = float(flux)

            surface.SpectrumType = SpeosSim.SourceSurface.EnumSpectrumType.Library
            if spectrum_full:
                surface.SpectrumValueLibrary = spectrum_full

            surface.RayLength = 5  # mm

            # Assign the first face of the body as the emissive surface
            emissive_face = FaceSelection.Create(body.Faces[0])
            surface.EmissiveFaces.Set(emissive_face.Items)

            print("✓ Created light source: {0} | Flux: {1} | Spectrum: {2}".format(body_name, flux, spectrum_full))
