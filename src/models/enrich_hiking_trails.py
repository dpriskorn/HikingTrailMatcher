import logging
from typing import Any, Dict, List, Optional

from pydantic import validate_arguments
from wikibaseintegrator import WikibaseIntegrator  # type: ignore
from wikibaseintegrator.wbi_helpers import execute_sparql_query  # type: ignore
from wikibaseintegrator.wbi_login import Login  # type: ignore

import config
from src.console import console
from src.enums import OsmIdSource, Status
from src.exceptions import MissingInformationError, NoItemError
from src.models.project_base_model import ProjectBaseModel
from src.models.trail_item import TrailItem

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)


class EnrichHikingTrails(ProjectBaseModel):
    rdf_entity_prefix = "http://www.wikidata.org/entity/"
    wbi: Optional[WikibaseIntegrator]
    item_ids: List[str] = []
    sparql_result: Any

    class Config:
        arbitrary_types_allowed = True

    def __get_hiking_trails_missing_osm_id__(self) -> None:
        with console.status("Getting hiking paths from WDQS"):
            self.__get_sparql_result__()
            # if config.loglevel == logging.DEBUG:
            #     console.print(result)
            self.__extract_item_ids__()

    def __get_sparql_result__(self):
        """Get all hiking trails and subtrails in the specified country and
        with labels in the specified language"""
        self.setup_wbi()
        # Support all subclasses of Q2143825 hiking trail
        self.sparql_result = execute_sparql_query(
            f"""
            SELECT DISTINCT ?item ?itemLabel WHERE {{
              ?item wdt:P31/wdt:P279* wd:Q2143825;
                    wdt:P17 wd:{config.country_qid}.
              minus{{?item wdt:P402 []}}
              # Fetch labels also
              SERVICE wikibase:label
              {{ bd:serviceParam wikibase:language "{config.language_code}". }}
            }}
            """
        )

    @validate_arguments
    def __extract_wcdqs_json_entity_id__(
        self, data: Dict, sparql_variable: str = "item"
    ) -> str:
        """We default to "item" as sparql value because
        it is customary in the Wikibase ecosystem"""
        return str(data[sparql_variable]["value"].replace(self.rdf_entity_prefix, ""))

    @validate_arguments
    def __extract_item_ids__(self) -> None:
        """Yield item ids from a sparql result"""
        self.item_ids = []
        if self.sparql_result:
            for binding in self.sparql_result["results"]["bindings"]:
                self.item_ids.append(
                    self.__extract_wcdqs_json_entity_id__(data=binding)
                )
        console.print(f"Got {self.number_of_items} from WDQS")

    def add_osm_property_to_items(self):
        """We setup WBI, lookup first in OSM Wikidata Link
        and then fallback to labelmatching using the
        Waymaked Trails API"""
        # get all hiking paths in sweden without osm id
        self.__get_hiking_trails_missing_osm_id__()
        # We set up WBI once here and reuse it for every TrailItem
        self.setup_wbi()
        self.__login_to_wikidata__()
        self.__iterate_items__()

    @staticmethod
    def __lookup_in_osm_wikidata_link__(trail_item: TrailItem) -> TrailItem:
        """We lookup in OSM Wikidata Link and mutate the object and then return it"""
        trail_item.lookup_using_osm_wikidata_link()
        if not trail_item.osm_wikidata_link_return:
            raise MissingInformationError()
        if trail_item.osm_wikidata_link_return.single_match:
            logger.info("Got single match")
            trail_item.__ask_user_to_approve_match_from_osm_wikidata_link__()
        else:
            if trail_item.osm_wikidata_link_return.no_match:
                console.print("Got no match from OSM Wikidata Link API")
        # Return mutated object
        return trail_item

    @staticmethod
    def __lookup_in_waymarked_trails__(trail_item: TrailItem) -> None:
        trail_item.fetch_and_lookup_from_waymarked_trails_and_present_choice_to_user()
        # if trail_item.questionary_return.quit:
        #     break
        if trail_item.questionary_return.could_not_decide:
            if not trail_item.item:
                raise NoItemError()
            console.print(
                f"Try looking at {trail_item.waymarked_hiking_trails_search_url} "
                f"and see if any fit with {trail_item.item.get_entity_url()}"
            )
            trail_item.try_matching_again()
        else:
            trail_item.osm_id_source = OsmIdSource.QUESTIONNAIRE
            trail_item.enrich_wikidata()
        # We don't return anything here because we are done

    def __login_to_wikidata__(self):
        logger.debug(f"Trying to log in to the Wikibase as {config.user_name}")
        self.wbi = WikibaseIntegrator(
            login=Login(user=config.user_name, password=config.bot_password),
        )

    @property
    def number_of_items(self) -> int:
        return len(self.item_ids)

    def __iterate_items__(self):
        logger.debug("__iterate_items__: running")
        count = 1
        for qid in self.item_ids:
            console.print(f"Working on {count}/{self.number_of_items}")
            trail_item = TrailItem(qid=qid, wbi=self.wbi)
            if trail_item.time_to_check_again():
                logger.debug("It's time to check")
                trail_item = self.__lookup_in_osm_wikidata_link__(trail_item=trail_item)
                if (
                    trail_item.osm_wikidata_link_match_prompt_return == Status.DECLINED
                    or trail_item.osm_wikidata_link_return.no_match is True
                ):
                    logger.info("Falling back to Waymarked Trails API")
                    # TODO annotate the results here are by downloading their
                    #  geometry from Overpass API and checking if
                    #  each of them are in the right
                    #  1) country 2) region 3) municipality
                    self.__lookup_in_waymarked_trails__(trail_item=trail_item)
            else:
                logger.info(
                    f"Skipping item with recent last update statement, "
                    f"see {trail_item.item.get_entity_url()}"
                )
            count += 1
            logger.debug("end of loop")
