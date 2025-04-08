import os

from ansys_optical_automation.scdm_core.base import BaseSCDM


class PreProcessingASP(BaseSCDM):
    """
    Provides all methods for preprocessing Speos geometries.

    Because of an API limitation, this class does not support
    multiple Speos sessions. Only one session can be attached
    at a time.
    """

    def __init__(self, SpaceClaim):
        """
        Base class that contains all commonly used objects. This class serves more as an abstract class.

        Parameters
        ----------
        SpaceClaim : SpaceClaim object
            SpaceClaim object.
        """
        super(PreProcessingASP, self).__init__(
            SpaceClaim, ["V19", "V20", "V21", "V22", "V23", "V231", "V232", "V241", "V242", "V251"]
        )

    def create_dict_by_color(self):
        """
        Create a dictionary for named selection generation, stitching one element per color.

        Returns
        -------
        dict
            Dictionary with an index of color codes and values for a list of bodies.
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
        Create a dictionary for materials defined in Catia.

        Returns
        -------
        dict
            Dictionary with an index of material names and values for a list of bodies.
        """

        def get_real_original(item):
            """
            Get real original selection to obtain material information.

            Parameters
            ----------
            item : SpaceClaim part
                SpaceClaim part.

            Returns
            -------
            SpaceClaim part
                SpaceClaim part.
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
         Stitch all bodies in a component into groups by group size.

        Parameters
        ----------
        comp : SpaceClaim Component
            Spaceclaim component.
        index : int
            Index of the group to return.
        group_size : int
            Size of the group.

        Returns
        -------
        list
            List of bodies defined by the index.

        Examples
        --------
        >>>In-> [body1, body2] [body3, body4], [body5, body6], [body7, body8], [body9]
        Out-> return [body3, body4]
        """
        stitch_group = self.List[self.IDesignBody]()
        for i, body in enumerate(self.ComponentExtensions.GetBodies(comp)):
            if index * group_size <= i < (index + 1) * group_size:
                stitch_group.Add(body)
        return stitch_group

    def __stitch_group_list(self, comp, total_iter, group_size):
        """
        Get a list of bodies by group.

        Parameters
        ----------
        comp : SpaceClaim Component
            SpaceClaim component.
        total_iter : int
            Total number of groups to generate from the component.
        group_size : int
            Size of each group.

        Returns
        -------
        list
            List of bodies by group.

        Examples
        --------
        Assume that the SpaceClaim component has these groups:

        >>>body1 body2 body3 body4 body5 body6 body7 body8 body9

        If the group size is set to ``2``, the list that is returned would look like this:

        >>>[[body1, body2] [body3, body4], [body5, body6], [body7, body8], [body9]]
        """
        stitch_group_list = []
        for i in range(total_iter):
            group = self.__stitch_group(comp, i, group_size)
            stitch_group_list.append(group)
        return stitch_group_list

    def stitch_comp(self, comp, max_group_limit):
        """
        Stitch according to component structure. Surfaces inside the Component provided are stitched
        group by group whose seize is defined by group size

        Parameters
        ----------
        comp : SpaceClaim Component
            SpaceClaim component.
        max_group_limit : int
            group size

        Returns
        -------


        """

        all_bodies = self.ComponentExtensions.GetBodies(comp)
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
        Stitch all bodies based on a dictionary.

        Parameters
        ----------
        conversion_dict : dict
            Dictionary with values for a list of bodies.
        """
        for item in conversion_dict:
            sel = self.Selection.Create(conversion_dict[item])
            self.StitchFaces.FixSpecific(sel)

    def remove_duplicates(self, comp):
        """
        Remove duplicated surfaces with a given component.

        Parameters
        ----------
        comp : SpaceClaim Component
            SpaceClaim component.
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
        """Check whether any part was imported by a geometry update."""
        return self

    def check_volume_conflict(self):
        """Check for volume conflict, returning two lists of conflicting bodies."""
        return self

    def resolve_volume_conflict(self):
        """Resolve volume conflict based on the material definition."""
        return self

    def __get_all_surface_bodies(self, part):
        """
        Seperate solids from surface bodies for a geometrical set named selection conversion.

        Parameters
        ----------
        part : Spaceclaim Part
            SpaceClaim part.

        Returns
        -------
        SpaceClaim Surfaces
            All surface bodies from the part.
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
        Generate a list of geometrical set names from geometry names.

        Parameters
        ----------
        part : Spaceclaim Part
            SpaceClaim part.
        bodies_only : bool, optional
            Whether to process only volume bodies. The default is ``True``.

        Returns
        -------
        list
            List of geometrical set names.
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
        Get bodies for each geometrical set.
        !!!This function does not includes Meshed bodies!!!

        Parameters
        ----------
        part : Spaceclaim Part
            SpaceClaim part.
        bodies_only : bool, optional
            Whether to process only volume bodies. The default is ``True``.

        Returns
        -------
        list
            List of body IDs in order of geometrical set names.
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
        Convert lists to dictionaries.

        Parameters
        ----------
        part : SpaceClaim part
            SpaceClaim part.
        bodies_only : bool, optional
            Whether to process only volume bodies. The default is ``True``.

        Returns
        -------
        dict
            Dictionary for each list.
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
        Get Catia geometrical set as a named selection.

        Parameters
        ----------
        part : SpaceClaim part
            SpaceClaim part.
        """
        conversion_dict = self.__convert_list_to_dict(part)
        self.create_named_selection(conversion_dict)

    def create_named_selection(self, conversion_dict):
        """
        Create a named selection from a dictionary.

        Parameters
        ----------
        conversion_dict : dict
            Dictionary with an index of names with a value of a list of bodies.
        """
        for item in conversion_dict:
            sel = self.Selection.Create(conversion_dict[item])
            if sel != self.Selection.Empty():
                second = self.Selection.Empty()
                result = self.NamedSelection.Create(sel, second).CreatedNamedSelection
                result.Name = item.strip()

    def find_component(self, component_name):
        """
        Find all components with a given name.

        Parameters
        ----------
        component_name : str
            Name for searching components.

        Returns
        -------
        list
            List of components with the given name.
        """
        root = self.GetRootPart()
        all_components = root.GetDescendants[self.IComponent]()
        found_components = []
        for component in all_components:
            if component_name in component.Content.Master.DisplayName:
                found_components.append(component)
        return found_components
