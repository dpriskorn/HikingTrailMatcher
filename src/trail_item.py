import logging
from typing import Dict, List, Optional

import requests
from pydantic import validate_arguments
from questionary import Choice
from wikibaseintegrator import WikibaseIntegrator  # type: ignore
from wikibaseintegrator.datatypes import ExternalID, Item, Time  # type: ignore
from wikibaseintegrator.entities import ItemEntity  # type: ignore
from wikibaseintegrator.models import Reference, References
from wikibaseintegrator.wbi_enums import (  # type: ignore
    WikibaseDatePrecision,
    WikibaseSnakType,
)

import config
from src.console import console
from src.enums import ItemEnum, OsmIdSource, Property, Status
from src.osm_wikidata_link_result import OsmWikidataLinkResult
from src.osm_wikidata_link_return import OsmWikidataLinkReturn
from src.project_base_model import ProjectBaseModel
from src.questionary_return import QuestionaryReturn
from src.waymarked_result import WaymarkedResult
from src.wikidata_time_format import WikidataTimeFormat

logger = logging.getLogger(__name__)
osm_wikidata_link = "OSM Wikidata Link"


class DebugExit(BaseException):
    pass


class TrailItem(ProjectBaseModel):
    waymarked_results: List[WaymarkedResult] = []
    choices: List[Choice] = []
    label: str = ""
    item: Optional[ItemEntity]
    description: str = ""
    wbi: WikibaseIntegrator
    qid: str = ""
    questionary_return: QuestionaryReturn = QuestionaryReturn()
    osm_ids: List[str] = []
    osm_wikidata_link_return: OsmWikidataLinkReturn = OsmWikidataLinkReturn()
    osm_wikidata_link_results: List[OsmWikidataLinkResult] = []
    osm_wikidata_link_match_prompt_return: Optional[Status]
    osm_wikidata_link_data: Dict = dict()
    already_fetched_item_details: bool = False
    osm_id_source: Optional[OsmIdSource]
    chosen_osm_id: int = 0

    class Config:
        arbitrary_types_allowed = True

    @property
    def open_in_josm(self):
        if self.osm_ids:
            string_list = [str(id) for id in self.osm_ids]
            return (
                f"http://localhost:8111/load_object?"
                f"new_layer=true&objects={','.join(string_list)}"
            )

    @property
    def waymarked_hiking_trails_search_url(self):
        if self.label:
            return f"https://hiking.waymarkedtrails.org/#search?query={self.label}"
        else:
            return ""

    @property
    def wd_url(self):
        if self.qid:
            return f"https://www.wikidata.org/wiki/{self.qid}"
        else:
            return ""

    def __convert_waymarked_results_to_choices__(self):
        for result in self.waymarked_results:
            title = f"{result.name}"
            if result.id:
                title += f" ({result.id})"
            if result.ref:
                title += f", ref: {result.ref}"
            if result.group:
                title += f", group: {result.group}"
            if result.itinerary:
                title += f", itinerary: {', '.join(result.itinerary)}"
            choice = Choice(title=title, value=QuestionaryReturn(osm_id=result.id))
            self.choices.append(choice)

    def __remove_waymaked_result_duplicates__(self):
        self.waymarked_results = list(set(self.waymarked_results))

    # def __clear_attributes__(self):
    #     self.waymarked_results = self.choices = []
    #     self.label = self.qid = self.description = ""
    #     self.item = None

    def __get_item_details__(self):
        if not self.already_fetched_item_details:
            if not self.wbi:
                raise ValueError("self.wbi missing")
            self.item = self.wbi.item.get(self.qid)
            if self.item:
                # We hardcode swedish for now
                label = self.item.labels.get("sv")
                if label:
                    self.label = label.value
                description = self.item.descriptions.get("sv")
                if description:
                    self.description = description.value
                # aliases = item.aliases.get("sv")
                self.already_fetched_item_details = True
            else:
                raise Exception("self.item was None")

    @validate_arguments()
    def __lookup_label_on_waymarked_trails_and_ask_user_to_choose_a_match__(
        self,
    ) -> None:
        if not self.label:
            raise ValueError("self.label was empty")
        if not isinstance(self.label, str):
            raise TypeError("self.label was not a str")
        logger.info(f"looking up: {self.label}")
        self.__lookup_in_the_waymarked_trails_database__(search_term=self.label)
        self.__prepare_choices__()
        self.questionary_return = self.__ask_question__()

    def __prepare_choices__(self):
        self.__remove_waymaked_result_duplicates__()
        self.__convert_waymarked_results_to_choices__()
        self.choices.append(
            Choice(
                title="Unable to decide whether these match",
                value=QuestionaryReturn(could_not_decide=True),
            )
        )
        self.choices.append(
            Choice(title="None of these match", value=QuestionaryReturn(no_match=True))
        )

    @validate_arguments()
    def __ask_question__(self) -> QuestionaryReturn:
        # present the result to the user to choose from
        import questionary

        return_ = questionary.select(
            f"Which of these match '{self.label}' with description '{self.description}'?",
            choices=self.choices,
        ).ask()  # returns value of selection or None if user cancels
        if isinstance(return_, QuestionaryReturn):
            return return_
        else:
            exit()
            # raise TypeError("not a QuestionaryReturn")

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
            if config.loglevel == logging.DEBUG:
                console.print(data)
            for result in data.get("results"):
                if not isinstance(result, dict):
                    raise TypeError("result was not a dictionary")
                self.waymarked_results.append(WaymarkedResult(**result))

    def fetch_and_lookup_from_waymarked_trails_and_present_choice_to_user(self):
        """We collect all the information and help the user choose the right match"""
        if not self.wbi:
            raise ValueError("self.wbi missing")
        self.__get_item_details__()
        self.__lookup_label_on_waymarked_trails_and_ask_user_to_choose_a_match__()

    # @validate_arguments()
    def enrich_wikidata(self):
        """We enrich Wikidata based on the choice of the user"""
        if self.osm_id_source == OsmIdSource.QUESTIONNAIRE:
            self.chosen_osm_id = self.questionary_return.osm_id
        else:
            self.chosen_osm_id = self.osm_wikidata_link_results[0].id
        if self.item:
            if self.chosen_osm_id:
                self.__add_osm_id_to_item__()
            else:
                console.print("No match, adding no value = true to WD")
                claim = ExternalID(
                    prop_nr=Property.OSM_RELATION_ID.value,
                    value=None,
                    qualifiers=[self.__time_today_statement__()],
                )
                # Not documented, see https://github.com/LeMyst/WikibaseIntegrator/blob/9bc58824d2def664c950d53cca845524b93ec051/test/test_wbi_core.py#L199
                claim.mainsnak.snaktype = WikibaseSnakType.NO_VALUE
                self.item.add_claims(claims=claim)
            if config.upload_to_wikidata:
                self.item.write(
                    summary="Added match to OSM via the [[Wikidata:Tools/hiking trail_item matcher|hiking trail_item matcher]]"
                )
                console.print(f"Upload done, see {self.wd_url}")

    @staticmethod
    def __time_today_statement__():
        time_object = WikidataTimeFormat()
        return Time(
            prop_nr=Property.POINT_IN_TIME.value,
            time=time_object.day,
            precision=WikibaseDatePrecision.DAY,
        )

    def lookup_using_osm_wikidata_link(self) -> None:
        """Lookup first in OSM
        See documentation here https://osm.wikidata.link/tagged/"""
        url = f"https://osm.wikidata.link/tagged/api/item/{self.qid}"
        result = requests.get(url)
        if result.status_code == 200:
            data = result.json()
            console.print(data)
            self.osm_wikidata_link_data = data
            self.__parse_response_from_osm_wikidata_link__()
        else:
            raise Exception(f"Got {result.status_code} from the API")

    def __parse_response_from_osm_wikidata_link__(self):
        osm_objects = self.osm_wikidata_link_data.get("osm")
        if osm_objects:
            # We got data about an OSM object having this QID
            # It could be a node or a way which we do not care about
            if len(osm_objects) > 0:
                # Gather the information we need
                self.__populate_osm_ids__()
                # Act on it
                if len(self.osm_ids) > 1:
                    self.__hanndle_multiple_matches__()
                elif len(self.osm_ids) == 1:
                    self.__handle_single_match__()
                else:
                    # We got no osm_ids ergo the osm_object we got was not a relation
                    self.osm_wikidata_link_return = OsmWikidataLinkReturn(no_match=True)
        else:
            self.osm_wikidata_link_return = OsmWikidataLinkReturn(no_match=True)

    def __ask_user_to_approve_match_from_osm_wikidata_link__(self) -> None:
        self.__get_item_details__()
        # inform user that we match based on
        match = self.osm_wikidata_link_results[0]
        console.print(
            "Match found via OSM Wikidata Link:\n"
            f"Id: {match.id}\n"
            f"Name: {match.tags.name}\n"
            f"Url: {self.osm_url(osm_id=match.id)}"
        )
        if self.description:
            question = (
                f"Does the above match '{self.label}' with the description "
                f"'{self.description}' in Wikidata?(Y/n)"
            )
        else:
            question = f"Does the above match '{self.label}' (description missing) in Wikidata?(Y/n)"
        answer = console.input(question)
        if answer == "" or answer.lower() == "y":
            # we got enter/yes
            self.osm_id_source = OsmIdSource.OSM_WIKIDATA_LINK
            self.enrich_wikidata()
            self.osm_wikidata_link_match_prompt_return = Status.ACCEPTED
        else:
            self.osm_wikidata_link_match_prompt_return = Status.DECLINED

    @staticmethod
    def osm_url(osm_id: int = 0):
        if osm_id:
            return f"https://www.openstreetmap.org/relation/{osm_id}"
        else:
            return ""

    def __populate_osm_ids__(self):
        """We only care about relations so we discard everything else"""
        osm_objects = self.osm_wikidata_link_data.get("osm")
        for item in osm_objects:
            if item.get("type") == "relation":
                self.osm_wikidata_link_results.append(OsmWikidataLinkResult(**item))
                # We store the ids also in a list to easier handle
                # the opening in JOSM and logic here
                self.osm_ids.append(item.get("id"))

    def __hanndle_multiple_matches__(self):
        # we got multiple matches so we ask the user to fix the situation in JOSM
        console.print(
            f"We got {len(self.osm_ids)} matches from {osm_wikidata_link}. "
            f"Please download the relations in JOSM and ensure 1-1 link. "
            f"Click here to open in JOSM with remote control "
            f"{self.open_in_josm}"
        )
        self.osm_wikidata_link_return = OsmWikidataLinkReturn(multiple_matches=True)

    def __handle_single_match__(self):
        # We only got one relation that matches.
        logger.info("We only got one relation that matches")
        self.osm_wikidata_link_return = OsmWikidataLinkReturn(single_match=True)

    def __add_osm_id_to_item__(self):
        console.print(f"Got match, adding OSM = {self.chosen_osm_id} to WD")
        if self.osm_id_source == OsmIdSource.QUESTIONNAIRE:
            self.item.add_claims(
                claims=ExternalID(
                    prop_nr=Property.OSM_RELATION_ID.value,
                    value=str(self.chosen_osm_id),
                )
            )
        else:
            # We got it from OSM Wikidata Link so add a reference
            reference = Reference()
            reference.add(
                Item(
                    prop_nr=Property.STATED_IN, value=str(ItemEnum.OPENSTREETMAP.value)
                )
            )
            reference.add(self.__time_today_statement__())
            self.item.add_claims(
                claims=ExternalID(
                    prop_nr=Property.OSM_RELATION_ID.value,
                    value=str(self.chosen_osm_id),
                    references=References().add(reference=reference),
                )
            )
