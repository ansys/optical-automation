import os

from ansys_optical_automation.interop_process.BSDF_converter import BsdfStructure


def unittest_run():
    """
    main function to run conversion.

    Returns
    -------


    """
    # Test 1
    bsdf_data = BsdfStructure()
    cwd = os.path.dirname(os.path.realpath(__file__))
    bsdf_data.filename_input = os.path.join(cwd, "example_models", "test_13_planesymmetric_brdf_zemax.bsdf")
    bsdf_data.import_data(0)
    bsdf_data.write_speos_anisotropicbsdf_file()

    # Test 2
    bsdf_data = BsdfStructure()
    cwd = os.path.dirname(os.path.realpath(__file__))
    bsdf_data.filename_input = os.path.join(cwd, "example_models", "test_13_planesymmetric_btdf_zemax.bsdf")
    bsdf_data.import_data(0)
    bsdf_data.write_speos_anisotropicbsdf_file()

    # Test 3
    bsdf_data = BsdfStructure()
    cwd = os.path.dirname(os.path.realpath(__file__))
    bsdf_data.filename_input = os.path.join(cwd, "example_models", "test_13_asymmetrical4d_btdf_zemax.bsdf")
    bsdf_data.import_data(0)
    bsdf_data.write_speos_anisotropicbsdf_file()

    # Test 3
    bsdf_data = BsdfStructure()
    cwd = os.path.dirname(os.path.realpath(__file__))
    bsdf_data.filename_input = os.path.join(cwd, "example_models", "test_13_brdf_one_wavelength_speos.brdf")
    bsdf_data.import_data(0)
    bsdf_data.write_zemax_file(0)
