import os

from .config import LUMERICAL_VERSION
from .workflows.run_test_10_stack_interop import unittest_run


class TestStackInteropAPI:
    """
    Defines conditions for running unit tests in PyTest.
    """

    def setup_class(self):
        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.reference_file_speos = os.path.join(
            self.local_path, "workflows", "example_models", "test_10_stack_interop_speos_reference.coated"
        )
        self.reference_file_zemax = os.path.join(
            self.local_path, "workflows", "example_models", "test_10_stack_interop_speos_reference.dat"
        )
        self.results_file_speos = os.path.join(
            self.local_path, "workflows", "example_models", "test_10_stack_interop.coated"
        )
        self.results_file_zemax = os.path.join(
            self.local_path, "workflows", "example_models", "test_10_stack_interop.dat"
        )
        self.clean_results(self)  # no idea why but you have to pass there self

        print("Start Lumerical to generate file for tests.")
        unittest_run(LUMERICAL_VERSION)

    def teardown_class(self):
        """
        Called after all tests are completed to clean the results file.

        On fail will report traceback with lines where the code failed.
        """
        self.clean_results(self)

        print("\n\n\n\n\n###############################")
        # print(self.results.get("error", "All tests are successful."))
        print("###############################\n\n\n\n\n")

    def clean_results(self):
        """
        Delete results file to avoid confusion.
        Returns:
        """
        if os.path.isfile(self.results_file_speos):
            os.remove(self.results_file_speos)
        if os.path.isfile(self.results_file_zemax):
            os.remove(self.results_file_zemax)

    def test_01_stack_speos_generated(self):
        """
        Verify ldf content loaded and speos coated file generated
        Returns:
        -------
        None
        """
        assert os.path.exists(self.results_file_speos)

    def test_02_verify_generated_speos_coated_file(self):
        """
        Verify speos coated file is corrected generated via comparing to a reference
        Returns
        -------
        None
        """

        res_file = open(self.results_file_speos, "r")
        ref_file = open(self.reference_file_speos, "r")
        res = res_file.read()
        ref = ref_file.read()
        res_file.close()
        ref_file.close()
        assert res == ref

    def test_03_stack_speos_generated(self):
        """
        Verify ldf content loaded and zemax dat file generated
        Returns:
        -------
        None
        """
        assert os.path.exists(self.results_file_zemax)

    def test_04_verify_generated_zemax_coated_file(self):
        """
        Verify zemax dat file is corrected generated via comparing to a reference
        Returns
        -------
        None
        """

        res_file = open(self.results_file_zemax, "r")
        ref_file = open(self.reference_file_zemax, "r")
        res = res_file.read()
        ref = ref_file.read()
        res_file.close()
        ref_file.close()
        assert res == ref
