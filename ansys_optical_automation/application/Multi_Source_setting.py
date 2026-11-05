# Python Script, API Version = V261

from System import Math

#Default setting
#Material name = source_mat
SOURCE_GEOMETRY_NAME = "source"       # geometry to copy
SURFACE_SOURCE_NAME  = "source_set"   # Speos surface source to copy

DEG2RAD = Math.PI / 180.0

#GUI
def ask_grid_parameters():
    """Open a Windows Forms dialog; return a params dict or None if cancelled."""
    import clr
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
    from System.Windows.Forms import (
        Form, Label, TextBox, Button, GroupBox, DialogResult, ComboBox,
        ComboBoxStyle, FormBorderStyle, FormStartPosition, MessageBox,
        MessageBoxButtons, MessageBoxIcon)
    from System.Drawing import Point as DPoint, Size, Font, FontStyle

    # --- layout sizing constants (enlarge the whole dialog here) ----------
    UI_FONT        = Font("Segoe UI", 11.0)         # base font for all controls
    GROUP_FONT     = Font("Segoe UI", 11.0, FontStyle.Bold)
    MARGIN         = 16                              # left/right margin & gaps
    GROUP_W        = 800                             # group box width
    ROW_H          = 100                              # vertical pitch per row
    LABEL_X        = 20
    LABEL_W        = 230
    FIELD_X        = 250                             # x of textbox / combo
    FIELD_W        = 200
    FIELD_H        = 60
    GROUP_TOP_PAD  = 50                              # space below group title
    GROUP_BOT_PAD  = 30
    BTN_W          = 130
    BTN_H          = 50
    FORM_W         = GROUP_W + 2 * MARGIN            # client width

    form = Form()
    form.Text = u"H / V Source Copy"
    form.Font = UI_FONT
    form.FormBorderStyle = FormBorderStyle.FixedDialog
    form.StartPosition = FormStartPosition.CenterScreen
    form.MaximizeBox = False
    form.MinimizeBox = False

    boxes = {}
    combos = {}

    def _group(title, y, n_rows):
        gb = GroupBox()
        gb.Text = title
        gb.Font = GROUP_FONT
        gb.Location = DPoint(MARGIN, y)
        gb.Size = Size(GROUP_W, GROUP_TOP_PAD + ROW_H * n_rows + GROUP_BOT_PAD)
        form.Controls.Add(gb)
        return gb

    def add_group(title, y, rows):
        gb = _group(title, y, len(rows))
        ry = GROUP_TOP_PAD
        for key, label, default in rows:
            lbl = Label()
            lbl.Text = label
            lbl.Font = UI_FONT
            lbl.Location = DPoint(LABEL_X, ry + 4)
            lbl.Size = Size(LABEL_W, FIELD_H)
            gb.Controls.Add(lbl)
            tb = TextBox()
            tb.Font = UI_FONT
            tb.Text = str(default)
            tb.Location = DPoint(FIELD_X, ry)
            tb.Size = Size(FIELD_W, FIELD_H)
            gb.Controls.Add(tb)
            boxes[key] = tb
            ry += ROW_H
        return y + gb.Size.Height + MARGIN

    def add_axis_group(title, y, rows):
        """rows = list of (key, label, default_axis_letter)."""
        gb = _group(title, y, len(rows))
        ry = GROUP_TOP_PAD
        for key, label, default_axis in rows:
            lbl = Label()
            lbl.Text = label
            lbl.Font = UI_FONT
            lbl.Location = DPoint(LABEL_X, ry + 4)
            lbl.Size = Size(LABEL_W, FIELD_H)
            gb.Controls.Add(lbl)
            cb = ComboBox()
            cb.Font = UI_FONT
            cb.DropDownStyle = ComboBoxStyle.DropDownList
            cb.Items.Add("X")
            cb.Items.Add("Y")
            cb.Items.Add("Z")
            cb.SelectedItem = default_axis
            cb.Location = DPoint(FIELD_X, ry)
            cb.Size = Size(FIELD_W, FIELD_H)
            gb.Controls.Add(cb)
            combos[key] = cb
            ry += ROW_H
        return y + gb.Size.Height + MARGIN

    y = MARGIN
   
    y = add_axis_group(u"Reference axis roles (X/Y/Z of the selected frame)", y, [
        ("h_axis", u"Horizontal H rotation axis", "Z"),
        ("v_axis", u"Vertical V rotation axis", "Y"),
    ])
    y = add_group(u"H Horizontal (about H axis) [deg]", y, [
        ("h_start", u"Start", -60.0),
        ("h_end",   u"End",    60.0),
        ("h_step",  u"Step",  10.0),
    ])
    y = add_group(u"V Vertical (about V axis) [deg]", y, [
        ("v_start", u"Start", -20.0),
        ("v_end",   u"End",    20.0),
        ("v_step",  u"Step",  10.0),
    ])
    y = add_group(u"Distance (from axis origin) [mm]", y, [
        ("distance", u"Distance", 500.0),
    ])

    btn_gap = 24
    total_btn_w = 2 * BTN_W + btn_gap
    btn_x0 = (FORM_W - total_btn_w) // 2

    ok_btn = Button()
    ok_btn.Text = u"OK"
    ok_btn.Font = UI_FONT
    ok_btn.DialogResult = DialogResult.OK
    ok_btn.Location = DPoint(btn_x0, y + 4)
    ok_btn.Size = Size(BTN_W, BTN_H)
    form.Controls.Add(ok_btn)

    cancel_btn = Button()
    cancel_btn.Text = u"Cancel"
    cancel_btn.Font = UI_FONT
    cancel_btn.DialogResult = DialogResult.Cancel
    cancel_btn.Location = DPoint(btn_x0 + BTN_W + btn_gap, y + 4)
    cancel_btn.Size = Size(BTN_W, BTN_H)
    form.Controls.Add(cancel_btn)

    form.ClientSize = Size(FORM_W, y + BTN_H + 2 * MARGIN)
    form.AcceptButton = ok_btn
    form.CancelButton = cancel_btn

    while True:
        dr = form.ShowDialog()
        if dr != DialogResult.OK:
            form.Dispose()
            return None
        try:
            data = {}
            for key in ("h_start", "h_end", "h_step",
                        "v_start", "v_end", "v_step", "distance"):
                data[key] = float(boxes[key].Text)
        except ValueError:
            MessageBox.Show(u"All input values must be numeric.", u"Input Error",
                            MessageBoxButtons.OK, MessageBoxIcon.Error)
            continue
        data["h_axis"] = str(combos["h_axis"].SelectedItem)
        data["v_axis"] = str(combos["v_axis"].SelectedItem)
        if data["h_axis"] == data["v_axis"]:
            MessageBox.Show(u"The horizontal H axis and vertical V axis must be different.",
                            u"Input Error", MessageBoxButtons.OK,
                            MessageBoxIcon.Error)
            continue
        if data["h_step"] <= 0 or data["v_step"] <= 0:
            MessageBox.Show(u"H / V step must be greater than 0.", u"Input Error",
                            MessageBoxButtons.OK, MessageBoxIcon.Error)
            continue
        if data["distance"] <= 0:
            MessageBox.Show(u"Distance must be greater than 0.", u"Input Error",
                            MessageBoxButtons.OK, MessageBoxIcon.Error)
            continue
        form.Dispose()
        return data


