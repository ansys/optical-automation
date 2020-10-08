import sys
import os


class Preprocessing_asp(object):
    """
    This class contains all the methods to Pre-process Ansys SPEOS Geometries
    As per Api limitation only one session at the time can be attached.
    For this reason the class does not support multiple Ansys SPEOS  sessions.
    """

    def create_dict_by_Color(self):
        """
        Create a dictionary for Named selection generation/stitch one element per color
        :return: Dictionary {color code: List of bodies with color}
        """
        Dic = {}
        all_body = GetRootPart().GetAllBodies()
        for body in all_body:
            sel = Selection.Create(body)
            ColorInfo = ColorHelper.GetColor(sel).ToString()
            if ColorInfo not in Dic:
                Dic.update({ColorInfo: List[IDesignBody]()})
            Dic[ColorInfo].Add(body)
        return Dic

    def create_dict_by_Material(self):
        """
        Create a dictionary for Named selection generation/stitch one element per Catia Material6
        :return: Dictionary {materialname: List of bodies with mat}
        """

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
        return Dic

    def stitch(self, Dic):
        """
        stitch all elemnt per dictionary items-> color/material
        """
        for item in Dic:
            sel = Selection.Create(Dic[item])
            result = StitchFaces.FixSpecific(sel)

    def check_geometry_update(self):
        """
        Verify weather any part was imported by geometry update
        """
        return self

    def check_volume_conflict(self):
        """
        find volume conflict, return two list of conflicting bodies?
        """
        return self

    def resolve_volume_conflict(self):
        """
        resolve volume Conflict based on material definition
        """
        return self

    def __get_all_surface_bodies(self, part):
        """
        Function to seperate solids from surface bodies for Geometrical set named selection conversion
        :param part:    input Spaceclaim Part
        :return:        return all surface bdoies from input part
        """
        allbodies = part.GetAllBodies()
        allsurface = part.GetAllBodies()
        allsurface.Clear()
        for body in allbodies:
            if body.GetMidSurfaceAspect() != None:
                allsurface.Add(body)
        return (allsurface)

    def __create_geometricalsetnames_list(self, part):
        """
        generate List of geometric sets from geometry names
        :param part:    Spaceclaim Part to get Geometric set names from
        :return:        List of geometrical sets names
        """

        allbodies = self.__get_all_surface_bodies(part)
        t = 0
        geometricalsets = []
        for body in allbodies:
            str_test = body.GetName()
            test = True
            while test:
                geo_set_name_test, content = path.split(str_test)
                if content != "":
                    if True != geometricalsets.__contains__(geo_set_name_test) and geo_set_name_test != "":
                        geometricalsets.append(geo_set_name_test)
                    str_test = geo_set_name_test
                else:
                    if geo_set_name_test != "":
                        if True != geometricalsets.__contains__(content) and content != "":
                            geometricalsets.append(content)
                    test = False
        return (geometricalsets)

    def __get_bodies_for_geometrical_sets(self, part):
        """
        get bodies for each geometrical set
        :param part:    Spaceclaim Part to get Geometric set from
        :return:        List of body IDs in order of geo set names
        """
        bodylist = []
        geometricalsets = self.__create_geometricalsetnames_list(part)
        allsurface = self.__get_all_surface_bodies(part)
        for item in geometricalsets:
            bodylist.append([])
        t = 0
        for sbody in allsurface:
            k = 0
            for item in geometricalsets:
                testlist = bodylist[k]
                str_test = sbody.GetName()
                if str_test.Contains(item):
                    testlist.append(t)
                    bodylist[k] = testlist
                k = k + 1
            t = t + 1
        return (bodylist)

    def __convert_list_to_dict(self, input_list, part):
        """
        Convert the lists to dictionaries
        :param input_list:  List of Body IDs
        :param part:        Spaceclaim Part to convert
        :return:
        """
        dictionary = {}
        geo_list = self.__create_geometricalsetnames_list(part)
        surfacebodies = self.__get_all_surface_bodies(part)
        i = 0
        for item in input_list:
            test = item
            for c in test:
                if geo_list[i] not in dictionary:
                    dictionary.update({geo_list[i]: List[IDesignBody]()})
                dictionary[geo_list[i]].Add(surfacebodies[c])
            i = i + 1
        return dictionary

    def geosets_conversion(self, part):
        """
        Get Catia Geometrical set as Named selection
        :param part:
        :return:
        """
        bodylist = self.__get_bodies_for_geometrical_sets(part)
        dic = self.__convert_list_to_dict(bodylist, part)
        self.create_named_selection(dic)

    @staticmethod
    def create_named_selection(Dic):
        """
        Create a Named selection from dictionary
        :param Dic:  Dictionary{Name of Named selection: LIst of bodies}
        """
        for item in Dic:
            sel = Selection.Create(Dic[item])
            if sel != Selection.Empty():
                second = Selection.Empty()
                Result = NamedSelection.Create(sel, second).CreatedNamedSelection
                Result.SetName(item.strip())

