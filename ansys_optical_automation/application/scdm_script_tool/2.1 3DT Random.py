import ctypes
import os
import random

import clr

clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Drawing import Point
from System.Drawing import Size
from System.Windows.Forms import Application
from System.Windows.Forms import Button
from System.Windows.Forms import DialogResult
from System.Windows.Forms import Form
from System.Windows.Forms import FormStartPosition
from System.Windows.Forms import Label
from System.Windows.Forms import Panel
from System.Windows.Forms import ProgressBar
from System.Windows.Forms import ProgressBarStyle
from System.Windows.Forms import TextBox
from System.Windows.Forms import Timer

# -------------------------------------------------------------------------
# Windows MessageBox flags (for reference)
#   MB_OK: show OK button
#   MB_ICONINFORMATION: use information icon
#   MB_TOPMOST: keep message box on top
# -------------------------------------------------------------------------
MB_OK = 0x00000000
MB_ICONINFORMATION = 0x00000040
MB_TOPMOST = 0x00040000


def show_message(message, title="Message"):
    """
    Show a Windows message box anchored to the current foreground window.

    This helper obtains the foreground window handle (HWND) and displays
    a top-most informational MessageBox using the Win32 API.

    Parameters
    ----------
    message : str
        The text content to display in the message box.
    title : str, optional
        The caption/title for the message box window, by default "Message".

    Returns
    -------
    int
        The result code returned by MessageBoxW (IDOK, etc.).
    """
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    ctypes.windll.user32.MessageBoxW(hwnd, message, title, MB_OK | MB_ICONINFORMATION | MB_TOPMOST)


# === Simple progress window with animated bounce ===
class ProgressWindow(Form):
    """A minimal progress dialog with a continuously bouncing progress bar."""

    def __init__(self):
        """
        Initialize the progress window UI and start the bounce animation timer.

        Creates a label and a continuous ProgressBar that 'bounces' by
        incrementing/decrementing its value on each timer tick.
        """
        Form.__init__(self)
        self.Text = "Processing..."
        self.Size = Size(500, 120)
        self.StartPosition = FormStartPosition.CenterScreen
        self.TopMost = True
        self.ControlBox = False

        # Explanatory label
        self.label = Label()
        self.label.Text = "Please wait while processing..."
        self.label.AutoSize = True
        self.label.Location = Point(20, 15)
        self.Controls.Add(self.label)

        # Progress bar (continuous style for smooth animation)
        self.bar = ProgressBar()
        self.bar.Location = Point(20, 40)
        self.bar.Width = 440
        self.bar.Style = ProgressBarStyle.Continuous
        self.bar.Minimum = 0
        self.bar.Maximum = 100
        self.bar.Value = 0
        self.Controls.Add(self.bar)

        # Timer to animate the bar value
        self.timer = Timer()
        self.timer.Interval = 30  # ms
        self.timer.Tick += self.animate_bar
        self.direction = 1
        self.timer.Start()

    def animate_bar(self, sender, event):
        """
        Animate the progress bar by bouncing between 0 and 100.

        On each timer tick, increase/decrease the bar value and invert
        direction at the endpoints. Uses Application.DoEvents() to keep
        the UI responsive.

        Parameters
        ----------
        sender : object
            The event source (Timer).
        event : System.EventArgs
            Event data.

        Returns
        -------
        None
        """
        try:
            new_val = self.bar.Value + self.direction * 2
            if new_val >= 100:
                new_val = 100
                self.direction = -1
            elif new_val <= 0:
                new_val = 0
                self.direction = 1
            self.bar.Value = new_val
            Application.DoEvents()
        except Exception:
            # Silently ignore transient UI exceptions
            pass


