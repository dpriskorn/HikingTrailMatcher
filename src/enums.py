from enum import Enum, auto


class Property(Enum):
    OSM_RELATION_ID = "P402"
    POINT_IN_TIME = "P585"
    RETRIEVED = "P813"
    STATED_IN = "P248"


class ItemEnum(Enum):
    OPENSTREETMAP = "Q936"


class OsmIdSource(Enum):
    QUESTIONNAIRE = auto()
    OSM_WIKIDATA_LINK = auto()


class Status(Enum):
    ACCEPTED = auto()
    DECLINED = auto()
