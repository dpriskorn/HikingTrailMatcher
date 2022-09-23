import logging
from typing import List, Optional

import requests
from pydantic import validate_arguments
from questionary import Choice
from wikibaseintegrator import WikibaseIntegrator  # type: ignore
from wikibaseintegrator.datatypes import ExternalID, Time  # type: ignore
from wikibaseintegrator.entities import ItemEntity  # type: ignore
from wikibaseintegrator.wbi_enums import (  # type: ignore
    WikibaseDatePrecision,
    WikibaseSnakType,
)

import config
from src.console import console
from src.enums import Property
from src.project_base_model import ProjectBaseModel
from src.questionary_return import QuestionaryReturn
from src.waymarked_result import WaymarkedResult
from src.wikidata_time_format import WikidataTimeFormat

logger = logging.getLogger(__name__)


class TrailItem(ProjectBaseModel):
    waymarked_results: List[WaymarkedResult] = []
    choices: List[Choice] = []
    label: str = ""
    item: Optional[ItemEntity]
    description: str = ""
    wbi: WikibaseIntegrator
    qid: str = ""
    return_: QuestionaryReturn = QuestionaryReturn()

    class Config:
        arbitrary_types_allowed = True

    @property
    def osm_url(self):
        if self.return_.osm_id:
            return f"https://www.openstreetmap.org/relation/{self.return_.osm_id}"
        else:
            return ""

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

    def __get_item_information__(self):
        if self.wbi:
            self.item = self.wbi.item.get(self.qid)
            if self.item:
                # TODO avoid hardcoding swedish
                label = self.item.labels.get("sv")
                if label:
                    self.label = label.value
                description = self.item.descriptions.get("sv")
                if description:
                    self.description = description.value
                # aliases = item.aliases.get("sv")

    @validate_arguments()
    def __lookup_osm_relation_id_and_ask_user_to_choose_a_match__(self) -> None:
        if not self.label:
            raise ValueError("self.label was empty")
        if not isinstance(self.label, str):
            raise TypeError("self.label was not a str")
        logger.info(f"looking up: {self.label}")
        self.__lookup_in_the_waymarked_trails_database__(search_term=self.label)
        self.__prepare_choices__()
        self.return_ = self.__ask_question__()

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
            #raise TypeError("not a QuestionaryReturn")

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
                if not isinstance(result, dict):
                    raise TypeError("result was not a dictionary")
                self.waymarked_results.append(WaymarkedResult(**result))

    def fetch_and_lookup_and_present_choice_to_user(self):
        self.__get_item_information__()
        self.__lookup_osm_relation_id_and_ask_user_to_choose_a_match__()

    def enrich_wikidata(self):
        osm_id = self.return_.osm_id
        if self.item:
            if osm_id:
                console.print(f"Got match, adding OSM = {osm_id} to WD")
                self.item.add_claims(
                    claims=ExternalID(
                        prop_nr=Property.OSM_RELATION_ID.value,
                        value=str(osm_id),
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
                self.item.add_claims(claims=claim)
            if config.upload_to_wikidata:
                self.item.write()

    @staticmethod
    def __time_today_statement__():
        time_object = WikidataTimeFormat()
        return Time(
            prop_nr=Property.POINT_IN_TIME.value,
            time=time_object.day,
            precision=WikibaseDatePrecision.DAY,
        )

