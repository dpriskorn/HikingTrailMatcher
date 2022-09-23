import logging
from enum import Enum
from typing import Dict, Iterable, List, Optional

import requests  # type: ignore
from pydantic import BaseModel, validate_arguments
from questionary import Choice
from rich.console import Console
from wikibaseintegrator import WikibaseIntegrator, wbi_config  # type: ignore
from wikibaseintegrator.datatypes import ExternalID, Time  # type: ignore
from wikibaseintegrator.wbi_enums import WikibaseDatePrecision, WikibaseSnakType
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
    label: str = ""

    class Config:
        arbitrary_types_allowed = True

    @validate_arguments()
    def __lookup_osm_relation_id__(self) -> Optional[str]:
        if not self.label:
            raise ValueError("self.label was empty")
        if not isinstance(self.label, str):
            raise TypeError("self.label was not a str")
        logger.info(f"looking up: {self.label}")
        self.__lookup_in_the_waymarked_trails_database__(search_term=self.label)
        self.__prepare_choices__()
        return self.__ask_question__()

    def __prepare_choices__(self):
        self.__remove_waymaked_result_duplicates__()
        self.__convert_waymarked_results_to_choices__()
        self.choices.append(Choice(title="None of these match", value=""))

    @validate_arguments()
    def __ask_question__(self) -> Optional[str]:
        # present the result to the user to choose from
        import questionary
        result = questionary.select(
            f"Which of these match '{self.label}'?",
            choices=self.choices,
        ).ask()  # returns value of selection or None if user cancels
        if result:
            logger.info(f"{result} was chosen")
        elif result == "":
            logger.info("No match chosen")
        else:
            logger.info("User quit")
        return result

    @validate_arguments()
    def __lookup_in_the_waymarked_trails_database__(self, search_term: str) -> None:
        if not search_term:
            raise ValueError("search_term was empty")
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

    def __get_sparql_result__(self):
        # For now we limit to swedish trails
        self.__setup_wbi_()
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
        self.__setup_wbi_()
        wbi = WikibaseIntegrator()
        for qid in items:
            self.__clear_attributes__()
            item = wbi.item.get(qid)
            self.label = item.labels.get("sv").value
            # aliases = item.aliases.get("sv")
            osm_id = self.__lookup_osm_relation_id__()
            if osm_id is None:
                break
            if osm_id:
                console.print(f"Got match, adding OSM = {osm_id} to WD")
                item.add_claims(
                    claims=ExternalID(
                        prop_nr=Property.OSM_RELATION_ID.value, value=str(osm_id)
                    )
                )
            else:
                console.print("No match, adding no value = true to WD")
                claim = ExternalID(
                    prop_nr=Property.OSM_RELATION_ID.value,
                    value=None,
                    qualifiers=[self.__time_today_statement__()],
                )
                # Not documented, see https://github.com/LeMyst/WikibaseIntegrator/blob/9bc58824d2def664c950d53cca845524b93ec051/test/test_wbi_core.py#L199
                claim.mainsnak.snaktype = WikibaseSnakType.NO_VALUE
                item.add_claims(claims=claim)

    def __convert_waymarked_results_to_choices__(self):
        for result in self.waymarked_results:
            choice = Choice(title=result.name, value=result.id)
            self.choices.append(choice)

    @staticmethod
    def __time_today_statement__():
        time_object = WikidataTimeFormat()
        return Time(
            prop_nr=Property.POINT_IN_TIME.value,
            time=time_object.day,
            precision=WikibaseDatePrecision.DAY,
        )

    def __remove_waymaked_result_duplicates__(self):
        self.waymarked_results = list(set(self.waymarked_results))

    def __clear_attributes__(self):
        self.waymarked_results = []
        self.choices = []
        self.label = ""

    @staticmethod
    def __setup_wbi_():
        wbi_config.config[
            "USER_AGENT"
        ] = "hiking-trail-scraper, see https://github.com/dpriskorn/hiking_trail_scraper/"
