from src.wikidata_time_format import WikidataTimeFormat


class TestWikidataTimeFormat:
    def test_day(self):
        wdtf = WikidataTimeFormat()
        assert isinstance(wdtf.day, str)
