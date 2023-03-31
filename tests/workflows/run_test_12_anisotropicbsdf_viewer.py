import os

from ansys_optical_automation.interop_process.BSDF_converter import (
    obsolete_convert_zemax_to_speos_bsdf,
)


def unittest_run():
    """
    main function to run conversion.

    Returns
    -------


    """
    cwd = os.path.dirname(os.path.realpath(__file__))
    inputFilepath = os.path.join(cwd, "example_models", "test_12_anisotropicbsdf_viewer_zemax.bsdf")
    outputFilepath = os.path.join(cwd, "example_models", "test_12_anisotropicbsdf_viewer_speos.bsdf")
    obsolete_convert_zemax_to_speos_bsdf(inputFilepath, outputFilepath, 1, 1)