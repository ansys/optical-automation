import json
import os

from .workflows.run_test_09_xmp_viewer import unittest_run


class TestXmpViewerAPI:
    """
    Defines conditions for running unit tests in PyTest.
    """

    def setup_class(self):
        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.results_file = os.path.join(self.local_path, "workflows", "test_09_xmp_viewer_results.json")
        reference_file = os.path.join(self.local_path, "workflows", "test_09_xmp_viewer_reference_results.json")
        self.clean_results(self)  # no idea why but you have to pass there self

        print("Start XMPviewer to generate the JSON file for tests.")
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

    def test_01_source_list(self):
        """
        Compares the sourcelist to the reference
        Returns
        -------
        None
        """
        res = self.results.get("source_list", None)
        ref = self.reference_results["source_list"]
        assert res == ref

    def test_02_export_data(self):
        """
        compare exported data size
        Returns
        -------
        None
        """
        allowed_exports = ["txt", "png", "bmp", "jpg", "tiff", "pf", "ies"]
        for export_type in allowed_exports:
            res = self.results.get("export_" + export_type, None)
            ref = self.reference_results["export_" + export_type]
            assert res == ref

    def test_03_import_txt(self):
        """
        compares imported xmp size
        Returns
        -------
        None
        """
        res = self.results.get("xmp_import", None)
        ref = self.reference_results["xmp_import"]
        assert res == ref

    def test_04_import_advanced(self):
        """
        Returns
        -------


        """
        res = self.results.get("xmp_import_data", None)
        ref = self.reference_results["xmp_import_data"]
        assert res == ref

    def test_05_export_measures(self):
        """
        compares size of exported measures txt
        Returns
        -------
        None
        """
        res = self.results.get("xmp_measures", None)
        ref = self.reference_results["xmp_measures"]
        assert res == ref

    def test_06_spectrum_export(self):
        """
        compares spectral values from xmp to the reference values
        Returns
        -------

        """
        res = self.results.get("xmp_measures", None)
        ref = self.reference_results["xmp_measures"]
        assert res == ref
