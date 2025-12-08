"""
Create Speos rectangular reflectors from SpaceClaim coordinate systems.

This script runs inside Ansys Speos (IronPython). From the current
SpaceClaim selection, it builds one rectangular surface (reflector)
per selected coordinate system, using a single support body and a
special coordinate system used as global target axis system.

How it works
------------
- The user selects:
  * One body that will act as a freeform support.
  * Several coordinate systems.
  * Among those coordinate systems, one must have the name given by
    ``DEFAULT_TARGET_CS_NAME`` (by default ``"target"``).
- The script uses:
  * Each coordinate system origin as the focal point.
  * Each coordinate system X / Y axes for the local style axis system.
  * The target CS X / Y axes for the global target axis and orientation.
- A Windows Forms dialog lets the user define:
  * Styling parameters (XStart, XEnd, YStart, YEnd, XSize, YSize).
  * Pillow definition (radii or freeform group).

Notes
-----
- Requires the SpaceClaim and Speos .NET assemblies to be available
  in the IronPython environment.
- The script assumes ``GetRootPart``, ``Selection``, ``FaceSelection``
  and ``SpeosDes`` are provided by the Speos scripting context.
"""

import ctypes

import clr

# IMPORTANT: load .NET assemblies before importing from them
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from SpaceClaim.Api.V252 import CoordinateSystem
from SpaceClaim.Api.V252 import DesignBody  # TO UPDATE with your version if needed
from System.Drawing import Font
from System.Drawing import FontStyle
from System.Drawing import Point
from System.Drawing import Size
from System.Windows.Forms import Application
from System.Windows.Forms import Button
from System.Windows.Forms import DialogResult
from System.Windows.Forms import Form
from System.Windows.Forms import FormStartPosition
from System.Windows.Forms import Label
from System.Windows.Forms import RadioButton
from System.Windows.Forms import TextBox

# GetRootPart, Selection, FaceSelection, SpeosDes are provided by the environment.

# -----------------------------------------------------------
# CONFIGURATION FLAGS & DEFAULTS
# -----------------------------------------------------------
ENABLE_GUI = True  # Set to False if you want to bypass the GUI and use defaults

# Name of the Coordinate System used as global target
DEFAULT_TARGET_CS_NAME = "target"

# Default "Styling" parameters
DEFAULT_STYLE_XSTART = -10.0
DEFAULT_STYLE_XEND = 10.0
DEFAULT_STYLE_YSTART = 0.0
DEFAULT_STYLE_YEND = 20.0
DEFAULT_STYLE_XSIZE = 2.0
DEFAULT_STYLE_YSIZE = 2.0

# Default "Pillow Definition" mode and parameters
#   Mode can be "Radii" or "Freeform"
DEFAULT_PILLOW_MODE = "Radii"

# Defaults if mode == "Radii"
DEFAULT_RADII_XRADIUS = 10.0
DEFAULT_RADII_YRADIUS = 10.0

# Defaults if mode == "Freeform"
DEFAULT_FREEFORM_XSTART = -10.0
DEFAULT_FREEFORM_XEND = 10.0
DEFAULT_FREEFORM_YSTART = -10.0
DEFAULT_FREEFORM_YEND = 10.0

# -----------------------------------------------------------
# WIN32 MessageBox helper (topmost popup)
# -----------------------------------------------------------
MB_OK = 0x00000000
MB_ICONINFORMATION = 0x00000040
MB_TOPMOST = 0x00040000


def get_foreground_hwnd():
    """Return the handle to the current foreground window.

    Returns
    -------
    int
        Win32 window handle (HWND) of the current foreground window.
    """
    return ctypes.windll.user32.GetForegroundWindow()


def show_message(message, title="Message"):
    """Show a simple topmost message box.

    Parameters
    ----------
    message : str
        Text to display in the message box.
    title : str, optional
        Title of the message box window, by default ``"Message"``.
    """
    hwnd = get_foreground_hwnd()
    ctypes.windll.user32.MessageBoxW(
        hwnd,
        message,
        title,
        MB_OK | MB_ICONINFORMATION | MB_TOPMOST,
    )


