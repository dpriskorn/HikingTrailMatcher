from unittest import TestCase

from wikibaseintegrator import WikibaseIntegrator  # type: ignore

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
