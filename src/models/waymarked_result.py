import logging
from typing import Dict, List

from OSMPythonTools.api import Api  # type: ignore
from pydantic import BaseModel
from requests import Session

import config
from src.console import console
from src.models.subroute import Subroute


class WaymarkedResult(BaseModel):
    """Models the JSON response from the Waymarked Trails API"""

    id: int
    group: str = ""
    name: str
    ref: str = ""
    itinerary: List[str] = []
    session: Session = Session()
    subroutes: List[Subroute] = []
    details: Dict = {}
    # These are meters
    official_length: float = 0
    mapped_length: float = 0
    description: str = ""

    class Config:
        arbitrary_types_allowed = True

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return self.id

    def get_details(self):
        self.__fetch_details__()
        self.__parse_details__()

    def __fetch_details__(self):
        url = f"https://hiking.waymarkedtrails.org/api/v1/details/relation/{self.id}"
        # pass the session to this
        response = self.session.get(url, timeout=config.request_timeout)
        if response.status_code == 200:
            self.details = response.json()
            logging.info("Got details from Waymarked Trails API")
            if config.loglevel == logging.DEBUG:
                console.print(self.details)
        else:
            raise Exception(
                f"got {response.status_code} from the "
                f"Waymarked Trails API when trying to fetch details, see {url}"
            )

    def __parse_details__(self):
        """Parse the details into attributes"""
        if self.details:
            self.official_length = self.details.get("official_length")
            self.mapped_length = self.details.get("mapped_length")
            self.description = self.details.get("description")
            subroutes = self.details.get("subroutes")
            if subroutes:
                for route in subroutes:
                    self.subroutes.append(Subroute(**route))

    @property
    def number_of_subroutes(self) -> int:
        return len(self.subroutes)

    @property
    def __names_of_subroutes__(self) -> List[str]:
        return [route.name for route in self.subroutes]

    @property
    def names_of_subroutes_as_string(self) -> str:
        if self.number_of_subroutes:
            return ", ".join(self.__names_of_subroutes__)
        else:
            return ""

    @property
    def already_has_wikidata_tag(self) -> bool:
        """This check uses the Openstreetmap API because it is fast"""
        api = Api()
        relation = api.query(f"relation/{self.id}")
        wikidata = relation.tag("wikidata")
        logging.debug(f"wikidata tag: {wikidata}")
        if wikidata is None:
            return False
        else:
            return True
