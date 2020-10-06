# Copyright (C) 2019 ANSYS, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

import sys
import os
lib_path = os.path.abspath(os.path.join('../../SPEOS_scripts/ASP_start_Library'))
sys.path.append(lib_path)
print sys.path
from ASPcontrol import SCDMcontrol

class Preprocessing_asp(object):
    """
    This class contains all the methods to Pre-process Ansys SPEOS Geometries
    As per Api limitation only one session at the time can be attached.
    For this reason the class does not support multiple Ansys SPEOS  sessions.
    """

    def create_dict_by_Color(self):
        Dic = {}
        all_body = GetRootPart().GetAllBodies()
        for body in all_body:
            sel = Selection.Create(body)
            ColorInfo = ColorHelper.GetColor(sel).ToString()
            if ColorInfo not in Dic:
                Dic.update({ColorInfo: List[IDesignBody]()})
            Dic[ColorInfo].Add(body)

    def create_dict_by_Material(self):
        def GetRealOrigianl(item):
            result = item
            while result.GetOriginal():
                result = result.GetOriginal()
            return result

        Dic = {}
        all_body = GetRootPart().GetAllBodies()
        for body in all_body:
            ibody = GetRealOrigianl(body)
            MaterialName = ibody.Material.Name
            if MaterialName not in Dic:
                Dic.update({MaterialName: List[IDesignBody]()})
            Dic[MaterialName].Add(body)

    def stitch(self, Dic):
        for item in Dic:
            sel = Selection.Create(Dic[item])
            result = StitchFaces.FixSpecific(sel)
        return self


    def check_geometry_update(self):
        return self
    def check_volume_conflict(self):
        return self

    def resolve_volume_conflict(self):
        return self

    def create_named_selection(self, Dic):
        for item in Dic:
            sel = Selection.Create(Dic[item])
            second = Selection.Empty()
            Result = NamedSelection.Create(sel, second).CreatedNamedSelection
            Result.SetName(item)
        return self


# sc = Preprocessing_asp(graphical_mode=True)
# sc.open_spaceclaim_session()
# sc.create_dict_by_Material()
# sc.close_spaceclaim_session()