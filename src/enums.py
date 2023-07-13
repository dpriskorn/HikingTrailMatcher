from enum import Enum, auto


class Property(Enum):
    OSM_RELATION_ID = "P402"
    POINT_IN_TIME = "P585"
    RETRIEVED = "P813"
    STATED_IN = "P248"
    NOT_FOUND_IN = "P9660"
    LAST_UPDATE = "P5017"
    BASED_ON_HEURISTIC = "P887"


class ItemEnum(Enum):
    OPENSTREETMAP = "Q936"
    LOOKUP_IN_WAYMARKED_TRAILS_API = "Q119970009"
    USER_VALIDATION = "Q119970060"


class OsmIdSource(Enum):
    QUESTIONNAIRE = auto()
    OSM_WIKIDATA_LINK = auto()


class Status(Enum):
    ACCEPTED = auto()
    DECLINED = auto()