def frange_inclusive(start, end, step):
    """Inclusive float range, robust to rounding and ascending/descending."""
    if step == 0:
        return [start]
    step = abs(step)
    if end < start:
        step = -step
    n = int(round((end - start) / step))
    vals = [start + i * step for i in range(n + 1)]
    tol = abs(step) * 1e-6
    lo, hi = min(start, end), max(start, end)
    return [v for v in vals if (lo - tol) <= v <= (hi + tol)]


def _show_message(text, title, icon="info"):
    """Show a simple OK message box.  icon: 'info' | 'warning' | 'error'."""
    import clr
    clr.AddReference("System.Windows.Forms")
    from System.Windows.Forms import (MessageBox, MessageBoxButtons,
                                      MessageBoxIcon)
    icons = {
        "info": MessageBoxIcon.Information,
        "warning": MessageBoxIcon.Warning,
        "error": MessageBoxIcon.Error,
    }
    MessageBox.Show(text, title, MessageBoxButtons.OK,
                    icons.get(icon, MessageBoxIcon.Information))


def _ask_ok_cancel(text, title):
    """Show an OK/Cancel message box.  Returns True if OK was pressed."""
    import clr
    clr.AddReference("System.Windows.Forms")
    from System.Windows.Forms import (MessageBox, MessageBoxButtons,
                                      MessageBoxIcon, DialogResult)
    dr = MessageBox.Show(text, title, MessageBoxButtons.OKCancel,
                         MessageBoxIcon.Information)
    return dr == DialogResult.OK


