# Python Script, API Version = V232
from ansys_optical_automation.speos_process.speos_sensors import IntensitySensor


def get_axis_system():
    """
    To get axis_system from users.

    Returns
    -------
    SpaceClaim Selection
    """
    Window.ActiveWindow.SelectionFilter = SelectionFilterType.Axes
    ctypes.windll.user32.MessageBoxW(
        0, "Select a reference Axis System for the sensors and press Ok", "Axis Selection", 0x40000
    )

    if len(Selection.GetActive().Items) == 1:
        sel = Selection.GetActive().Items[0]
        Window.ActiveWindow.SelectionFilter = SelectionFilterType.Smart
        return sel

    else:
        print("Error No selection")
        Window.ActiveWindow.SelectionFilter = SelectionFilterType.Smart
        sys = GetRootPart().CoordinateSystems[-1]
        sel = sys
        return sel


def create_dialog_form(form_text, form_size, form_min_max_box, form_position, form_border):
    """
    create form to show the dialog later based on the information provided.

    Parameters
    ----------
    form_text : str
        information of the header
    form_size : list
        wide and height of the form
    form_min_max_box : list[bool, bool]
        to have the min and max function
    form_position : FormStartPosition
        position to create the form
    form_border : FormBorderStyle
        Stype of the border

    Returns
    -------
    Form

    """
    form = Form()
    form.Size = Size(form_size[0], form_size[1])
    form.Text = form_text
    form.StartPosition = form_position
    form.MaximizeBox = form_min_max_box[0]
    form.MinimizeBox = form_min_max_box[1]
    form.FormBorderStyle = form_border
    return form


def create_dialog_label(form, label_text, label_location, label_size):
    """
    create label inside the form with information provided.

    Parameters
    ----------
    form : form
    label_text : str
        text shown inside lable
    label_location : list
        x and y location
    label_size : list
        wide and height of label

    Returns
    -------
    label

    """
    label = Label()
    label.Text = label_text
    label.Location = Point(label_location[0], label_location[1])
    label.Size = Size(label_size[0], label_size[1])
    form.Controls.Add(label)
    return label


def create_dialog_radio_button(form, button_location, button_checked, button_size):
    """
    create radio button side the form with provided information.

    Parameters
    ----------
    form : form
    button_location : list
        x and y location of the button created
    button_checked : bool
        default status of the button as True checked, False otherwise
    button_size : list
        wide and height of the button

    Returns
    -------
    RadioButton

    """
    radio = RadioButton()
    radio.Location = Point(button_location[0], button_location[1])
    radio.Checked = button_checked
    radio.Size = Size(button_size[0], button_size[1])
    form.Controls.Add(radio)
    return radio


def create_dialog_button(form, button_text, button_location):
    """
    create button inside the form with information provided.

    Parameters
    ----------
    form : form
    button_text : str
        texture shown inside the button
    button_location : list
        x and y location

    Returns
    -------
    button

    """
    button = Button(Text=button_text)  # Creates a Windows Form Application
    button.Location = Point(button_location[0], button_location[1])  # Button Location
    button.DialogResult = DialogResult.OK
    form.Controls.Add(button)
    return button


