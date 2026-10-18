from decimal import Decimal

from adaptive import (
    MAX_LEVEL,
    MIN_LEVEL,
    SUBJECT_TOPICS,
    Progress,
    pick_topic,
    update_progress,
)


def test_starts_at_level_1():
    assert Progress().level == 1


def test_two_correct_levels_up():
    p = Progress()
    p, event = update_progress(p, True)
    assert event == "same" and p.level == 1
    p, event = update_progress(p, True)
    assert event == "level_up" and p.level == 2
    assert p.correct_streak == 0


def test_never_above_max():
    p = Progress(level=MAX_LEVEL)
    for _ in range(4):
        p, event = update_progress(p, True)
    assert p.level == MAX_LEVEL
    assert event == "same"


def test_two_wrong_levels_down():
    p = Progress(level=3)
    p, _ = update_progress(p, False)
    p, event = update_progress(p, False)
    assert event == "level_down" and p.level == 2


def test_never_below_min():
    p = Progress()
    for _ in range(4):
        p, _ = update_progress(p, False)
    assert p.level == MIN_LEVEL


def test_wrong_answer_resets_correct_streak():
    p = Progress()
    p, _ = update_progress(p, True)
    p, _ = update_progress(p, False)
    p, event = update_progress(p, True)
    assert event == "same" and p.level == 1


def test_totals_are_counted():
    p = Progress()
    p, _ = update_progress(p, True)
    p, _ = update_progress(p, False)
    assert p.total_answered == 2 and p.total_correct == 1


def test_from_dict_handles_dynamodb_decimals():
    p = Progress.from_dict({"level": Decimal("3"), "total_correct": Decimal("5")})
    assert p.level == 3 and isinstance(p.level, int)
    assert p.total_correct == 5 and p.total_answered == 0


def test_topics_rotate():
    first = pick_topic("math", 0)
    assert pick_topic("math", len(SUBJECT_TOPICS["math"])) == first
    assert pick_topic("science", 1) != pick_topic("science", 0)