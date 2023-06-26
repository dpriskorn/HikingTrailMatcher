from unittest import TestCase

import config
from src.models.enrich_hiking_trails import EnrichHikingTrails


class TestEnrichHikingTrails(TestCase):
    # def test_add_osm_property_to_items(self):
    #     eht = EnrichHikingTrails()
    #     with self.assertRaises(NotImplementedError):
    #         eht.add_osm_property_to_items()

    def test___get_hiking_trails_missing_osm_id__(self):
        eht = EnrichHikingTrails()
        eht.__get_hiking_trails_missing_osm_id__()
        assert eht.number_of_items > 0

    def test_setup_wbi(self):
        eht = EnrichHikingTrails()
        eht.setup_wbi()

    def test___get_en_usa_hiking_trails_missing_osm_id__(self):
        eht = EnrichHikingTrails()
        # This controls which hiking trails to fetch and work on
        config.language_code = "en"
        config.country_qid = "Q30"
        eht.__get_hiking_trails_missing_osm_id__()
        assert eht.number_of_items > 0

    def test___get_sv_sweden_hiking_trails_missing_osm_id__(self):
        eht = EnrichHikingTrails()
        # This controls which hiking trails to fetch and work on
        config.language_code = "sv"
        config.country_qid = "Q34"
        eht.__get_hiking_trails_missing_osm_id__()
        assert eht.number_of_items > 0
