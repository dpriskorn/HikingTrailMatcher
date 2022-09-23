from typing import List

from pydantic import BaseModel


class WaymarkedResult(BaseModel):
    """Models the JSON response from the Waymarked Trails API"""

    id: int
    group: str = ""
    name: str
    ref: str = ""
    itinerary: List[str] = []

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return self.id
