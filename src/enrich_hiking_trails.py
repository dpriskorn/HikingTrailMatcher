import logging
from typing import Dict, Iterable, Optional

import requests  # type: ignore
from pydantic import validate_arguments
from wikibaseintegrator import WikibaseIntegrator, wbi_config  # type: ignore
from wikibaseintegrator.datatypes import ExternalID, Item, Time  # type: ignore
from wikibaseintegrator.wbi_enums import (  # type: ignore
    WikibaseDatePrecision,
    WikibaseSnakType,
)
from wikibaseintegrator.wbi_helpers import execute_sparql_query  # type: ignore
from wikibaseintegrator.wbi_login import Login  # type: ignore

import config
from src.console import console
from src.enums import OsmIdSource
from src.project_base_model import ProjectBaseModel
from src.trail_item import TrailItem

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)


class EnrichHikingTrails(ProjectBaseModel):
    rdf_entity_prefix = "http://www.wikidata.org/entity/"
    wbi: Optional[WikibaseIntegrator]

    class Config:
        arbitrary_types_allowed = True

    def __get_hiking_trails_missing_osm_id__(self) -> Iterable[str]:
        result = self.__get_sparql_result__()
        if config.loglevel == logging.DEBUG:
            console.print(result)
        return self.__extract_item_ids__(sparql_result=result)

    def __get_sparql_result__(self):
        # For now we limit to swedish trails
        self.setup_wbi()
        # We hardcode swedish for now
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
        # We set up WBI once here and reuse it for every TrailItem
        self.setup_wbi()
        self.__login_to_wikidata__()
        for qid in items:
            trail = TrailItem(qid=qid, wbi=self.wbi)
            trail.fetch_and_lookup_and_present_choice_to_user()
            if trail.questionary_return.quit:
                break
            elif trail.questionary_return.could_not_decide:
                console.print(
                    f"Try looking at {trail.waymarked_hiking_trails_search_url} "
                    f"and see if any fit with {trail.wd_url}"
                )
            else:
                trail.enrich_wikidata(osm_id_source=OsmIdSource.QUESTIONNAIRE)

    def __login_to_wikidata__(self):
        logger.debug(f"Trying to log in to the Wikibase as {config.user_name}")
        self.wbi = WikibaseIntegrator(
            login=Login(user=config.user_name, password=config.bot_password),
        )
