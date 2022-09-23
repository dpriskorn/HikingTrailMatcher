from typing import Iterable
from unittest import TestCase

from src.enrich_hiking_trails import EnrichHikingTrails
from src.waymarked_result import WaymarkedResult


class TestEnrichHikingTrails(TestCase):
    def test_add_osm_property_to_items(self):
        eht = EnrichHikingTrails()
        with self.assertRaises(NotImplementedError):
            eht.add_osm_property_to_items()

    def test___get_hiking_trails_missing_osm_id__(self):
        eht = EnrichHikingTrails()
        qids = eht.__get_hiking_trails_missing_osm_id__()
        assert isinstance(qids, Iterable)
        for qid in qids:
            assert isinstance(qid, str)

    def test___lookup_in_the_waymarked_trails_database__(self):
        eht = EnrichHikingTrails()
        eht.__lookup_in_the_waymarked_trails_database__(search_term="Kungsleden")
        assert len(eht.waymarked_results) == 2
        assert eht.waymarked_results[0].id == 254324

    def test_remove_duplicates(self):
        eht = EnrichHikingTrails()
        eht.waymarked_results.append(WaymarkedResult(name="test", id=1))
        eht.waymarked_results.append(WaymarkedResult(name="test", id=1))
        assert len(eht.waymarked_results) == 2
        eht.__remove_waymaked_result_duplicates__()
        assert len(eht.waymarked_results) == 1
