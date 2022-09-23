from pydantic import BaseModel


class WaymarkedResult(BaseModel):
    id: int
    name: str

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return self.id