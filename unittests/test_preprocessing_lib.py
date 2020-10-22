import unittest
from SPEOS_scripts.ASP_start_Libary.ASPcontrol import SCDMControl


class PreprocessingTest(unittest.TestCase):
    scdm = SCDMControl(graphical_mode=True)
    @classmethod
    def setUpClass(cls):
        cls.scdm.open_spaceclaim_session()

    @classmethod
    def tearDownClass(cls):
        cls.scdm.close_spaceclaim_session()


    def test_preprocessing(self):
        self.assertEqual(True, False)




if __name__ == '__main__':
    unittest.main()
