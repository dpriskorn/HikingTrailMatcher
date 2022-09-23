from pydantic import BaseModel
from wikibaseintegrator import wbi_config  # type: ignore

import config


class ProjectBaseModel(BaseModel):
    @staticmethod
    def setup_wbi():
        wbi_config.config[
            "USER_AGENT"
        ] = config.user_agent
