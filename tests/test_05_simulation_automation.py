import json
import os

from ansys_optical_automation.scdm_core.utils import run_scdm_batch

from .config import API_VERSION
from .config import SCDM_VERSION

os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


class TestSimAutomation:
    """
    Defines conditions for running unit tests in PyTest.
    """

    def setup_class(self):
        """
        Called before tests to initialize the ``scdm`` class and open a new SCDM session.
        Returns:
        """

        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.results_file = os.path.join(self.local_path, "workflows", "test_05_results.json")
        reference_file = os.path.join(self.local_path, "workflows", "test_05_reference_results.json")
        self.clean_results(self)  # no idea why but you have to pass there self
        scdm_script_path = os.path.join(self.local_path, "workflows", "run_test_05_simulation_automation.py")
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

    def test_01_sim_created(self):
        """
        Compare the result of the ``Simulation`` class initialization method.
        Returns: None
        """

        ref = self.reference_results["simulation_created"]
        res = self.results.get("simulation_created", None)
        assert res == ref

    def test_02_camera_spectra(self):
        """
        Compare the result of the ``Camera.set_sensitivity`` method.
        Returns: None
        """
        res_red = self.results.get("red_spectrum", None)
        ref_red = self.reference_results["red_spectrum"]
        res_green = self.results.get("green_spectrum", None)
        ref_green = self.reference_results["green_spectrum"]
        res_blue = self.results.get("blue_spectrum", None)
        ref_blue = self.reference_results["blue_spectrum"]
        test_passed = res_red == ref_red and res_green == ref_green and res_blue == ref_blue
        assert test_passed

    def test_03_camera_exists(self):
        """
        Compare the result of the ``Camera`` class initialization method.
        Returns: None
        """
        res = self.results.get("camera_exists", None)
        ref = self.reference_results["camera_exists"]
        assert res == ref

    def test_04_grid_exported(self):
        """
        Compare the result of the ``Simulation.export_grid`` method.
        Returns: None
        """
        res = self.results.get("grid_exported", None)
        ref = self.reference_results["grid_exported"]
        assert res == ref

    def test_05_camera_distortion(self):
        """
        Compare the result of the ``Camera.set_distortion`` method.
        Returns: None
        """
        res = self.results.get("distortion", None)
        ref = self.reference_results["distortion"]
        assert res == ref

    def test_06_check_output(self):
        """
        Compare the result of the ``Simulation.run_simulation`` method.
        Returns: None
        """
        res = self.results.get("output_exists", None)
        ref = self.reference_results["output_exists"]
        assert res == ref

    def test_07_grid_parameters(self):
        """
        Compare the result of the ``Simulation.set_grid_params`` method.
        Returns: None
        """
        res = self.results.get("grid_parameters", None)
        ref = self.reference_results["grid_parameters"]
        assert res == ref

    def test_08_camera_transmittance(self):
        """
        Compare the result of ``Camera.set_transmittance`` method.
        Returns: None
        """
        res = self.results.get("transmittance", None)
        ref = self.reference_results["transmittance"]
        assert res == ref

    def test_09_curves_exported(self):
        """
        Compare the result of the ``Simulation.export_grid`` method.
        Returns: None
        """
        res = self.results.get("curves_exported", None)
        ref = self.reference_results["curves_exported"]
        assert res == ref

    def test_10_sensor_added(self):
        """
        Compare the result of the ``Simulation.add_sensor`` method.
        Returns: None
        """
        res = self.results.get("sensor_added", None)
        ref = self.reference_results["sensor_added"]
        assert res == ref

    def test_11_sensor_name(self):
        """
        Compare the result of the ``Simulation.add_sensor`` method.
        Returns: None
        """
        res = self.results.get("sensor_name", None)
        ref = self.reference_results["sensor_name"]
        assert res == ref
