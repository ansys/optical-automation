import json
import os
import subprocess


class TestVRLabExportAPI:
    """
    Class to define conditions for run of unit tests in PyTest
    """

    def setup_class(self):
        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.results_file = os.path.join(self.local_path, "workflows", "test_07_VRLab_results.json")
        reference_file = os.path.join(self.local_path, "workflows", "test_07_VRLab_reference_results.json")
        self.clean_results(self)  # no idea why but you have to pass there self

        script_path = os.path.join(self.local_path, "workflows", "test_07_run_VRLab_export.py")
        print("Start VRLab to generate JSON file for tests")
        command = ["python", script_path]
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

    def test_01_check_exported_images_name_size(self):
        """
        Function to compare the results of the created images with the expected images
        Returns: None
        """
        res = self.results.get("VRImages", None)
        ref = self.reference_results["VRImages"]
        assert res == ref
