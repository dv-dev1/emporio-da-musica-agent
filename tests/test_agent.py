import json

from emporio.agent import _decode, _is_transient


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


class _Error(Exception):
    def __init__(self, status_code, code=None):
        self.status_code = status_code
        self.body = {"error": {"code": code}} if code else {}


def test_a_rate_limit_is_worth_retrying():
    assert _is_transient(_Error(429))


def test_a_malformed_tool_call_is_worth_retrying():
    """gpt-oss emits its commentary channel as a tool call now and then.

    Groq rejects it with a 400 the next sample will not repeat.
    """
    assert _is_transient(_Error(400, "tool_use_failed"))


def test_a_bad_key_is_not():
    assert not _is_transient(_Error(401))
    assert not _is_transient(_Error(404))
