import logging

from OSMPythonTools.api import Api  # noqa: F401 - ensures dep loaded

import config
from src.models.generate_osmchange import OsmChangeGenerator

logging.basicConfig(level=config.loglevel)

if __name__ == "__main__":
    gen = OsmChangeGenerator()
    gen.generate()
