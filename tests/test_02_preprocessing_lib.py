import json
import os
import subprocess

from ansys_optical_automation.scdm_core.base import get_scdm_install_location
from tests.ansys_arm.ansys_arm import write_arm_log

# User Input
SCDM_VERSION = 221  # version of SCDM you want to test

# Code
scdm_install_dir = get_scdm_install_location(SCDM_VERSION)


class TestPreprocessing:
    """
    Class to define conditions for run of unit tests in PyTest
    """

    def setup_class(self):
        """
        Called before tests to initialize scdm class and open new SCDM session
        Returns:
        """

        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.results_file = os.path.join(self.local_path, "workflows", "test_02_results.json")
        reference_file = os.path.join(self.local_path, "workflows", "test_02_reference_results.json")
        self.clean_results(self)  # no idea why but you have to pass there self
        self.testlog_file = os.path.join(self.local_path, "workflows", "testlog.log")

        # remove ARM log file if exists
        if os.path.isfile(self.testlog_file):
            os.remove(self.testlog_file)

        scdm_exe = os.path.join(scdm_install_dir, "SpaceClaim.exe")
        scdm_script_path = os.path.join(self.local_path, "workflows", "test_02_run_preprocessing_lib.py")
        print("Start SCDM to generate JSON file for tests")
        command = [
            scdm_exe,
            r"/RunScript={}".format(scdm_script_path),
            r"/Headless=True",
            r"/Splash=False",
            r"/Welcome=False",
            r"/ExitAfterScript=True",
            r"/ScriptAPI=21",
        ]
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

    def test_01_check_color(self):
        """
        Function to compare the results of create_dict_by_color()
        Returns: None
        """
        # Generate test log for ARM
        res = self.results.get("colors", None)
        ref = self.reference_results["colors"]
        test_passed = res == ref
        write_arm_log(self.testlog_file, test_id=1, test_name="check_color", test_passed=test_passed)
        assert test_passed

    def test_02_duplicates_and_stitch(self):
        """
        Function to compare the results of remove_duplicates() and stitch_comp()
        Returns: None
        """
        # Generate test log for ARM
        res = self.results.get("center_coord", None)
        ref = self.reference_results["center_coord"]
        test_passed = res == ref
        write_arm_log(self.testlog_file, test_id=2, test_name="duplicates_and_stitch", test_passed=test_passed)
        assert test_passed

    def test_03_check_materials(self):
        """
        Function to compare the results of create_dict_by_material()
        Returns: None
        """
        # Generate test log for ARM
        res = self.results.get("materials", None)
        ref = self.reference_results["materials"]
        test_passed = res == ref
        write_arm_log(self.testlog_file, test_id=3, test_name="check_materials", test_passed=test_passed)
        assert test_passed

    def test_04_check_name_selection(self):
        """
        Function to compare the results of create_named_selection()
        Returns: None
        """
        # Generate test log for ARM
        res = self.results.get("name_selection", None)
        ref = self.reference_results["name_selection"]
        test_passed = res == ref
        write_arm_log(self.testlog_file, test_id=4, test_name="check_name_selection", test_passed=test_passed)
        assert test_passed
