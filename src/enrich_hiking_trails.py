import logging
from enum import Enum
from typing import Dict, Iterable, List, Optional

import questionary
import requests  # type: ignore
from pydantic import BaseModel, validate_arguments
from questionary import Choice
from rich.console import Console
from wikibaseintegrator import WikibaseIntegrator, wbi_config  # type: ignore
from wikibaseintegrator.datatypes import ExternalID, Time  # type: ignore
from wikibaseintegrator.wbi_enums import WikibaseDatePrecision
from wikibaseintegrator.wbi_helpers import execute_sparql_query  # type: ignore

import config
from src.waymarked_result import WaymarkedResult
from src.wikidata_time_format import WikidataTimeFormat

console = Console()
logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)


class Property(Enum):
    POINT_IN_TIME = "P585"
    OSM_RELATION_ID = "P402"


class EnrichHikingTrails(BaseModel):
    rdf_entity_prefix = "http://www.wikidata.org/entity/"
    waymarked_results: List[WaymarkedResult] = []
    choices: List[Choice] = []

    class Config:
        arbitrary_types_allowed = True

    def __lookup_osm_relation_id__(self, label: str, aliases: List[str]) -> str:
        self.__lookup_in_the_waymarked_trails_database__(search_term=label)
        self.__remove_waymaked_result_duplicates__()
        self.__convert_waymarked_results_to_choices__()
        self.choices.append(Choice(title="None of these match", value=""))
        # present the result to the user to choose from
        result = questionary.select(
            "Which of these match?",
            choices=self.choices,
        ).ask()  # returns value of selection
        if result:
            logger.info(f"{result} was chosen")
        else:
            logger.info("No match chosen")
        return str(result)

    def __lookup_in_the_waymarked_trails_database__(self, search_term) -> None:
        url = (
            f"https://hiking.waymarkedtrails.org/api/v1/list/search?query={search_term}"
        )
        result = requests.get(url=url)
        if result.status_code == 200:
            data = result.json()
            console.print(data)
            for result in data.get("results"):
                self.waymarked_results.append(WaymarkedResult(**result))

    def __get_hiking_trails_missing_osm_id__(self) -> Iterable[str]:
        result = self.__get_sparql_result__()
        if config.loglevel == logging.DEBUG:
            console.print(result)
        return self.__extract_item_ids__(sparql_result=result)

    @staticmethod
    def __get_sparql_result__():
        wbi_config.config[
            "USER_AGENT"
        ] = "hiking-trail-scraper, see https://github.com/dpriskorn/hiking_trail_scraper/"
        # For now we limit to swedish trails
        return execute_sparql_query(
            """
            SELECT DISTINCT ?item ?itemLabel WHERE {
              ?item wdt:P31 wd:Q2143825;
                    wdt:P17 wd:Q34.
              minus{?item wdt:P402 []}
              SERVICE wikibase:label { bd:serviceParam wikibase:language "sv,en". } # Hjälper dig hämta etiketten på ditt språk, om inte annat på engelska
            }
            """
        )

    @validate_arguments
    def __extract_wcdqs_json_entity_id__(
        self, data: Dict, sparql_variable: str = "item"
    ) -> str:
        """We default to "item" as sparql value because it is customary in the Wikibase ecosystem"""
        return str(data[sparql_variable]["value"].replace(self.rdf_entity_prefix, ""))

    @validate_arguments
    def __extract_item_ids__(self, sparql_result: Optional[Dict]) -> Iterable[str]:
        """Yield item ids from a sparql result"""
        if sparql_result:
            yielded = 0
            for binding in sparql_result["results"]["bindings"]:
                if item_id := self.__extract_wcdqs_json_entity_id__(data=binding):
                    yielded += 1
                    yield item_id
            if number_of_bindings := len(sparql_result["results"]["bindings"]):
                logger.info(f"Yielded {yielded} bindings out of {number_of_bindings}")

    def add_osm_property_to_items(self):
        # get all hiking paths in sweden without osm id
        items = self.__get_hiking_trails_missing_osm_id__()
        for qid in items:
            wbi = WikibaseIntegrator()
            item = wbi.item.get(qid)
            label = item.labels.get("sv")
            aliases = item.aliases.get("sv")
            osm_id = self.__lookup_osm_relation_id__(label=label, aliases=aliases)
            if osm_id:
                console.print(f"Got match, adding OSM = {osm_id} to WD")
                item.add_claims(
                    claims=ExternalID(
                        prop_nr=Property.OSM_RELATION_ID.value, value=osm_id
                    )
                )
            else:
                console.print("No match, adding no value = true to WD")
                item.add_claims(
                    claims=ExternalID(
                        prop_nr=Property.OSM_RELATION_ID.value,
                        no_value=True,
                        qualifiers=[self.__time_today_statement__()],
                    )
                )

    def __convert_waymarked_results_to_choices__(self):
        for result in self.waymarked_results:
            choice = Choice(title=result.name, value=result.id)
            self.choices.append(choice)

    def __time_today_statement__(self):
        time_object = WikidataTimeFormat()
        return Time(
            prop_nr=Property.POINT_IN_TIME.value,
            time=time_object.day,
            precision=WikibaseDatePrecision.DAY,
        )

    def __remove_waymaked_result_duplicates__(self):
        self.waymarked_results = list(set(self.waymarked_results))

