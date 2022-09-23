from src.project_base_model import ProjectBaseModel


class QuestionaryReturn(ProjectBaseModel):
    osm_id: int = 0
    could_not_decide: bool = False
    no_match: bool = False
    quit: bool = False
