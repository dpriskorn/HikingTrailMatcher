from src.waymarked_result import WaymarkedResult


class TestWaymarkedResult:
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
        wr.__parse_details__()
        assert wr.official_length == 500000.0
        assert wr.mapped_length == 607380.0
        assert wr.description == "hiking trail in Uppland"


    def test_number_of_subroutes(self):
        data = {
            "type": "relation",
            "id": 241043,
            "name": "Upplandsleden",
            "group": "NAT",
            "symbol_description": "orange bar",
            "symbol_id": "osmc_NAT_white_bar_orange",
        }
        wr = WaymarkedResult(**data)
        wr.get_details()
        assert wr.number_of_subroutes == 36