# -----------------------------------------------------------
# UX for "Styling" + "Pillow Definition"
# -----------------------------------------------------------
class RectangularParametersForm(Form):
    """Dialog to edit styling and pillow parameters for rectangular surfaces.

    The form exposes two logical sections.

    Styling
        Global rectangular styling parameters:
        ``XStart``, ``XEnd``, ``YStart``, ``YEnd``, ``XSize``, ``YSize``.

    Pillow Definition
        Choice between:

        * Radii: ``XRadius``, ``YRadius``.
        * Freeform group: ``Group XStart``, ``Group XEnd``,
          ``Group YStart``, ``Group YEnd``.

    After a successful ``Compute`` (``DialogResult.OK``), the parsed values
    are available as instance attributes.

    Attributes
    ----------
    Style_XStart, Style_XEnd, Style_YStart, Style_YEnd : float
        Global rectangular styling bounds.
    Style_XSize, Style_YSize : float
        Pillow size parameters in X and Y.
    PillowMode : {"Radii", "Freeform"}
        Selected pillow definition mode.
    Radii_XRadius, Radii_YRadius : float
        Pillow radii values (only valid when ``PillowMode == "Radii"``).
    Free_XStart, Free_XEnd, Free_YStart, Free_YEnd : float
        Group bounds (only valid when ``PillowMode == "Freeform"``).
    """

    def __init__(self):
        Form.__init__(self)

        self.Text = "Rectangular Surface Parameters"
        # Higher form so buttons are clearly below the Pillow section
        self.Size = Size(420, 500)
        self.StartPosition = FormStartPosition.CenterScreen
        self.TopMost = True

        # ---- Section: Styling ----
        lbl_styling = Label()
        lbl_styling.Text = "Styling"
        lbl_styling.Font = Font(lbl_styling.Font, FontStyle.Bold)
        lbl_styling.Location = Point(20, 15)
        lbl_styling.AutoSize = True
        self.Controls.Add(lbl_styling)

        # TextBoxes for Styling
        self.tb_style_xstart = TextBox()
        self.tb_style_xend = TextBox()
        self.tb_style_ystart = TextBox()
        self.tb_style_yend = TextBox()
        self.tb_style_xsize = TextBox()
        self.tb_style_ysize = TextBox()

        self.tb_style_xstart.Text = str(DEFAULT_STYLE_XSTART)
        self.tb_style_xend.Text = str(DEFAULT_STYLE_XEND)
        self.tb_style_ystart.Text = str(DEFAULT_STYLE_YSTART)
        self.tb_style_yend.Text = str(DEFAULT_STYLE_YEND)
        self.tb_style_xsize.Text = str(DEFAULT_STYLE_XSIZE)
        self.tb_style_ysize.Text = str(DEFAULT_STYLE_YSIZE)

        self._build_styling_layout(top_y=40)

        # ---- Section: Pillow Definition ----
        lbl_pillow = Label()
        lbl_pillow.Text = "Pillow Definition"
        lbl_pillow.Font = Font(lbl_pillow.Font, FontStyle.Bold)
        lbl_pillow.Location = Point(20, 200)
        lbl_pillow.AutoSize = True
        self.Controls.Add(lbl_pillow)

        # Radio buttons for Pillow mode
        self.rb_radii = RadioButton()
        self.rb_radii.Text = "Radii"
        self.rb_radii.Location = Point(30, 230)
        self.rb_radii.AutoSize = True
        self.rb_radii.Checked = DEFAULT_PILLOW_MODE == "Radii"
        self.rb_radii.CheckedChanged += self.on_mode_changed
        self.Controls.Add(self.rb_radii)

        self.rb_freeform = RadioButton()
        self.rb_freeform.Text = "Freeform"
        self.rb_freeform.Location = Point(120, 230)
        self.rb_freeform.AutoSize = True
        self.rb_freeform.Checked = DEFAULT_PILLOW_MODE == "Freeform"
        self.rb_freeform.CheckedChanged += self.on_mode_changed
        self.Controls.Add(self.rb_freeform)

        # TextBoxes for Radii mode
        self.tb_radii_xradius = TextBox()
        self.tb_radii_yradius = TextBox()
        self.tb_radii_xradius.Text = str(DEFAULT_RADII_XRADIUS)
        self.tb_radii_yradius.Text = str(DEFAULT_RADII_YRADIUS)

        # TextBoxes for Freeform mode (group pillow)
        self.tb_free_xstart = TextBox()
        self.tb_free_xend = TextBox()
        self.tb_free_ystart = TextBox()
        self.tb_free_yend = TextBox()
        self.tb_free_xstart.Text = str(DEFAULT_FREEFORM_XSTART)
        self.tb_free_xend.Text = str(DEFAULT_FREEFORM_XEND)
        self.tb_free_ystart.Text = str(DEFAULT_FREEFORM_YSTART)
        self.tb_free_yend.Text = str(DEFAULT_FREEFORM_YEND)

        # Place pillow controls a bit higher, leaving room for buttons below
        self._build_pillow_layout(top_y=260)

        # OK and Cancel buttons – clearly under the Pillow Definition section
        self.btn_ok = Button()
        self.btn_ok.Text = "Compute"
        self.btn_ok.Location = Point(80, 430)
        self.btn_ok.Click += self.on_ok
        self.Controls.Add(self.btn_ok)

        self.btn_cancel = Button()
        self.btn_cancel.Text = "Cancel"
        self.btn_cancel.Location = Point(220, 430)
        self.btn_cancel.Click += self.on_cancel
        self.Controls.Add(self.btn_cancel)

        # Initialize enable/disable state based on default radio selection
        self.update_pillow_controls()

    # ------------- Layout helpers -------------

    def _build_styling_layout(self, top_y):
        """Create labels and place TextBoxes for the Styling section.

        Parameters
        ----------
        top_y : int
            Vertical offset (in pixels) from the top of the form where
            the styling controls should start.
        """
        labels = [
            ("XStart", self.tb_style_xstart),
            ("XEnd", self.tb_style_xend),
            ("YStart", self.tb_style_ystart),
            ("YEnd", self.tb_style_yend),
            ("XSize", self.tb_style_xsize),
            ("YSize", self.tb_style_ysize),
        ]

        dy = 24
        for i, (text, tb) in enumerate(labels):
            y = top_y + i * dy

            lbl = Label()
            lbl.Text = text
            lbl.Location = Point(20, y + 3)
            lbl.AutoSize = True
            self.Controls.Add(lbl)

            tb.Width = 100
            tb.Location = Point(120, y)
            self.Controls.Add(tb)

    def _build_pillow_layout(self, top_y):
        """Create and position controls for the Pillow Definition section.

        Parameters
        ----------
        top_y : int
            Vertical offset (in pixels) from the top of the form where
            the pillow controls should start.
        """
        # Radii controls
        lbl_rx = Label()
        lbl_rx.Text = "XRadius"
        lbl_rx.Location = Point(40, top_y + 3)
        lbl_rx.AutoSize = True
        self.Controls.Add(lbl_rx)

        self.tb_radii_xradius.Width = 100
        self.tb_radii_xradius.Location = Point(140, top_y)
        self.Controls.Add(self.tb_radii_xradius)

        lbl_ry = Label()
        lbl_ry.Text = "YRadius"
        lbl_ry.Location = Point(40, top_y + 27)
        lbl_ry.AutoSize = True
        self.Controls.Add(lbl_ry)

        self.tb_radii_yradius.Width = 100
        self.tb_radii_yradius.Location = Point(140, top_y + 24)
        self.Controls.Add(self.tb_radii_yradius)

        # Freeform controls
        free_top = top_y

        lbl_fx = Label()
        lbl_fx.Text = "Group XStart"
        lbl_fx.Location = Point(260, free_top + 3)
        lbl_fx.AutoSize = True
        self.Controls.Add(lbl_fx)

        self.tb_free_xstart.Width = 80
        self.tb_free_xstart.Location = Point(260, free_top + 20)
        self.Controls.Add(self.tb_free_xstart)

        lbl_fx2 = Label()
        lbl_fx2.Text = "Group XEnd"
        lbl_fx2.Location = Point(260, free_top + 47)
        lbl_fx2.AutoSize = True
        self.Controls.Add(lbl_fx2)

        self.tb_free_xend.Width = 80
        self.tb_free_xend.Location = Point(260, free_top + 64)
        self.Controls.Add(self.tb_free_xend)

        lbl_fy = Label()
        lbl_fy.Text = "Group YStart"
        lbl_fy.Location = Point(260, free_top + 91)
        lbl_fy.AutoSize = True
        self.Controls.Add(lbl_fy)

        self.tb_free_ystart.Width = 80
        self.tb_free_ystart.Location = Point(260, free_top + 108)
        self.Controls.Add(self.tb_free_ystart)

        lbl_fy2 = Label()
        lbl_fy2.Text = "Group YEnd"
        lbl_fy2.Location = Point(260, free_top + 135)
        lbl_fy2.AutoSize = True
        self.Controls.Add(lbl_fy2)

        self.tb_free_yend.Width = 80
        self.tb_free_yend.Location = Point(260, free_top + 152)
        self.Controls.Add(self.tb_free_yend)

    # ------------- Pillow mode handling -------------

    def on_mode_changed(self, sender, event):
        """Update controls when Radii/Freeform selection changes."""
        self.update_pillow_controls()

    def update_pillow_controls(self):
        """Enable or disable controls depending on the active pillow mode."""
        is_radii = self.rb_radii.Checked
        is_free = self.rb_freeform.Checked

        # Radii controls
        self.tb_radii_xradius.Enabled = is_radii
        self.tb_radii_yradius.Enabled = is_radii

        # Freeform controls
        self.tb_free_xstart.Enabled = is_free
        self.tb_free_xend.Enabled = is_free
        self.tb_free_ystart.Enabled = is_free
        self.tb_free_yend.Enabled = is_free

    # ------------- OK / Cancel -------------

    def on_ok(self, sender, event):
        """Parse all user inputs and store them in attributes.

        If some value is invalid, an error is shown and the form remains open.
        """
        try:
            # Styling
            self.Style_XStart = float(self.tb_style_xstart.Text)
            self.Style_XEnd = float(self.tb_style_xend.Text)
            self.Style_YStart = float(self.tb_style_ystart.Text)
            self.Style_YEnd = float(self.tb_style_yend.Text)
            self.Style_XSize = float(self.tb_style_xsize.Text)
            self.Style_YSize = float(self.tb_style_ysize.Text)

            # Pillow mode
            if self.rb_radii.Checked:
                self.PillowMode = "Radii"
                self.Radii_XRadius = float(self.tb_radii_xradius.Text)
                self.Radii_YRadius = float(self.tb_radii_yradius.Text)
            elif self.rb_freeform.Checked:
                self.PillowMode = "Freeform"
                self.Free_XStart = float(self.tb_free_xstart.Text)
                self.Free_XEnd = float(self.tb_free_xend.Text)
                self.Free_YStart = float(self.tb_free_ystart.Text)
                self.Free_YEnd = float(self.tb_free_yend.Text)
            else:
                show_message(
                    "Please select a Pillow Definition mode (Radii or Freeform).",
                    "Input Error",
                )
                return

        except Exception:
            show_message("Invalid numeric input. Please check all fields.", "Input Error")
            return

        self.DialogResult = DialogResult.OK
        self.Close()

    def on_cancel(self, sender, event):
        """Handle user cancellation."""
        self.DialogResult = DialogResult.Cancel
        self.Close()


