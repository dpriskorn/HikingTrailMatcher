from unittest import TestCase

from wikibaseintegrator import WikibaseIntegrator  # type: ignore

import config
from src.console import console
from src.trail_item import TrailItem
from src.waymarked_result import WaymarkedResult


class TestTrailItem(TestCase):
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
        trail_item.waymarked_results.append(WaymarkedResult(name="test", id=1))
        trail_item.waymarked_results.append(WaymarkedResult(name="test2", id=2))
        trail_item.__convert_waymarked_results_to_choices__()
        assert len(trail_item.choices) == 2
        assert trail_item.choices[0].title == "test (1)"
        assert trail_item.choices[0].value.osm_id == 1

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
