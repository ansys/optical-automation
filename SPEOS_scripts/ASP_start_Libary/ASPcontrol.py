# Copyright (C) 2019 ANSYS, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
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




sc = SCDMControl(graphical_mode=True)
sc.open_spaceclaim_session()
#sc.import_and_save_cad_in_spaceclaim("D:\\Ansys_filter_2poles.step", "D:\\", "test_import")
#sc.close_spaceclaim_session()

