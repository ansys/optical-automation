import json
import os
import subprocess

from tests.config import SCDM_INSTALL_DIR

speos_path = os.path.join(os.path.dirname(SCDM_INSTALL_DIR), "Optical Products", "Speos", "Bin", "SpeosSC.Manifest.xml")
os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


class TestSensorAPI:
    """
    Class to define conditions for run of unit tests in PyTest
    """

    def setup_class(self):
        """
        Called before tests to initialize scdm class and open new SCDM session
        Returns:
        """

        self.local_path = os.path.dirname(os.path.realpath(__file__))
        self.results_file = os.path.join(self.local_path, "workflows", "test_03_results.json")
        reference_file = os.path.join(self.local_path, "workflows", "test_03_reference_results.json")
        self.clean_results(self)  # no idea why but you have to pass there self

        scdm_exe = os.path.join(SCDM_INSTALL_DIR, "SpaceClaim.exe")
        scdm_script_path = os.path.join(self.local_path, "workflows", "test_03_run_speos_sensors.py")
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
        subprocess.call(command)

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
        self.clean_results(self)

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

    def test_01_check_camera_created(self):
        """
        Function to compare the results of the camera class initialization
        Returns: None
        """
        res = self.results.get("camera_exists", None)
        ref = self.reference_results["camera_exists"]
        assert res == ref

    def test_02_check_origin(self):
        """
        Function to compare the results of Camera.set_position() - Camera origin
        Returns: None
        """
        res = self.results.get("camera_origin", None)
        ref = self.reference_results["camera_origin"]
        assert res == ref

    def test_03_check_x_axis(self):
        """
        Function to compare the results of Camera.set_position() - X Direction
        Returns: None
        """
        res = self.results.get("camera_x_axis", None)
        ref = self.reference_results["camera_x_axis"]
        assert res == ref

    def test_04_check_y_axis(self):
        """
        Function to compare the results of Camera.set_position() - Y Direction
        Returns: None
        """
        res = self.results.get("camera_y_axis", None)
        ref = self.reference_results["camera_y_axis"]
        assert res == ref

    def test_05_check_x_reverse_true(self):
        """
        Function to compare the results of Camera.set_position() - Y Direction
        Returns: None
        """
        res = self.results.get("camera_x_reverse_true", None)
        ref = self.reference_results["camera_x_reverse_true"]
        assert res == ref

    def test_06_check_y_reverse_true(self):
        """
        Function to compare the results of Camera.set_position() - Y Direction
        Returns: None
        """
        res = self.results.get("camera_y_reverse_true", None)
        ref = self.reference_results["camera_y_reverse_true"]
        assert res == ref

    def test_07_check_origin_axsys(self):
        """
        Function to compare the results of Camera.set_position() - Y Direction
        Returns: None
        """
        res = self.results.get("camera_origin_axsys", None)
        ref = self.reference_results["camera_origin_axsys"]
        assert res == ref

    def test_08_check_x_reverse_false(self):
        """
        Function to compare the results of Camera.set_position() - Y Direction
        Returns: None
        """
        res = self.results.get("camera_x_reverse_false", None)
        ref = self.reference_results["camera_x_reverse_false"]
        assert res == ref

    def test_09_check_y_reverse_false(self):
        """
        Function to compare the results of Camera.set_position() - Y Direction
        Returns: None
        """
        res = self.results.get("camera_y_reverse_false", None)
        ref = self.reference_results["camera_y_reverse_false"]
        assert res == ref

    def test_10_intensity_created(self):
        """
        Function to compare the results of IntensitySensor class initialization method
        Returns: None
        """
        res = self.results.get("intensity_exists", None)
        ref = self.reference_results["intensity_exists"]
        assert res == ref

    def test_11_intensity_origin(self):
        """
        Function to compare the results of IntensitySensor.set_position() - origin
        Returns: None
        """
        res = self.results.get("intensity_origin", None)
        ref = self.reference_results["intensity_origin"]
        assert res == ref

    def test_12_check_x_axis(self):
        """
        Function to compare the results of IntensitySensor.set_position() - X Direction
        Returns: None
        """
        res = self.results.get("intensity_x_axis_type", None)
        ref = self.reference_results["intensity_x_axis_type"]
        assert res == ref

    def test_13_check_y_axis(self):
        """
        Function to compare the results of IntensitySensor.set_position() - Y Direction
        Returns: None
        """
        res = self.results.get("intensity_y_axis_type", None)
        ref = self.reference_results["intensity_y_axis_type"]
        assert res == ref

    def test_14_intensity_format_a(self):
        """
        Function to compare the results of IntensitySensor.set_format() - "iesnatypeA"
        Returns: None
        """
        res = self.results.get("intensity_format_A", None)
        ref = self.reference_results["intensity_format_A"]
        assert res == ref

    def test_15_intensity_format_b(self):
        """
        Function to compare the results of IntensitySensor.set_format() - "iesnatypeB"
        Returns: None
        """
        res = self.results.get("intensity_format_B", None)
        ref = self.reference_results["intensity_format_B"]
        assert res == ref

    def test_16_intensity_format_c(self):
        """
        Function to compare the results of IntensitySensor.set_format() - "iesnatypeC"
        Returns: None
        """
        res = self.results.get("intensity_format_C", None)
        ref = self.reference_results["intensity_format_C"]
        assert res == ref

    def test_17_intensity_format_eulumdat(self):
        """
        Function to compare the results of IntensitySensor.set_format() - "eulumdat"
        Returns: None
        """
        res = self.results.get("intensity_format_eulumdat", None)
        ref = self.reference_results["intensity_format_eulumdat"]
        assert res == ref

    def test_18_intensity_format_xmp(self):
        """
        Function to compare the results of IntensitySensor.set_format() - "xmp"
        Returns: None
        """
        res = self.results.get("intensity_format_xmp", None)
        ref = self.reference_results["intensity_format_xmp"]
        assert res == ref

    def test_19_wavelength_start(self):
        """
        Function to compare the results of IntensitySensor.set_wavelength() - w_start
        Returns: None
        """
        res = self.results.get("wavelength_start", None)
        ref = self.reference_results["wavelength_start"]
        assert res == ref

    def test_20_wavelength_end(self):
        """
        Function to compare the results of IntensitySensor.set_wavelength() - w_end
        Returns: None
        """
        res = self.results.get("wavelength_end", None)
        ref = self.reference_results["wavelength_end"]
        assert res == ref

    def test_21_wavelength_sampling(self):
        """
        Function to compare the results of IntensitySensor.set_wavelength() - w_sampling
        Returns: None
        """
        res = self.results.get("wavelength_sampling", None)
        ref = self.reference_results["wavelength_sampling"]
        assert res == ref

    def test_22_wavelength_resolution(self):
        """
        Function to compare the results of IntensitySensor.set_wavelength() - w_resolution
        Returns: None
        """
        res = self.results.get("wavelength_resolution", None)
        ref = self.reference_results["wavelength_resolution"]
        assert res == ref

    def test_23_layer_source(self):
        """
        Function to compare the results of IntensitySensor.set_layer() - source
        Returns: None
        """
        res = self.results.get("layer_source", None)
        ref = self.reference_results["layer_source"]
        assert res == ref

    def test_24_layer_none(self):
        """
        Function to compare the results of IntensitySensor.set_layer() - none
        Returns: None
        """
        res = self.results.get("layer_none", None)
        ref = self.reference_results["layer_none"]
        assert res == ref

    def test_25_layer_face(self):
        """
        Function to compare the results of IntensitySensor.set_layer() - face
        Returns: None
        """
        res = self.results.get("layer_face", None)
        ref = self.reference_results["layer_face"]
        assert res == ref

    def test_26_layer_sequence(self):
        """
        Function to compare the results of IntensitySensor.set_layer() - sequence
        Returns: None
        """
        res = self.results.get("layer_sequence", None)
        ref = self.reference_results["layer_sequence"]
        assert res == ref

    def test_27_range_x_start(self):
        """
        Function to compare the results of IntensitySensor.set_range() - x_start
        Returns: None
        """
        res = self.results.get("x_start", None)
        ref = self.reference_results["x_start"]
        assert res == ref

    def test_28_range_x_end(self):
        """
        Function to compare the results of IntensitySensor.set_range() - x_end
        Returns: None
        """
        res = self.results.get("x_end", None)
        ref = self.reference_results["x_end"]
        assert res == ref

    def test_29_range_y_start(self):
        """
        Function to compare the results of IntensitySensor.set_range() - y_start
        Returns: None
        """
        res = self.results.get("y_start", None)
        ref = self.reference_results["y_start"]
        assert res == ref

    def test_30_range_y_end(self):
        """
        Function to compare the results of IntensitySensor.set_range() - y_end
        Returns: None
        """
        res = self.results.get("y_end", None)
        ref = self.reference_results["y_end"]
        assert res == ref

    def test_31_range_x_mirrored(self):
        """
        Function to compare the results of IntensitySensor.set_range() - x_mirrored
        Returns: None
        """
        res = self.results.get("x_mirrored", None)
        ref = self.reference_results["x_mirrored"]
        assert res == ref

    def test_32_range_x_start_mirrored(self):
        """
        Function to compare the results of IntensitySensor.set_range() - x_mirrored
        Returns: None
        """
        res = self.results.get("x_start_mirrored", None)
        ref = self.reference_results["x_start_mirrored"]
        assert res == ref

    def test_33_range_y_mirrored(self):
        """
        Function to compare the results of IntensitySensor.set_range() - y_mirrored
        Returns: None
        """
        res = self.results.get("y_mirrored", None)
        ref = self.reference_results["y_mirrored"]
        assert res == ref

    def test_34_range_y_start_mirrored(self):
        """
        Function to compare the results of IntensitySensor.set_range() - y_mirrored
        Returns: None
        """
        res = self.results.get("y_start_mirrored", None)
        ref = self.reference_results["y_start_mirrored"]
        assert res == ref

    def test_35_sampling_x(self):
        """
        Function to compare the results of IntensitySensor.set_sampling() - x_sampling
        Returns: None
        """
        res = self.results.get("x_sampling", None)
        ref = self.reference_results["x_sampling"]
        assert res == ref

    def test_36_sampling_y(self):
        """
        Function to compare the results of IntensitySensor.set_sampling() - y_sampling
        Returns: None
        """
        res = self.results.get("y_sampling", None)
        ref = self.reference_results["y_sampling"]
        assert res == ref

    def test_37_resolution_x(self):
        """
        Function to compare the results of IntensitySensor.set_resolution() - x_resolution
        Returns: None
        """
        res = self.results.get("x_resolution", None)
        ref = self.reference_results["x_resolution"]
        assert res == ref

    def test_38_resolution_y(self):
        """
        Function to compare the results of IntensitySensor.set_resolution() - y_resolution
        Returns: None
        """
        res = self.results.get("y_resolution", None)
        ref = self.reference_results["y_resolution"]
        assert res == ref

    def test_39_type_photometric(self):
        """
        Function to compare the results of IntensitySensor.set_type() - photometric
        Returns: None
        """
        res = self.results.get("type_photometric", None)
        ref = self.reference_results["type_photometric"]
        assert res == ref

    def test_40_type_colorimetric(self):
        """
        Function to compare the results of IntensitySensor.set_type() - colorimetric
        Returns: None
        """
        res = self.results.get("type_colorimetric", None)
        ref = self.reference_results["type_colorimetric"]
        assert res == ref

    def test_41_type_radiometric(self):
        """
        Function to compare the results of IntensitySensor.set_type() - radiometric
        Returns: None
        """
        res = self.results.get("type_radiometric", None)
        ref = self.reference_results["type_radiometric"]
        assert res == ref

    def test_42_type_spectral(self):
        """
        Function to compare the results of IntensitySensor.set_type() - spectral
        Returns: None
        """
        res = self.results.get("type_spectral", None)
        ref = self.reference_results["type_spectral"]
        assert res == ref
