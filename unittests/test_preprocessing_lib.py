import unittest
import sys

sys.path.append(r"D:\Git\AnsysAutomation\SCLib")
sys.path.append(r"C:\git\ansys_automation\SCLib")
from SCDMControl import SCDMControl

class PreprocessingTest(unittest.TestCase):
    scdm = SCDMControl(graphical_mode=True, version=211, api_version="V20")

    def __init__(self, args):
        unittest.TestCase.__init__(self, args)
        self.scdm = PreprocessingTest.scdm

    @classmethod
    def setUpClass(cls):
        cls.scdm.open_spaceclaim_session()

    @classmethod
    def tearDownClass(cls):
        cls.scdm.close_spaceclaim_session()

    def test_preprocessing(self):
        # self.assertEqual(True, False)

        import_settings = self.scdm.scdm_api.ImportOptions.Create()

        self.scdm.send_command(self.scdm.scdm_api.Document.Open, r"input\poor_geom.scdoc", import_settings)
        sc_doc = self.scdm.scdm_api.Window.ActiveWindow.Document
        self.scdm.send_command(self.scdm.scdm_api.Document.SaveAs, sc_doc, r"input\poor_geom2.scdoc")


if __name__ == '__main__':
    unittest.main()
