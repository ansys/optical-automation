import json
import subprocess
import sys
import os

sys.path.append(r"D:\Git\AnsysAutomation\SCLib")  # temp paths until updates not in SCLib package
sys.path.append(r"C:\git\ansys_automation\SCLib")

import scdm_api_import
scdm_install_dir = scdm_api_import.get_scdm_location(211)


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
        self.results_file = os.path.join(self.local_path, "input", "results.json")
        reference_file = os.path.join(self.local_path, "input", "reference_results.json")
        self.clean_results(self)  # no idea why but you have to pass there self

        scdm_exe = os.path.join(scdm_install_dir, "SpaceClaim.exe")
        scdm_script_path = os.path.join(self.local_path, "input", "run_preprocessing_asp.py")
        print("Start SCDM to generate JSON file for tests")
        command = [scdm_exe, r'/RunScript={}'.format(scdm_script_path),
                   r"/Headless=True", r"/Splash=False", r"/Welcome=False", r"/ExitAfterScript=True",
                   r"/ScriptAPI=20"]
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
        assert self.results.get("colors", None) == self.reference_results["colors"]

    def test_02_duplicates_and_stitch(self):
        """
        Function to compare the results of remove_duplicates() and stitch_comp()
        Returns: None
        """
        assert self.results.get("center_coord", None) == self.reference_results["center_coord"]

    def test_03_check_mateirals(self):
        """
        Function to compare the results of create_dict_by_material()
        Returns: None
        """
        assert self.results.get("materials", None) == self.reference_results["materials"]

    def test_04_check_name_selection(self):
        """
        Function to compare the results of create_named_selection()
        Returns: None
        """
        assert self.results.get("name_selection", None) == self.reference_results["name_selection"]

