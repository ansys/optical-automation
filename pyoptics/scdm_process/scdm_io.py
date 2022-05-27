import os

from pyoptics.scdm_core.base import BaseSCDM


class ScdmIO(BaseSCDM):
    """
    This class contains all the methods to import and output SpaceClaim/Ansys SPEOS project.
    For this reason the class does not support multiple Ansys SPEOS  sessions.
    """

    def __init__(self, SpaceClaim):
        super(ScdmIO, self).__init__(SpaceClaim, ["V19", "V20", "V21"])

    def __valid_file(self, file):
        """
        Parameters
        ----------
        file: str
            string describing the location of a file

        Returns
        -------
        bool: True such file is existing, False otherwise
        """
        return os.path.isfile(file)

    def __apply_lock(self, component):
        """
        This function apply lock to the all bodies under provided component
        Parameters
        ----------
        component: spaceclaim component

        Returns
        -------

        """
        for body in self.ComponentExtensions.GetAllBodies(component):
            body_selection = self.Selection.CreateByObjects(body)
            self.ViewHelper.LockBodies(body_selection, True)

    def __apply_internalize(self, component):
        """
        This function internalize the component provided
        Parameters
        ----------
        component: spaceclaim component

        Returns
        -------
        None

        """
        group_selection = self.Selection.CreateByObjects(component)
        self.ComponentHelper.InternalizeAll(group_selection, True, None)

    def __apply_anchor(self, component):
        """
        This function add anchor conditions to structure component provided
        Parameters
        ----------
        component: spaceclaim component

        Returns
        -------
        None

        """
        self.AnchorCondition.Create(component.Parent, component)
        for item in self.ComponentExtensions.GetAllComponents(component):
            if self.ComponentExtensions.GetAllComponents(item).Count != 0:
                self.AnchorCondition.Create(item.Parent, item)

    def __get_speos_source_under_component(self, component_group):
        """
        Parameters
        ----------
        component_group: spaceclaim group

        Returns
        -------
        a list speos sources
        """
        speos_sources_list = []
        for component in self.ComponentExtensions.GetAllComponents(component_group):
            for speos_object in component.Content.CustomObjects:
                if "Source" in speos_object.Type:
                    speos_sources_list.append(speos_object)
        return speos_sources_list

    def __create_speos_sources_group(self, component, name):
        """
        This function will create a speos source group for the surface sources defined under component provided
        Parameters
        ----------
        component: spaceclaim group
        name: str
            a string provided to name to speos source group

        Returns
        -------
        None
        """
        speos_source_list = self.__get_speos_source_under_component(component)
        source_selection = self.Selection.CreateByObjects(speos_source_list)
        if name:
            source_selection.CreateAGroup(name)
        else:
            source_selection.CreateAGroup("speos_sources_group")

    def __group_components(self, component_list, name, anchor, lock, internalize, speos_source_group):
        """
        Parameters
        ----------
        component_list: list
            a list of spaceclaim component
        name: str
            string given to the name of group
        anchor: bool
            True if anchor is required, False otherwise
        lock: bool
            True if lock is required, False otherwise
        internalize: bool
            True if internalize is required, False otherwise
        speos_source_group: bool
            True if speos surfaces under imported part needs to be group, False, otherwise

        Returns
        -------
        True if grouping is successful, False otherwise
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
        Parameters
        ----------
        component: SpaceClaim component

        Returns
        -------
        a list of axis systems which are under the component provided
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
        Parameters
        ----------
        external_part: a SpaceClaim file
            a spaceclaim file to be imported
        axis_system_list: an axis system
            a list of axis system
        name: string
            a name given to the group which grouping the imported parts
        anchor: bool
            True if anchor is required, False otherwise
        lock: bool
            True if lock is required, False otherwise
        internalize: bool
            True if internalize is required, False otherwise
        speos_source_group: bool
            True if speos surfaces under imported part needs to be group, False, otherwise

        Returns
        -------
        None
        """
        if not self.__valid_file(external_part):
            error_msg = "Invalid project directory, please check"
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
