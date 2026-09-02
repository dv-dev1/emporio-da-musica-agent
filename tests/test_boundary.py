"""The tool boundary, exercised the way a language model actually calls it.

A JSON schema is a request, not a constraint: the model sends numbers as
strings, booleans as the word "false", and sometimes nothing that parses at all.
None of that is allowed to reach SQL or raise.
"""

import gc
import sqlite3
import warnings

import pytest

from emporio import tools
from emporio.memory import History


@pytest.mark.parametrize(
    "raw, expected",
    [
        (True, True), (False, False),
        ("true", True), ("True", True),
        ("false", False), ("False", False), ("no", False), ("não", False), ("0", False),
        (None, True), ("", False),
    ],
)
def test_booleans_arrive_as_strings_and_still_mean_what_they_say(raw, expected):
    assert tools._as_bool(raw) is expected


def test_a_stock_filter_sent_as_the_string_false_is_actually_turned_off():
    on = tools.search_products(query="giannini", only_in_stock=True)
    off = tools.search_products(query="giannini", only_in_stock="false")
    assert off["count"] > on["count"]


@pytest.mark.parametrize("raw", ["600", 600, 600.0, " 600 "])
def test_price_ceilings_accept_whatever_shape_they_arrive_in(raw):
    assert tools.search_products(query="violão", max_price=raw)["count"] == 5


@pytest.mark.parametrize("bad", ["abc", None, "", {}, []])
def test_an_unparseable_id_is_an_error_not_a_traceback(bad):
    assert "error" in tools.get_product(bad)
    assert "error" in tools.get_order(bad, "lucas.mendes@jmail.com")


def test_a_string_id_still_finds_its_row():
    assert tools.get_product("81")["name"].startswith("Yamaha C40")
    assert "status" in tools.get_order("4", "lucas.mendes@jmail.com")


def test_the_result_limit_is_capped_however_it_is_asked_for():
    assert tools.search_products(query="", limit=500)["count"] <= tools.MAX_RESULTS
    assert tools.search_products(query="", limit="500")["count"] <= tools.MAX_RESULTS
    assert tools.search_products(query="", limit=0)["count"] >= 1


def test_every_declared_tool_is_callable_by_name():
    for name in tools.REGISTRY:
        schema = next(s for s in tools.SCHEMAS if s["function"]["name"] == name)
        required = schema["function"]["parameters"].get("required", [])
        assert set(required) <= set(tools.REGISTRY[name].__code__.co_varnames)


def test_the_schemas_and_the_registry_do_not_drift_apart():
    declared = {schema["function"]["name"] for schema in tools.SCHEMAS}
    assert declared == set(tools.REGISTRY)


def test_no_tool_call_leaves_a_database_handle_behind():
    with warnings.catch_warnings():
        warnings.simplefilter("error", ResourceWarning)
        history = History("boundary-leak")
        for _ in range(20):
            tools.search_products(query="violão", limit=2)
            tools.get_order(4, "lucas.mendes@jmail.com")
            history.append("user", "oi")
            history.messages()
        history.clear()
        gc.collect()
    assert not [o for o in gc.get_objects() if isinstance(o, sqlite3.Connection)]
