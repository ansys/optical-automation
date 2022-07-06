import os

from ansys_optical_automation.scdm_core.base import BaseSCDM


class PreProcessingASP(BaseSCDM):
    """
    This class contains all the methods to Pre-process Ansys SPEOS Geometries
    As per Api limitation only one session at the time can be attached.
    For this reason the class does not support multiple Ansys SPEOS  sessions.
    """

    def __init__(self, SpaceClaim):
        """
        Base class that contains all common used objects. This class serves more as an abstract class.

        Parameters
        ----------
        SpaceClaim : SpaceClaim object
            a SpaceClaim object.
        """
        super(PreProcessingASP, self).__init__(SpaceClaim, ["V19", "V20", "V21"])

    def create_dict_by_color(self):
        """
        Function to create a dictionary for Named selection generation/stitch one element per color

        Returns
        -------
        dict
            a dictionary with index of color code and value of a list of bodies
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
        Function to create a dictionary for based on materials defined in Catia.

        Returns
        -------
        dict
            a dictionary with index of material name and value of a list of bodies.
        """

        def get_real_original(item):
            """
            Function to get real original selection in order to get the material info.

            Parameters
            ----------
            item : SpaceClaim part
                a SpaceClaim part.

            Returns
            -------
            SpaceClaim part
                a SpaceClaim part.
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
        Function to stitch all bodies in component into groups of group_size.
        Example:
            In-> [body1, body2] [body3, body4], [body5, body6], [body7, body8], [body9]
            Out-> return [body3, body4]

        Parameters
        ----------
        comp : SpaceClaim Component
            a given Spaceclaim component.
        index : int
            index of the group to return.
        group_size : int
            the size of group.

        Returns
        -------
        list
            list of bodies defined by index.
        """
        stitch_group = self.List[self.IDesignBody]()
        for i, body in enumerate(self.ComponentExtensions.GetBodies(comp)):
            if index * group_size <= i < (index + 1) * group_size:
                stitch_group.Add(body)
        return stitch_group

    def __stitch_group_list(self, comp, total_iter, group_size):
        """
        Function to return a list group.
        Examples:
            e.g. body1 body2 body3 body4 body5 body6 body7 body8 body9.

        Parameters
        ----------
        comp : SpaceClaim Component
            a given SpaceClaim component.
        total_iter : int
            total number of group generated from the component.
        group_size : int
            size of each group.

        Returns
        -------
        list
            list of bodies.
            examples:
                [[body1, body2] [body3, body4], [body5, body6], [body7, body8], [body9]]
        """
        stitch_group_list = []
        for i in range(total_iter):
            group = self.__stitch_group(comp, i, group_size)
            stitch_group_list.append(group)
        return stitch_group_list

    def stitch_comp(self, comp):
        """
        Function to apply stitch according to component structure.

        Parameters
        ----------
        comp : SpaceClaim Component
            given component.
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
        Function to stitch all bodies based on dictionary.

        Parameters
        ----------
        conversion_dict : dict
            a dictionary with value of list of bodies.
        """
        for item in conversion_dict:
            sel = self.Selection.Create(conversion_dict[item])
            self.StitchFaces.FixSpecific(sel)

    def remove_duplicates(self, comp):
        """
        Function to remove duplicated surfaces with a given component.

        Parameters
        ----------
        comp : SpaceClaim Component
            a given SpaceClaim component.
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
        """Verify weather any part was imported by geometry update."""
        return self

    def check_volume_conflict(self):
        """Find volume conflict, return two list of conflicting bodies."""
        return self

    def resolve_volume_conflict(self):
        """Resolve volume Conflict based on material definition."""
        return self

    def __get_all_surface_bodies(self, part):
        """
        Function to seperate solids from surface bodies for Geometrical set named selection conversion.

        Parameters
        ----------
        part : Spaceclaim Part
            a given SpaceClaim prt.

        Returns
        -------
        Spacelciam Surfaces
            all surface bodies from input part.
        """
        all_bodies = self.PartExtensions.GetAllBodies(part)
        all_surface = self.PartExtensions.GetAllBodies(part)
        if len(all_surface):
            all_surface.Clear()
        for body in all_bodies:
            if self.DesignBodyExtensions.GetMidSurfaceAspect(body):
                all_surface.Add(body)
        return all_surface

    def __create_geometrical_set_names_list(self, part, bodies_only=True):
        """
        Function to generate List of geometric sets from geometry names.

        Parameters
        ----------
        part : Spaceclaim Part
            a given SpaceClaim part.
        bodies_only : bool
            true if only processing volume bodies otherwise false.

        Returns
        -------
        list
            List of geometrical sets names.
        """
        if bodies_only:
            all_bodies = self.__get_all_surface_bodies(part)
        else:
            all_bodies = self.PartExtensions.GetAllBodies(part)
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

    def __get_bodies_for_geometrical_sets(self, part, bodies_only=True):
        """
        Function to get bodies for each geometrical set.

        Parameters
        ----------
        part : Spaceclaim Part
            a given SpaceClaim part.
        bodies_only : bool
            true if only processing volume bodies otherwise false.

        Returns
        -------
        list
            List of body IDs in order of geo set names.
        """
        geometrical_sets = self.__create_geometrical_set_names_list(part, bodies_only)
        if bodies_only:
            all_surface = self.__get_all_surface_bodies(part)
        else:
            all_surface = self.PartExtensions.GetAllBodies(part)
        body_list = [[] for _i in range(len(geometrical_sets))]

        for i, sbody in enumerate(all_surface):
            body_name = sbody.Name
            for k, item in enumerate(geometrical_sets):
                if item in body_name:
                    body_list[k].append(i)
        return body_list

    def __convert_list_to_dict(self, part, bodies_only=True):
        """
        Convert the lists to dictionaries.

        Parameters
        ----------
        part : SpaceClaim part
            a given SpaceClaim part.
        bodies_only : bool

        Returns
        -------
        dict
        """
        dictionary = {}
        body_list = self.__get_bodies_for_geometrical_sets(part, bodies_only)
        geo_list = self.__create_geometrical_set_names_list(part, bodies_only)
        if bodies_only:
            surface_bodies = self.__get_all_surface_bodies(part)
        else:
            surface_bodies = self.PartExtensions.GetAllBodies(part)

        for i, body_ids_list in enumerate(body_list):
            for body_id in body_ids_list:
                if geo_list[i] not in dictionary:
                    dictionary[geo_list[i]] = self.List[self.IDesignBody]()
                dictionary[geo_list[i]].Add(surface_bodies[body_id])

        return dictionary

    def geo_sets_conversion(self, part):
        """
        Get Catia Geometrical set as Named selection.

        Parameters
        ----------
        part : SpaceClaim part
            a given SpaceClaim part.
        """
        conversion_dict = self.__convert_list_to_dict(part)
        self.create_named_selection(conversion_dict)

    def create_named_selection(self, conversion_dict):
        """
        Create a Named selection from dictionary.

        Parameters
        ----------
        conversion_dict : dict
            a Dictionary with index of Name with value of List of bodies.
        """
        for item in conversion_dict:
            sel = self.Selection.Create(conversion_dict[item])
            if sel != self.Selection.Empty():
                second = self.Selection.Empty()
                result = self.NamedSelection.Create(sel, second).CreatedNamedSelection
                result.Name = item.strip()

    def find_component(self, component_name):
        """
        Function to find all components with given name.

        Parameters
        ----------
        component_name : str
            name used for searching components.

        Returns
        -------
        list
            a list of SpaceClaim component with the given name.
        """
        root = self.GetRootPart()
        all_components = root.GetDescendants[self.IComponent]()
        found_components = []
        for component in all_components:
            if component_name in component.Content.Master.DisplayName:
                found_components.append(component)
        return found_components
