from src.models.project_base_model import ProjectBaseModel


class QuestionaryReturn(ProjectBaseModel):
    osm_id: int = 0
    more_information: bool = False
    no_match: bool = False
    skip: bool = False
