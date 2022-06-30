import json
import os

from ansys_optical_automation.scdm_core.utils import run_scdm_batch

from .config import API_VERSION
from .config import SCDM_VERSION

os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


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
        scdm_script_path = os.path.join(self.local_path, "workflows", "run_test_02_preprocessing_lib.py")
        run_scdm_batch(SCDM_VERSION, API_VERSION, scdm_script_path)

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
        assert res == ref

    def test_02_duplicates_and_stitch(self):
        """
        Function to compare the results of remove_duplicates() and stitch_comp()
        Returns: None
        """
        # Generate test log for ARM
        res = self.results.get("center_coord", None)
        ref = self.reference_results["center_coord"]
        assert res == ref

    def test_03_check_materials(self):
        """
        Function to compare the results of create_dict_by_material()
        Returns: None
        """
        # Generate test log for ARM
        res = self.results.get("materials", None)
        ref = self.reference_results["materials"]
        assert res == ref

    def test_04_check_name_selection(self):
        """
        Function to compare the results of create_named_selection()
        Returns: None
        """
        # Generate test log for ARM
        res = self.results.get("name_selection", None)
        ref = self.reference_results["name_selection"]
        assert res == ref
