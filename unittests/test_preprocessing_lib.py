import subprocess
import sys
import os
import pytest
sys.path.append(r"D:\Git\AnsysAutomation\SCLib")  # temp paths until updates not in SCLib package
sys.path.append(r"C:\git\ansys_automation\SCLib")

import scdm_api_import
scdm_api_import.perform_imports(211, "V20")
from scdm_api_import import *


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
        scdm_exe = os.path.join(scdm_install_dir, "SpaceClaim.exe")
        scdm_script_path = os.path.join(self.local_path, "input", "run_preprocessing_asp.py")
        print("Start SCDM to generate JSON file for tests")
        command = [scdm_exe, r'/RunScript={}'.format(scdm_script_path),
                   r"/Headless=True", r"/Splash=False", r"/Welcome=False", r"/ExitAfterScript=True"]
        subprocess.call(command)

        self.json_file = os.path.join(self.local_path, "input", "results.json")

    def teardown_class(self):
        """
        Called after all tests are completed to clean up SCDM session
        Returns:
        """
        if os.path.isfile(self.json_file):
            os.remove(self.json_file)

    def test_01_check_json(self):
        assert os.path.isfile(self.json_file), "results.json file does not exist"

    def test_02_check_color(self):
        """
        Function to run flow of test in SCDM
        Returns: None
        """


