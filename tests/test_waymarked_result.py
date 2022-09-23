from src.waymarked_result import WaymarkedResult


class TestWaymarkedResult:
    def test_waymarked_result_all_supported_fields(self):
        data =  {
            'type': 'relation',
            'id': 241043,
            'name': 'Upplandsleden',
            'group': 'NAT',
            'itinerary': ['Knivsta', 'Forsby'],
            'symbol_description': 'orange bar',
            'symbol_id': 'osmc_NAT_white_bar_orange'
        }
        wr = WaymarkedResult(**data)
        assert wr.name == "Upplandsleden"
        assert wr.id == 241043
        assert wr.group == "NAT"
        assert len(wr.itinerary) == 2
        assert wr.itinerary[0] == 'Knivsta'

    def test_waymarked_result_no_itinerary(self):
        data =  {
            'type': 'relation',
            'id': 241043,
            'name': 'Upplandsleden',
            'group': 'NAT',
            'symbol_description': 'orange bar',
            'symbol_id': 'osmc_NAT_white_bar_orange'
        }
        wr = WaymarkedResult(**data)
        assert wr.name == "Upplandsleden"
        assert wr.id == 241043
        assert len(wr.itinerary) == 0
