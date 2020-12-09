# Copyright (C) 2020 ANSYS, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

import os
from SPEOS_scripts.SpaceClaimCore.base import BaseSCDM


class PreProcessingASP(BaseSCDM):
    """
    This class contains all the methods to Pre-process Ansys SPEOS Geometries
    As per Api limitation only one session at the time can be attached.
    For this reason the class does not support multiple Ansys SPEOS  sessions.
    """
    def __init__(self, SpaceClaim):
        """
        Args:
            SpaceClaim: SpaceClaim object
        """
        super(PreProcessingASP, self).__init__(SpaceClaim, ["V19", "V20"])

    def create_dict_by_color(self):
        """
        Create a dictionary for Named selection generation/stitch one element per color
        :return: Dictionary {color code: List of bodies with color}
        """
        conversion_dict = {}
        root = self.GetRootPart()
        all_body = self.PartExtensions.GetAllBodies(root)
        for body in all_body:
            sel = self.Selection.Create(body)
            color_info = self.ColorHelper.GetColor(sel).ToString()
            if color_info not in conversion_dict:
                conversion_dict[color_info] = self.List[self.IDesignBody]()
            conversion_dict[color_info].Add(body)
        return conversion_dict

    def create_dict_by_material(self):
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
            while self.GetOriginal(item):
                item = self.GetOriginal(item)
            original = item
            return original

        conversion_dict = {}
        root = self.GetRootPart()
        all_body = self.PartExtensions.GetAllBodies(root)
        for body in all_body:
            ibody = get_real_original(body)
            try:
                material_name = ibody.Material.Name
            except AttributeError:
                continue

            if material_name not in conversion_dict:
                conversion_dict[material_name] = self.List[self.IDesignBody]()
            conversion_dict[material_name].Add(body)
        return conversion_dict

    def __stitch_group(self, comp, index, group_size):
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

        stitch_group = self.List[self.IDesignBody]()
        for i, body in enumerate(self.ComponentExtensions.GetBodies(comp)):
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
            stitch_group_list.append(group)
        return stitch_group_list

    def stitch_comp(self, comp):
        """
        apply stitch according to component structure
        para comp: given component
        """
        all_bodies = self.ComponentExtensions.GetBodies(comp)
        max_group_limit = 200
        while True:
            num_bodies = len(all_bodies)
            total_iter = int(num_bodies / max_group_limit) + 1
            stitch_group_list = self.__stitch_group_list(comp, total_iter, max_group_limit)
            for group in stitch_group_list:
                sel = self.Selection.Create(group)
                self.StitchFaces.FindAndFix(sel)

            all_bodies = self.ComponentExtensions.GetBodies(comp)
            num_bodies_after_stitch = len(all_bodies)
            if num_bodies_after_stitch == num_bodies:
                break

    def stitch(self, conversion_dict):
        """
        stitch all element per dictionary items-> color/material
        """
        for item in conversion_dict:
            sel = self.Selection.Create(conversion_dict[item])
            self.StitchFaces.FixSpecific(sel)

    def remove_duplicates(self, comp):
        """
        Remove duplicated surfaces
        param part: input SpaceClaim part
        :return:
        """
        all_bodies = self.ComponentExtensions.GetBodies(comp)
        while True:
            sel = self.Selection.Create(all_bodies)
            num_bodies = len(all_bodies)
            self.FixDuplicateFaces.FindAndFix(sel)

            all_bodies = self.ComponentExtensions.GetBodies(comp)
            num_bodies_after_duplicates = len(all_bodies)
            if num_bodies == num_bodies_after_duplicates:
                # number of surfaces before and after Duplicates become the same, no more duplicates found
                break

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
        all_bodies = self.PartExtensions.GetAllBodies(part)
        all_surface = self.PartExtensions.GetAllBodies(part)
        if len(all_surface):
            all_surface.Clear()
        for body in all_bodies:
            if self.DesignBodyExtensions.GetMidSurfaceAspect(body):
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
            body_name = body.Name
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

        geometrical_sets = self.__create_geometrical_set_names_list(part)
        all_surface = self.__get_all_surface_bodies(part)
        body_list = [[] for _i in range(len(geometrical_sets))]

        for i, sbody in enumerate(all_surface):
            body_name = sbody.Name
            for k, item in enumerate(geometrical_sets):
                if item in body_name:
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
                    dictionary[geo_list[i]] = self.List[self.IDesignBody]()
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

    def create_named_selection(self, conversion_dict):
        """
        Create a Named selection from dictionary
        :param conversion_dict:  Dictionary{Name of Named selection: LIst of bodies}
        """
        for item in conversion_dict:
            sel = self.Selection.Create(conversion_dict[item])
            if sel != self.Selection.Empty():
                second = self.Selection.Empty()
                result = self.NamedSelection.Create(sel, second).CreatedNamedSelection
                result.Name = item.strip()
