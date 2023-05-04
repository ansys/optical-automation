import os

from .workflows.run_test_13_anisotropicbsdf_viewer import unittest_run


class TestAnisotropicbsdfAPI:
    """
    Defines conditions for running unit tests in PyTest.
    """

    def setup_class(self):
        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.reference_file_speos_1 = os.path.join(
            self.local_path,
            "workflows",
            "example_models",
            "test_13_planesymmetric_brdf_speos_reference.anisotropicbsdf",
        )
        self.reference_file_speos_2 = os.path.join(
            self.local_path,
            "workflows",
            "example_models",
            "test_13_planesymmetric_btdf_speos_reference.anisotropicbsdf",
        )
        self.reference_file_speos_3 = os.path.join(
            self.local_path,
            "workflows",
            "example_models",
            "test_13_asymmetrical4d_btdf_speos_reference.anisotropicbsdf",
        )

        self.results_file_speos_1 = os.path.join(
            self.local_path, "workflows", "example_models", "test_13_planesymmetric_brdf_zemax.anisotropicbsdf"
        )
        self.results_file_speos_2 = os.path.join(
            self.local_path, "workflows", "example_models", "test_13_planesymmetric_btdf_zemax.anisotropicbsdf"
        )
        self.results_file_speos_3 = os.path.join(
            self.local_path, "workflows", "example_models", "test_13_asymmetrical4d_btdf_zemax.anisotropicbsdf"
        )

        self.clean_results(self)  # no idea why but you have to pass there self

        print("Start Anisotropic BSDF to generate file for tests.")
        unittest_run()

    def teardown_class(self):
        """
        Called after all tests are completed to clean the results file.

        On fail will report traceback with lines where the code failed.
        """
        self.clean_results(self)

    def clean_results(self):
        """
        Delete results file to avoid confusion.
        Returns:
        """
        if os.path.isfile(self.results_file_speos_1):
            os.remove(self.results_file_speos_1)
        if os.path.isfile(self.results_file_speos_2):
            os.remove(self.results_file_speos_2)
        if os.path.isfile(self.results_file_speos_3):
            os.remove(self.results_file_speos_3)

    def test_01_speos_anisotropic_bsdf_generated(self):
        """
        Verify brdf content is loaded and file generated
        Returns:
        -------
        None
        """
        assert os.path.exists(self.results_file_speos_1)
        assert os.path.exists(self.results_file_speos_2)
        assert os.path.exists(self.results_file_speos_3)

    def test_02_verify_generated_speos_brdf_planesymmetric_bsdf_file(self):
        """
        Verify brdf file is corrected generated via comparing to a reference
        Returns
        -------
        None
        """

        res_file = open(self.results_file_speos_1, "r")
        ref_file = open(self.reference_file_speos_1, "r")
        res = res_file.read()
        ref = ref_file.read()
        res_file.close()
        ref_file.close()
        assert res == ref

    def test_03_verify_generated_speos_btdf_planesymmetric_bsdf_file(self):
        """
        Verify brdf file is corrected generated via comparing to a reference
        Returns
        -------
        None
        """

        res_file = open(self.results_file_speos_2, "r")
        ref_file = open(self.reference_file_speos_2, "r")
        res = res_file.read()
        ref = ref_file.read()
        res_file.close()
        ref_file.close()
        assert res == ref

    def test_04_verify_generated_speos_btdf_anisotropic_bsdf_file(self):
        """
        Verify brdf file is corrected generated via comparing to a reference
        Returns
        -------
        None
        """

        res_file = open(self.results_file_speos_3, "r")
        ref_file = open(self.reference_file_speos_3, "r")
        res = res_file.read()
        ref = ref_file.read()
        res_file.close()
        ref_file.close()
        assert res == ref
