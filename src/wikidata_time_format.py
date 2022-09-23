from datetime import datetime

class WikidataTimeFormat:
    """Takes a datetime as input and outputs the chosen precision"""

    datetime_: datetime = datetime.today()

    @property
    def day(self):
        return datetime.strftime(self.datetime, "+%Y-%m-%dT00:00:00Z")

    def __init__(self, datetime_: datetime = None):
        if datetime is None:
            self.datetime = datetime(datetime_.today())
            raise ValueError("Got no datetime")
        else:
            self.datetime_ = datetime_
