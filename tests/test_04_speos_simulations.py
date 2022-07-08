import json
import os

from ansys_optical_automation.scdm_core.utils import run_scdm_batch

from .config import API_VERSION
from .config import SCDM_VERSION

os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


class TestSimAPI:
    """
    Defines conditions for running unit tests in PyTest.
    """

    def setup_class(self):
        """
        Called before tests to initialize the ``scdm`` class and open a new SCDM session.
        Returns:
        """

        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.results_file = os.path.join(self.local_path, "workflows", "test_04_results.json")
        reference_file = os.path.join(self.local_path, "workflows", "test_04_reference_results.json")
        self.clean_results(self)  # no idea why but you have to pass there self
        scdm_script_path = os.path.join(self.local_path, "workflows", "run_test_04_speos_simulations.py")
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
        print(self.results.get("error", "All tests are successful"))
        print("###############################\n\n\n\n\n")

    def clean_results(self):
        """
        Delete results file to avoid confusion.
        Returns:
        """
        if os.path.isfile(self.results_file):
            os.remove(self.results_file)

    def test_01_check_sim_created(self):
        """
        Compare the results of the ``Simulation`` class initialization method.
        Returns: None
        """
        res = self.results.get("simulation_created", None)
        ref = self.reference_results["simulation_created"]
        assert res == ref

    def test_02_test_select_geometrical_sets(self):
        """
        Compare the results of the ``select_geometrical_sets`` method.
        Returns: None
        """
        res = self.results.get("number_of_selected_bodies_in_geoset", None)
        ref = self.reference_results["number_of_selected_bodies_in_geoset"]
        assert res == ref

    def test_03_test_select_geometries(self):
        """
        Compare the results of the ``select_geometries`` method.
        Returns: None
        """
        res = self.results.get("number_of_selected_bodies_in_component", None)
        ref = self.reference_results["number_of_selected_bodies_in_component"]
        assert res == ref

    def test_04_test_define_geometries(self):
        """
        Compare the results of the ``define_geometries`` method.
        Returns: None
        """
        res = self.results.get("number_of_geos_defined", None)
        ref = self.reference_results["number_of_geos_defined"]
        assert res == ref

    def test_05_test_rays_limit(self):
        """
        Compare the results of the ``set_rays_limit`` method.
        Returns: None
        """
        res = self.results.get("number_of_passes", None)
        ref = self.reference_results["number_of_passes"]
        assert res == ref