def orientation_selection_dialog():
    """
    Asks users to select the orientation for intensity sensors.

    Returns
    -------
    tuples
        status of orientation options, example:
            Rear: True, False, False, False
            Left: False, True, False, False
            Right: False, False, True, False
            Front: False, False, False, True

    """
    global txtbox1
    global txtbox2
    form = create_dialog_form(
        form_text="Sensor orientation",
        form_size=[190, 170],
        form_min_max_box=[False, False],
        form_position=FormStartPosition.CenterScreen,
        form_border=FormBorderStyle.FixedSingle,
    )
    button = create_dialog_button(form, button_text="OK", button_location=[52, 110])
    info_text = "Choose orientation of the sensors relative to the selected axis system:"
    create_dialog_label(form, info_text, label_location=[5, 10], label_size=[180, 44])
    create_dialog_label(form, label_text="+X", label_location=[35, 54], label_size=[25, 22])
    create_dialog_label(form, label_text="+Y", label_location=[35, 76], label_size=[25, 22])
    create_dialog_label(form, label_text="- Y", label_location=[100, 54], label_size=[25, 22])
    create_dialog_label(form, label_text="- X", label_location=[100, 76], label_size=[25, 22])
    front_option_radio_button = create_dialog_radio_button(
        form, button_location=[60, 50], button_checked=True, button_size=[25, 22]
    )
    left_option_radio_button = create_dialog_radio_button(
        form, button_location=[60, 72], button_checked=False, button_size=[25, 22]
    )
    right_option_radio_button = create_dialog_radio_button(
        form, button_location=[125, 50], button_checked=False, button_size=[25, 22]
    )
    rear_option_radio_button = create_dialog_radio_button(
        form, button_location=[125, 72], button_checked=False, button_size=[25, 22]
    )
    button.Click += click  # Add event handler
    form.ShowDialog()
    if front_option_radio_button.Checked:
        return "Front"
    elif left_option_radio_button.Checked:
        return "Left"
    elif right_option_radio_button.Checked:
        return "Right"
    elif rear_option_radio_button.Checked:
        return "Rear"
    else:
        error_message = "incorrect selection"
        raise ValueError(error_message)


def click(sender, event):
    """function to check if selection is checked."""


def apply_usesr_options(axys_sys, option_selected, type, speos_senor):
    """
    check the orientation selected and provide corresponding settings of a intensity sensor.

    Parameters
    ----------
    axys_sys : SpaceClaim SpaceClaim coordinate system
        a SpaceClaim SpaceClaim coordinate system
    option_selected : str
        "Rear"/"Left"/"Right"/"Front"
    type : str
        sensor type selected
    speos_senor : SPEOS sensor object
    """
    axes = axys_sys.GetDescendants[ICoordinateAxis]()
    axis_x = axes[0]
    axis_y = axes[1]
    axis_z = axes[2]
    if option_selected == "Front":
        if type == "IESNATypeA":
            speos_senor.set_position(axes=[axis_z, axis_x], origin=axys_sys, y_reverse=True)
        else:
            speos_senor.set_position(axes=[axis_y, axis_z], origin=axys_sys, x_reverse=True)
    elif option_selected == "Right":
        if type == "IESNATypeA":
            speos_senor.set_position(axes=[axis_z, axis_y], origin=axys_sys)
        else:
            speos_senor.set_position(axes=[axis_x, axis_z], origin=axys_sys, x_reverse=True)
    elif option_selected == "Left":
        if type == "IESNATypeA":
            speos_senor.set_position(axes=[axis_z, axis_y], origin=axys_sys, y_reverse=True)
        else:
            speos_senor.set_position(axes=[axis_x, axis_z], origin=axys_sys)
    elif option_selected == "Rear":
        if type == "IESNATypeA":
            speos_senor.set_position(axes=[axis_z, axis_x], origin=axys_sys)
        else:
            speos_senor.set_position(axes=[axis_y, axis_z], origin=axys_sys)


def create_intensity_sensor(
    sensor_name,
    option_selected,
    sensor_origin,
    sensor_type,
    x_y_samplings,
    w_sampling=None,
    layer=None,
    integration=None,
):
    """
    create sensor based on the information provided.

    Parameters
    ----------
    sensor_name : str
        name used for sensor
    option_selected : str
        orientation option selected by user
    sensor_origin : SpaceClaim coordinate system
    sensor_type : str
        type of sensor to be created
    x_y_samplings : list[int, int]
        list of x-sampling and y-sampling
    w_sampling : int
        wavelength sampling
    layer : str
        type of layer setting for intensity sensor. Default as None
    integration : float
        integration value for intensity sensor

    Returns
    -------
    sensor_obj:
        SPEOS sensor object

    """
    sensor_obj = IntensitySensor(option_selected + "_" + sensor_name, SpeosSim, SpaceClaim)
    apply_usesr_options(sensor_origin, option_selected, sensor_type, sensor_obj)
    if layer is not None:
        sensor_obj.set_layer(layer)
    if sensor_type == "IESNATypeA":
        sensor_obj.set_format(sensor_format="IESNATypeA")
        sensor_obj.set_sampling(x_sampling=x_y_samplings[0], y_sampling=x_y_samplings[1])
    if sensor_type == "XMP":
        sensor_obj.set_format(sensor_format="XMP")
        sensor_obj.set_range(x_mirrored=True, y_mirrored=True, x_start=-90, x_end=90, y_start=-90, y_end=90)
        sensor_obj.set_sampling(x_sampling=x_y_samplings[0], y_sampling=x_y_samplings[1])
        sensor_obj.set_wavelength(w_sampling=w_sampling)
    if integration is not None:
        sensor_obj.set_integration_angle(integration)
    return sensor_obj


