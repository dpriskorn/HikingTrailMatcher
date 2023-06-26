from pydantic import BaseModel


class Subroute(BaseModel):
    name: str = ""
    id: int
    ref: str = ""
