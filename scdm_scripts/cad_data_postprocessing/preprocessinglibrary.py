# Copyright (C) 2020 ANSYS, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

import os


class PreProcessingASP(object):
    """
    This class contains all the methods to Pre-process Ansys SPEOS Geometries
    As per Api limitation only one session at the time can be attached.
    For this reason the class does not support multiple Ansys SPEOS  sessions.
    """

    @staticmethod
    def create_dict_by_color():
        """
        Create a dictionary for Named selection generation/stitch one element per color
        :return: Dictionary {color code: List of bodies with color}
        """
        conversion_dict = {}
        all_body = GetRootPart().GetAllBodies()
        for body in all_body:
            sel = Selection.Create(body)
            color_info = ColorHelper.GetColor(sel).ToString()
            if color_info not in conversion_dict:
                conversion_dict[color_info] = List[IDesignBody]()
            conversion_dict[color_info].Add(body)
        return conversion_dict

    @staticmethod
    def create_dict_by_material():
        """
        Create a dictionary for Named selection generation/stitch one element per Catia Material6
        return: Dictionary {material name: List of bodies with mat}
        """

        def get_real_original(item):
            """
            get the original body info
            Args:
                item: SpaceClaim body item

            Returns: the original SpaceClaim body item

            """
            result = item
            while result.GetOriginal():
                result = result.GetOriginal()
            return result

        conversion_dict = {}
        all_body = GetRootPart().GetAllBodies()
        for body in all_body:
            ibody = get_real_original(body)
            material_name = ibody.Material.Name
            if material_name not in conversion_dict:
                conversion_dict[material_name] = List[IDesignBody]()
            conversion_dict[material_name].Add(body)
        return conversion_dict

    @staticmethod
    def __stitch_group(comp, index, group_size):
        """
        split all bodies in component into groups of group_size.
        Example:
            In-> [body1, body2] [body3, body4], [body5, body6], [body7, body8], [body9]
            Out-> return [body3, body4]
        Args:
            comp:  given component
            index: index of the group to return
            group_size: the size of group

        Returns: list of bodies defined by index

        """

        stitch_group = List[IDesignBody]()
        for i, body in enumerate(comp.GetBodies()):
            if index * group_size <= i < (index + 1) * group_size:
                stitch_group.Add(body)
        return stitch_group

    def __stitch_group_list(self, comp, total_iter, group_size):
        """
        return a list group
        para comp: given component
        para total_iter: total number of group generated from the component
        para batch: size of each group
        e.g. body1 body2 body3 body4 body5 body6 body7 body8 body9
        return [[body1, body2] [body3, body4], [body5, body6], [body7, body8], [body9]]
        """
        stitch_group_list = []
        for i in range(total_iter):
            group = self.__stitch_group(comp, i, group_size)
            print len(group)
            stitch_group_list.append(group)
        return stitch_group_list

    def stitch_comp(self, comp):
        """
        apply stitch according to component structure
        para comp: given component
        """
        print "processing ", comp.GetName()
        num_bodies = len(comp.GetBodies())
        max_group_limit = 200
        while True:
            total_iter = int(num_bodies / max_group_limit) + 1
            stitch_group_list = self.__stitch_group_list(comp, total_iter, max_group_limit)
            for group in stitch_group_list:
                print "1st working on one group"
                sel = Selection.Create(group)
                result = StitchFaces.FindAndFix(sel)
            num_bodies_after_stitch = len(comp.GetBodies())
            print "Start with ", num_bodies, " and end with ", num_bodies_after_stitch
            print "continue"
            if num_bodies_after_stitch == num_bodies:
                break
        print "next component"

    @staticmethod
    def stitch(conversion_dict):
        """
        stitch all element per dictionary items-> color/material
        """
        for item in conversion_dict:
            sel = Selection.Create(conversion_dict[item])
            result = StitchFaces.FixSpecific(sel)

    @staticmethod
    def remove_duplicates(comp):
        """
        Remove duplicated surfaces
        param part: input SpaceClaim part
        :return:
        """
        print "processing ", comp.GetName()
        while True:
            sel = Selection.Create(comp.GetBodies())
            num_bodies = len(comp.GetBodies())
            result = FixDuplicateFaces.FindAndFix(sel)
            num_bodies_after_duplicates = len(comp.GetBodies())
            print "start with ", num_bodies, " and end with ", num_bodies_after_duplicates
            print "continue"
            if num_bodies == num_bodies_after_duplicates:
                # number of surfaces before and after Duplicates become the same, no more duplicates found
                break
        print "next component"

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

    @staticmethod
    def __get_all_surface_bodies(part):
        """
        Function to seperate solids from surface bodies for Geometrical set named selection conversion
        :param part:    input Spaceclaim Part
        :return:        return all surface bodies from input part
        """
        all_bodies = part.GetAllBodies()
        all_surface = part.GetAllBodies()
        all_surface.Clear()
        for body in all_bodies:
            if body.GetMidSurfaceAspect():
                all_surface.Add(body)
        return all_surface

    def __create_geometrical_set_names_list(self, part):
        """
        generate List of geometric sets from geometry names
        :param part:    Spaceclaim Part to get Geometric set names from
        :return:        List of geometrical sets names
        """

        all_bodies = self.__get_all_surface_bodies(part)
        geometrical_sets = []

        for body in all_bodies:
            body_name = body.GetName()
            while True:
                geo_set_name_test, content = os.path.split(body_name)
                if content:
                    if geo_set_name_test and not geometrical_sets.__contains__(geo_set_name_test):
                        geometrical_sets.append(geo_set_name_test)
                    body_name = geo_set_name_test
                else:
                    if geo_set_name_test:
                        if content and not geometrical_sets.__contains__(content):
                            geometrical_sets.append(content)
                    break
        return geometrical_sets

    def __get_bodies_for_geometrical_sets(self, part):
        """
        get bodies for each geometrical set
        :param part:    Spaceclaim Part to get Geometric set from
        :return:        List of body IDs in order of geo set names
        """
        body_list = []
        geometrical_sets = self.__create_geometrical_set_names_list(part)
        all_surface = self.__get_all_surface_bodies(part)
        for item in geometrical_sets:
            body_list.append([])
        for i, sbody in enumerate(all_surface):
            body_name = sbody.GetName()
            for k, item in enumerate(geometrical_sets):
                if body_name.Contains(item):
                    body_list[k].append(i)
        return body_list

    def __convert_list_to_dict(self, part):
        """
        Convert the lists to dictionaries
        :param part:        Spaceclaim Part to convert
        :return:
        """
        dictionary = {}
        body_list = self.__get_bodies_for_geometrical_sets(part)
        geo_list = self.__create_geometrical_set_names_list(part)
        surface_bodies = self.__get_all_surface_bodies(part)

        for i, body_ids_list in enumerate(body_list):
            for body_id in body_ids_list:
                if geo_list[i] not in dictionary:
                    dictionary[geo_list[i]] = List[IDesignBody]()
                dictionary[geo_list[i]].Add(surface_bodies[body_id])

        return dictionary

    def geo_sets_conversion(self, part):
        """
        Get Catia Geometrical set as Named selection
        :param part:
        :return:
        """
        conversion_dict = self.__convert_list_to_dict(part)
        self.create_named_selection(conversion_dict)

    @staticmethod
    def create_named_selection(conversion_dict):
        """
        Create a Named selection from dictionary
        :param conversion_dict:  Dictionary{Name of Named selection: LIst of bodies}
        """
        for item in conversion_dict:
            sel = Selection.Create(conversion_dict[item])
            if sel != Selection.Empty():
                second = Selection.Empty()
                result = NamedSelection.Create(sel, second).CreatedNamedSelection
                result.SetName(item.strip())

