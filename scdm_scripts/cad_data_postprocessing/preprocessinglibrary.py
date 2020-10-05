#preprocessing class
#
from os import path


class Preprocessing_asp():
    def stitch(self):

    def check_geometry_update(self):

    def check_volume_conflict(self):

    def resolve_volume_conflict(self):

    def __create_named_selection(self, selection, str_name):


    def __get_all_surface_bodies(self, part):
        allbodies = part.GetAllBodies()
        allsurface = part.GetAllBodies()
        allsurface.Clear()
        for body in allbodies:
            if body.GetMidSurfaceAspect() != None:
                allsurface.Add(body)
        return (allsurface)

    def __get_geometrical_set(self, part):
        bodienames = []
        allbodies = self.__get_all_surface_bodies(part)
        t = 0
        geometricalsets = []
        for body in allbodies:
            str_test = body.GetName()
            test = True
            while test:
                geo_set_name_test, content = path.split(str_test)
                if content != "":
                    if True != geometricalsets.__contains__(geo_set_name_test):
                        geometricalsets.append(geo_set_name_test)
                    str_test = geo_set_name_test
                else:
                    if geo_set_name_test != "":
                        if True != geometricalsets.__contains__(content):
                            geometricalsets.append(content)
                    test = False
        return(geometricalsets)

    def __get_bodies_for geometrical_sets()
        bodylist = []
        testlist = []
        for item in geometricalsets:
            bodylist.append([])
        t = 0
        for sbody in allsurface:
            k = 0
            for item in test2:
                testlist = bodylist[k]
                str_test = sbody.GetName()
                if str_test.Contains(item):
                    testlist.append(t)
                    bodylist[k] = testlist
                k = k + 1
            t = t + 1





