import json
import os

from .workflows.run_test_12_coating import unittest_run


class TestCoatingfileAPI:
    """
    Defines conditions for running unit tests in PyTest.
    """

    def setup_class(self):
        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.results_file = os.path.join(self.local_path, "workflows", "test_12_coatingfile_results.json")
        reference_file = os.path.join(self.local_path, "workflows", "test_12_coatingfile_reference_results.json")
        self.clean_results(self)  # no idea why but you have to pass there self

        print("Start Coating converter to generate the JSON file for tests.")
        unittest_run()

        with open(self.results_file) as file:
            self.results = json.load(file)

        with open(reference_file) as file:
            self.reference_results = json.load(file)

    def teardown_class(self):
        """
        Called after all tests are completed to clean the results file.

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

    def test_01_convert_coating_to_coating1(self):
        """
        Verify coating to coating1.coated conversion works correctly.
        Returns:
        -------
        None
        """
        res = self.results.get("coating1_convert_coated", None)
        assert res is True

    def test_01_convert_coating_to_coating2(self):
        """
        Verify coating to coating2.coated conversion works correctly.
        Returns:
        -------
        None
        """
        res = self.results.get("coating2_convert_coated", None)
        assert res is True
