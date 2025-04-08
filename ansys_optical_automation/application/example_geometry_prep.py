# Python Script, API Version = V232
# we find this example gives the best performance at ACISC mode
from ansys_optical_automation.scdm_process.preprocessing_library import PreProcessingASP


def run_stitch_prep(component, max_stitch_group):
    """
    function apply stitch to component.

    Parameters
    ----------
    component : SCDM Component
    max_stitch_group : int
        maximum number bodies applied for one stitch operation

    Returns
    -------


    """
    Prep = PreProcessingASP(SpaceClaim)
    Prep.stitch_comp(component, max_stitch_group)


def main():
    """
    main function to run geometry pre-processing.

    Returns
    -------


    """
    for comp in GetRootPart().GetAllComponents():
        run_stitch_prep(comp, 50)


main()
