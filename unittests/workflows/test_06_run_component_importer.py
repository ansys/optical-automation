import json
import os
import sys
import traceback

unittest_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.dirname(unittest_path)  # get path of speos_migration library
sys.path.append(lib_path)

from ansys_optical_automation.scdm_process.scdm_io import ScdmIO

scdm_file = os.path.join(unittest_path, "workflows", "example_models", "test_06_geometry.scdocx")
led_file = os.path.join(unittest_path, "workflows", "example_models", "SPEOS input files", "LY.scdocx")
results_json = os.path.join(unittest_path, "workflows", "test_06_results.json")


def check_align_and_angle(axis1, axis2):
    """
    Parameters
    ----------
    axis1: list
        a list containing location and orientation information
    axis2: list
        a list containing location and orientation information

    Returns
    -------
    bool: True if two list match each other, False otherwise
    """
    for i in range(12):
        if abs(axis1[i] - axis2[i]) > 0.1:
            return False
    return True


def extract_scdm_structure():
    """
    Returns
    -------
    dictionary {component name: [sub-component names]}
        a dictionary describing the structure level
    """
    structure = {}
    for comp in GetRootPart().GetComponents():
        structure[comp.GetName()] = []
        if comp.GetComponents().Count != 0:
            for item in comp.GetComponents():
                structure[comp.GetName()].append(item.GetName())
    return structure


def check_if_anchored():
    """
    Returns
    -------
    bool: True if anchor is properly applied, False otherwise
    """
    test_component = GetRootPart().GetComponents()[-1]
    original_position = [
        test_component.GetCoordinateSystems()[0].Frame.Origin.X,
        test_component.GetCoordinateSystems()[0].Frame.Origin.Y,
        test_component.GetCoordinateSystems()[0].Frame.Origin.Z,
    ]

    selection = Selection.Create(test_component)
    direction = Direction.DirZ
    options = MoveOptions()
    Move.Translate(selection, direction, MM(20), options)

    new_position = [
        test_component.GetCoordinateSystems()[0].Frame.Origin.X,
        test_component.GetCoordinateSystems()[0].Frame.Origin.Y,
        test_component.GetCoordinateSystems()[0].Frame.Origin.Z,
    ]
    return original_position == new_position


def check_if_locked():
    """
    Function to check if lock operation is applied properly
    Returns
    -------
    Bool: True if lock is correctly applied, False otherwise
    """
    test_component = GetRootPart().GetComponents()[-1]
    try:
        test_component.Delete()
        return False
    except Exception as ex:
        return True


def compare_target_axis_system_with_imported_part_location(target_axis_system_list, imported_part_location_list):
    """
    Parameters
    ----------
    target_axis_system_list: list
        a list containing target axis system information
    imported_part_location_list: list
        a list containing import part location information

    Returns
    -------
    bool: True if two locations match, False otherwise

    """
    if len(target_axis_system_list) != len(imported_part_location_list):
        return False

    item_nums = len(target_axis_system_list)
    for idx in range(item_nums):
        target_axis_system = target_axis_system_list[idx]
        imported_part_location = imported_part_location_list[idx]

        match_check = check_align_and_angle(target_axis_system, imported_part_location)
        if match_check is False:
            return False
    return True


