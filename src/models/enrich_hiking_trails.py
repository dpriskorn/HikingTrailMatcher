import logging
from datetime import date, datetime
from typing import Any, Dict

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
    wbi: WikibaseIntegrator | None = None
    items: list[TrailItem] = list()
    sparql_result: Any = dict()
    matched_count: int = 0

    class Config:
        arbitrary_types_allowed = True

    def __get_hiking_trails_missing_osm_id__(self) -> None:
        """Fetch hiking trails missing OSM ID and populate TrailItem objects"""
        # with console.status("Getting hiking paths from WDQS"):
        self.__get_sparql_result__()
        self.__extract_items_from_sparql__()

    def __extract_items_from_sparql__(self) -> None:
        """Create TrailItem objects from SPARQL results including last_update"""
        if self.sparql_result:
            for binding in self.sparql_result["results"]["bindings"]:
                # pprint(binding)
                qid = self.__extract_wcdqs_json_entity_id__(data=binding)
                # Extract last_update if present
                last_update_str = binding.get("lastUpdate", {}).get("value")
                logger.debug(f"got last update string: {last_update_str}")
                last_update = None
                if last_update_str:
                    try:
                        last_update = datetime.fromisoformat(last_update_str)
                    except ValueError:
                        raise Exception(
                            f"Failed to parse last_update for {qid}: {last_update_str}"
                        )
                trail_item = TrailItem(qid=qid, wbi=self.wbi, last_update=last_update)
                # pprint(trail_item)
                # input("press enter to cont")
                self.items.append(trail_item)
        print(f"Got {len(self.items)} TrailItems from WDQS")
        # exit(0)

    @property
    def number_of_items(self) -> int:
        return len(self.items)

    def __iterate_items__(self):
        logger.debug("__iterate_items__: running")
        for count, trail_item in enumerate(self.items, start=1):
            console.print(f"Working on {count}/{self.number_of_items}")
            if trail_item.time_to_check_again():
                logger.debug("It's time to check")
                trail_item = self.__lookup_in_osm_wikidata_link__(trail_item=trail_item)
                if (
                    trail_item.osm_wikidata_link_match_prompt_return == Status.DECLINED
                    or trail_item.osm_wikidata_link_return.no_match is True
                ):
                    logger.info("Falling back to Waymarked Trails API")
                    self.__lookup_in_waymarked_trails__(trail_item=trail_item)
            else:
                logger.info(
                    f"Skipping item with recent last update statement, "
                    f"see {trail_item.qid}"
                )
        logger.debug("Finished iterating over items")

    # def __get_hiking_trails_missing_osm_id__(self) -> None:
    #     with console.status("Getting hiking paths from WDQS"):
    #         self.__get_sparql_result__()
    #         # if config.loglevel == logging.DEBUG:
    #         #     console.print(result)
    #         self.__extract_item_ids__()

    def __get_sparql_result__(self):
        """Get all hiking trails and subtrails in the specified country and
        with labels in the specified language"""
        self.setup_wbi()
        # Support all subclasses of Q2143825 hiking trail
        # minus paths that already have a link to OSM relation
        # minus discontinued hiking paths
        self.sparql_result = execute_sparql_query(
            f"""
            SELECT ?item ?lastUpdate WHERE {{
              ?item wdt:P31/wdt:P279* wd:Q2143825;
                    wdt:P17 wd:{config.country_qid}.

              MINUS {{ ?item wdt:P402 [] }}
              MINUS {{ ?item wdt:P31 wd:Q116787033 }}

              OPTIONAL {{
                ?item p:P9660 ?statement.
                ?statement ps:P9660 wd:Q936.      # must be OpenStreetMap
                ?statement pq:P5017 ?lastUpdate.  # qualifier date
              }}
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

    # @validate_arguments
    # def __extract_item_ids__(self) -> None:
    #     """Yield item ids from a sparql result"""
    #     self.item_ids = []
    #     if self.sparql_result:
    #         for binding in self.sparql_result["results"]["bindings"]:
    #             self.item_ids.append(
    #                 self.__extract_wcdqs_json_entity_id__(data=binding)
    #             )
    #     console.print(f"Got {self.number_of_items} from WDQS")

    def add_osm_property_to_items(self):
        """We setup WBI, lookup first in OSM Wikidata Link
        and then fallback to labelmatching using the
        Waymaked Trails API"""
        # We set up WBI once here and reuse it for every TrailItem
        self.setup_wbi()
        self.__login_to_wikidata__()
        self.__get_hiking_trails_missing_osm_id__()
        self.__iterate_items__()
        self.__add_to_runlog__()

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

    def __lookup_in_waymarked_trails__(self, trail_item: TrailItem) -> None:
        trail_item.fetch_and_lookup_from_waymarked_trails_and_present_choice_to_user()
        if trail_item.questionary_return.skip:
            # return early
            return
        if trail_item.questionary_return.more_information:
            if not trail_item.item:
                raise NoItemError()
            console.print(
                f"Try looking at {trail_item.waymarked_hiking_trails_search_url} "
                f"and see if any fit with {trail_item.item.get_entity_url()}"
            )
            trail_item.try_matching_again()
        trail_item.osm_id_source = OsmIdSource.QUESTIONNAIRE
        trail_item.enrich_wikidata()
        if trail_item.chosen_osm_id:
            self.matched_count += 1
        print(f"Total matched (so far in this session): {self.matched_count}")
        # We don't return anything here because we are done with this item

    def __login_to_wikidata__(self):
        logger.debug(f"Trying to log in to the Wikibase as {config.user_name}")
        self.wbi = WikibaseIntegrator(
            login=Login(user=config.user_name, password=config.bot_password),
        )
        print(f"Successfully logged in to Wikidata as {config.user_name}")

    def __add_to_runlog__(self):
        """Append an entry like "* 2024-02-20 matched 1 trail"
        to the file 'RUNLOG.md' using self.matched_count and the current date"""
        today_str = date.today().isoformat()
        entry = f"* {today_str} matched {self.matched_count} trail"
        if self.matched_count != 1:
            entry += "s"
        entry += f" lang:{config.language_code} country:{config.country_qid}\n"

        with open("RUNLOG.md", "a", encoding="utf-8") as f:
            f.write(entry)
