from datetime import datetime
from unittest import TestCase

from dateutil.tz import tzutc
from wikibaseintegrator import WikibaseIntegrator  # type: ignore

import config
from src.console import console
from src.models.trail_item import TrailItem
from src.models.waymarked_result import WaymarkedResult


class TestTrailItem(TestCase):
    last_update_test_item = (
        "Q7407905"  # small trail in USA which I hope won't change much
    )

    def test___lookup_in_the_waymarked_trails_database__(self):
        trail_item = TrailItem(wbi=WikibaseIntegrator())
        trail_item.__lookup_in_the_waymarked_trails_database__(search_term="Kungsleden")
        assert len(trail_item.waymarked_results) == 2
        assert trail_item.waymarked_results[0].id == 254324

    def test_remove_duplicates(self):
        trail_item = TrailItem(wbi=WikibaseIntegrator())
        trail_item.waymarked_results.append(WaymarkedResult(name="test", id=1))
        trail_item.waymarked_results.append(WaymarkedResult(name="test", id=1))
        assert len(trail_item.waymarked_results) == 2
        trail_item.__remove_waymaked_result_duplicates__()
        assert len(trail_item.waymarked_results) == 1

    def test_convert_to_choices(self):
        trail_item = TrailItem(wbi=WikibaseIntegrator())
        trail_item.waymarked_results.append(WaymarkedResult(name="test", id=10528596))
        trail_item.__convert_waymarked_results_to_choices__()
        assert len(trail_item.choices) == 1
        assert trail_item.choices[0].title == "test (10528596)"
        assert trail_item.choices[0].value.osm_id == 10528596

    def test_lookup_in_osm_wikidata_link_api_no_match(self):
        trail_item = TrailItem(wbi=WikibaseIntegrator(), qid="Q820225")
        trail_item.lookup_using_osm_wikidata_link()
        # console.print(trail_item.osm_wikidata_link_return)
        assert trail_item.osm_wikidata_link_return.no_match is True
        assert len(trail_item.osm_wikidata_link_results) == 0

    def test_lookup_in_osm_wikidata_link_api_single_match_node(self):
        trail_item = TrailItem(wbi=WikibaseIntegrator(), qid="Q130177")
        trail_item.lookup_using_osm_wikidata_link()
        assert trail_item.osm_wikidata_link_return.no_match is True
        assert len(trail_item.osm_wikidata_link_results) == 0

    def test_lookup_in_osm_wikidata_link_api_single_match_relation(self):
        trail_item = TrailItem(wbi=WikibaseIntegrator(), qid="Q59780")
        trail_item.lookup_using_osm_wikidata_link()
        assert trail_item.osm_wikidata_link_return.single_match is True
        assert len(trail_item.osm_wikidata_link_results) == 1

    def test_lookup_in_osm_wikidata_link_api_multiple_relations(self):
        trail_item = TrailItem(wbi=WikibaseIntegrator(), qid="Q151653")
        trail_item.lookup_using_osm_wikidata_link()
        console.print(trail_item.osm_wikidata_link_return.dict())
        assert trail_item.osm_wikidata_link_return.multiple_matches is True

    def test___get_item_details__(self):
        trail_item = TrailItem(wbi=WikibaseIntegrator(), qid="Q151653")
        # Get english
        config.language_code = "en"
        trail_item.__get_item_details__()
        assert trail_item.label == "E1 European long distance path"
        assert trail_item.description == "walking path"
        trail_item.label = trail_item.description = ""
        config.language_code = "sv"
        trail_item.__get_item_details__()
        assert trail_item.label == ""
        assert trail_item.description == ""

    def test___get_item_details_no_value(self):
        trail_item = TrailItem(wbi=WikibaseIntegrator(), qid=self.last_update_test_item)
        trail_item.__get_item_details__()
        assert trail_item.last_update is not None
        print(trail_item.last_update)
        assert (
            datetime(day=23, month=6, year=2023, tzinfo=tzutc())
            == trail_item.last_update
        )

    def test_last_update_statement_exists(self):
        trail_item = TrailItem(wbi=WikibaseIntegrator(), qid=self.last_update_test_item)
        trail_item.__get_item_details__()
        assert trail_item.last_update is not None

    def test_time_to_check_again(self):
        trail_item = TrailItem(wbi=WikibaseIntegrator(), qid=self.last_update_test_item)
        assert trail_item.time_to_check_again() is False

    def test_time_to_check_again_lets_check(self):
        trail_item = TrailItem(wbi=WikibaseIntegrator())
        trail_item.last_update = datetime(day=24, month=9, year=2020, tzinfo=tzutc())
        assert trail_item.time_to_check_again(testing=True) is True

    def test_has_osm_way_property_false(self):
        trail_item = TrailItem(wbi=WikibaseIntegrator(), qid=self.last_update_test_item)
        trail_item.__get_item_details__()
        assert trail_item.has_osm_way_property is False

    def test_has_osm_way_property_true(self):
        trail_item = TrailItem(wbi=WikibaseIntegrator(), qid="Q1692894")
        trail_item.__get_item_details__()
        assert trail_item.has_osm_way_property is True