def get_selected_axis_system():
    """Return the selected axis system (object exposing .Axes), or None."""
    sel = Selection.GetActive()
    if sel is None or sel.Count == 0:
        return None
    for item in sel.Items:
        if hasattr(item, "Axes"):
            return item
        master = getattr(item, "Master", None)
        if master is not None and hasattr(master, "Axes"):
            return master
    return None


def axis_frame_data(axis_system):
    """Return (origin_point, x_dir, y_dir, z_dir) from an axis system.
    Verified: axis.Frame.Origin and axis.Axes[i].Shape.Geometry.Direction."""
    origin = None
    fr = getattr(axis_system, "Frame", None)
    if fr is not None and hasattr(fr, "Origin"):
        origin = fr.Origin
    if origin is None:
        origin = getattr(axis_system, "Origin", None)
    if origin is None:
        origin = Point.Create(MM(0), MM(0), MM(0))

    def axis_dir(idx, fallback):
        try:
            return axis_system.Axes[idx].Shape.Geometry.Direction
        except Exception:
            try:
                fr2 = axis_system.Frame
                return [fr2.DirX, fr2.DirY, fr2.DirZ][idx]
            except Exception:
                return fallback

    x_dir = axis_dir(0, Direction.DirX)
    y_dir = axis_dir(1, Direction.DirY)
    z_dir = axis_dir(2, Direction.DirZ)
    return origin, x_dir, y_dir, z_dir


def local_to_global_point(origin, x_dir, y_dir, z_dir, lx, ly, lz):
    """Map local (lx,ly,lz) in mm within the axis frame to a global Point."""
    gx = origin.X + x_dir.X * MM(lx) + y_dir.X * MM(ly) + z_dir.X * MM(lz)
    gy = origin.Y + x_dir.Y * MM(lx) + y_dir.Y * MM(ly) + z_dir.Y * MM(lz)
    gz = origin.Z + x_dir.Z * MM(lx) + y_dir.Z * MM(ly) + z_dir.Z * MM(lz)
    return Point.Create(gx, gy, gz)

def _vdot(a, b):
    return a.X * b.X + a.Y * b.Y + a.Z * b.Z


def _vcross(a, b):
    """Cross product a x b, returned as a (normalized) Direction."""
    cx = a.Y * b.Z - a.Z * b.Y
    cy = a.Z * b.X - a.X * b.Z
    cz = a.X * b.Y - a.Y * b.X
    return Direction.Create(cx, cy, cz)


def pick_axis_dir(axis_letter, x_dir, y_dir, z_dir):
    """Return the Direction for 'X' | 'Y' | 'Z'."""
    return {"X": x_dir, "Y": y_dir, "Z": z_dir}[axis_letter]


def forward_direction(h_dir, v_dir):
    """Forward (0-deg reference) direction = V x H.
    Verified: H=Z, V=Y gives +X (the skill-file default)."""
    return _vcross(v_dir, h_dir)

