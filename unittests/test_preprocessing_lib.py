import unittest
#from SPEOS_scripts.ASP_start_Libary.ASPcontrol import SCDMControl
import sys
sys.path.append(r"D:\Git\AnsysAutomation\SCLib")
from SCDMControl import SCDMControl

class PreprocessingTest(unittest.TestCase):
    scdm = SCDMControl(graphical_mode=True)
    def __init__(self, args):
        super().__init__(args)
        self.scdm = PreprocessingTest.scdm

    @classmethod
    def setUpClass(cls):
        cls.scdm.open_spaceclaim_session()

    @classmethod
    def tearDownClass(cls):
        cls.scdm.close_spaceclaim_session()


    def test_preprocessing(self):
        #self.assertEqual(True, False)
        print(dir(self.scdm.scdm_api.Document))
        print(dir(self.scdm.scdm_api.Scripting))
        self.scdm.import_and_save_cad_in_spaceclaim("input\poor_geom.scdoc", "input", "poor_geom2")
        # self.scdm.scdm_api.WriteBlock.ExecuteTask("Open the document",
        #                                      lambda: self.scdm.scdm_api.Document.Open(r"input\poor_geom.scdoc"))
        # sc_doc = self.scdm.scdm_api.Window.ActiveWindow.Document
        # self.scdm.scdm_api.WriteBlock.ExecuteTask("SaveAs the document",
        #                                      lambda: self.scdm.scdm_api.Document.SaveAs(sc_doc, r"input\poor_geom2.scdoc"))

        #self.scdm.scdm_api.Api.DocumentOpen.Execute(r"input\poor_geom.scdoc")
        #self.scdm.scdm_api.Api.DocumentSave.Execute(r"input\poor_geom2.scdoc")


if __name__ == '__main__':
    unittest.main()
