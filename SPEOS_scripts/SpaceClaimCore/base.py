import clr
import os

clr.AddReference('System.Collections')
from System.Collections.Generic import List

class BaseSCDM(object):
    def __init__(self, scdm_api):
        """
        Base class that contains all common used objects. This class serves more as an abstract class
        Args:
            scdm_api: SpaceClaim.Api.V<API version> object
        """
        self.List = List
        self.scdm_api = scdm_api

        self.ColorHelper = scdm_api.Scripting.Helpers.ColorHelper
        self.ComponentExtensions = scdm_api.Scripting.Extensions.ComponentExtensions
        self.FixDuplicateFaces = scdm_api.Scripting.Commands.FixDuplicateFaces
        self.GetOriginal = scdm_api.Scripting.Extensions.DocObjectExtensions.GetOriginal
        self.GetRootPart = scdm_api.Scripting.Helpers.DocumentHelper.GetRootPart
        self.IDesignBody = scdm_api.IDesignBody
        self.NamedSelection = scdm_api.Scripting.Commands.NamedSelection
        self.PartExtensions = scdm_api.Scripting.Extensions.PartExtensions
        self.Selection = scdm_api.Scripting.Selection.Selection
        self.StitchFaces = scdm_api.Scripting.Commands.StitchFaces


def get_scdm_install_location(version):
    """
    Function to get installation path of SpaceClaim
    Args:
        version (int): version in format <XXX> eg 211

    Returns: path of SCDM installation
    """

    ansys_install_dir = os.environ["AWP_ROOT{}".format(version)]
    scdm_install_dir = os.path.join(ansys_install_dir, "scdm")
    return scdm_install_dir
