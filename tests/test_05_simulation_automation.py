import json
import os
import subprocess

from ansys_optical_automation.scdm_core.base import get_scdm_install_location

# User Input
SCDM_VERSION = 221  # version of SCDM you want to test

# Code
scdm_install_dir = get_scdm_install_location(SCDM_VERSION)
speos_path = os.path.join(os.path.dirname(scdm_install_dir), "Optical Products", "SPEOS", "Bin", "SpeosSC.Manifest.xml")


class TestSimAutomation:
    """
    Class to define conditions for run of unit tests in PyTest
    """

    def setup_class(self):
        """
        Called before tests to initialize scdm class and open new SCDM session
        Returns:
        """

        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.results_file = os.path.join(self.local_path, "workflows", "test_05_results.json")
        reference_file = os.path.join(self.local_path, "workflows", "test_05_reference_results.json")
        self.clean_results(self)  # no idea why but you have to pass there self

        scdm_exe = os.path.join(scdm_install_dir, "SpaceClaim.exe")
        scdm_script_path = os.path.join(self.local_path, "workflows", "test_05_run_simulation_automation.py")
        print("Start SPEOS to generate JSON file for tests")
        command = [
            scdm_exe,
            r"/AddInManifestFile={}".format(speos_path),
            r"/RunScript={}".format(scdm_script_path),
            r"/Headless=True",
            r"/Splash=False",
            r"/Welcome=False",
            r"/ExitAfterScript=True",
            r"/ScriptAPI=21",
        ]
        print(command)
        subprocess.call(command)

        with open(self.results_file) as file:
            self.results = json.load(file)

        with open(reference_file) as file:
            self.reference_results = json.load(file)

    def teardown_class(self):
        """
        Called after all tests are completed to clean up SCDM session
        clean results file.

        On fail will report traceback with lines where code failed
        """
        self.clean_results(self)

        print("\n\n\n\n\n###############################")
        print(self.results.get("error", "All tests are successful"))
        print("###############################\n\n\n\n\n")

    def clean_results(self):
        """
        Delete results file to avoid confusion
        Returns:
        """
        if os.path.isfile(self.results_file):
            os.remove(self.results_file)

    def test_01_sim_created(self):
        """
        Function to compare the result of Simulation class init method
        Returns: None
        """

        ref = self.reference_results["simulation_created"]
        res = self.results.get("simulation_created", None)
        assert res == ref

    def test_02_camera_spectra(self):
        """
        Function to compare the result of Camera.set_sensitivity()
        Returns: None
        """
        res_red = self.results.get("red_spectrum", None)
        ref_red = self.reference_results["red_spectrum"]
        res_green = self.results.get("green_spectrum", None)
        ref_green = self.reference_results["green_spectrum"]
        res_blue = self.results.get("blue_spectrum", None)
        ref_blue = self.reference_results["blue_spectrum"]
        test_passed = res_red == ref_red and res_green == ref_green and res_blue == ref_blue
        assert test_passed

    def test_03_camera_exists(self):
        """
        Function to compare the result of Camera class init method
        Returns: None
        """
        res = self.results.get("camera_exists", None)
        ref = self.reference_results["camera_exists"]
        assert res == ref

    def test_04_grid_exported(self):
        """
        Function to compare the result of Simulation.export_grid()
        Returns: None
        """
        res = self.results.get("grid_exported", None)
        ref = self.reference_results["grid_exported"]
        assert res == ref

    def test_05_camera_distortion(self):
        """
        Function to compare the result of Camera.set_distortion()
        Returns: None
        """
        res = self.results.get("distortion", None)
        ref = self.reference_results["distortion"]
        assert res == ref

    def test_06_check_output(self):
        """
        Function to compare the result of Simulation.run_simulation()
        Returns: None
        """
        res = self.results.get("output_exists", None)
        ref = self.reference_results["output_exists"]
        assert res == ref

    def test_07_grid_parameters(self):
        """
        Function to compare the result of Simulation.set_grid_params()
        Returns: None
        """
        res = self.results.get("grid_parameters", None)
        ref = self.reference_results["grid_parameters"]
        assert res == ref

    def test_08_camera_transmittance(self):
        """
        Function to compare the result of Camera.set_transmittance()
        Returns: None
        """
        res = self.results.get("transmittance", None)
        ref = self.reference_results["transmittance"]
        assert res == ref

    def test_09_curves_exported(self):
        """
        Function to compare the result of Simulation.export_grid()
        Returns: None
        """
        res = self.results.get("curves_exported", None)
        ref = self.reference_results["curves_exported"]
        assert res == ref

    def test_10_sensor_added(self):
        """
        Function to compare the result of Simulation.add_sensor()
        Returns: None
        """
        res = self.results.get("sensor_added", None)
        ref = self.reference_results["sensor_added"]
        assert res == ref

    def test_11_sensor_name(self):
        """
        Function to compare the result of Simulation.add_sensor()
        Returns: None
        """
        res = self.results.get("sensor_name", None)
        ref = self.reference_results["sensor_name"]
        assert res == ref
