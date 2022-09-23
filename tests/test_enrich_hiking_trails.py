from typing import Iterable
from unittest import TestCase

from src.enrich_hiking_trails import EnrichHikingTrails


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
