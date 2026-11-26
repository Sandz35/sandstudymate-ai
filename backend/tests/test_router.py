import pytest

from router import parse_route


def test_in_scope_route():
    r = parse_route('{"in_scope": true, "subject": "Math", "topic": "percentages", '
                    '"search_query": "percent of a number", "reply": "Great!"}')
    assert r["subject"] == "math"
    assert r["topic"] == "percentages"


def test_out_of_scope_route():
    r = parse_route('{"in_scope": false, "reply": "Try fractions instead!"}')
    assert r == {"in_scope": False, "reply": "Try fractions instead!"}


def test_bad_subject_rejected():
    with pytest.raises(ValueError):
        parse_route('{"in_scope": true, "subject": "history", "topic": "kings", "reply": "ok"}')


def test_non_json_rejected():
    with pytest.raises(ValueError):
        parse_route("I think you mean fractions")
