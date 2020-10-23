import sys
import pytest
sys.path.append(r"D:\Git\AnsysAutomation\SCLib")  # temp paths until updates not in SCLib package
sys.path.append(r"C:\git\ansys_automation\SCLib")
from SCDMControl import SCDMControl


class TestPreprocessing:
    """
    Class to define conditions for run of unit tests in PyTest
    """
    def setup_class(self):
        """
        Called before tests to initialize scdm class and open new SCDM session
        Returns:
        """

        self.scdm = SCDMControl(graphical_mode=True, version=211, api_version="V20")
        self.scdm.open_spaceclaim_session()

    def teardown_class(self):
        """
        Called after all tests are completed to clean up SCDM session
        Returns:
        """

        self.scdm.close_spaceclaim_session()

    def test_preprocessing(self):
        """
        Function to run flow of test in SCDM
        Returns: None
        """

        import_settings = self.scdm.scdm_api.ImportOptions.Create()

        self.scdm.send_command(self.scdm.scdm_api.Document.Open, r"input\poor_geom.scdoc", import_settings)
        sc_doc = self.scdm.scdm_api.Window.ActiveWindow.Document
        self.scdm.send_command(self.scdm.scdm_api.Document.SaveAs, sc_doc, r"input\poor_geom2.scdoc")