# Source geometry copy
def find_source_selection(name):
    """Return a Selection for the geometry named `name`, or None."""
    sel = Selection.CreateByNames(name)
    if sel is not None and sel.Count > 0:
        return sel
    return None


def _rodrigues(v, k, ang):
    """Rotate vector tuple v=(x,y,z) about unit axis Direction k by ang (rad)."""
    c = Math.Cos(ang)
    s = Math.Sin(ang)
    kx, ky, kz = k.X, k.Y, k.Z
    kdotv = kx * v[0] + ky * v[1] + kz * v[2]
    kcross = (ky * v[2] - kz * v[1],
              kz * v[0] - kx * v[2],
              kx * v[1] - ky * v[0])
    return (v[0] * c + kcross[0] * s + kx * kdotv * (1 - c),
            v[1] * c + kcross[1] * s + ky * kdotv * (1 - c),
            v[2] * c + kcross[2] * s + kz * kdotv * (1 - c))


def copy_source_hv(source_sel, axis_origin, h_dir, v_dir, fwd_dir,
                   h_rad, v_rad, distance):
    opts_copy = MoveOptions()
    opts_copy.Copy = True
    mres = Move.Translate(source_sel, Vector.Create(MM(0), MM(0), MM(0)),
                          opts_copy, None)
    if not getattr(mres, "Success", False):
        return mres
    created = list(mres.CreatedBodies)
    if not created:
        return mres

    if abs(v_rad) > 1e-9:
        v_line = Line.Create(axis_origin, v_dir)
        Move.Rotate(Selection.CreateByObjects(created), v_line,
                    v_rad, MoveOptions(), None)
    if abs(h_rad) > 1e-9:
        h_line = Line.Create(axis_origin, h_dir)
        Move.Rotate(Selection.CreateByObjects(created), h_line,
                    h_rad, MoveOptions(), None)

    fwd = (fwd_dir.X, fwd_dir.Y, fwd_dir.Z)
    fwd = _rodrigues(fwd, v_dir, v_rad)
    fwd = _rodrigues(fwd, h_dir, h_rad)
    target_pt = Point.Create(axis_origin.X + MM(distance * fwd[0]),
                             axis_origin.Y + MM(distance * fwd[1]),
                             axis_origin.Z + MM(distance * fwd[2]))
    anchor = Move.GetAnchorPoint(Selection.CreateByObjects(created))
    move_vec = Vector.Create(target_pt.X - anchor.X,
                             target_pt.Y - anchor.Y,
                             target_pt.Z - anchor.Z)
    Move.Translate(Selection.CreateByObjects(created), move_vec,
                   MoveOptions(), None)

    return mres

# Optical properties setting
def _safe_set(obj, attr, value):
    try:
        setattr(obj, attr, value)
        return True
    except Exception:
        return False


def _safe_get(obj, attr):
    """Read a property, tolerating .NET 'not defined in current state' errors.
    Returns (ok, value).  getattr() alone is NOT enough: conditional Speos
    properties raise on access, which getattr's default does not catch."""
    try:
        return True, getattr(obj, attr)
    except Exception:
        return False, None


def _copy_attr(src, dst, attr):
    ok, val = _safe_get(src, attr)
    if ok and val is not None:
        _safe_set(dst, attr, val)


def find_body_by_name(name):
    """Return the first body named `name` in the active part, or None."""
    try:
        for b in GetRootPart().Bodies:
            try:
                if b.GetName() == name:
                    return b
            except Exception:
                pass
    except Exception:
        pass
    return None


def _face_index_in_body(body_faces, linked_face):
    """Return the index of linked_face within body_faces, or -1."""
    for i, f in enumerate(body_faces):
        try:
            if f.Equals(linked_face):
                return i
        except Exception:
            pass
    return -1

MATERIAL_NAME = "source_mat" 

