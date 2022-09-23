from pydantic import BaseModel
from wikibaseintegrator import wbi_config  # type: ignore


class ProjectBaseModel(BaseModel):
    @staticmethod
    def setup_wbi():
        wbi_config.config[
            "USER_AGENT"
        ] = "hiking-trail-scraper, see https://github.com/dpriskorn/hiking_trail_scraper/"
