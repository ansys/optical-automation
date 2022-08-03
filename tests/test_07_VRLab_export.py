import json
import os
import subprocess

import pytest

from .workflows.run_test_07_VRLab_export import unittest_run

Nvidia_GPU = False
try:
    subprocess.check_output("nvidia-smi")
    Nvidia_GPU = True
except Exception:
    Nvidia_GPU = False


@pytest.mark.skipif(Nvidia_GPU is False, reason="does not have gpu on runner")
class TestVRLabExportAPI:
    """
    Defines conditions for running unit tests in PyTest.
    """

    def setup_class(self):
        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.results_file = os.path.join(self.local_path, "workflows", "test_07_VRLab_results.json")
        reference_file = os.path.join(self.local_path, "workflows", "test_07_VRLab_reference_results.json")
        self.clean_results(self)  # no idea why but you have to pass there self

        print("Start VRLab to generate the JSON file for tests.")
        unittest_run()

        with open(self.results_file) as file:
            self.results = json.load(file)

        with open(reference_file) as file:
            self.reference_results = json.load(file)

    def teardown_class(self):
        """
        Called after all tests are completed to the VRlabs session and clean the results file.

        On fail will report traceback with lines where the code failed.
        """
        self.clean_results(self)

        print("\n\n\n\n\n###############################")
        print(self.results.get("error", "All tests are successful."))
        print("###############################\n\n\n\n\n")

    def clean_results(self):
        """
        Delete results file to avoid confusion.
        Returns:
        """
        if os.path.isfile(self.results_file):
            os.remove(self.results_file)

    def test_01_check_exported_images_name_size(self):
        """
        Compare the results of created images with expected images.
        Returns: None
        """
        res = self.results.get("VRImages", None)
        ref = self.reference_results["VRImages"]
        assert res == ref