def add_bodies_to_material(material, bodies):
    """Append `bodies` to the material's VolumeGeometries, keeping whatever is
    already linked.  VolumeGeometries.Set() replaces the whole list, so the
    existing linked bodies are read first and merged with the new ones.

    Returns the resulting linked-body count (or -1 on failure).
    """
    if material is None or not bodies:
        return -1
    try:
        vg = material.VolumeGeometries
    except Exception:
        return -1

    # existing linked bodies
    existing = []
    try:
        for o in vg.LinkedObjects:
            existing.append(o)
    except Exception:
        existing = []

    combined = list(existing)
    for b in bodies:
        dup = False
        for e in existing:
            try:
                if e.Equals(b):
                    dup = True
                    break
            except Exception:
                pass
        if not dup:
            combined.append(b)

    try:
        vg.Set(combined)
        return material.VolumeGeometries.Count
    except Exception:
        return -1


def get_emissive_face_map(src, source_body):
    result = []
    if source_body is None:
        return result
    try:
        body_faces = [f for f in source_body.Faces]
    except Exception:
        return result
    try:
        ef = src.EmissiveFaces
        n = ef.Count
    except Exception:
        return result
    for i in range(n):
        of = ef[i]
        # reverse flag
        ok, rev = _safe_get(of, "ReverseDirection")
        if not ok:
            rev = False

        idx = -1
        try:
            linked = of.Face.LinkedObject
            idx = _face_index_in_body(body_faces, linked)
        except Exception:
            idx = -1
        result.append((idx, rev))
    return result


def unique_source_name(base):
    if SpeosSim.SourceSurface.Find(base) is None:
        return base
    i = 1
    while SpeosSim.SourceSurface.Find("%s_%d" % (base, i)) is not None:
        i += 1
    return "%s_%d" % (base, i)


def clone_surface_source(src, copy_body, emissive_map, new_name):
    new_src = SpeosSim.SourceSurface.Create()
    new_src.Name = unique_source_name(new_name)

    copy_faces = []
    try:
        copy_faces = [f for f in copy_body.Faces]
    except Exception:
        copy_faces = []

    chosen = []
    reverse_flags = []
    for (idx, rev) in emissive_map:
        if 0 <= idx < len(copy_faces):
            chosen.append(copy_faces[idx])
            reverse_flags.append(rev)

    if chosen:
        new_src.EmissiveFaces.Set(chosen)

        for j in range(new_src.EmissiveFaces.Count):
            if j < len(reverse_flags):
                _safe_set(new_src.EmissiveFaces[j], "ReverseDirection",
                          reverse_flags[j])
    else:

        if copy_faces:
            new_src.EmissiveFaces.Set(copy_faces)

    for attr in ("SpectrumType", "FluxType", "IntensityType",
                 "IntensityOrientation"):
        _copy_attr(src, new_src, attr)

    for attr in ("SpectrumValueWavelength", "SpectrumValueTemperature",
                 "SpectrumValueLibrary"):
        _copy_attr(src, new_src, attr)

    for attr in ("FluxFromIntensityFile", "FluxValueLuminous",
                 "FluxValueRadiant", "FluxValueIntensity"):
        _copy_attr(src, new_src, attr)

    for attr in ("IntensityTotalAngle", "IntensityFWHMAngle",
                 "IntensityFWHMAngleX", "IntensityFWHMAngleY",
                 "IntensityN", "IntensityFile",
                 "IntensityDiagramSize", "IntensityDiagramFixedSize",
                 "DisplayIntensityDiagram"):
        _copy_attr(src, new_src, attr)

    for attr in ("ExitanceVariable", "ExitanceReverse",
                 "ExitanceFile", "NbRays", "RayLength", "RelativeLag"):
        _copy_attr(src, new_src, attr)

    return new_src