# === GUI with editable control points ===
class DynamicProbabilityForm(Form):
    """
    A form to define and edit (x, probability) control points interactively.

    The form maintains a list of rows where each row contains:
    - Probability (float in [0, 1])
    - X percentage (float in [0, 100])
    The first (0%, prob) and last (100%, prob) points are fixed.
    """

    def __init__(self):
        """
        Initialize the form layout, default rows, and action buttons.

        Sets up:
        - A panel for editable rows
        - '+' / '-' to add/remove rows
        - 'Run' to confirm and compute normalized points list
        """
        Form.__init__(self)
        self.Text = "Control Points – Remove patterns"
        self.Size = Size(460, 500)
        self.TopMost = True
        self.StartPosition = FormStartPosition.CenterScreen

        # Container for input rows
        self.panel = Panel()
        self.panel.Location = Point(10, 40)
        self.panel.Size = Size(430, 320)
        self.Controls.Add(self.panel)

        # Column labels
        self.add_label_row("Probability", "X percentage")

        # Rows storage ((TextBox prob, TextBox xperc), ...)
        self.rows = []
        # Fixed endpoints: x=0% and x=100%
        self._add_row_inputs(0.0, 0.0, fixed=True)
        self._add_row_inputs(1.0, 100.0, fixed=True)

        # Add row button
        self.addButton = Button()
        self.addButton.Text = "+"
        self.addButton.Location = Point(30, 380)
        self.addButton.Click += self.add_row
        self.Controls.Add(self.addButton)

        # Remove row button
        self.removeButton = Button()
        self.removeButton.Text = "-"
        self.removeButton.Location = Point(80, 380)
        self.removeButton.Click += self.remove_row
        self.Controls.Add(self.removeButton)

        # Confirm / run button
        self.runButton = Button()
        self.runButton.Text = "Run"
        self.runButton.Location = Point(340, 380)
        self.runButton.Click += self.on_run
        self.Controls.Add(self.runButton)

        # Output: normalized points list [(x_norm, p), ...]
        self.points = []
        # Ensure form comes to front when shown
        self.Shown += self.bring_to_front

    def bring_to_front(self, sender, event):
        """
        Force the form to be top-most and focused when shown.

        Parameters
        ----------
        sender : object
            Event source.
        event : System.EventArgs
            Event data.

        Returns
        -------
        None
        """
        self.TopMost = True
        self.BringToFront()
        self.Focus()
        self.Activate()
        Application.DoEvents()

    def add_label_row(self, label1, label2):
        """
        Create static column labels above the input panel.

        Parameters
        ----------
        label1 : str
            Text for the first column label (probability).
        label2 : str
            Text for the second column label (x percentage).

        Returns
        -------
        None
        """
        l1 = Label()
        l1.Text = label1
        l1.Location = Point(10, 10)
        l1.AutoSize = True
        self.Controls.Add(l1)

        l2 = Label()
        l2.Text = label2
        l2.Location = Point(200, 10)
        l2.AutoSize = True
        self.Controls.Add(l2)

    def add_row(self, sender=None, event=None):
        """
        Insert a new editable row before the last fixed endpoint.

        Parameters
        ----------
        sender : object, optional
            Event source (button), by default None.
        event : System.EventArgs, optional
            Event data, by default None.

        Returns
        -------
        None
        """
        index = len(self.rows) - 1
        self._add_row_inputs(0.5, 50.0, fixed=False, insert_index=index)
        self._redraw_rows()

    def remove_row(self, sender=None, event=None):
        """
        Remove the last editable row (keeps the two fixed endpoints).

        Parameters
        ----------
        sender : object, optional
            Event source (button), by default None.
        event : System.EventArgs, optional
            Event data, by default None.

        Returns
        -------
        None
        """
        if len(self.rows) > 2:
            self.panel.Controls.Remove(self.rows[-2][0])
            self.panel.Controls.Remove(self.rows[-2][1])
            del self.rows[-2]
            self._redraw_rows()

    def _add_row_inputs(self, prob, xperc, fixed=False, insert_index=None):
        """
        Create a pair of TextBoxes for probability and x-percentage.

        Parameters
        ----------
        prob : float
            Initial probability value (0..1).
        xperc : float
            Initial x-percentage value (0..100).
        fixed : bool, optional
            If True, x-percentage field is disabled, by default False.
        insert_index : int, optional
            Index to insert the row at; defaults to append behavior.

        Returns
        -------
        None
        """
        tb_prob = TextBox()
        tb_prob.Text = str(prob)
        tb_prob.Width = 100

        tb_x = TextBox()
        tb_x.Text = str(xperc)
        tb_x.Width = 100
        tb_x.Enabled = not fixed

        if insert_index is None:
            insert_index = len(self.rows)

        self.rows.insert(insert_index, (tb_prob, tb_x))
        self._redraw_rows()

    def _redraw_rows(self):
        """
        Position TextBoxes in the panel with consistent vertical spacing.

        Iterates over the stored rows and sets their locations. Adds them
        to the panel if not already added.

        Returns
        -------
        None
        """
        for i, (tb_p, tb_x) in enumerate(self.rows):
            y = i * 30
            tb_p.Location = Point(10, y)
            tb_x.Location = Point(200, y)
            if tb_p.Parent is None:
                self.panel.Controls.Add(tb_p)
                self.panel.Controls.Add(tb_x)

    def on_run(self, sender, event):
        """
        Validate inputs, sort by x-percentage, and produce normalized points.

        Reads all (prob, x%) rows, converts to floats, sorts by x%, then
        normalizes x to [0..1] and stores points internally as (x_norm, prob).
        Sets DialogResult to OK and closes on success; otherwise shows an error.

        Parameters
        ----------
        sender : object
            Event source (Run button).
        event : System.EventArgs
            Event data.

        Returns
        -------
        None
        """
        try:
            raw = [(float(tb_p.Text), float(tb_x.Text)) for tb_p, tb_x in self.rows]
            sorted_points = sorted(raw, key=lambda p: p[1])
            self.points = [(x / 100.0, p) for p, x in sorted_points]
            self.DialogResult = DialogResult.OK
            self.Close()
        except Exception:
            show_message("Invalid input. Please check values.", "Input Error")


