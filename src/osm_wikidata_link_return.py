from pydantic import BaseModel


class OsmWikidataLinkReturn(BaseModel):
    """Models a return from the API"""
    multiple_matches: bool = False # only relations considered
    single_match: bool = False
    no_match: bool = False