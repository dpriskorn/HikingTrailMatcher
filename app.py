import logging

import config
from src.models.enrich_hiking_trails import EnrichHikingTrails

logging.basicConfig(level=config.loglevel)

eht = EnrichHikingTrails()
eht.add_osm_property_to_items()