# -----------------------------------------------------------
# Helper: get all parameters (Styling + Pillow Definition)
# -----------------------------------------------------------
def get_all_parameters():
    """Return all styling and pillow parameters.

    The values are taken either from the GUI (when ``ENABLE_GUI`` is True)
    or from the default constants defined at module level.

    Returns
    -------
    dict
        Dictionary with the following keys:

        ``"style"`` : tuple of float
            ``(x_start, x_end, y_start, y_end, x_size, y_size)``.
        ``"pillow_mode"`` : {"Radii", "Freeform"}
            Selected pillow definition mode.
        ``"radii"`` : tuple of float
            ``(x_radius, y_radius)`` for radii-based pillows.
        ``"freeform"`` : tuple of float
            ``(group_x_start, group_x_end, group_y_start, group_y_end)``
            for freeform group pillows.
    """
    if not ENABLE_GUI:
        # GUI disabled -> direct defaults
        style = (
            DEFAULT_STYLE_XSTART,
            DEFAULT_STYLE_XEND,
            DEFAULT_STYLE_YSTART,
            DEFAULT_STYLE_YEND,
            DEFAULT_STYLE_XSIZE,
            DEFAULT_STYLE_YSIZE,
        )

        if DEFAULT_PILLOW_MODE == "Radii":
            return {
                "style": style,
                "pillow_mode": "Radii",
                "radii": (DEFAULT_RADII_XRADIUS, DEFAULT_RADII_YRADIUS),
                "freeform": (
                    DEFAULT_FREEFORM_XSTART,
                    DEFAULT_FREEFORM_XEND,
                    DEFAULT_FREEFORM_YSTART,
                    DEFAULT_FREEFORM_YEND,
                ),
            }

        return {
            "style": style,
            "pillow_mode": "Freeform",
            "radii": (DEFAULT_RADII_XRADIUS, DEFAULT_RADII_YRADIUS),
            "freeform": (
                DEFAULT_FREEFORM_XSTART,
                DEFAULT_FREEFORM_XEND,
                DEFAULT_FREEFORM_YSTART,
                DEFAULT_FREEFORM_YEND,
            ),
        }

    # GUI enabled -> show form
    form = RectangularParametersForm()
    form.Show()

    while form.Visible:
        Application.DoEvents()

    if form.DialogResult != DialogResult.OK:
        raise Exception("Operation cancelled by the user.")

    style = (
        form.Style_XStart,
        form.Style_XEnd,
        form.Style_YStart,
        form.Style_YEnd,
        form.Style_XSize,
        form.Style_YSize,
    )

    if form.PillowMode == "Radii":
        radii = (form.Radii_XRadius, form.Radii_YRadius)
        freef = (
            DEFAULT_FREEFORM_XSTART,
            DEFAULT_FREEFORM_XEND,
            DEFAULT_FREEFORM_YSTART,
            DEFAULT_FREEFORM_YEND,
        )
    else:
        radii = (DEFAULT_RADII_XRADIUS, DEFAULT_RADII_YRADIUS)
        freef = (form.Free_XStart, form.Free_XEnd, form.Free_YStart, form.Free_YEnd)

    return {
        "style": style,
        "pillow_mode": form.PillowMode,
        "radii": radii,
        "freeform": freef,
    }


