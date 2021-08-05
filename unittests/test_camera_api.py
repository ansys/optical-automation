import json
import subprocess
import os
from SPEOS_scripts.SpaceClaimCore.base import get_scdm_install_location

# User Input
SCDM_VERSION = 212  # version of SCDM you want to test

# Code
scdm_install_dir = get_scdm_install_location(SCDM_VERSION)
speos_path = os.path.join(os.path.dirname(scdm_install_dir), "Optical Products", "SPEOS", "Bin", "SpeosSC.Manifest.xml")


class TestMaterialAPI:
    """
    Class to define conditions for run of unit tests in PyTest
    """

    def setup_class(self):
        """
        Called before tests to initialize scdm class and open new SCDM session
        Returns:
        """

        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.results_file = os.path.join(self.local_path, "input", "results_camera.json")
        reference_file = os.path.join(self.local_path, "input", "reference_results_camera.json")
        self.clean_results(self)  # no idea why but you have to pass there self

        scdm_exe = os.path.join(scdm_install_dir, "SpaceClaim.exe")
        scdm_script_path = os.path.join(self.local_path, "input", "run_camera_api.py")
        print("Start SPEOS to generate JSON file for tests")
        command = [scdm_exe,
                   r"/AddInManifestFile={}".format(speos_path),
                   r'/RunScript={}'.format(scdm_script_path),
                   r"/Headless=True", r"/Splash=False", r"/Welcome=False", r"/ExitAfterScript=True",
                   r"/ScriptAPI=21"]
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

    def test_01_check_camera_created(self):
        """
        Function to compare the results of the camera class initialization
        Returns: None
        """
        res = self.results.get("camera_exists", None)
        ref = self.reference_results["camera_exists"]
        assert res == ref

    def test_02_check_origin(self):
        """
        Function to compare the results of Camera.set_position() - Camera origin
        Returns: None
        """
        res = self.results.get("camera_origin", None)
        ref = self.reference_results["camera_origin"]
        assert res == ref

    def test_03_check_x_axis(self):
        """
        Function to compare the results of Camera.set_position() - X Direction
        Returns: None
        """
        res = self.results.get("camera_x_axis", None)
        ref = self.reference_results["camera_x_axis"]
        assert res == ref

    def test_04_check_y_axis(self):
        """
        Function to compare the results of Camera.set_position() - Y Direction
        Returns: None
        """
        res = self.results.get("camera_y_axis", None)
        ref = self.reference_results["camera_y_axis"]
        assert res == ref

    def test_05_check_x_reverse_true(self):
        """
        Function to compare the results of Camera.set_position() - Y Direction
        Returns: None
        """
        res = self.results.get("camera_x_reverse_true", None)
        ref = self.reference_results["camera_x_reverse_true"]
        assert res == ref

    def test_06_check_y_reverse_true(self):
        """
        Function to compare the results of Camera.set_position() - Y Direction
        Returns: None
        """
        res = self.results.get("camera_y_reverse_true", None)
        ref = self.reference_results["camera_y_reverse_true"]
        assert res == ref

    def test_07_check_origin_axsys(self):
        """
        Function to compare the results of Camera.set_position() - Y Direction
        Returns: None
        """
        res = self.results.get("camera_origin_axsys", None)
        ref = self.reference_results["camera_origin_axsys"]
        assert res == ref

    def test_08_check_x_reverse_false(self):
        """
        Function to compare the results of Camera.set_position() - Y Direction
        Returns: None
        """
        res = self.results.get("camera_x_reverse_false", None)
        ref = self.reference_results["camera_x_reverse_false"]
        assert res == ref

    def test_09_check_y_reverse_false(self):
        """
        Function to compare the results of Camera.set_position() - Y Direction
        Returns: None
        """
        res = self.results.get("camera_y_reverse_false", None)
        ref = self.reference_results["camera_y_reverse_false"]
        assert res == ref
