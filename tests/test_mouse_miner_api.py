from unittest import mock
from utils.mousemine_api import get_mousemine_references_from_webservice


@mock.patch('utils.mousemine_api.Service')
def test_get_mousemine_references_return_empty(mock_service):
    mock_service.return_value.new_query.return_value.rows.return_value = []
    mouse_miner_references = get_mousemine_references_from_webservice()
    assert(mouse_miner_references == [])
