import json

from emporio.agent import _decode


def test_arguments_come_back_as_a_dict():
    assert _decode('{"product_id": 81}') == {"product_id": 81}


def test_the_empty_key_a_no_argument_tool_produces_is_dropped():
    assert _decode('{"": {}}') == {}


def test_malformed_json_does_not_raise():
    assert _decode("{not json") == {}
    assert _decode("") == {}
    assert _decode("[1, 2]") == {}


def test_a_valid_call_survives_a_junk_key():
    assert _decode(json.dumps({"query": "violão", "": {}})) == {"query": "violão"}
