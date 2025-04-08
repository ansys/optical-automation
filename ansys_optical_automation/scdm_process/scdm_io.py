import os

from ansys_optical_automation.scdm_core.base import BaseSCDM


class ScdmIO(BaseSCDM):
    """
    Provides all methods for importing and exporting a SpaceClaim or Speos project.

    This class does not support multiple Speos sessions.
    """

    def __init__(self, SpaceClaim):
        super(ScdmIO, self).__init__(
            SpaceClaim, ["V19", "V20", "V21", "V22", "V23", "V231", "V232", "V241", "V242", "V251"]
        )

    def __valid_file(self, file):
        """
        Check whether a file exists and is valid.

        Parameters
        ----------
        file : str
            Full path to the file.

        Returns
        -------
        bool
            ``True`` when successful, ``False`` when failed.
        """
        return os.path.isfile(file)

    def __apply_lock(self, component):
        """
        Apply lock to all bodies under a component.

        Parameters
        ----------
        component : SpaceClaim component
            SpaceClaim component.
        """
        for body in self.ComponentExtensions.GetAllBodies(component):
            body_selection = self.Selection.CreateByObjects(body)
            self.ViewHelper.LockBodies(body_selection, True)

    def __apply_internalize(self, component):
        """
        Internalize a component.

        Parameters
        ----------
        component : SpaceClaim component
            SpaceClaim component.
        """
        group_selection = self.Selection.CreateByObjects(component)
        self.ComponentHelper.InternalizeAll(group_selection, True, None)

    def __apply_anchor(self, component):
        """
        Add anchor conditions to a structure component.

        Parameters
        ----------
        component : SpaceClaim component
        """
        self.AnchorCondition.Create(component.Parent, component)
        for item in self.ComponentExtensions.GetAllComponents(component):
            if self.ComponentExtensions.GetAllComponents(item).Count != 0:
                self.AnchorCondition.Create(item.Parent, item)

    def __get_speos_source_under_component(self, component_group):
        """
        Get Speos source elements defined under a component.

        Parameters
        ----------
        component_group : SpaceClaim group

        Returns
        -------
        list
            List of Speos sources.
        """
        speos_sources_list = []
        for component in self.ComponentExtensions.GetAllComponents(component_group):
            for speos_object in component.Content.CustomObjects:
                if "Source" in speos_object.Type:
                    speos_sources_list.append(speos_object)
        return speos_sources_list

    def __create_speos_sources_group(self, component, name):
        """
        Create a Speos source group for the surface sources defined under a component.

        Parameters
        ----------
        component : SpaceClaim component
            SpaceClaim component.
        name : str
            Name for the Speos source group.
        """
        speos_source_list = self.__get_speos_source_under_component(component)
        source_selection = self.Selection.CreateByObjects(speos_source_list)
        if name:
            source_selection.CreateAGroup(name)
        else:
            source_selection.CreateAGroup("speos_sources_group")

    def __group_components(self, component_list, name, anchor, lock, internalize, speos_source_group):
        """
        Group a list of components.

        Parameters
        ----------
        component_list : list
            List of SpaceClaim components.
        name : str
            Name for the group.
        anchor : bool
            Whether an anchor is required.
        lock : bool
            Whether a lock is required.
        internalize : bool
            Whether to internalize.
        speos_source_group : bool
            Whether to group Speos surfaces under the imported part.

        Returns
        -------
        bool
            ``True`` when succcessful, ``False`` when failed.
        """
        selection = self.Selection.CreateByObjects(component_list)
        result = self.ComponentHelper.MoveBodiesToComponent(selection)

        grouped_group = self.PartExtensions.GetComponents(self.GetRootPart())[-1]
        if name:
            self.SetName(grouped_group, name)

        if anchor:
            self.__apply_anchor(grouped_group)

        if internalize:
            try:
                self.__apply_internalize(grouped_group)
            except Exception as error:
                raise TypeError("Selected file has been locked. Details: " + str(error))

        if lock:
            self.__apply_lock(grouped_group)

        if speos_source_group:
            self.__create_speos_sources_group(grouped_group, name)

        return result

    def get_axis_systems_under_component(self, component):
        """
        Get the axis system under a component.

        Parameters
        ----------
        component : SpaceClaim component
            SpaceClaim component.

        Returns
        -------
        list
            List of axis systems that are under the component.
        """
        axis_system_list = []
        for axis_system in self.ComponentExtensions.GetCoordinateSystems(component):
            if axis_system.Master.Name != "" and axis_system.IsVisible(None) is True:
                axis_system_list.append(axis_system)
        return axis_system_list

    def import_part_at_axis_system(
        self,
        external_part,
        axis_system_list,
        name=None,
        anchor=False,
        lock=False,
        internalize=False,
        speos_source_group=False,
    ):
        """
        Import component at a given axis system.

        Parameters
        ----------
        external_part : SpaceClaim file
            SpaceClaim file to import.
        axis_system_list : list
            List of axis systems.
        name : string, optional
            Name for the group to use for grouping imported parts. The default is ``None``.
        anchor : bool, optional
            Whether an anchor is required. The default is ``False``.
        lock : bool, optional
            Whether a lock is required. The default is ``False``.
        internalize : bool, optional
            Whether to internalize. The default is ``False``.
        speos_source_group : bool, optional
            Whether to group Speos surfaces under the imported part. The default is ``False``.
        """
        if not self.__valid_file(external_part):
            error_msg = "Invalid project directory."
            raise ValueError(error_msg)

        if len(axis_system_list) == 0:
            return

        imported_component_group = []
        self.ComponentHelper.SetRootActive()
        for axis_system in axis_system_list:
            self.Selection.CreateByObjects(axis_system).SetActive()
            self.DocumentInsert.Execute(external_part)
            component_imported = self.PartExtensions.GetComponents(self.GetRootPart())[-1]
            imported_component_group.append(component_imported)
        self.__group_components(imported_component_group, name, anchor, lock, internalize, speos_source_group)
