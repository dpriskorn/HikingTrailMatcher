from unittest import TestCase

from wikibaseintegrator import WikibaseIntegrator  # type: ignore

from src.console import console
from src.trail_item import TrailItem
from src.waymarked_result import WaymarkedResult


class TestTrailItem(TestCase):
    def test___lookup_in_the_waymarked_trails_database__(self):
        eht = TrailItem(wbi=WikibaseIntegrator())
        eht.__lookup_in_the_waymarked_trails_database__(search_term="Kungsleden")
        assert len(eht.waymarked_results) == 2
        assert eht.waymarked_results[0].id == 254324

    def test_remove_duplicates(self):
        eht = TrailItem(wbi=WikibaseIntegrator())
        eht.waymarked_results.append(WaymarkedResult(name="test", id=1))
        eht.waymarked_results.append(WaymarkedResult(name="test", id=1))
        assert len(eht.waymarked_results) == 2
        eht.__remove_waymaked_result_duplicates__()
        assert len(eht.waymarked_results) == 1

    def test_convert_to_choices(self):
        eht = TrailItem(wbi=WikibaseIntegrator())
        eht.waymarked_results.append(WaymarkedResult(name="test", id=1))
        eht.waymarked_results.append(WaymarkedResult(name="test2", id=2))
        eht.__convert_waymarked_results_to_choices__()
        assert len(eht.choices) == 2
        assert eht.choices[0].title == "test (1)"
        assert eht.choices[0].value.osm_id == 1

    def test_lookup_in_osm_wikidata_link_api_no_match(self):
        eht = TrailItem(wbi=WikibaseIntegrator(), qid="Q820225")
        eht.__lookup_in_osm_wikidata_link_api__()
        assert eht.osm_wikidata_link_return.no_match is True
        assert len(eht.osm_wikidata_link_results) == 0

    def test_lookup_in_osm_wikidata_link_api_single_match_node(self):
        eht = TrailItem(wbi=WikibaseIntegrator(), qid="Q130177")
        eht.__lookup_in_osm_wikidata_link_api__()
        assert eht.osm_wikidata_link_return.no_match is True
        assert len(eht.osm_wikidata_link_results) == 0

    def test_lookup_in_osm_wikidata_link_api_single_match_relation(self):
        eht = TrailItem(wbi=WikibaseIntegrator(), qid="Q59780")
        eht.__lookup_in_osm_wikidata_link_api__()
        assert eht.osm_wikidata_link_return.single_match is True
        assert len(eht.osm_wikidata_link_results) == 1

    def test_lookup_in_osm_wikidata_link_api_multiple_relations(self):
        eht = TrailItem(wbi=WikibaseIntegrator(), qid="Q151653")
        eht.__lookup_in_osm_wikidata_link_api__()
        console.print(eht.osm_wikidata_link_return.dict())
        assert eht.osm_wikidata_link_return.multiple_matches is True