def extract_axis_information(axis_system):
    """
    Parameters
    ----------
    axis_system: spaceclaim axis system

    Returns
    -------
    list
        a list containing axis system information:
            [position x, position y, position z,
            x_axis x,  x_axis y, x_axis z,
            y_axis x, y_axis y, y_axis z,
            z_axis x, z_axis y, z_axis z]

    """
    axis_system_information = []
    if axis_system.GetName() != "" and axis_system.IsVisible(None) is True:
        axis_system_position = axis_system.Frame.Origin
        axis_system_axes = axis_system.Axes
        axis_system_information = [
            axis_system_position.X,
            axis_system_position.Y,
            axis_system_position.Z,
            axis_system_axes[0].Shape.Geometry.Direction[0],
            axis_system_axes[0].Shape.Geometry.Direction[1],
            axis_system_axes[0].Shape.Geometry.Direction[2],
            axis_system_axes[1].Shape.Geometry.Direction[0],
            axis_system_axes[1].Shape.Geometry.Direction[1],
            axis_system_axes[1].Shape.Geometry.Direction[2],
            axis_system_axes[2].Shape.Geometry.Direction[0],
            axis_system_axes[2].Shape.Geometry.Direction[1],
            axis_system_axes[2].Shape.Geometry.Direction[2],
        ]
    return axis_system_information


def extract_axis_system_info_under_component(component):
    """

    Parameters
    ----------
    component: spaceclaim component

    Returns
    -------
    list:
        a list of axis system information list about location and orientation under the component

    """
    axis_system_list = []
    for axis_system in component.GetCoordinateSystems():
        extracted_information = extract_axis_information(axis_system)
        if len(extracted_information) != 0:
            axis_system_list.append(extracted_information)
    return axis_system_list


def extract_imported_part_location_info_under_component(group):
    """
    Parameters
    ----------
    group: spaceclaim component

    Returns
    -------
    list:
        a list of imported parts' information list about location and orientation information

    """
    imported_part_location_list = []
    for component in group.GetComponents():
        for axis_system in component.GetAllCoordinateSystems():
            extracted_information = extract_axis_information(axis_system)
            if len(extracted_information) != 0:
                imported_part_location_list.append(extracted_information)
    return imported_part_location_list


def extract_number_of_groups():
    """

    Returns
    -------
    a dictionary which describe the group created in the project

    """
    created_group_information = {}
    for name_selection in GetActiveWindow().Groups:
        ns_name = name_selection.GetName()
        created_group_information[ns_name] = []
        for item in name_selection.Members:
            created_group_information[ns_name].append(item.Type)
    return created_group_information


def main():
    """
    This main function will be run to test the import APIs
    Returns
    -------
    None

    """
    DocumentOpen.Execute(scdm_file)
    led_importer = ScdmIO(SpaceClaim)

    initial_axis_system_info_list = []
    imported_part_location_list = []
    for comp in GetRootPart().GetAllComponents():
        name = comp.GetName()

        # pyoptics to extract target axis system
        axis_system_list = led_importer.get_axis_systems_under_component(comp)
        if len(axis_system_list) == 0:
            continue

        # unittest extract axis location information to be imported
        axis_system_found = extract_axis_system_info_under_component(comp)
        initial_axis_system_info_list.extend(axis_system_found)

        # pyoptics to import parts
        led_importer.import_part_at_axis_system(
            led_file, axis_system_list, name, anchor=True, lock=True, internalize=True, speos_source_group=True
        )

        # extract imported part location information
        grouped_component = GetRootPart().GetComponents()[-1]
        imported_part_location_list.extend(extract_imported_part_location_info_under_component(grouped_component))

    results_dict["target axis systems location"] = initial_axis_system_info_list
    results_dict["imported parts locations"] = imported_part_location_list
    results_dict["compare imported with target locations"] = compare_target_axis_system_with_imported_part_location(
        initial_axis_system_info_list, imported_part_location_list
    )
    results_dict["check anchor"] = check_if_anchored()
    results_dict["check lock"] = check_if_locked()
    results_dict["check speos sources group"] = extract_number_of_groups()
    results_dict["components structure"] = extract_scdm_structure()
    # options = ExportOptions.Create()
    # DocumentSave.Execute(r"C:\Users\plu\Desktop\Test2.scdocx", options)


results_dict = {}
try:
    main()
except Exception:
    print("exception in main")
    results_dict["error"] = traceback.format_exc()

with open(results_json, "w") as file:
    json.dump(results_dict, file, indent=4)