def process_mapping_file(input_file, control_points, master_name):
    """
    Filter an .OPT3DMapping file based on an x-dependent removal probability.

    The function:
    1) Reads the mapping file and parses X values.
    2) Normalizes X by the maximum X found.
    3) Interpolates a probability from control_points for each line.
    4) Keeps a line if random.random() >= probability.
    5) Writes a new file with the filtered lines and returns its path.

    Parameters
    ----------
    input_file : str
        Full path to the source .OPT3DMapping file.
    control_points : list of tuple(float, float)
        List of (x_norm, probability) pairs, with x_norm in [0..1] and
        probability in [0..1]. Must be sorted by x_norm.
    master_name : str
        Base name used to build the output filename.

    Returns
    -------
    str
        Full path to the newly written .OPT3DMapping file.
    """
    with open(input_file, "r") as f:
        lines = f.readlines()

    data_lines = lines[1:]

    # Parse X from each line; keep original line for later writing
    parsed = []
    for line in data_lines:
        parts = line.strip().split()
        x = float(parts[0])
        parsed.append((x, line))

    # Normalize X by maximum
    x_max = max([x for x, _ in parsed])
    filtered_lines = []

    # Probabilistic filtering per normalized X
    for x, line in parsed:
        x_norm = x / x_max
        p = interpolate_probability(x_norm, control_points)
        if random.random() >= p:
            filtered_lines.append(line)

    new_count = len(filtered_lines)

    # Encode control points in filename for traceability
    points_str = "_".join(["p{:.1f}-{:.1f}".format(p, x * 100) for x, p in control_points])
    output_file = os.path.join(os.path.dirname(input_file), "{}_{}.OPT3DMapping".format(master_name, points_str))

    # Write new header (count) and kept lines
    with open(output_file, "w") as f:
        f.write("{}\n".format(new_count))
        for line in filtered_lines:
            f.write(line)

    return output_file


def interpolate_probability(x_norm, control_points):
    """
    Linearly interpolate a probability value for a given normalized x.

    Given a sorted list of control points [(x0, p0), (x1, p1), ...],
    returns the linear interpolation for x_norm between the surrounding
    points. If x_norm exceeds the last point, returns the last probability.

    Parameters
    ----------
    x_norm : float
        Normalized x in [0..1].
    control_points : list of tuple(float, float)
        Sorted (x, p) pairs where x in [0..1] and p in [0..1].

    Returns
    -------
    float
        Interpolated probability in [0..1].
    """
    for i in range(len(control_points) - 1):
        x0, p0 = control_points[i]
        x1, p1 = control_points[i + 1]
        if x0 <= x_norm <= x1:
            return p0 + (p1 - p0) * ((x_norm - x0) / (x1 - x0))
    return control_points[-1][1]


# -----------------------------------------------------------------------------
# Main execution block
# Attempts to:
#   1) Validate selection (exactly one 3D Texture)
#   2) Switch mapping to 'FromFile'
#   3) Open control-points editor, collect points
#   4) Process mapping file and update texture
# Errors are surfaced via message boxes.
# -----------------------------------------------------------------------------
try:
    selected_items = Selection.GetActive().Items

    if len(selected_items) != 1:
        show_message("Please select exactly one 3D Texture object.", "Selection Error")
    else:
        master = selected_items[0].GetMaster()
        if str(master.Type) != "SPEOS_SC.SIM.SpeosWrapperComponent3DTexture":
            show_message("Selected object is not a valid 3D Texture.", "Type Error")
        else:
            dTexture = SpeosSim.Component3DTexture.Find(master.Name)
            dTexture.MappingType = SpeosSim.Component3DTexture.EnumMappingType.FromFile
            original_path = os.path.normpath(dTexture.MappingFileFullPath)

            # Open the dynamic control-points form (modal-like loop)
            form = DynamicProbabilityForm()
            form.Show()
            while form.Visible:
                Application.DoEvents()

            if form.DialogResult == DialogResult.OK:
                control_points = form.points

                show_message("Please wait while the mapping file and texture are being computed.", "Processing")

                # Process mapping file and update the texture
                new_file = process_mapping_file(original_path, control_points, master.Name)
                dTexture.MappingFile = new_file
                dTexture.Compute()
                show_message("Mapping file processed and updated successfully.", "Done")
except Exception as e:
    # Catch-all to surface unexpected exceptions to the user
    show_message("Unexpected error:{}".format(str(e)), "Script Error")
