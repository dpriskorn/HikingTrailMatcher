from enum import Enum


class Property(Enum):
    POINT_IN_TIME = "P585"
    OSM_RELATION_ID = "P402"


class OsmIdSource:
    QUESTIONNAIRE = 0
    OSM_WIKIDATA_LINK = 1


class Status(Enum):
    ACCEPTED = 0
    DECLINED = 1
