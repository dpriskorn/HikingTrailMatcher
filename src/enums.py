from enum import Enum, auto


class Property(Enum):
    POINT_IN_TIME = "P585"
    OSM_RELATION_ID = "P402"


class OsmIdSource:
    QUESTIONNAIRE = auto()
    OSM_WIKIDATA_LINK = auto()
