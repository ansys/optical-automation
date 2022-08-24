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


def orientation_selection_dialog():
    """
    Asks users to select the orientation for intensity sensors.

    Returns
    -------
    bool, bool, bool, bool
        status of orientation options

    """
    global txtbox1
    global txtbox2
    form = Form()  # Creates a Windows Form Application
    form.Size = Size(190, 170)
    form.Text = "Sensor orientation"  # Name for that form
    form.StartPosition = FormStartPosition.CenterScreen
    form.MaximizeBox = False
    form.MinimizeBox = False
    form.FormBorderStyle = FormBorderStyle.FixedSingle

    button = Button(Text="OK")  # Creates a Windows Form Application
    button.Location = Point(52, 110)  # Button Location
    button.DialogResult = DialogResult.OK

    lab = Label()
    lab.Text = "Choose orientation of the sensors relative to the selected axis system:"
    lab.Location = Point(5, 10)
    lab.Size = Size(180, 44)

    move_x = 15
    lab1 = Label()  # Creates label
    lab1.Text = "+X"  # Label Text
    lab1.Location = Point(20 + move_x, 54)
    lab1.Size = Size(25, 22)
    lab2 = Label()  # Creates label
    lab2.Location = Point(20 + move_x, 76)  # Label Location
    lab2.Text = "+Y"  # Label Text
    lab2.Size = Size(25, 22)

    radio1 = RadioButton()
    radio1.Location = Point(45 + move_x, 50)
    radio1.Checked = True
    radio1.Size = Size(25, 22)
    radio2 = RadioButton()
    radio2.Location = Point(45 + move_x, 72)
    radio2.Checked = False
    radio2.Size = Size(25, 22)

    lab3 = Label()  # Creates label
    lab3.Text = "- Y"  # Label Text
    lab3.Location = Point(85 + move_x, 54)
    lab3.Size = Size(25, 22)
    lab4 = Label()  # Creates label
    lab4.Location = Point(85 + move_x, 76)  # Label Location
    lab4.Text = "- X"  # Label Text
    lab4.Size = Size(25, 22)

    radio3 = RadioButton()
    radio3.Location = Point(110 + move_x, 50)
    radio3.Checked = False
    radio3.Size = Size(25, 22)
    radio4 = RadioButton()
    radio4.Location = Point(110 + move_x, 72)
    radio4.Checked = False
    radio4.Size = Size(25, 22)

    form.Controls.Add(lab)  # Add Label
    form.Controls.Add(lab1)  # Add Label
    form.Controls.Add(lab2)  # Add Label
    form.Controls.Add(lab3)  # Add Label
    form.Controls.Add(lab4)  # Add Label
    form.Controls.Add(radio1)
    form.Controls.Add(radio2)
    form.Controls.Add(radio3)
    form.Controls.Add(radio4)
    form.Controls.Add(button)
    button.Click += click  # Add event handler
    form.ShowDialog()
    return radio1.Checked, radio2.Checked, radio3.Checked, radio4.Checked


def click(sender, event):
    """function to check if selection is checked."""


