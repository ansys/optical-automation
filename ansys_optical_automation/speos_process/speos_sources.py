from ansys_optical_automation.scdm_core.base import BaseSCDM


class Source(BaseSCDM):
    """
    Provides the parent class for all Speos Source types.

    This class contains methods and properties that are common to all Source elements.
    It shouldn't be used by itself. Subclasses should be used instead.
    """

    def __init__(self, name, SpeosSim, SpaceClaim):
        super(Source, self).__init__(SpaceClaim, ["V19", "V20", "V21", "V22", "V23"])
        self.speos_sim = SpeosSim
        self.name = name
        self.speos_object = None


class SourceLightField(Source):
    """
    Provides methods for defining the Speos LocalMeshing.
    """

    def __init__(self, name, SpeosSim, SpaceClaim):
        super(SourceLightField, self).__init__(name, SpeosSim, SpaceClaim)
        if self.speos_sim.SourceLightField.Find(self.name):
            self.speos_object = self.speos_sim.SourceLightField.Find(self.name)
        else:
            self.speos_object = self.speos_sim.SourceLightField.Create()
            self.speos_object.Name = self.name
