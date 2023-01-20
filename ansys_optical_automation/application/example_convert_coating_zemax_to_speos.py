import numpy as np

# repo_path=r"your repository location"
# sys.path.append(repo_path)
from ansys_optical_automation.interop_process.Coating_converter_speos_zemax_Analysis import Coating_converter_speos_zemax_Analysis


# USER INPUT
coatingfilename = "CoatingFileExample.dat"
coatingfolder = r"C:\Data\Zemax\Coatings"
user_wavelength_min = 0.31
user_wavelength_max = 0.9
nb_wavelength = 5
speos_wavelength_units_um = 1000  # Wavelength unit in Speos in um
# Coating substrates: 2 coatings are extracted per substrates: air -> substrate and substrate -> air
substrate_catalog = "SCHOTT"
# substrate_name = ["N-SK16", "N-SF56", "SF4"]
substrate_name = ["N-BK7"]
nb_digits = 6  # Number of digits
skip_lines = 4 # Zemax returns 401 points when reading the R/T analysis. skip_lines = 4 means we read only 81 points

Coating_converter_speos_zemax_Analysis(coatingfilename, coatingfolder,
                                       substrate_catalog, substrate_name,
                                       user_wavelength_min, user_wavelength_max,
                                       nb_wavelength, speos_wavelength_units_um,
                                       nb_digits,
                                       skip_lines)