def create_intensity_sensors(axys_sys, orientation_option):
    """
    create sensor at the location of provided coordinate system with properties from user.

    Parameters
    ----------
    axys_sys : SpaceClaim coordinate system
    orientation_option : str
        options for intensity sensor orientation: Front, Rear, Left, or Right
    """
    axes = axys_sys.GetDescendants[ICoordinateAxis]()
    axis_x = axes[0]
    axis_y = axes[1]
    axis_z = axes[2]

    axes_iesna = []
    axes_xmp = []
    iesna_y_rev = False
    xmp_x_rev = False
    name = ""
    if orientation_option == "Rear":
        axes_iesna = [axis_z, axis_x]
        axes_xmp = [axis_y, axis_z]
        iesna_y_rev = False
        xmp_x_rev = False
        name = "Rear_"
    elif orientation_option == "Left":
        axes_iesna = [axis_z, axis_y]
        axes_xmp = [axis_x, axis_z]
        iesna_y_rev = False
        xmp_x_rev = True
        name = "Left_"
    elif orientation_option == "Right":
        axes_iesna = [axis_z, axis_y]
        axes_xmp = [axis_x, axis_z]
        iesna_y_rev = True
        xmp_x_rev = False
        name = "Right_"
    elif orientation_option == "Front":
        axes_iesna = [axis_z, axis_x]
        axes_xmp = [axis_y, axis_z]
        iesna_y_rev = True
        xmp_x_rev = True
        name = "Front_"

    sampling_ies_hq = 721
    sampling_ies_lq = 361
    sampling_xmp_hq = 720
    sampling_xmp_lq = 360
    w_sampling_hq = 61
    w_sampling_lq = 31

    std_liq_IES = IntensitySensor(name + "StdLiqIES", SpeosSim, SpaceClaim)
    std_liq_IES.set_position(axes=axes_iesna, origin=axys_sys, y_reverse=iesna_y_rev)
    std_liq_IES.set_format(sensor_format="IESNATypeA")
    std_liq_IES.set_sampling(x_sampling=sampling_ies_hq, y_sampling=sampling_ies_hq)

    std_lig_color_5nm = IntensitySensor(name + "StdLigColor5nm", SpeosSim, SpaceClaim)
    std_lig_color_5nm.set_position(axes=axes_xmp, origin=axys_sys, x_reverse=xmp_x_rev)
    std_lig_color_5nm.set_format(sensor_format="XMP")
    std_lig_color_5nm.set_sampling(x_sampling=sampling_xmp_hq, y_sampling=sampling_xmp_hq)
    std_lig_color_5nm.set_wavelength(w_sampling=w_sampling_hq)
    std_lig_color_5nm.set_range(-90, 90, -90, 90, True, True)

    std_lig_color_10nm = IntensitySensor(name + "StdLigColor10nm", SpeosSim, SpaceClaim)
    std_lig_color_10nm.set_position(axes=axes_xmp, origin=axys_sys, x_reverse=xmp_x_rev)
    std_lig_color_10nm.set_format(sensor_format="XMP")
    std_lig_color_10nm.set_sampling(x_sampling=sampling_xmp_hq, y_sampling=sampling_xmp_hq)
    std_lig_color_10nm.set_wavelength(w_sampling=w_sampling_lq)
    std_lig_color_10nm.set_range(x_mirrored=True, y_mirrored=True, x_start=-90, x_end=90, y_start=-90, y_end=90)

    std_iq_IES = IntensitySensor(name + "StdSiqIES", SpeosSim, SpaceClaim)
    std_iq_IES.set_position(axes=axes_iesna, origin=axys_sys, y_reverse=iesna_y_rev)
    std_iq_IES.set_format(sensor_format="IESNATypeA")
    std_iq_IES.set_sampling(x_sampling=sampling_ies_lq, y_sampling=sampling_ies_lq)

    std_sig_color_5nm = IntensitySensor(name + "StdSigColor5nm", SpeosSim, SpaceClaim)
    std_sig_color_5nm.set_position(axes=axes_xmp, origin=axys_sys, x_reverse=xmp_x_rev)
    std_sig_color_5nm.set_format(sensor_format="XMP")
    std_sig_color_5nm.set_sampling(x_sampling=sampling_xmp_lq, y_sampling=sampling_xmp_lq)
    std_sig_color_5nm.set_wavelength(w_sampling=w_sampling_hq)
    std_sig_color_5nm.set_range(x_mirrored=True, y_mirrored=True, x_start=-90, x_end=90, y_start=-90, y_end=90)

    std_sig_color_10nm = IntensitySensor(name + "StdSigColor10nm", SpeosSim, SpaceClaim)
    std_sig_color_10nm.set_position(axes=axes_xmp, origin=axys_sys, x_reverse=xmp_x_rev)
    std_sig_color_10nm.set_format(sensor_format="XMP")
    std_sig_color_10nm.set_sampling(x_sampling=sampling_xmp_lq, y_sampling=sampling_xmp_lq)
    std_sig_color_10nm.set_wavelength(w_sampling=w_sampling_lq)
    std_sig_color_10nm.set_range(x_mirrored=True, y_mirrored=True, x_start=-90, x_end=90, y_start=-90, y_end=90)


def main():
    """
    main function to export multiple intensity sensors
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
        opt1, opt2, opt3, opt4 = orientation_selection_dialog()
        if opt1:
            create_intensity_sensors(axys_sys, "Rear")
        elif opt2:
            create_intensity_sensors(axys_sys, "Left")
        elif opt3:
            create_intensity_sensors(axys_sys, "Right")
        elif opt4:
            create_intensity_sensors(axys_sys, "Front")
    else:
        create_intensity_sensors(argsDict["origin"], argsDict["orientation"])


main()
