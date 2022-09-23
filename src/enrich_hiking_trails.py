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
from src.enums import OsmIdSource, Status
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
        """We setup WBI, lookup first in OSM Wikidata Link
        and then fallback to labelmatching using the
        Waymaked Trails API"""
        # get all hiking paths in sweden without osm id
        items = self.__get_hiking_trails_missing_osm_id__()
        # We set up WBI once here and reuse it for every TrailItem
        self.setup_wbi()
        self.__login_to_wikidata__()
        for qid in items:
            trail_item = TrailItem(qid=qid, wbi=self.wbi)
            trail_item = self.__lookup_in_osm_wikidata_link__(trail_item=trail_item)
            if trail_item.osm_wikidata_link_match_prompt_return == Status.DECLINED:
                # Fallback to Waymarked Trails API
                self.__lookup_in_waymarked_trails__(trail_item=trail_item)

    @staticmethod
    def __lookup_in_osm_wikidata_link__(trail_item: TrailItem) -> TrailItem:
        """We lookup in OSM Wikidata Link and mutate the object and then return it"""
        trail_item.lookup_using_osm_wikidata_link()
        if trail_item.osm_wikidata_link_return.single_match:
            trail_item.__ask_user_to_approve_match_from_osm_wikidata_link__()
        else:
            if trail_item.osm_wikidata_link_return.no_match:
                console.print(f"Got no match from OSM Wikidata Link API")
        # Return mutated object
        return trail_item

    @staticmethod
    def __lookup_in_waymarked_trails__(trail_item: TrailItem) -> None:
        trail_item.fetch_and_lookup_from_waymarked_trails_and_present_choice_to_user()
        # if trail_item.questionary_return.quit:
        #     break
        if trail_item.questionary_return.could_not_decide:
            console.print(
                f"Try looking at {trail_item.waymarked_hiking_trails_search_url} "
                f"and see if any fit with {trail_item.wd_url}"
            )
        else:
            trail_item.enrich_wikidata(osm_id_source=OsmIdSource.QUESTIONNAIRE)
        # We don't return anything here because we are done

    def __login_to_wikidata__(self):
        logger.debug(f"Trying to log in to the Wikibase as {config.user_name}")
        self.wbi = WikibaseIntegrator(
            login=Login(user=config.user_name, password=config.bot_password),
        )
