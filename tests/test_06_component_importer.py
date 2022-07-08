import json
import os

from ansys_optical_automation.scdm_core.utils import run_scdm_batch

from .config import API_VERSION
from .config import SCDM_VERSION

os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


class TestComponentImporterAPI:
    """
    Defines conditions for running unit tests in PyTest.
    """

    def setup_class(self):
        """
        Called before tests to initialize the ``scdm`` class and open a new SCDM session.
        Returns:
        """

        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.results_file = os.path.join(self.local_path, "workflows", "test_06_results.json")
        reference_file = os.path.join(self.local_path, "workflows", "test_06_reference_results.json")
        self.clean_results(self)  # no idea why but you have to pass there self
        scdm_script_path = os.path.join(self.local_path, "workflows", "run_test_06_component_importer.py")
        run_scdm_batch(SCDM_VERSION, API_VERSION, scdm_script_path)

        with open(self.results_file) as file:
            self.results = json.load(file)

        with open(reference_file) as file:
            self.reference_results = json.load(file)

    def teardown_class(self):
        """
        Called after all tests are completed to clean up the SCDM session
        and clean the results file.

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
        -------
        None
        """
        if os.path.isfile(self.results_file):
            os.remove(self.results_file)

    def test_01_check_target_axis_system_information(self):
        """
        Check that axis system information is extracted correctly.
        Returns:
        -------
        None
        """
        res = self.results.get("target axis systems location", None)
        ref = self.reference_results["target axis systems location"]
        assert res == ref

    def test_02_check_imported_part_location(self):
        """
        Check parts are imported correctly.
        Returns:
        -------
        None
        """
        res = self.results.get("imported parts locations", None)
        ref = self.reference_results["imported parts locations"]
        assert res == ref

    def test_03_compared_target_and_imported_locations(self):
        """
        Compare target and imported part locations.
        Returns
        -------
        None
        """
        res = self.results.get("compare imported with target locations", None)
        assert res is True

    def test_04_check_anchor_operation(self):
        """
        Check if the anchor is applied correctly.
        Returns:
        -------
        None
        """
        res = self.results.get("check anchor", None)
        assert res is True

    def test_05_check_anchor_operation(self):
        """
        Check if the lock is applied correctly.
        Returns:
        -------
        None
        """
        res = self.results.get("check lock", None)
        assert res is True

    def test_06_check_imported_structure(self):
        """
        Compare the structure results after the ``LED`` class is imported.
        Returns:
        -------
        None
        """
        res = self.results.get("components structure", None)
        ref = self.reference_results["components structure"]
        assert res == ref

    def test_07_check_source_group_created(self):
        """
        Check if groups of Speos surface sources have been created.
        Returns
        -------
        None
        """
        res = self.results.get("check speos sources group", None)
        ref = self.reference_results["check speos sources group"]
        assert res == ref
