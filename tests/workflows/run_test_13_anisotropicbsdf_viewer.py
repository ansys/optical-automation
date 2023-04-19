import os

from ansys_optical_automation.interop_process.BSDF_converter import BsdfStructure


def unittest_run():
    """
    main function to run conversion.

    Returns
    -------


    """
    bsdf_data = BsdfStructure()
    cwd = os.path.dirname(os.path.realpath(__file__))
    bsdf_data.filename_input = os.path.join(cwd, "example_models", "test_12_anisotropicbsdf_viewer_zemax.bsdf")
    # outputFilepath = os.path.join(cwd, "example_models", "test_12_anisotropicbsdf_viewer_speos.bsdf")
    bsdf_data.import_data(0)
    bsdf_data.write_speos_anisotropicbsdf_file()
