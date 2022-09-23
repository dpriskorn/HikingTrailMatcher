from datetime import datetime

from pydantic import BaseModel


class WikidataTimeFormat(BaseModel):
    """Takes a datetime as input and outputs the chosen precision"""

    datetime_: datetime = datetime.today()

    @property
    def day(self):
        return datetime.strftime(self.datetime_, "+%Y-%m-%dT00:00:00Z")

