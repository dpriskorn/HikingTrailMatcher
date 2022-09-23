from pydantic import BaseModel


class Tags(BaseModel):
    name: str
    ref: str = ""


class OsmWikidataLinkResult(BaseModel):
    """Models the JSON response from the OSM Wikidata Link API"""

    id: int
    tags: Tags
