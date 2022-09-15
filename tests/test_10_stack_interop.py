import os

from .workflows.run_test_10_stack_interop import unittest_run


class TestStackInteropAPI:
    """
    Defines conditions for running unit tests in PyTest.
    """

    def setup_class(self):
        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.reference_file = os.path.join(
            self.local_path, "workflows", "example_models", "test_10_stack_interop_speos_reference.coated"
        )
        self.results_file = os.path.join(self.local_path, "workflows", "example_models", "test_10_stack_interop.coated")
        self.clean_results(self)  # no idea why but you have to pass there self

        print("Start Lumerical to generate file for tests.")
        unittest_run()

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
        if os.path.isfile(self.results_file):
            os.remove(self.results_file)

    def test_01_stack_speos_generated(self):
        """
        Verify sdf content loaded is correct
        Returns:
        -------
        None
        """
        assert os.path.exists(self.results_file)

    def test_02_verify_generated_coated_file(self):

        res_file = open(self.results_file, "r")
        ref_file = open(self.reference_file, "r")
        res = res_file.read()
        ref = ref_file.read()
        res_file.close()
        ref_file.close()
        assert res == ref
