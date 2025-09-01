from unittest import TestCase

from src.models.waymarked_result import WaymarkedResult


class TestWaymarkedResult(TestCase):
    def test_waymarked_result_all_supported_fields(self):
        data = {
            "type": "relation",
            "id": 241043,
            "name": "Upplandsleden",
            "group": "NAT",
            "itinerary": ["Knivsta", "Forsby"],
            "symbol_description": "orange bar",
            "symbol_id": "osmc_NAT_white_bar_orange",
        }
        wr = WaymarkedResult(**data)
        assert wr.name == "Upplandsleden"
        assert wr.id == 241043
        assert wr.group == "NAT"
        assert len(wr.itinerary) == 2
        assert wr.itinerary[0] == "Knivsta"

    def test_waymarked_result_no_itinerary(self):
        data = {
            "type": "relation",
            "id": 241043,
            "name": "Upplandsleden",
            "group": "NAT",
            "symbol_description": "orange bar",
            "symbol_id": "osmc_NAT_white_bar_orange",
        }
        wr = WaymarkedResult(**data)
        assert wr.name == "Upplandsleden"
        assert wr.id == 241043
        assert len(wr.itinerary) == 0

    # def test_get_details(self):
    #     data = {
    #         "type": "relation",
    #         "id": 241043,
    #         "name": "Upplandsleden",
    #         "group": "NAT",
    #         "symbol_description": "orange bar",
    #         "symbol_id": "osmc_NAT_white_bar_orange",
    #     }
    #     wr = WaymarkedResult(**data)
    #     wr.get_details()

    def test_fetch_details(self):
        data = {
            "type": "relation",
            "id": 241043,
            "name": "Upplandsleden",
            "group": "NAT",
            "symbol_description": "orange bar",
            "symbol_id": "osmc_NAT_white_bar_orange",
        }
        wr = WaymarkedResult(**data)
        wr.__fetch_details__()
        assert wr.details is not None

    def test_parse_details(self):
        wr = WaymarkedResult(id=1014050, name="skåneleden")
        wr.get_details()
        assert wr.official_length == 1300000.0
        assert wr.mapped_length == 1453603
        assert wr.description is None

    def test_number_of_subroutes(self):
        wr = WaymarkedResult(id=1014050, name="skåneleden")  # skåneleden
        wr.get_details()
        assert wr.number_of_subroutes == 6

    def test_already_has_wikidata_tag_true(self):
        wr = WaymarkedResult(id=1014050, name="skåneleden")  # skåneleden
        wr.get_details()
        assert wr.fetch_wikidata_tag_information is True

    def test_already_has_wikidata_tag_false(self):
        wr = WaymarkedResult(id=10528596, name="test")  # östra leden på kebnekaise
        wr.get_details()
        assert wr.fetch_wikidata_tag_information is False
