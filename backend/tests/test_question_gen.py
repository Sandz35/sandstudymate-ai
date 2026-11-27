import pytest

from question_gen import parse_question

GOOD = (
    '{"question": "What is 3 x 4?", "choices": ["7", "12", "34", "1"], '
    '"answer_index": 1, "explanation": "3 groups of 4 is 12.", "hint": "Skip count by 4."}'
)


def test_parses_clean_json():
    q = parse_question(GOOD)
    assert q["answer_index"] == 1
    assert len(q["choices"]) == 4


def test_parses_json_wrapped_in_text():
    q = parse_question("Here you go:\n" + GOOD + "\nGood luck!")
    assert q["question"].startswith("What is")


def test_rejects_wrong_number_of_choices():
    with pytest.raises(ValueError):
        parse_question('{"question": "Q", "choices": ["a", "b"], "answer_index": 0}')


def test_rejects_bad_answer_index():
    with pytest.raises(ValueError):
        parse_question('{"question": "Q", "choices": ["a", "b", "c", "d"], "answer_index": 7}')


def test_rejects_non_json():
    with pytest.raises(ValueError):
        parse_question("Sorry, I cannot help with that.")
