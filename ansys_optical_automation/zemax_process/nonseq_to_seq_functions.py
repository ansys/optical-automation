import numpy as np
from numpy.linalg import inv
import math
import os
from ansys_optical_automation.zemax_process.base import BaseZOS

class OSModeConverter:
    def __init__(self, nscfilename=None, nsc_elements=None, object_materials=None, reverseflag_ob1=False):
        """
        The function is to convert systems from OpticStudio Non-sequential to Sequential.
        Rays are always traced with predefined sequence.
        Either order of rays hitting the NSC objects are provided, or rotation and position matrices are needed.
        Z orientation of each surface in sequential mode will be checked through chief ray tracing when the surface is
        added except the default global reference(surface1).
        Manually do Z reverse for the 1st object by flag argument reverseflag_ob1.
        Parameters
        ----------
        nscfilename: string
            Name of the NSC file to convert
        nsc_elements: list
            order of rays hitting the NSC objects, stored in integer list
        object_materials: list
            materials of the objects, stored in string list
        reverseflag_ob1: bool
            Z reverse flag for the 1st object, True to reverse, default as False
        """
        self.nscfilename = nscfilename
        self.nsc_elements = nsc_elements
        self.object_materials = object_materials
        self.reverseflag_ob1=reverseflag_ob1

        self.zos = BaseZOS()
        self.the_system = self.zos.the_application.PrimarySystem


    def angle2rm(self,theta_x, theta_y, theta_z, order):
        """
        function that converts rotation angles to rotation matrix
        Parameters
        ----------
        theta_x: float
            tilt X, in degree
        theta_y: float
            tilt Y, in degree
        theta_z: float
            tilt Z, in degree
        order: integer
            0 if intrinsic rotation, otherwise extrinsic

        Returns
        -------
        rotation_matrix

        """
        theta_x = theta_x * math.pi / 180
        theta_y = theta_y * math.pi / 180
        theta_z = theta_z * math.pi / 180

        rotation_matrix = np.eye(3)

        if (order == 0):
            rotation_matrix[0, 0] = math.cos(theta_y) * math.cos(theta_z)
            rotation_matrix[0, 1] = -math.cos(theta_y) * math.sin(theta_z)
            rotation_matrix[0, 2] = math.sin(theta_y);

            rotation_matrix[1, 0] = math.cos(theta_x) * math.sin(theta_z) + math.sin(theta_x) * math.sin(theta_y) * math.cos(theta_z)
            rotation_matrix[1, 1] = math.cos(theta_x) * math.cos(theta_z) - math.sin(theta_x) * math.sin(theta_y) * math.sin(theta_z)
            rotation_matrix[1, 2] = -math.sin(theta_x) * math.cos(theta_y)

            rotation_matrix[2, 0] = math.sin(theta_x) * math.sin(theta_z) - math.cos(theta_x) * math.sin(theta_y) * math.cos(theta_z)
            rotation_matrix[2, 1] = math.sin(theta_x) * math.cos(theta_z) + math.cos(theta_x) * math.sin(theta_y) * math.sin(theta_z)
            rotation_matrix[2, 2] = math.cos(theta_x) * math.cos(theta_y)

        else:

            rotation_matrix[0, 0] = math.cos(theta_y) * math.cos(theta_z)
            rotation_matrix[0, 1] = -math.sin(theta_z) * math.cos(theta_x) + math.sin(theta_x) * math.sin(theta_y) * math.cos(theta_z)
            rotation_matrix[0, 2] = math.sin(theta_x) * math.sin(theta_z) + math.cos(theta_x) * math.sin(theta_y) * math.cos(theta_z)

            rotation_matrix[1, 0] = math.cos(theta_y) * math.sin(theta_z)
            rotation_matrix[1, 1] = math.cos(theta_x) * math.cos(theta_z) + math.sin(theta_x) * math.sin(theta_y) * math.sin(theta_z)
            rotation_matrix[1, 2] = -math.cos(theta_z) * math.sin(theta_x) + math.cos(theta_x) * math.sin(theta_y) * math.sin(theta_z)

            rotation_matrix[2, 0] = -math.sin(theta_y)
            rotation_matrix[2, 1] = math.sin(theta_x) * math.cos(theta_y)
            rotation_matrix[2, 2] = math.cos(theta_x) * math.cos(theta_y)

        return rotation_matrix


    def rm2angle(self,rotation_matrix):
        """
        function that converts rotation matrix to rotation angles
        Parameters
        ----------
        rotation_matrix: list
            3X3 list array

        Returns
        -------
        tilt_x: float
            tilt X, in degree
        tilt_y: float
             tilt Y, in degree
        tilt_z: float
             tilt Z, in degree
        """
        tilt_x = math.atan2(-rotation_matrix[1, 2], rotation_matrix[2, 2]) * 180 / math.pi
        tilt_y = math.asin(rotation_matrix[0, 2]) * 180 / math.pi
        tilt_z = math.atan2(-rotation_matrix[0, 1], rotation_matrix[0, 0]) * 180 / math.pi
        return tilt_x, tilt_y, tilt_z


    def test_reverse(self,rotation_matrix, toSurf, thesystem, last_rotation_matrix, ref_rotation_matrix):
        """
        function to test whether tilt 180 degree needed, it uses chief ray tracing result in sequential system to determine
        the direction after refraction into the media following to Surf, if the surface orientation is opposite to the chief
        ray direction, then the surface tilt about local Y 180 degree
        Parameters
        ----------
        rotation_matrix: list
            rotation matrix of the surface to be added in SE system
        toSurf: integer
            the surface rays hit
        thesystem: IOpticalSystem
            the system chief ray will trace
        last_rotation_matrix: list
            3X3 rotation matrix of the last surface
        ref_rotation_matrix: list
            3X3 rotation matrix of the reference surface

        Returns
        -------
        rotation_matrix_1 : list
            3X3 reversed rotation matrix of the current surface
        """
        raytrace = thesystem.Tools.OpenBatchRayTrace();
        re = raytrace.SingleRayNormUnpol(self.zos.zosapi.Tools.RayTrace.RaysType.Real, toSurf, 1, 0.0, 0.0, 0.0, 0.0, False)
        l = re[6]
        m = re[7]
        n = re[8]
        raytrace.Close()
        vi = np.array([[l], [m], [n]])

        vi = inv(ref_rotation_matrix).dot(last_rotation_matrix).dot(vi)

        # vi=inv(ref_rotation_matrix)@last_rotation_matrix@vi
        thisn = inv(ref_rotation_matrix).dot(rotation_matrix)

        condition = vi.T[0].dot(thisn[:, 2])
        if (condition < 0):
            rotation_matrix = rotation_matrix.dot(self.angle2rm(0, 180, 0, 0))
        rotation_matrix_1 = rotation_matrix;
        return rotation_matrix_1

    def get_objects_position_info(self,nsc_elements):
        """
        Get the rotation and position matrices for a group of NSC objects relative to the NSC surface origin.
        Parameters
        ----------
        nsc_elements: list of integers
            List of NSC objects number. The default is the definition of nsc_elements

        Returns
        -------
        list_rotation_matrix,list_position
            rotation matrices list and positions list

        """
        #nsc_elements=self.nsc_elements
        sucess=self.the_system.LoadFile(self.nscfilename, False)
        print("Load NSC objects from: "+ self.the_system.SystemFile+"\n")
        list_rotation_matrix=[]
        list_position = []
        rotation_matrix = np.eye(3)
        # T=np.array([[0,0,0]]) This will cause problem, pitfall: python will treat elements of T as integer
        position = np.array([[0.0, 0.0, 0.0]])
        if nsc_elements is not None:
            for obj_num in nsc_elements:
                success, rotation_matrix[0, 0], rotation_matrix[0, 1], rotation_matrix[0, 2], rotation_matrix[1, 0], \
                rotation_matrix[1, 1], rotation_matrix[1, 2], rotation_matrix[2, 0], rotation_matrix[2, 1], rotation_matrix[2, 2], \
                position[0][0], position[0][1], position[0][2] = self.the_system.NCE.GetMatrix(obj_num)
                list_rotation_matrix.append(rotation_matrix.tolist())
                list_position.append(position.tolist())
            return list_rotation_matrix,list_position
        else:
            raise ValueError("list of NSC Objects for get_objects_position_info() is required, None detected!")



    def convert(self,list_rotation_matrix,list_position,reverseflag_ob1):
        """
        Build the sequential system according to the given rotation and position matrices, reverse the orientation
        of Z axis if necessary.
        Parameters
        ----------

        list_rotation_matrix: list of floats
            the rotation matrices for a group of NSC objects relative to the NSC surface origin.

        list_position: list of floats
            the XYZ position for a group of NSC objects relative to the NSC surface origin.
        reverseflag_ob1: bool, optional
            True if the orientation of Z axis for the first object need to be reversed, default as False.
        """

        se_sys = self.zos.the_application.CreateNewSystem(self.zos.zosapi.SystemType.Sequential)
        materials=self.object_materials
        surface_type_coordinatebreak = se_sys.LDE.GetSurfaceAt(1).GetSurfaceTypeSettings\
            (self.zos.zosapi.Editors.LDE.SurfaceType.CoordinateBreak)
        rotation_matrix=np.array(list_rotation_matrix[0])
        position=np.array(list_position[0])
        if (reverseflag_ob1):
            reversed_rotation_matrix=self.angle2rm(0, 180, 0, 0)
            rotation_matrix = rotation_matrix.dot(reversed_rotation_matrix)

        # ref_rotation_matrix= RM  pitfall: this will pass the address of RM to ref_rotation_matrix, which is not correct, for intermediate variable, use list instead
        ref_rotation_matrix = np.array(rotation_matrix.tolist())  # Elements in list cannot be changed

        multiplier = inv(ref_rotation_matrix)
        substract = np.array(position.tolist())

        for i in range(1, len(list_rotation_matrix)):

            last_rotation_matrix = np.array(rotation_matrix.tolist())
            rotation_matrix = np.array(list_rotation_matrix[i])
            position = np.array(list_position[i])

            rotation_matrix = self.test_reverse(rotation_matrix, 2 * i, se_sys, last_rotation_matrix, ref_rotation_matrix)
            rotation_matrix_wrt_last_surf = multiplier.dot(rotation_matrix)
            local_position = position.dot(multiplier) - substract.dot(multiplier)

            tilt_angle = self.rm2angle(rotation_matrix_wrt_last_surf)

            se_sys.LDE.InsertNewSurfaceAt(2 * i)
            se_sys.LDE.InsertNewSurfaceAt(2 * i + 1)
            se_sys.LDE.GetSurfaceAt(2 * i - 1).Thickness = local_position[0][2]
            se_sys.LDE.GetSurfaceAt(2 * i).ChangeType(surface_type_coordinatebreak)
            se_sys.LDE.GetSurfaceAt(2 * i).GetCellAt(12).DoubleValue = local_position[0][0]  # DecenterX
            se_sys.LDE.GetSurfaceAt(2 * i).GetCellAt(13).DoubleValue = local_position[0][1]  # DecenterY
            se_sys.LDE.GetSurfaceAt(2 * i).GetCellAt(14).DoubleValue = tilt_angle[0]  # TiltX
            se_sys.LDE.GetSurfaceAt(2 * i).GetCellAt(15).DoubleValue = tilt_angle[1]  # TiltY
            se_sys.LDE.GetSurfaceAt(2 * i).GetCellAt(16).DoubleValue = tilt_angle[2]  # TiltZ
            se_sys.LDE.GetSurfaceAt(2 * i + 1).Material = materials[i]

            multiplier = np.array(inv(rotation_matrix).tolist())
            substract = np.array(position.tolist())

        directory = os.path.dirname(self.the_system.SystemFile)
        se_sys.SaveAs(directory + '\\NSCtoSE3py.zmx')
        print("Conversion completed ! ")