def create_intensity_sensors(axys_sys, orientation_option):
    """
    create sensor at the location of provided coordinate system with properties from user.

    Parameters
    ----------
    axys_sys : SpaceClaim coordinate system
    orientation_option : str
        options for intensity sensor orientation: Front, Rear, Left, or Right
    """

    sampling_ies_hq = 721
    sampling_ies_lq = 361
    sampling_xmp_hq = 720
    sampling_xmp_lq = 360
    w_sampling_hq = 61
    w_sampling_lq = 31

    create_intensity_sensor(
        "StdLiqIES",
        orientation_option,
        axys_sys,
        "IESNATypeA",
        x_y_samplings=[sampling_ies_hq, sampling_ies_hq],
        integration=0.25,
    )
    create_intensity_sensor(
        "StdSiqIES",
        orientation_option,
        axys_sys,
        "IESNATypeA",
        x_y_samplings=[sampling_ies_lq, sampling_ies_lq],
        integration=0.5,
    )
    create_intensity_sensor(
        "StdLigColor5nm",
        orientation_option,
        axys_sys,
        "XMP",
        x_y_samplings=[sampling_xmp_hq, sampling_xmp_hq],
        w_sampling=w_sampling_hq,
        layer="source",
    )
    create_intensity_sensor(
        "StdLigColor10nm",
        orientation_option,
        axys_sys,
        "XMP",
        x_y_samplings=[sampling_xmp_hq, sampling_xmp_hq],
        w_sampling=w_sampling_lq,
        layer="source",
    )
    create_intensity_sensor(
        "StdSigColor5nm",
        orientation_option,
        axys_sys,
        "XMP",
        x_y_samplings=[sampling_xmp_lq, sampling_xmp_lq],
        w_sampling=w_sampling_hq,
        layer="source",
    )
    create_intensity_sensor(
        "StdSigColor10nm",
        orientation_option,
        axys_sys,
        "XMP",
        x_y_samplings=[sampling_xmp_lq, sampling_xmp_lq],
        w_sampling=w_sampling_lq,
        layer="source",
    )


def main():
    """
    main function to create multiple intensity sensors based on user input
    """
    mode = None
    try:
        argsDict
        mode = 1
    except Exception:
        mode = 0

    if mode == 0:
        global clr, Application, Button, Form, TextBox, Label, CheckBox, RadioButton, FormStartPosition
        global FormBorderStyle, DialogResult, Point, Size, SelectionFilterType, ctypes
        import clr

        clr.AddReference("System.Windows.Forms")
        clr.AddReference("System.Drawing")
        import ctypes

        from SpaceClaim.Api.V21 import SelectionFilterType
        from System.Drawing import Point
        from System.Drawing import Size
        from System.Windows.Forms import Application
        from System.Windows.Forms import Button
        from System.Windows.Forms import CheckBox
        from System.Windows.Forms import DialogResult
        from System.Windows.Forms import Form
        from System.Windows.Forms import FormBorderStyle
        from System.Windows.Forms import FormStartPosition
        from System.Windows.Forms import Label
        from System.Windows.Forms import RadioButton
        from System.Windows.Forms import TextBox

        axys_sys = get_axis_system()
        orientation_option_selected = orientation_selection_dialog()
        create_intensity_sensors(axys_sys, orientation_option_selected)
    else:
        create_intensity_sensors(argsDict["origin"], argsDict["orientation"])


main()
