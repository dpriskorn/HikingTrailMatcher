import logging
from typing import Dict, List

from OSMPythonTools.api import Api  # type: ignore
from pydantic import BaseModel
from requests import Session

import config
from src.console import console
from src.models.subroute import Subroute

# Silence chatty warning messages
logging.getLogger("OSMPythonTools").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


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
    wikidata: str = ""

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
            logging.debug("Got details from Waymarked Trails API")
            if config.loglevel == logging.DEBUG and config.debug_json:
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
                    if isinstance(route, str):
                        logger.debug(f"Skipping str route {route}")
                        # exit(0)
                    else:
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

    def fetch_wikidata_tag_information(self) -> None:
        """This check uses the Openstreetmap API because it is very fast"""
        api = Api()
        relation = api.query(f"relation/{self.id}")
        wikidata = relation.tag("wikidata")
        if wikidata:
            self.wikidata = wikidata
            logging.debug(f"wikidata tag: {wikidata}")
        else:
            logger.debug(f"No wikidata tag found for {self.id}")