# Surface source copy
def all_surface_source_names():
    names = []
    try:
        for o in SpeosSim.Command.GetSpeosObjectsInActivePart():
            try:
                nm = o.GetMaster().Name
            except Exception:
                continue
            if SpeosSim.SourceSurface.Find(nm) is not None:
                names.append(nm)
    except Exception:
        pass
    return names

# MAIN

def main():
    proceed = _ask_ok_cancel(
        u"Before continuing, make sure you have selected the reference\n"
        u"axis system (coordinate system) in the SpaceClaim tree or scene.\n\n"
        u"In the next dialog you will choose which of this frame's\n"
        u"X / Y / Z axes is the Horizontal (H) and Vertical (V) rotation axis.\n"
        u"(The 0-deg reference direction is automatically V axis x H axis.)\n\n"
        u"Press [OK] if the axis is selected, or [Cancel] to abort.",
        u"Select Reference Axis")
    if not proceed:
        print("Cancelled by user at the axis-selection prompt.")
        return

    axis_system = get_selected_axis_system()
    if axis_system is None:
        _show_message(
            u"No axis system is selected.\n\n"
            u"Please select a reference axis (coordinate system) in the\n"
            u"SpaceClaim tree or scene, then run the script again.",
            u"No Axis Selected", "warning")
        print("ERROR: No axis system is selected.")
        return
    try:
        axis_name = axis_system.Name
    except Exception:
        axis_name = "<unnamed>"
    print("Reference axis system: %s" % axis_name)
    origin, x_dir, y_dir, z_dir = axis_frame_data(axis_system)

    if find_source_selection(SOURCE_GEOMETRY_NAME) is None:
        _show_message(
            u"Geometry '%s' was not found.\n\n"
            u"Create and name the geometry to copy before running."
            % SOURCE_GEOMETRY_NAME,
            u"Geometry Not Found", "error")
        print("ERROR: Geometry '%s' not found in the scene."
              % SOURCE_GEOMETRY_NAME)
        return
    src0 = SpeosSim.SourceSurface.Find(SURFACE_SOURCE_NAME)
    if src0 is None:
        _show_message(
            u"Surface source '%s' was not found.\n\n"
            u"Create and name the surface source before running."
            % SURFACE_SOURCE_NAME,
            u"Surface Source Not Found", "error")
        print("ERROR: Surface source '%s' not found." % SURFACE_SOURCE_NAME)
        return

    source_body = find_body_by_name(SOURCE_GEOMETRY_NAME)
    emissive_map = get_emissive_face_map(src0, source_body)
    print("Original emissive faces (body_index, reverse): %s" % emissive_map)
    if not emissive_map:
        print("WARNING: could not map original emissive faces; copies will fall "
              "back to using all faces (reverse-normal may not be preserved).")

    material = SpeosSim.Material.Find(MATERIAL_NAME)
    if material is None:
        print("WARNING: material '%s' not found; copied bodies will NOT be added "
              "to any material." % MATERIAL_NAME)

    params = ask_grid_parameters()
    if params is None:
        print("Cancelled by user. No copies created.")
        return

    h_dir = pick_axis_dir(params["h_axis"], x_dir, y_dir, z_dir)
    v_dir = pick_axis_dir(params["v_axis"], x_dir, y_dir, z_dir)

    ortho_dot = _vdot(h_dir, v_dir)
    if abs(ortho_dot) > 1e-6:
        import math as _m
        try:
            ang_deg = _m.degrees(_m.acos(max(-1.0, min(1.0, abs(ortho_dot)))))
        except Exception:
            ang_deg = -1.0
        proceed = _ask_ok_cancel(
            u"The selected horizontal H axis (%s) and vertical V axis (%s)\n"
            u"are not orthogonal (the angle between them is not 90 degrees).\n\n"
            u"If they are not orthogonal, the rotation result may differ from intent.\n\n"
            u"Press [OK] to continue anyway, or [Cancel] to abort."
            % (params["h_axis"], params["v_axis"]),
            u"Axes Not Orthogonal")
        if not proceed:
            print("Cancelled: chosen H/V axes are not orthogonal.")
            return

    fwd_dir = forward_direction(h_dir, v_dir)

    h_vals = frange_inclusive(params["h_start"], params["h_end"],
                              params["h_step"])
    v_vals = frange_inclusive(params["v_start"], params["v_end"],
                              params["v_step"])
    distance = params["distance"]

    print("H axis: %s   V axis: %s" % (params["h_axis"], params["v_axis"]))
    print("H values (deg): %s" % h_vals)
    print("V values (deg): %s" % v_vals)
    print("Distance (mm): %g" % distance)
    total = len(h_vals) * len(v_vals)
    print("Total copies to create: %d" % total)

    created = 0
    index = 0
    all_copied_bodies = [] 
    for h_deg in h_vals:
        for v_deg in v_vals:
            index += 1
            h_rad = h_deg * DEG2RAD
            v_rad = v_deg * DEG2RAD

            source_sel = find_source_selection(SOURCE_GEOMETRY_NAME)
            src_orig = SpeosSim.SourceSurface.Find(SURFACE_SOURCE_NAME)
            if source_sel is None or src_orig is None:
                print("  [%d] ERROR: source geometry/source lost; aborting."
                      % index)
                break

            mres = copy_source_hv(source_sel, origin, h_dir, v_dir, fwd_dir,
                                  h_rad, v_rad, distance)
            ok = getattr(mres, "Success", mres is not None)
            if not ok:
                print("  [%d] H=%g V=%g : geometry copy FAILED"
                      % (index, h_deg, v_deg))
                continue

            suffix = "H%g_V%g" % (h_deg, v_deg)
            try:
                created_bodies = list(mres.CreatedBodies)
            except Exception:
                created_bodies = []

            for i, body in enumerate(created_bodies):
                try:
                    body_name = "%s_%s" % (SOURCE_GEOMETRY_NAME, suffix)
                    if len(created_bodies) > 1:
                        body_name = "%s_%d" % (body_name, i)
                    body.SetName(body_name)
                except Exception:
                    pass

                all_copied_bodies.append(body)

            new_src_name = "%s_%s" % (SURFACE_SOURCE_NAME, suffix)
            if created_bodies:
                try:

                    clone_surface_source(src_orig, created_bodies[0],
                                         emissive_map, new_src_name)
                except Exception as e:
                    print("  [%d] WARNING: source clone failed: %s"
                          % (index, e))
            else:
                print("  [%d] WARNING: no copied body; surface source skipped."
                      % index)

            created += 1
            print("  [%d] H=%g V=%g -> copy placed" % (index, h_deg, v_deg))

    print("Done. %d / %d copies created." % (created, total))
    print("Surface sources now in scene: %d" % len(all_surface_source_names()))

    mat_result = -1
    if material is not None and all_copied_bodies:
        mat_result = add_bodies_to_material(material, all_copied_bodies)
        if mat_result >= 0:
            print("Added %d copied bodies to material '%s' (now %d volumes)."
                  % (len(all_copied_bodies), MATERIAL_NAME, mat_result))
        else:
            print("WARNING: failed to add copied bodies to material '%s'."
                  % MATERIAL_NAME)

    if material is not None:
        mat_line = (u"Material '%s' volumes : %d" % (MATERIAL_NAME, mat_result)) \
            if mat_result >= 0 else \
            (u"Material '%s' add : failed" % MATERIAL_NAME)
    else:
        mat_line = u"Material '%s' : not found (not added)" % MATERIAL_NAME

    _show_message(
        u"Operation completed.\n\n"
        u"Reference axis   : %s\n"
        u"Horizontal H axis: %s\n"
        u"Vertical V axis  : %s\n"
        u"Copies created   : %d / %d\n"
        u"Surface source   : %d\n"
        u"%s"
        % (axis_name, params["h_axis"], params["v_axis"],
           created, total, len(all_surface_source_names()), mat_line),
        u"Copy Complete", "info")

# Run
main()
