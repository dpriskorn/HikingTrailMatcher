from enum import Enum


class Property(Enum):
    OSM_RELATION_ID = "P402"
    POINT_IN_TIME = "P585"
    RETRIEVED = "P813"
    STATED_IN = "P248"


class ItemEnum(Enum):
    OPENSTREETMAP = "Q936"


class OsmIdSource:
    QUESTIONNAIRE = 0
    OSM_WIKIDATA_LINK = 1


class Status(Enum):
    ACCEPTED = 0
    DECLINED = 1
