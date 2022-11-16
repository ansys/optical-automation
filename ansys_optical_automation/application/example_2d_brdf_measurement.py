import csv
import os

from ansys_optical_automation.post_process.dpf_brdf_viewer import BrdfMeasurementPoint
from ansys_optical_automation.post_process.dpf_brdf_viewer import BrdfStructure


def convert_export(input_csv, output_path):
    """
    main function to convert 2d data into brdf and export.

    Parameters
    ----------
    input_csv : str
        path of csv file recording the 2d data.
    output_path : str
        path for the brdf to be exported.

    Returns
    -------


    """
    wavelength_list = []
    brdf_data = None
    with open(input_csv) as file:
        content = csv.reader(file, delimiter=",")
        FirstRow = True
        for row in content:
            if FirstRow:
                wavelength_list = [item.split("nm")[0] for item in row][2:]
                wavelength_list = [float(item) for item in wavelength_list]
                brdf_data = BrdfStructure(wavelength_list)
            else:
                for wavelength_idx, wavelength in enumerate(wavelength_list):
                    brdf_data.measurement_2d_brdf.append(
                        BrdfMeasurementPoint(float(row[0]), wavelength, float(row[1]), float(row[2 + wavelength_idx]))
                    )
            FirstRow = False
        brdf_data.convert(sampling=1)
        brdf_data.export_to_speos(output_path)


def main():
    """
    main function to run conversion.

    Returns
    -------


    """
    cwd = os.path.realpath(__file__)
    repo = os.path.dirname(os.path.dirname(os.path.dirname(cwd)))
    measurement_2d_file = os.path.join(repo, "tests", "workflows", "example_models", "test_brdf_viewer_2D_data.csv")
    convert_export(measurement_2d_file, r"D:\\")


main()
