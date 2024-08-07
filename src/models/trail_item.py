import logging
import textwrap
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import quote

import pydash
import questionary
import requests
from dateutil.parser import parse  # type: ignore
from dateutil.tz import tzutc  # type: ignore
from pydantic import validate_arguments
from questionary import Choice
from wikibaseintegrator import WikibaseIntegrator  # type: ignore
from wikibaseintegrator.datatypes import ExternalID, Item, Time  # type: ignore
from wikibaseintegrator.entities import ItemEntity  # type: ignore
from wikibaseintegrator.models import Claim, Reference, References  # type: ignore
from wikibaseintegrator.wbi_enums import (  # type: ignore
    ActionIfExists,
    WikibaseDatePrecision,
    WikibaseSnakType,
)

import config
from src.console import console
from src.enums import ItemEnum, OsmIdSource, Property, Status
from src.exceptions import NoItemError, SummaryError
from src.models.osm_wikidata_link_result import OsmWikidataLinkResult
from src.models.osm_wikidata_link_return import OsmWikidataLinkReturn
from src.models.project_base_model import ProjectBaseModel
from src.models.questionary_return import QuestionaryReturn
from src.models.waymarked_result import WaymarkedResult
from src.models.wikidata_time_format import WikidataTimeFormat

logger = logging.getLogger(__name__)
osm_wikidata_link = "OSM Wikidata Link"


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
    last_update: Optional[datetime]
    summary: str = ""
    testing: bool = False

    class Config:
        arbitrary_types_allowed = True

    @property
    def has_osm_way_property(self) -> bool:
        if not self.item:
            raise NoItemError()
        if self.item.claims.get(property="P10689"):
            return True
        else:
            return False

    @property
    def open_in_josm_urls(self):
        if self.osm_ids:
            string_list = [f"r{str(id_)}" for id_ in self.osm_ids]
            return (
                f"http://localhost:8111/load_object?"
                f"new_layer=true&objects={','.join(string_list)}"
            )

    @property
    def waymarked_hiking_trails_search_url(self):
        if self.label:
            return (
                f"https://hiking.waymarkedtrails.org/#search?query={quote(self.label)}"
            )
        else:
            return ""

    def __convert_waymarked_results_to_choices__(self):
        for result in self.waymarked_results:
            # We only want choices which are missing a Wikidata tag
            if not result.already_has_wikidata_tag:
                title = f"{result.name}"
                if result.id:
                    title += f" ({result.id})"
                if result.ref:
                    title += f", ref: {result.ref}"
                if result.number_of_subroutes:
                    title += f", subroutes #: {result.number_of_subroutes}"
                if result.names_of_subroutes_as_string:
                    title += f", subroutes: {result.names_of_subroutes_as_string}"
                # if result.description:
                #     title += f", description: {result.description}"
                if result.group:
                    title += f", group: {result.group}"
                if result.itinerary:
                    title += f", itinerary: {', '.join(result.itinerary)}"
                choice = Choice(
                    title=textwrap.fill(title, 100),
                    value=QuestionaryReturn(osm_id=result.id),
                )
                self.choices.append(choice)

    def __remove_waymaked_result_duplicates__(self):
        self.waymarked_results = list(set(self.waymarked_results))

    # def __clear_attributes__(self):
    #     self.waymarked_results = self.choices = []
    #     self.label = self.qid = self.description = ""
    #     self.item = None

    def __get_item_details__(self):
        """Get the details we need from Wikidata"""
        if not self.already_fetched_item_details:
            if not self.wbi:
                raise ValueError("self.wbi missing")
            self.item = self.wbi.item.get(self.qid)
            if self.item:
                label = self.item.labels.get(config.language_code)
                if label:
                    self.label = label.value
                description = self.item.descriptions.get(config.language_code)
                if description:
                    self.description = description.value
                # aliases = item.aliases.get("sv")
                self.__parse_not_found_in_osm_last_update_statement__()
                self.already_fetched_item_details = True
            else:
                raise Exception("self.item was None")

    def __parse_not_found_in_osm_last_update_statement__(self):
        try:
            osm_claims = self.item.claims.get(property=str(Property.NOT_FOUND_IN.value))
            if len(osm_claims) > 1:
                print(
                    f"More than one not found in-statement found on "
                    f"{self.item.get_entity_url()}. "
                    "Please go to Wikidata and make sure there is only one and rerun."
                )
            else:
                for osm_claim in osm_claims:
                    # logger.debug(osm_claim.mainsnak.datavalue)
                    if osm_claim.mainsnak.snaktype == WikibaseSnakType.KNOWN_VALUE:
                        value_id = pydash.get(osm_claim.mainsnak.datavalue, "value.id")
                        if value_id == ItemEnum.OPENSTREETMAP.value:
                            try:
                                last_update_list = osm_claim.qualifiers.get(
                                    property=str(Property.LAST_UPDATE.value)
                                )
                                if len(last_update_list) > 1:
                                    print(
                                        "Found more than one last update qualifier. "
                                        "Only considering the last one"
                                    )
                                for entry in last_update_list:
                                    date_string = pydash.get(
                                        entry.datavalue, "value.time"
                                    )
                                    logger.info(f"found date: {date_string}")
                                    date = parse(date_string[1:]).astimezone(tzutc())
                                    logger.info(f"found date: {date}")
                                    self.last_update = date
                            except KeyError:
                                logger.info(
                                    "No qualifier found for the not "
                                    "found in OSM-claim. Ignoring it"
                                )
                    else:
                        print("No not found in-property with a know value found")
        except KeyError:
            logger.info("No 'not found in'-claims on this item")

    def __lookup_label_on_waymarked_trails_and_ask_user_to_choose_a_match__(
        self,
    ) -> None:
        if not self.label:
            if not self.item:
                raise NoItemError()
            print(
                f"Skipping {self.item.get_entity_url()} because self.label "
                f"was empty in the chosen language"
            )
            if not self.testing:
                console.input("Press enter to continue")
            return
        if not isinstance(self.label, str):
            raise TypeError("self.label was not a str")
        logger.info(f"looking up: {self.label}")
        self.__lookup_in_the_waymarked_trails_database__(search_term=self.label)
        self.__remove_waymaked_result_duplicates__()
        self.__get_details_from_waymarked_trails__()
        self.__prepare_choices__()
        if len(self.choices) > 2:
            self.questionary_return = self.__ask_question__()
        else:
            if not self.item:
                raise NoItemError()
            console.print(
                f"No choices from Waymarked Trials "
                f"API = no match for "
                f"{self.item.get_entity_url()}"
            )
            return_ = QuestionaryReturn()
            return_.no_match = True
            self.questionary_return = return_

    def __prepare_choices__(self):
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

    def __ask_question__(self) -> QuestionaryReturn:
        """This presents a choice and returns"""
        # present the result to the user to choose from
        if not self.item:
            raise NoItemError()
        return_ = questionary.select(
            (
                f"Which of these match '{self.label}' "
                f"with description '{self.description}'? "
                f"(see {self.item.get_entity_url()})"
            ),
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
            f"https://hiking.waymarkedtrails.org/api/"
            f"v1/list/search?query={search_term}"
        )
        result = requests.get(url=url, timeout=config.request_timeout)
        if result.status_code == 200:
            data = result.json()
            if config.loglevel == logging.DEBUG:
                console.print(data)
            for result in data.get("results"):
                if not isinstance(result, dict):
                    raise TypeError("result was not a dictionary")
                self.waymarked_results.append(WaymarkedResult(**result))

    def __get_details_from_waymarked_trails__(self) -> None:
        [result.get_details() for result in self.waymarked_results]

    def fetch_and_lookup_from_waymarked_trails_and_present_choice_to_user(self):
        """We collect all the information and help
        the user choose the right match"""
        if not self.wbi:
            raise ValueError("self.wbi missing")
        self.__get_item_details__()
        if not self.has_osm_way_property:
            self.__lookup_label_on_waymarked_trails_and_ask_user_to_choose_a_match__()
        else:
            console.print(
                f"Skipping item {self.item.get_entity_url()} "
                f"which already has a OSM way property"
            )

    def enrich_wikidata(self):
        """We enrich Wikidata based on the choice of the user"""
        if self.osm_id_source == OsmIdSource.QUESTIONNAIRE:
            self.chosen_osm_id = self.questionary_return.osm_id
        else:
            self.chosen_osm_id = self.osm_wikidata_link_results[0].id
        if self.item:
            enrich = False
            if self.chosen_osm_id:
                logger.info("OSM ID confirmed")
                self.__add_osm_id_to_item__()
                self.__remove_not_found_in_osm_claim__()
                self.summary = (
                    "Added match to OpenStreetMap via "
                    "the [[Wikidata:Tools/hiking trail matcher"
                    "|hiking trail matcher]]"
                )
                enrich = True
            else:
                if self.questionary_return.no_match is True:
                    console.print("No match")
                    self.__add_or_replace_not_found_in_openstreetmap_claim__()
                    self.__remove_osm_relation_no_value_claim__()
                    self.summary = (
                        "Added not found in OpenStreetMap via "
                        "the [[Wikidata:Tools/hiking trail"
                        " matcher|hiking trail matcher]]"
                    )
                    enrich = True
                else:
                    logging.info("No enriching to be done")
            if enrich is True:
                if config.upload_to_wikidata:
                    if config.validate_before_upload:
                        print("Please validate that this json looks okay")
                        console.print(self.item.get_json())
                        console.input("Press enter to upload or ctrl+c to quit")
                    if self.summary:
                        self.item.write(summary=self.summary)
                        console.print(
                            f"Upload done, see {self.item.get_entity_url()} "
                            f"and https://hiking.waymarkedtrails.org/"
                            f"#route?id={self.questionary_return.osm_id}"
                        )
                    else:
                        raise SummaryError()
                else:
                    console.print(
                        "Not uploading because config.upload_to_wikidata is False"
                    )

    @staticmethod
    def __last_update_today_statement__():
        time_object = WikidataTimeFormat()
        return Time(
            prop_nr=Property.LAST_UPDATE.value,
            time=time_object.day,
            precision=WikibaseDatePrecision.DAY,
        )

    @staticmethod
    def __point_in_time_today_statement__():
        time_object = WikidataTimeFormat()
        return Time(
            prop_nr=Property.POINT_IN_TIME.value,
            time=time_object.day,
            precision=WikibaseDatePrecision.DAY,
        )

    @staticmethod
    def __retrieved_today_statement__():
        time_object = WikidataTimeFormat()
        return Time(
            prop_nr=Property.RETRIEVED.value,
            time=time_object.day,
            precision=WikibaseDatePrecision.DAY,
        )

    def lookup_using_osm_wikidata_link(self) -> None:
        """Lookup first in OSM
        See documentation here https://osm.wikidata.link/tagged/"""
        url = f"https://osm.wikidata.link/tagged/api/item/{self.qid}"
        result = requests.get(url, timeout=config.request_timeout)
        if result.status_code == 200:
            data = result.json()
            if config.loglevel == logging.DEBUG:
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
                    self.__handle_multiple_matches__()
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
            question = (
                f"Does the above match '{self.label}' "
                f"(description missing) in Wikidata?(Y/n)"
            )
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

    def __handle_multiple_matches__(self):
        # we got multiple matches so we ask the user to fix the situation in JOSM
        console.print(
            f"We got {len(self.osm_ids)} matches from {osm_wikidata_link}. "
            f"Please download the relations in JOSM and ensure 1-1 link. "
            f"Click here to open in JOSM with remote control "
            f"{self.open_in_josm_urls}"
        )
        if not self.testing:
            console.input("Press enter to continue")
        self.osm_wikidata_link_return = OsmWikidataLinkReturn(multiple_matches=True)

    def __handle_single_match__(self):
        # We only got one relation that matches.
        logger.info("We only got one relation that matches")
        self.osm_wikidata_link_return = OsmWikidataLinkReturn(single_match=True)

    def __add_osm_id_to_item__(self):
        console.print(
            f"Got match, adding " f"OSM relation id = {self.chosen_osm_id} to WD"
        )
        if self.osm_id_source == OsmIdSource.QUESTIONNAIRE:
            self.item.add_claims(
                claims=ExternalID(
                    prop_nr=Property.OSM_RELATION_ID.value,
                    value=str(self.chosen_osm_id),
                    references=[self.__create_heuristic_reference__()],
                ),
                # Replace no-value statement if it exists
                action_if_exists=ActionIfExists.REPLACE_ALL,
            )
        else:
            # We got it from OSM Wikidata Link so add a reference
            reference = Reference()
            reference.add(
                Item(
                    prop_nr=Property.STATED_IN.value,
                    value=str(ItemEnum.OPENSTREETMAP.value),
                )
            )
            reference.add(self.__retrieved_today_statement__())
            self.item.add_claims(
                claims=ExternalID(
                    prop_nr=Property.OSM_RELATION_ID.value,
                    value=str(self.chosen_osm_id),
                    references=References().add(reference=reference),
                ),
                # Replace no-value statement if it exists
                action_if_exists=ActionIfExists.REPLACE_ALL,
            )

    def time_to_check_again(self, testing: bool = False) -> bool:
        if not testing:
            self.__get_item_details__()
        if self.last_update:
            latest_date_for_new_check = datetime.now(tz=tzutc()) - timedelta(
                days=config.max_days_between_new_check
            )
            if latest_date_for_new_check > self.last_update:
                # Maximum number of days passed, let's check again
                logger.info("Time to check again")
                return True
            else:
                return False
        else:
            logger.info(
                "The item is missing a not found in osm claim "
                "with a last update qualifier statement"
            )
            return True

    def __add_or_replace_not_found_in_openstreetmap_claim__(self):
        claim = Item(
            prop_nr=Property.NOT_FOUND_IN.value,
            value=ItemEnum.OPENSTREETMAP.value,
            qualifiers=[self.__last_update_today_statement__()],
            references=[self.__create_heuristic_reference__()],
        )
        # We want to replace the current statement to avoid a long list of values
        # which have no value.
        self.item.add_claims(claims=claim, action_if_exists=ActionIfExists.REPLACE_ALL)

    @staticmethod
    def __based_on_heuristic_lookup__() -> Claim:
        return Item(
            prop_nr=Property.BASED_ON_HEURISTIC.value,
            value=ItemEnum.LOOKUP_IN_WAYMARKED_TRAILS_API.value,
        )

    @staticmethod
    def __based_on_heuristic_user_validation__() -> Claim:
        return Item(
            prop_nr=Property.BASED_ON_HEURISTIC.value,
            value=ItemEnum.USER_VALIDATION.value,
        )

    def __create_heuristic_reference__(self):
        return (
            Reference()
            .add(self.__based_on_heuristic_lookup__())
            .add(self.__based_on_heuristic_user_validation__())
        )

    def __remove_osm_relation_no_value_claim__(self):
        """This is a cleanup of a not so nice way to model it used earlier"""
        # Remove no-value claim
        try:
            if self.item.claims.get(Property.OSM_RELATION_ID.value):
                logger.info(
                    "Removing OSM relation id = no-value claim because "
                    "it was not a way to model the check that the community liked best"
                )
                self.item.claims.remove(Property.OSM_RELATION_ID.value)
        except KeyError:
            logger.debug("No OSM_RELATION_ID found on this item to clean up")

    def __remove_not_found_in_osm_claim__(self):
        try:
            claims = self.item.claims.get(Property.NOT_FOUND_IN.value)
            if claims:
                if len(claims) > 1:
                    # todo iterate and remove only the right one
                    console.print(claims)
                    raise NotImplementedError(
                        "removing only one of "
                        "multiple not-found-in-"
                        "statements is not supported yet"
                    )
                else:
                    logger.info("Removing 'not found in'-claim")
                    self.item.claims.remove(Property.OSM_RELATION_ID.value)
        except KeyError:
            logger.debug("No NOT_FOUND_IN found on this item to remove")

    def try_matching_again(self):
        if self.questionary_return.could_not_decide is True:
            result = questionary.select(
                "Do you want to match again after manually ",
                choices=[
                    Choice(title="Yes", value=True),
                    Choice(title="No", value=False),
                ],
            ).ask()
            if result:
                self.questionary_return = self.__ask_question__()
