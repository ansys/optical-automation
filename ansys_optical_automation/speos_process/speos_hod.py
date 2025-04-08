import math
import os

from ansys_optical_automation.scdm_core.base import BaseSCDM


class HOD(BaseSCDM):
    """this class is used to interact with hud optical design systems of Speos"""

    def __init__(self, name, SpeosDes, SpaceClaim):
        super(HOD, self).__init__(SpaceClaim, ["V23", "V231", "V232", "V241", "V242", "V251"])
        self.name = name
        self.speos_sim = SpeosDes
        self.speos_object = self.speos_sim.HUDOD.Find(name)
        if not self.speos_object:  # ifHUD doesn't exist -> create a new camera
            speos_object = self.speos_sim.HUDOD.Create()
            speos_object.Name = name
            self.computed = False
        self.computed = self.speos_object.IsUpToDate
        self.Errors = self.speos_object.StatusInfo

    def __update_errors(self, log=False):
        """
        Parameters
        ----------
        log

        Returns
        -------


        """
        self.Errors = self.speos_object.StatusInfo
        if log and len(self.Errors) > 0:
            print(self.speos_object.StatusInfo)
            return False
        elif log:
            print("no errors")
            return True

    def get_freeform_body_selection(self):
        """
        Returns
        -------


        """
        return self.BodySelection.CreateByNames("[" + self.name + "]_Freeform")

    def get_fold_mirror_body_selection(self):
        """
        Returns
        -------


        """
        return self.BodySelection.CreateByNames("[" + self.name + "]_Fold")

    def get_pgu_body_selection(self):
        """
        Returns
        -------


        """
        return self.BodySelection.CreateByNames("[" + self.name + "]_PGU")

    def get_optical_axis_selection(self):
        """
        Returns
        -------


        """
        return_selection = (
            self.Selection.CreateByNames("[" + self.name + "]_Optical Axis_0")
            + self.Selection.CreateByNames("[" + self.name + "]_Optical Axis_1")
            + self.Selection.CreateByNames("[" + self.name + "]_Optical Axis_2")
            + self.Selection.CreateByNames("[" + self.name + "]_Optical Axis_3")
        )

        return return_selection

    def export_to_zemax(self, output_dir, log=False):
        """
        Parameters
        ----------
        output_dir
        log

        """

        def length_squared(u):
            return sum([a**2 for a in u])

        def length(u):
            return math.sqrt(length_squared(u))

        def add(u, v):
            return [a + b for a, b in zip(u, v)]

        if self.__update_errors():
            print("object in error")
            return False
        lines = [
            str(self.speos_object.EyeboxOrientationType),
            str(self.speos_object.EBHorizontalSize),
            str(self.speos_object.EBHorizontalSampling),
            str(self.speos_object.EBVerticalSize),
            str(self.speos_object.EBVerticalSampling),
            str(self.speos_object.EyeboxConfigPositionDirectionType),
            str(self.speos_object.TIVirtualImageDistance),
            str(self.speos_object.TILookOverAngle),
            str(self.speos_object.TILookDownAngle),
            str(self.speos_object.TargetImageModeType),
            str(self.speos_object.TIHorizontalFOV),
            str(self.speos_object.TIVerticalFOV),
            str(self.speos_object.PGUHorizontalSampling),
            str(self.speos_object.PGUVerticalSampling),
            str(self.speos_object.PGUHorizontalSize),
            str(self.speos_object.PGUVerticalSize),
            str(self.speos_object.PGUHorizontalResolution),
            str(self.speos_object.PGUVerticalResolution),
            str(self.speos_object.ManufacturingX),
            str(self.speos_object.ManufacturingY),
        ]
        surface_bodies = (
            self.get_freeform_body_selection() + self.get_fold_mirror_body_selection() + self.get_pgu_body_selection()
        ).Items
        poly_lines = self.get_optical_axis_selection().Items
        edgesprev = self.Selection.CreateByObjects(surface_bodies).ConvertToEdges()
        curvesprev = self.Selection.CreateByObjects(poly_lines).ConvertToCurves()
        edges = self.Selection.CreateByObjects(surface_bodies).ConvertToEdges()
        curves = self.Selection.CreateByObjects(poly_lines).ConvertToCurves()
        if log:
            print(surface_bodies)
            print(poly_lines)
            print(edgesprev)
            print(curvesprev)
            print(edges)
            print(curves)
            print(len(curves.Items))
        n = 0
        # o = 0

        # Create New Part
        self.ComponentHelper.SetRootActive(None)
        selection = self.PartSelection.Create(self.GetRootPart())
        self.ComponentHelper.CreateNewComponent(selection, None)

        # Select 3 PTS for 1 Face#
        ext_pts_st = []
        ext_pts_end = []
        number_exp_pt = 0
        for i in edges:
            if log:
                print(str(i.StartPoint.Position))
                print(str(i.EndPoint.Position))
            ext_pts_st.append(i.StartPoint.Position)
            ext_pts_end.append(i.EndPoint.Position)
            number_exp_pt += 1

        face_count = 0
        total_find_count = 0
        ext_pts3for1 = []
        while face_count < 3:
            point_count = 0
            find_count = 0
            while point_count <= 3:
                numbering_ext_pt = point_count + face_count * 4
                if point_count == 0:
                    ext_pts3for1.append(ext_pts_st[numbering_ext_pt])
                    find_count += 1
                    total_find_count += 1
                    point_count += 1
                if ext_pts3for1[total_find_count - 1] == ext_pts_st[numbering_ext_pt + 1]:
                    ext_pts3for1.append(ext_pts_end[numbering_ext_pt + 1])
                    find_count += 1
                    total_find_count += 1
                    point_count += 1
                elif ext_pts3for1[total_find_count - 1] == ext_pts_end[numbering_ext_pt + 1]:
                    ext_pts3for1.append(ext_pts_st[numbering_ext_pt + 1])
                    find_count += 1
                    total_find_count += 1
                    point_count += 1
                if (
                    ext_pts3for1[total_find_count - 1] != ext_pts_end[numbering_ext_pt + 1]
                    and ext_pts3for1[total_find_count - 1] != ext_pts_st[numbering_ext_pt + 1]
                ):
                    if find_count < 3:
                        ext_pts3for1.append(ext_pts_st[numbering_ext_pt + 1])
                        find_count += 1
                        total_find_count += 1
                    if find_count < 3:
                        ext_pts3for1.append(ext_pts_end[numbering_ext_pt + 1])
                        find_count += 1
                        total_find_count += 1
                    point_count += 1
                if find_count >= 3:
                    break
            face_count += 1

        # Select 2 PTS(for H) for 1 Face#
        length_check = 0
        h_points = []
        while length_check < 3:
            length_index = length_check * 3
            length01 = length(ext_pts3for1[length_index] - ext_pts3for1[length_index + 1])
            length12 = length(ext_pts3for1[length_index + 1] - ext_pts3for1[length_index + 2])
            length20 = length(ext_pts3for1[length_index + 2] - ext_pts3for1[length_index])
            length_set = [length01, length12, length20]
            length_set_sort = sorted(length_set)
            if length_set_sort[1] == length01:
                if (ext_pts3for1[length_index])[1] < (ext_pts3for1[length_index + 1])[1]:
                    h_points.append(ext_pts3for1[length_index])
                    h_points.append(ext_pts3for1[length_index + 1])
                else:
                    h_points.append(ext_pts3for1[length_index + 1])
                    h_points.append(ext_pts3for1[length_index])
            elif length_set_sort[1] == length12:
                if (ext_pts3for1[length_index + 1])[1] < (ext_pts3for1[length_index + 2])[1]:
                    h_points.append(ext_pts3for1[length_index + 1])
                    h_points.append(ext_pts3for1[length_index + 2])
                else:
                    h_points.append(ext_pts3for1[length_index + 2])
                    h_points.append(ext_pts3for1[length_index + 1])
            elif length_set_sort[1] == length20:
                if (ext_pts3for1[length_index + 2])[1] < (ext_pts3for1[length_index])[1]:
                    h_points.append(ext_pts3for1[length_index + 2])
                    h_points.append(ext_pts3for1[length_index])
                else:
                    h_points.append(ext_pts3for1[length_index])
                    h_points.append(ext_pts3for1[length_index + 2])
            length_check += 1

        # Get Normals from Surfaces (will be used Only for PGU)
        nvs = []
        if (self.Vector.Cross(ext_pts3for1[1] - ext_pts3for1[0], ext_pts3for1[2] - ext_pts3for1[0]))[0] >= 0:
            nvs.append(self.Vector.Cross(ext_pts3for1[1] - ext_pts3for1[0], ext_pts3for1[2] - ext_pts3for1[0]))
        else:
            nvs.append(-self.Vector.Cross(ext_pts3for1[1] - ext_pts3for1[0], ext_pts3for1[2] - ext_pts3for1[0]))
        if (self.Vector.Cross(ext_pts3for1[4] - ext_pts3for1[3], ext_pts3for1[5] - ext_pts3for1[3]))[0] < 0:
            nvs.append(self.Vector.Cross(ext_pts3for1[4] - ext_pts3for1[3], ext_pts3for1[5] - ext_pts3for1[3]))
        else:
            nvs.append(-self.Vector.Cross(ext_pts3for1[4] - ext_pts3for1[3], ext_pts3for1[5] - ext_pts3for1[3]))
        if self.Vector.Cross(ext_pts3for1[7] - ext_pts3for1[6], ext_pts3for1[8] - ext_pts3for1[6])[0] >= 0:
            nvs.append(self.Vector.Cross(ext_pts3for1[7] - ext_pts3for1[6], ext_pts3for1[8] - ext_pts3for1[6]))
        else:
            nvs.append(-self.Vector.Cross(ext_pts3for1[7] - ext_pts3for1[6], ext_pts3for1[8] - ext_pts3for1[6]))

        # Get Normals from polyline wirh PGU from the Surface
        c_line_count = 0
        ptsfrom_poly = []
        for i in curves:
            ptsfrom_poly.append(i.EndPoint.Position)
            c_line_count += 1
        n_poly01 = (ptsfrom_poly[0] - ptsfrom_poly[1]) / length(ptsfrom_poly[0] - ptsfrom_poly[1])
        n_poly12 = (ptsfrom_poly[1] - ptsfrom_poly[2]) / length(ptsfrom_poly[1] - ptsfrom_poly[2])
        n_poly23 = (ptsfrom_poly[2] - ptsfrom_poly[3]) / length(ptsfrom_poly[2] - ptsfrom_poly[3])
        nvp1 = add(n_poly01, -n_poly12)
        nvp2 = add(n_poly12, -n_poly23)
        nvp1length = math.sqrt(nvp1[0] * nvp1[0] + nvp1[1] * nvp1[1] + nvp1[2] * nvp1[2])
        nvp2length = math.sqrt(nvp2[0] * nvp2[0] + nvp2[1] * nvp2[1] + nvp2[2] * nvp2[2])
        nvs2length = math.sqrt((nvs[2])[0] * (nvs[2])[0] + (nvs[2])[1] * (nvs[2])[1] + (nvs[2])[2] * (nvs[2])[2])
        nvp = [
            self.Vector.Create(nvp1[0] / nvp1length, nvp1[1] / nvp1length, nvp1[2] / nvp1length),
            self.Vector.Create(nvp2[0] / nvp2length, nvp2[1] / nvp2length, nvp2[2] / nvp2length),
            nvs[2] / nvs2length,
        ]

        # Center Point of Surfaces
        np_center = [ptsfrom_poly[1], ptsfrom_poly[2], ptsfrom_poly[3]]

        # HorV-Rotated
        hvr = [
            self.Vector.Create(
                (h_points[1])[0] - (h_points[0])[0],
                (h_points[1])[1] - (h_points[0])[1],
                (h_points[1])[2] - (h_points[0])[2],
            ),
            self.Vector.Create(
                (h_points[2])[0] - (h_points[3])[0],
                (h_points[2])[1] - (h_points[3])[1],
                (h_points[2])[2] - (h_points[3])[2],
            ),
            self.Vector.Create(
                (h_points[5])[0] - (h_points[4])[0],
                (h_points[5])[1] - (h_points[4])[1],
                (h_points[5])[2] - (h_points[4])[2],
            ),
        ]

        # For Freefrom M Hor
        hv = []
        x1 = (h_points[0])[0]
        y1 = (h_points[0])[1]
        z1 = (h_points[0])[2]
        aa = (nvp[0])[1] / (nvp[0])[0]
        bb = (np_center[0])[1] - aa * (np_center[0])[0]
        axa = aa * aa
        nn = 1 / (axa + 1)
        mm = 1 - axa
        x2 = nn * ((mm * x1) + (2 * aa * y1) - (2 * aa * bb))
        y2 = nn * ((2 * aa * x1) - (mm * y1) + (2 * bb))
        hv.append(self.Vector.Create(x2 - x1, y2 - y1, 0))
        point_o = self.Point.Create(self.M(x1), self.M(y1), self.M(z1))
        point_ori = self.Point.Create(self.M(x2), self.M(y2), self.M(z1))
        result = self.DesignCurve.Create(self.GetActivePart(), self.CurveSegment.Create(point_o, point_ori), True)
        if log:
            print(result)
        # For Fold M Hor
        x1 = (h_points[3])[0]
        y1 = (h_points[3])[1]
        z1 = (h_points[3])[2]
        aa = (nvp[1])[1] / (nvp[1])[0]
        bb = (np_center[1])[1] - aa * (np_center[1])[0]
        axa = aa * aa
        nn = 1 / (axa + 1)
        mm = 1 - axa
        x2 = nn * ((mm * x1) + (2 * aa * y1) - (2 * aa * bb))
        y2 = nn * ((2 * aa * x1) - (mm * y1) + (2 * bb))
        hv.append(self.Vector.Create(x2 - x1, y2 - y1, 0))
        point_o = self.Point.Create(self.M(x1), self.M(y1), self.M(z1))
        point_ori = self.Point.Create(self.M(x2), self.M(y2), self.M(z1))
        result = self.DesignCurve.Create(self.GetActivePart(), self.CurveSegment.Create(point_o, point_ori), True)
        if log:
            print(result)
        # ForPGU Hor
        x1 = (h_points[4])[0]
        y1 = (h_points[4])[1]
        z1 = (h_points[4])[2]
        aa = (nvp[2])[1] / (nvp[2])[0]
        bb = (np_center[2])[1] - aa * (np_center[2])[0]
        axa = aa * aa
        nn = 1 / (axa + 1)
        mm = 1 - axa
        x2 = nn * ((mm * x1) + (2 * aa * y1) - (2 * aa * bb))
        y2 = nn * ((2 * aa * x1) - (mm * y1) + (2 * bb))
        hv.append(self.Vector.Create(x2 - x1, y2 - y1, 0))
        point_o = self.Point.Create(self.M(x1), self.M(y1), self.M(z1))
        point_ori = self.Point.Create(self.M(x2), self.M(y2), self.M(z1))
        result = self.DesignCurve.Create(self.GetActivePart(), self.CurveSegment.Create(point_o, point_ori), True)
        if log:
            print(result)
        # Draw Normal Direction from Polyline
        draw_count = 0
        while draw_count < 3:
            point_start = np_center[draw_count]
            point_ctr_x = point_start[0]
            point_ctr_y = point_start[1]
            point_ctr_z = point_start[2]
            point_end = nvp[draw_count]
            point_end_x = 0.1 * point_end[0] + point_ctr_x
            point_end_y = 0.1 * point_end[1] + point_ctr_y
            point_end_z = 0.1 * point_end[2] + point_ctr_z
            point_start_scdm = self.Point.Create(self.M(point_ctr_x), self.M(point_ctr_y), self.M(point_ctr_z))
            point_end_scdm = self.Point.Create(self.M(point_end_x), self.M(point_end_y), self.M(point_end_z))
            result = self.DesignCurve.Create(
                self.GetActivePart(), self.CurveSegment.Create(point_start_scdm, point_end_scdm), True
            )
            if log:
                print(result)
            draw_count += 1

        # Cal/Print Angles
        disp_count = 0
        theta = [0, 0, 0]
        phi = [0, 0, 0]
        rotate = [0, 0, 0]
        while disp_count < 3:
            x = (nvp[disp_count])[0]
            y = (nvp[disp_count])[1]
            z = (nvp[disp_count])[2]
            r = math.sqrt(x * x + y * y + z * z)
            theta[disp_count] = math.atan2(y, x) * 180 / math.pi  # to degrees
            phi[disp_count] = math.acos(z / r) * 180 / math.pi - 90
            if log:
                print("with Z: ", theta[disp_count])
                print("with Y': ", phi[disp_count])
            hv_length = math.sqrt(
                (hv[disp_count])[0] * (hv[disp_count])[0]
                + (hv[disp_count])[1] * (hv[disp_count])[1]
                + (hv[disp_count])[2] * (hv[disp_count])[2]
            )
            hvr_length = math.sqrt(
                (hvr[disp_count])[0] * (hvr[disp_count])[0]
                + (hvr[disp_count])[1] * (hvr[disp_count])[1]
                + (hvr[disp_count])[2] * (hvr[disp_count])[2]
            )
            if (hvr[disp_count])[2] >= (hv[disp_count])[2]:
                rotate[disp_count] = (
                    math.acos(self.Vector.Dot(hv[disp_count], hvr[disp_count]) / (hv_length * hvr_length))
                    * 180
                    / math.pi
                )
            else:
                rotate[disp_count] = (
                    -math.acos(self.Vector.Dot(hv[disp_count], hvr[disp_count]) / (hv_length * hvr_length))
                    * 180
                    / math.pi
                )
            if log:
                print("with X'': ", rotate[disp_count])
            disp_count += 1

        # Display Axis (ONLY WORKS IF THERE IS NO AXIS)

        origin = self.Point.Create(self.M((np_center[0])[0]), self.M((np_center[0])[1]), self.M((np_center[0])[2]))
        x_direction = self.Direction.Create((nvp[0])[0], (nvp[0])[1], (nvp[0])[2])
        y_direction = self.Direction.Create((hv[0])[0], (hv[0])[1], (hv[0])[2])
        result = self.DatumOriginCreator.Create(origin, x_direction, y_direction)
        if log:
            print(result)
        selection = self.Selection.Create(self.GetActivePart().CoordinateSystems[0])
        axis = self.Move.GetAxis(selection, self.HandleAxis.X)
        options = self.MoveOptions()
        result = self.Move.Rotate(selection, axis, self.DEG(rotate[0]), options)
        if log:
            print(result)
        # Display Axis (ONLY WORKS IF THERE IS NO AXIS)
        origin = self.Point.Create(self.M((np_center[1])[0]), self.M((np_center[1])[1]), self.M((np_center[1])[2]))
        x_direction = self.Direction.Create((nvp[1])[0], (nvp[1])[1], (nvp[1])[2])
        y_direction = self.Direction.Create((hv[1])[0], (hv[1])[1], (hv[1])[2])
        result = self.DatumOriginCreator.Create(origin, x_direction, y_direction)
        if log:
            print(result)
        selection = self.Selection.Create(self.GetActivePart().CoordinateSystems[1])
        axis = self.Move.GetAxis(selection, self.HandleAxis.X)
        options = self.MoveOptions()
        result = self.Move.Rotate(selection, axis, self.DEG(rotate[1]), options)
        if log:
            print(result)
        # Display Axis (ONLY WORKS IF THERE IS NO AXIS)
        origin = self.Point.Create(self.M((np_center[2])[0]), self.M((np_center[2])[1]), self.M((np_center[2])[2]))
        x_direction = self.Direction.Create((nvp[2])[0], (nvp[2])[1], (nvp[2])[2])
        y_direction = self.Direction.Create((hv[2])[0], (hv[2])[1], (hv[2])[2])
        result = self.DatumOriginCreator.Create(origin, x_direction, y_direction)
        if log:
            print(result)
        selection = self.Selection.Create(self.GetActivePart().CoordinateSystems[2])
        axis = self.Move.GetAxis(selection, self.HandleAxis.X)
        options = self.MoveOptions()
        result = self.Move.Rotate(selection, axis, self.DEG(rotate[2]), options)
        # disp_count = 1
        # while disp_count < 3:
        #    origin=Point.Create(M((np_center[disp_count])[0]),M((np_center[disp_count])[1]),M((np_center[disp_count])[2]))
        #    x_Direction = Direction.Create((nvp[disp_count])[0],(nvp[disp_count])[1],(nvp[disp_count])[2])
        #    y_Direction = Direction.Create((hvr[disp_count])[0],(hvr[disp_count])[1],(hvr[disp_count])[2])
        #    result = DatumOriginCreator.Create(origin, x_Direction, y_Direction, Info1)
        #    disp_count += 1
        if log:
            print(result)
        with open(os.path.join(output_dir, "HUD_SpeosToZemax.txt"), "w") as f:
            f.writelines("\n".join(lines))
            f.write("\n")
            for index in range(0, 3):
                temp_list = self.speos_object.Projectors
                row_item = temp_list[index]
                projectors = [str(row_item.Distance), str(row_item.HorizontalAngle), str(row_item.VerticalAngle)]
                f.writelines("\n".join(projectors))
                f.writelines("\n")
                index += 1
            f.write("#Surface dimensions start from freeform and go to PGU. There are 4 edge dimensions per surface")
            for i in edgesprev:
                f.write("\n")
                f.write(str(i.Length))
            f.write("\n")
            f.write(
                "#Point coordinates start from Eyepoint and go to PGU. These are vertices of 4 polylines,"
                "so there are 8 vertices, 4 are duplicates"
            )
            for i in curvesprev:
                f.write("\n")
                n += 1
                f.write(str(n) + " ")
                f.write(str(i.StartPoint.Position))
                f.write("\n")
                f.write(str(n) + " ")
                f.write(str(i.EndPoint.Position))
            f.write("\n")
            f.write("#Rotation Angles(deg) for Z, Y', X'' (for 1st, 2nd and 3rd Surfaces)")
            for index in range(0, 3):
                f.writelines("\nZ  : ")
                f.writelines(str(theta[index]))
                f.writelines("\nY' : ")
                f.writelines(str(phi[index]))
                f.writelines("\nX'': ")
                f.writelines(str(rotate[index]))
                index += 1

        # Activate ROOT
        result = self.ComponentHelper.SetRootActive(None)
        if log:
            print(result)

    def export_ws(self, output_dir, file_type="stp"):
        windshieldGeometry = self.speos_object.WindshieldInnerSurface.LinkedObject
        windshieldGeometry = self.convert_object_version(windshieldGeometry)
        windshieldGeometry = self.Selection.Create(windshieldGeometry)
        # Create new design
        self.CreateNewDocument()
        self.Copy.Execute(windshieldGeometry)
        # Save as
        step_file_path = os.path.join(output_dir, self.speos_object.Name + ".windshield.export.stp")
        options = self.ExportOptions.Create()
        self.DocumentSave.Execute(step_file_path, options)
        self.CloseDocument()
        return step_file_path
