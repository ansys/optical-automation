# Copyright (C) 2020 ANSYS, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

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
        conversion_dictionary = {}
        all_body = GetRootPart().GetAllBodies()
        for body in all_body:
            sel = Selection.Create(body)
            ColorInfo = ColorHelper.GetColor(sel).ToString()
            if ColorInfo not in conversion_dictionary:
                conversion_dictionary.update({ColorInfo: List[IDesignBody]()})
            conversion_dictionary[ColorInfo].Add(body)
        return conversion_dictionary

    def create_dict_by_Material(self):
        """
        Create a dictionary for Named selection generation/stitch one element per Catia Material6
        :return: Dictionary {materialname: List of bodies with mat}
        """

        def get_real_original(item):
            result = item
            while result.GetOriginal():
                result = result.GetOriginal()
            return result
        conversion_dictionary = {}
        all_body = GetRootPart().GetAllBodies()
        for body in all_body:
            ibody = get_real_original(body)
            MaterialName = ibody.Material.Name
            if MaterialName not in conversion_dictionary:
                conversion_dictionary.update({MaterialName: List[IDesignBody]()})
            conversion_dictionary[MaterialName].Add(body)
        return conversion_dictionary

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
        :return:        return all surface bodies from input part
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
            body_name = body.GetName()
            while True:
                geo_set_name_test, content = os.path.split(body_name)
                if content:
                    if geo_set_name_test and not geometricalsets.__contains__(geo_set_name_test):
                        geometricalsets.append(geo_set_name_test)
                    body_name = geo_set_name_test
                else:
                    if geo_set_name_test:
                        if content and not geometricalsets.__contains__(content):
                            geometricalsets.append(content)
                    break
        return geometricalsets

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
        for i, sbody in enumerate(allsurface):
            body_name = sbody.GetName()
            for k, item in enumerate(geometricalsets):
                if body_name.Contains(item):
                    bodylist[k].append(i)
        return bodylist

    def __convert_list_to_dict(self, part):
        """
        Convert the lists to dictionaries
        :param body_list:  List of Body IDs
        :param part:        Spaceclaim Part to convert
        :return:
        """
        dictionary = {}
        body_list = self.__get_bodies_for_geometrical_sets(part)
        geo_list = self.__create_geometricalsetnames_list(part)
        surface_bodies = self.__get_all_surface_bodies(part)

        for i, body_ids_list in enumerate(body_list):
            for body_id in body_ids_list:
                if geo_list[i] not in dictionary:
                    dictionary[geo_list[i]] = List[IDesignBody]()
                dictionary[geo_list[i]].Add(surface_bodies[body_id])

        return dictionary

    def geosets_conversion(self, part):
        """
        Get Catia Geometrical set as Named selection
        :param part:
        :return:
        """
        dic = self.__convert_list_to_dict(part)
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

