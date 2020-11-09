import os
import clr
import sys

def import_clr(version, api_version):
    scdm_install_dir = get_scdm_location(version)

    # adding new reference paths
    sys.path.append(os.path.join(scdm_install_dir, "SpaceClaim.Api." + api_version))
    sys.path.append(scdm_install_dir)

    # adding new references
    api_name = 'SpaceClaim.Api.' + api_version
    clr.AddReference('SpaceClaim')
    clr.AddReference(api_name)
    clr.AddReference(api_name + '.Scripting')

    # importing new namespaces
    # scdm_api = __import__(api_name) # does not work
    exec("import {} as scdm_api".format(api_name), globals())

    clr.AddReference('System.Collections')
    from System.Collections.Generic import List
    return scdm_api, scdm_install_dir, List


def get_scdm_location(version):
    # set ansys version and installation directory
    ansys_install_dir = os.environ["AWP_ROOT{}".format(version)]
    scdm_install_dir = os.path.join(ansys_install_dir, "scdm")
    return scdm_install_dir


def perform_imports(version, api_version):
    global scdm_api, scdm_install_dir, List
    scdm_api, scdm_install_dir, List = import_clr(version, api_version)

    # all following imports are imported in alphabetic order
    global ColorHelper
    ColorHelper = scdm_api.Scripting.Helpers.ColorHelper

    global ComponentExtensions
    ComponentExtensions = scdm_api.Scripting.Extensions.ComponentExtensions

    global FixDuplicateFaces
    FixDuplicateFaces = scdm_api.Scripting.Commands.FixDuplicateFaces

    global GetOriginal
    GetOriginal = scdm_api.Scripting.Extensions.DocObjectExtensions.GetOriginal

    global GetRootPart
    GetRootPart = scdm_api.Scripting.Helpers.DocumentHelper.GetRootPart

    global IDesignBody
    IDesignBody = scdm_api.IDesignBody

    global NamedSelection
    NamedSelection = scdm_api.Scripting.Commands.NamedSelection

    global PartExtensions
    PartExtensions = scdm_api.Scripting.Extensions.PartExtensions

    global Selection
    Selection = scdm_api.Scripting.Selection.Selection

    global StitchFaces
    StitchFaces = scdm_api.Scripting.Commands.StitchFaces
