import logging
from enum import Enum
from typing import List, Optional, Dict, Iterable

from pydantic import BaseModel, validate_arguments
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.datatypes import ExternalID
from wikibaseintegrator.wbi_helpers import execute_sparql_query
from rich.console import Console

import config
console = Console()
logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)

class Property(Enum):
    OSM_RELATION_ID = ""

class EnrichHikingTrails(BaseModel):
    rdf_entity_prefix = "http://www.wikidata.org/entity/"

    def __lookup_osm_relation_id__(self, label: str, aliases: List[str]) -> str:
        # lookup in the waymarked trails database

        # present the result to the user (we alway want the first one)
        raise NotImplementedError()

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
                item.add_claims(claims=ExternalID(
                    prop_nr=Property.OSM_RELATION_ID.value,
                    value=osm_id
                ))

    def __get_hiking_trails_missing_osm_id__(self) -> Iterable[str]:
        result = self.__get_sparql_result__()
        if config.loglevel == logging.DEBUG:
            console.print(result)
        return self.__extract_item_ids__(sparql_result=result)

    def __get_sparql_result__(self):
        # For now we limit to swedish trails
        return execute_sparql_query("""
        SELECT DISTINCT ?item ?itemLabel WHERE {
          ?item wdt:P31 wd:Q2143825;
                wdt:P17 wd:Q34.
          minus{?item wdt:P402 []}
          SERVICE wikibase:label { bd:serviceParam wikibase:language "sv,en". } # Hjälper dig hämta etiketten på ditt språk, om inte annat på engelska
        }
        """)

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
