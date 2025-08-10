import logging

import config
from src.models.enrich_hiking_trails import EnrichHikingTrails

logging.basicConfig(level=config.loglevel)

print(
    f"Checking trails not updated for {config.max_days_between_new_check} "
    f"days for lang:{config.language_code} and country:{config.country_qid}"
)
eht = EnrichHikingTrails()
eht.add_osm_property_to_items()
