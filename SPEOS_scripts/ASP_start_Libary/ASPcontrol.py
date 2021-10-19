##################################################################
# ASPcontrol  - Copyright ANSYS. All Rights Reserved.
# ##################################################################
# CREATION:      2021.08.17
# VERSION:       1.0.0
#
# OVERVIEW
# ========
# This script is generated for showing scripting capabilities purpose.
# It contains a class with methods to control SpaceClaim
#
#
# ##################################################################
# https://opensource.org/licenses/MIT
#
# Copyright 2021 Ansys, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# The user agrees to this disclaimer and user agreement with the download or usage
# of the provided files.
#
# ##################################################################

# Python Script, API Version = V20 Beta


import sys
import clr
import os.path
import logging
import traceback
SpaceClaimVersion = "AWP_ROOT211"
# set ansys version and installation directory
AnsysInstallDir = os.environ[SpaceClaimVersion]
SCDMInstallDir = os.path.normpath(os.path.join(AnsysInstallDir, "scdm"))

# adding new reference paths
#sys.path.append(os.path.join(AnsysInstallDir, "scdm", "SpaceClaim.Api.V18"))
sys.path.append(os.path.join(AnsysInstallDir, "scdm"))
sys.path.append(os.path.join(AnsysInstallDir,"Optical Products","SPEOS","Bin"))
# adding new references
clr.AddReference('SpaceClaim.Api.V20')
clr.AddReference('SpaceClaim.Api.V18.Scripting')
# importing new namespaces
import SpaceClaim.Api.V20 as SC  # noqa E402
import SpaceClaim.Api.V18.Scripting  # noqa E402


class SCDMControl(object):
    """
    This class contains all the methods to control SpaceClaim
    As per Api limitation only one session at the time can be attached.
    For this reason the class does not support multiple SpaceClaim sessions.
    """
    def __init__(self, graphical_mode=False):
        """
        GraphicalMode = True|False (set to display the application window)
        """
        self.ShowApplication = graphical_mode  # used by API
        self.ShowSplashScreen = graphical_mode  # used by API
        self.NonGraphicalMode = not graphical_mode  # used by client-server
        self.version = 201
        self.logger = logging.getLogger(__name__)

    def __exit__(self, ex_type, ex_value, ex_traceback):
        # Write the trace stack to the log file if an exception occurred in the main script
        if ex_type:
            self._exception(ex_value, ex_traceback)

    def __enter__(self):
        return self
    def _exception(self, ex_value, tb_data):
        """
        writes the trace stack to the desktop when a python error occurs
        """
        tb_trace = traceback.format_tb(tb_data)
        tblist = tb_trace[0].split('\n')
        self.logger.error(str(ex_value))
        for el in tblist:
            self.logger.error(el)

    def import_and_save_cad_in_spaceclaim(self, CADFile, ProjectPath, ProjectName):
        """
        TO BE MOVED TO SPACECLAIM FOLDER
        :param CADFile:
        :param ProjectPath:
        :param ProjectName:
        :return:
        """
        SaveFile = os.path.join(ProjectPath, ProjectName + ".scdoc")

        ImportSettings = SC.ImportOptions.Create()
        ImportSettings.CleanUpBodies = True
        ImportSettings.StitchSurfaces = True
        SC.WriteBlock.ExecuteTask("Open the document", lambda: SC.Document.Open(CADFile, ImportSettings))

        SCDoc = SC.Window.ActiveWindow.Document

        SC.WriteBlock.ExecuteTask("SaveAs the document", lambda: SC.Document.SaveAs(SCDoc, SaveFile))

        return SaveFile

    def open_spaceclaim_session(self):
        """
        This method opens the SpaceClaim application and attaches the Api session to it
        """
        # set the startup options
        options = SC.StartupOptions(-1)  # number of milliseconds to wait, or -1 to wait indefinitely.
        options.ExecutableFolder = SCDMInstallDir
        options.ShowSplashScreen = self.ShowApplication
        options.ShowApplication = self.ShowSplashScreen
        options.ManifestFile = os.path.join(AnsysInstallDir,"Optical Products","SPEOS","Bin" ,"SpeosSC.Manifest.xml")
        # open SpaceClaim
        self.scdm = SC.Session.Start(options)
        # attach the Api to the SC session
        try:
            SC.Api.AttachToSession(self.scdm)
        except Exception as e:
            print(str(e))
            print("it's not possible to attach to new session")
        SC.Api.Initialize()
        SC.Api.AutoKeepAlive = True
    def close_spaceclaim_session(self):
        """
        This method closes the SpaceClaim application and detaches the Api session
        """
        SC.Session.Stop(self.scdm)

    def attach_to_existing_session(self):
        """
        This method attaches to an existing SC instance that is already open
        """
        self.scdm = SC.Session.GetSessions()
        SC.Api.AttachToSession(self.scdm[0])
        # SpaceClaim Api initialization
        SC.Api.Initialize()
        SC.Api.AutoKeepAlive = True
    class Input(object):
        """
        Required to RunScriptOnServer
        """
        def __init__(self, content, args):
            self.Content = content
            self.Args = args



if __name__ == "__main__":
    sc = SCDMControl(graphical_mode=True)
    sc.open_spaceclaim_session()
    sc.close_spaceclaim_session()

