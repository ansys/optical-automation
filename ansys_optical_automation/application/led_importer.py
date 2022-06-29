import os
import sys

appdata_path = os.getenv("AppData")
repo_path = os.path.join(appdata_path, "SpaceClaim", "Published Scripts")
sys.path.append(repo_path)

from ansys_optical_automation.scdm_process.scdm_io import ScdmIO


def selection_dialog_window():
    """
    This function asks user to select the file.

    Returns
    -------
    str
        file directory selected, otherwise False
    """
    open_dialog = OpenFileDialog()
    open_dialog.Filter = "ANSYS SPEOS files (*.scdoc;*.scdocx)|*.scdoc;*scdocx|All Files (*.*)|*.*"
    open_dialog.Show()
    if open_dialog.FileName == "":
        MessageBox.Show("You did not select any file")
        return False
    return open_dialog.FileName


def check_visual_status_dialog():
    """
    Function asks user to check the visual parts to be correct for later operation.

    Returns
    -------
    bool
        True if user would clicks check to confirm, False otherwise
    """
    response = InputHelper.PauseAndGetInput("Please only show coordinates where you would like to import LEDs")
    if not response.Success:
        MessageBox.Show("You canceled the operation")
        return False
    return True


def import_by_visual_status():
    """This function will import selected part based on the visual axis systems."""
    if not check_visual_status_dialog():
        return
    led_file = selection_dialog_window()
    if not led_file:
        return
    led_importer = ScdmIO(SpaceClaim)
    for component in GetRootPart().GetAllComponents():
        component_name = component.GetName()
        axis_system_list = led_importer.get_axis_systems_under_component(component)
        if len(axis_system_list) == 0:
            continue
        led_importer.import_part_at_axis_system(led_file, axis_system_list, component_name, True, True, True, True)


def import_by_selection():
    """The function will import selected scdm project on the selected axis."""
    led_file = selection_dialog_window()
    if not led_file:
        return

    axis_system_selection = Selection.GetActive()
    if len(axis_system_selection.GetItems[ICoordinateSystem]()) == 0:
        while True:
            input_return = InputHelper.PauseAndGetInput("Select the axis you want to import the part onto")
            if not input_return.Success:
                return
            axis_system_selection = input_return.PrimarySelection
            if len(axis_system_selection.GetItems[ICoordinateSystem]()) == 0:
                MessageBox.Show("The selection must contains at least one axis system to be able to import the part")
                continue
            break
    axis_system_list = axis_system_selection.GetItems[ICoordinateSystem]()
    led_importer = ScdmIO(SpaceClaim)
    led_importer.import_part_at_axis_system(led_file, axis_system_list, anchor=True, lock=True, internalize=True)


# Please select one of the following methods preferred for import
# import_by_selection()
# import_by_visual_status()
