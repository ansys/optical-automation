import json
import os

from ansys_optical_automation.scdm_core.utils import run_scdm_batch

from .config import API_VERSION
from .config import SCDM_VERSION

os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


class TestMaterialAPI:
    """
    Defines conditions for running unit tests in PyTest.
    """

    def setup_class(self):
        """
        Called before tests to initialize the ``scdm`` class and open a new SCDM session.
        Returns:
        """

        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.results_file = os.path.join(self.local_path, "workflows", "test01_results.json")
        reference_file = os.path.join(self.local_path, "workflows", "test_01_reference_results.json")
        self.clean_results(self)  # no idea why but you have to pass there self
        scdm_script_path = os.path.join(self.local_path, "workflows", "run_test_01_material_application.py")
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
        """
        if os.path.isfile(self.results_file):
            os.remove(self.results_file)

    def test_01_check_optical_props(self):
        """
        Compare the results of the ``create_speos_material`` and ``apply_geo_to_material`` methods.
        Returns: None
        """
        res = self.results.get("speos_materials", None)
        ref = self.reference_results["speos_materials"]
        assert res == ref

    def test_02_check_layers(self):
        """
        Compare the results of the ``apply_geo_to_layer`` method.
        Returns: None
        """
        res = self.results.get("speos_layers", None)
        ref = self.reference_results["speos_layers"]
        assert res == ref

    def test_03_check_layer_material_synch(self):
        """
        Compare the results of the ``SynchLayersMaterials.sync_op_from_layers`` method.
        Returns: None
        """
        res = self.results.get("layer_synch_to_material", None)
        ref = self.reference_results["layer_synch_to_material"]
        assert res == ref
