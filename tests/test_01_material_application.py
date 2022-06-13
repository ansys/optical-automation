import json
import os
import subprocess

from ansys_optical_automation.scdm_core.base import get_scdm_install_location

# User Input
SCDM_VERSION = 221  # version of SCDM you want to test

# Code
scdm_install_dir = get_scdm_install_location(SCDM_VERSION)
speos_path = os.path.join(os.path.dirname(scdm_install_dir), "Optical Products", "Speos", "Bin", "SpeosSC.Manifest.xml")
os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

out = open(r"C:\temp\Text_D.txt","w")
out.write("from Test")
out.close()

class TestMaterialAPI:
    """
    Class to define conditions for run of unit tests in PyTest
    """

    def setup_class(self):
        """
        Called before tests to initialize scdm class and open new SCDM session
        Returns:
        """

        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.results_file = os.path.join(self.local_path, "workflows", "test01_results.json")
        reference_file = os.path.join(self.local_path, "workflows", "test_01_reference_results.json")
        self.clean_results(self)  # no idea why but you have to pass there self

        scdm_exe = os.path.join(scdm_install_dir, "SpaceClaim.exe")
        scdm_script_path = os.path.join(self.local_path, "workflows", "test_01_run_material_application.py")
        print("Start SPEOS to generate JSON file for tests")
        command = [
            scdm_exe,
            r"/AddInManifestFile={}".format(speos_path),
            r"/RunScript={}".format(scdm_script_path),
            r"/Headless=True",
            r"/Splash=False",
            r"/Welcome=False",
            r"/ExitAfterScript=True",
            r"/ScriptAPI=21",
        ]
        print(command)
        # os.chdir(os.path.dirname(self.local_path))
        print("********" + os.path.dirname(self.local_path))
        p = subprocess.Popen(command, shell=True)
        p.wait()

        with open(self.results_file) as file:
            self.results = json.load(file)

        with open(reference_file) as file:
            self.reference_results = json.load(file)

    def teardown_class(self):
        """
        Called after all tests are completed to clean up SCDM session
        clean results file.

        On fail will report traceback with lines where code failed
        """
        # self.clean_results(self)

        print("\n\n\n\n\n###############################")
        print(self.results.get("error", "All tests are successful"))
        print("###############################\n\n\n\n\n")

    def clean_results(self):
        """
        Delete results file to avoid confusion
        Returns:
        """
        if os.path.isfile(self.results_file):
            os.remove(self.results_file)

    def test_01_check_optical_props(self):
        """
        Function to compare the results of create_speos_material() and apply_geo_to_material()
        Returns: None
        """
        res = self.results.get("speos_materials", None)
        ref = self.reference_results["speos_materials"]
        assert res == ref

    def test_02_check_layers(self):
        """
        Function to compare the results of apply_geo_to_layer()
        Returns: None
        """
        res = self.results.get("speos_layers", None)
        ref = self.reference_results["speos_layers"]
        assert res == ref

    def test_03_check_layer_material_synch(self):
        """
        Function to compare the results of SynchLayersMaterials.sync_op_from_layers()
        Returns: None
        """
        res = self.results.get("layer_synch_to_material", None)
        ref = self.reference_results["layer_synch_to_material"]
        assert res == ref
