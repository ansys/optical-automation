import json
import os

from ansys_optical_automation.lumerical_core.utils import run_lumerical_batch

from .config import LUMERICAL_VERSION

os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


class TestLumericalLaunchAPI:
    """
    Defines conditions for running unit tests in PyTest.
    """

    def setup_class(self):
        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.results_file = os.path.join(self.local_path, "workflows", "test_101_fdtd_launch_results.json")
        reference_file = os.path.join(self.local_path, "workflows", "test_101_fdtd_launch_reference_results.json")
        self.clean_results(self)  # no idea why but you have to pass there self

        lumerical_script_path = os.path.join(self.local_path, "workflows", "run_test_101_fdtd_launch.lsf")
        lumerical_pwd = os.path.join(self.local_path, "workflows")
        os.chdir(lumerical_pwd)
        print("lumerical script to run: ", lumerical_script_path)
        run_lumerical_batch("FDTD-Solutions", LUMERICAL_VERSION, lumerical_script_path)

        with open(self.results_file) as file:
            self.results = json.load(file)

        with open(reference_file) as file:
            self.reference_results = json.load(file)

    def teardown_class(self):
        """
        Called after all tests are completed to clean up the lumerical session
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

    def test_01_check_lumerical_launch(self):
        """
        Compare the results of created json with expected results.
        Returns: None
        """
        res = self.results.get("x", None)
        ref = self.reference_results["x"]
        assert res == ref