# -----------------------------------------------------------
# MAIN LOGIC
# -----------------------------------------------------------
try:
    active_selection = Selection.GetActive()
    selected_items = list(active_selection.Items)

    if len(selected_items) == 0:
        show_message(
            "No selection found. Please select one support body and one or more "
            "coordinate systems (including one named '{0}').".format(DEFAULT_TARGET_CS_NAME),
            "Selection Error",
        )
        raise SystemExit

    # Separate selection into support body / coordinate systems
    support_bodies = []
    coord_systems = []

    for item in selected_items:
        if isinstance(item, DesignBody):
            support_bodies.append(item)
        elif isinstance(item, CoordinateSystem):
            coord_systems.append(item)

    # --- Check support body conditions ---
    if len(support_bodies) == 0:
        show_message(
            "No support body found. Please select exactly one body plus coordinate systems.",
            "Selection Error",
        )
        raise SystemExit

    if len(support_bodies) > 1:
        show_message(
            "More than one support body (surface) is selected.\n" "Please select only ONE body as the support.",
            "Multiple Surfaces Found",
        )
        raise SystemExit

    # --- Check coordinate systems ---
    if len(coord_systems) == 0:
        show_message(
            "No Coordinate Systems found in the selection.\n"
            "Please select at least one Coordinate System plus '{0}'.".format(DEFAULT_TARGET_CS_NAME),
            "Selection Error",
        )
        raise SystemExit

    if len(coord_systems) < 2:
        show_message(
            "At least two Coordinate Systems are required:\n"
            "- One '{0}' Coordinate System.\n"
            "- At least one additional reflector Coordinate System.".format(DEFAULT_TARGET_CS_NAME),
            "Selection Error",
        )
        raise SystemExit

    # Find the target Coordinate System
    target_cs = None
    for cs in coord_systems:
        try:
            if cs.Name and cs.Name.lower() == DEFAULT_TARGET_CS_NAME.lower():
                target_cs = cs
                break
        except Exception:
            # If for some reason Name is not accessible, skip
            pass

    if target_cs is None:
        show_message(
            "No Coordinate System named '{0}' was found in the selection.\n"
            "Please create/select a CS called '{0}' to define the common target axes.".format(DEFAULT_TARGET_CS_NAME),
            "Target CS Not Found",
        )
        raise SystemExit

    # Reflector coordinate systems = all CS except target CS
    reflector_coord_systems = [cs for cs in coord_systems if cs is not target_cs]

    if len(reflector_coord_systems) == 0:
        show_message(
            "Only the '{0}' Coordinate System is selected.\n"
            "Please select at least one additional Coordinate System to create reflectors.".format(
                DEFAULT_TARGET_CS_NAME
            ),
            "No Reflector CS Found",
        )
        raise SystemExit

    support_body = support_bodies[0]

    # Use the first face of the selected body as support
    body_faces = list(support_body.Faces)
    if len(body_faces) == 0:
        show_message(
            "The selected body has no faces. Cannot create a support surface.",
            "Support Error",
        )
        raise SystemExit

    support_face = body_faces[0]

    # Get parameters from UX or defaults
    params = get_all_parameters()
    (
        style_xstart,
        style_xend,
        style_ystart,
        style_yend,
        style_xsize,
        style_ysize,
    ) = params["style"]

    pillow_mode = params["pillow_mode"]
    radii_xradius, radii_yradius = params["radii"]
    free_xstart, free_xend, free_ystart, free_yend = params["freeform"]

    show_message(
        "Creating one rectangular reflector per selected Coordinate System.\n"
        "Number of reflector CS: {0}\n"
        "Global Target CS: {1}\n"
        "Pillow mode: {2}".format(
            len(reflector_coord_systems),
            getattr(target_cs, "Name", DEFAULT_TARGET_CS_NAME),
            pillow_mode,
        ),
        "Processing",
    )

    root_part = GetRootPart()
    created_count = 0

    # Pre-build selections for the global target axis system
    target_axis_selection = Selection.Create(target_cs.Axes[0])
    target_orientation_selection = Selection.Create(target_cs.Axes[1])

    # ---------------------------------------------------
    # Loop over each reflector Coordinate System and create a reflector
    # ---------------------------------------------------
    for cs in reflector_coord_systems:
        optical_surface_rectangular = SpeosDes.RectangularSurface.Create()

        cs_name = cs.Name if hasattr(cs, "Name") else "CS"
        optical_surface_rectangular.Name = "OS_{0}".format(cs_name)

        # General / SourcePoint -> current CS
        sel_source_point = Selection.Create(cs)
        optical_surface_rectangular.General.SourcePoint.Set(sel_source_point.Items)

        # General / SupportType and SupportBody
        optical_surface_rectangular.General.SupportType = SpeosDes.OpticalFeatureGeneral.EnumSupportType.Freeform

        face_selection = FaceSelection.Create(support_face)
        optical_surface_rectangular.General.SupportBody.Set(face_selection.Items)

        # General / TargetAxis and TargetOrientation -> global target CS
        optical_surface_rectangular.General.TargetAxis.Set(target_axis_selection.Items)
        optical_surface_rectangular.General.TargetOrientation.Set(target_orientation_selection.Items)

        # Style / Axis system -> current CS axes
        style_axis_selection = Selection.Create(cs.Axes[0])
        optical_surface_rectangular.Style.StyleAxis.Set(style_axis_selection.Items)

        style_orientation_selection = Selection.Create(cs.Axes[1])
        optical_surface_rectangular.Style.StyleOrientation.Set(style_orientation_selection.Items)

        # Style / Rectangular definition and ranges
        optical_surface_rectangular.Style.XStart = style_xstart
        optical_surface_rectangular.Style.XEnd = style_xend
        optical_surface_rectangular.Style.YStart = style_ystart
        optical_surface_rectangular.Style.YEnd = style_yend

        optical_surface_rectangular.Style.Definition = (
            SpeosDes.OpticalFeatureStyleRectangular.EnumDefinition.ElementsSize
        )
        optical_surface_rectangular.Style.XSize = style_xsize
        optical_surface_rectangular.Style.YSize = style_ysize

        # Manufacturing (optional)
        optical_surface_rectangular.Manufacturing.DraftingType = "By angle"

        # ---------------------------------------------------
        # Pillow Definition (Group[0])
        # ---------------------------------------------------
        group0 = optical_surface_rectangular.Groups[0]

        if pillow_mode == "Radii":
            group0.GroupType = "Radii"
            group0.XRadius = radii_xradius
            group0.YRadius = radii_yradius
        else:
            group0.GroupType = "ReflectFreeform"
            group0.XStart = free_xstart
            group0.XEnd = free_xend
            group0.YStart = free_ystart
            group0.YEnd = free_yend

        # Compute the reflector
        optical_surface_rectangular.Compute()
        created_count += 1

    show_message(
        "Rectangular reflectors successfully created.\n"
        "Number of reflectors: {0}\n"
        "Global Target CS: {1}\n"
        "Pillow mode: {2}".format(
            created_count,
            getattr(target_cs, "Name", DEFAULT_TARGET_CS_NAME),
            pillow_mode,
        ),
        "Done",
    )

except Exception as e:  # noqa: BLE001
    show_message("Unexpected error: {0}".format(str(e)), "Script Error")
