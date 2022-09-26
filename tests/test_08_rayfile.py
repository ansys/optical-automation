import json
import os

from .workflows.run_test_08_rayfile import unittest_run


class TestRayfileAPI:
    """
    Defines conditions for running unit tests in PyTest.
    """

    def setup_class(self):
        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.results_file = os.path.join(self.local_path, "workflows", "test_08_rayfile_results.json")
        reference_file = os.path.join(self.local_path, "workflows", "test_08_rayfile_reference_results.json")
        self.clean_results(self)  # no idea why but you have to pass there self

        print("Start VRLab to generate the JSON file for tests.")
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

    def test_01_load_sdf_data(self):
        """
        Verify sdf content loaded is correct
        Returns:
        -------
        None
        """
        res = self.results.get("sdf_content", None)
        ref = self.reference_results["sdf_content"]
        assert res == ref

    def test_02_load_dat_data(self):
        """
        Verify dat content loaded is correct
        Returns:
        -------
        None
        """
        res = self.results.get("dat_content", None)
        ref = self.reference_results["dat_content"]
        assert res == ref

    def test_03_load_ray_data(self):
        """
        Verify ray content loaded is correct
        Returns:
        -------
        None
        """
        res = self.results.get("ray_content", None)
        ref = self.reference_results["ray_content"]
        assert res == ref

    def test_04_convert_dat_to_ray(self):
        """
        Verify dat to ray conversion works correctly
        Returns:
        -------
        None
        """
        res = self.results.get("dat_convert_ray", None)
        assert res is True

    def test_05_convert_ray_to_sdf(self):
        """
        Verify ray to sdf conversion works correctly.
        Returns:
        -------
        None
        """
        res = self.results.get("ray_convert_sdf", None)
        assert res is True

    def test_06_convert_sdf_to_ray(self):
        """
        Verify sdf to ray conversion works correctly.
        Returns:
        -------
        None
        """
        res = self.results.get("sdf_convert_ray", None)
        assert res is True

    def test_07_check_sdf_in_sim(self):
        """
        Check if a Simulation performed with a converted *.sdf file is working in Speos sim
        Returns:
        -------
        None
        """
        res = self.results.get("sdf_ray_sim", None)
        assert res is True

    def test_08_check_dat_in_sim(self):
        """
        Check if a Simulation performed with a converted *.dat file is working in Speos sim
        Returns:
        -------
        None
        """
        res = self.results.get("dat_ray_sim", None)
        assert res is True

    def test_09_check_ray_in_sim(self):
        """
        Check if a Simulation performed with a converted *.ray file is working in Zemax sim
        Returns:
        -------
        None
        """
        res = self.results.get("ray_sdf_sim", None)
        assert res is True
