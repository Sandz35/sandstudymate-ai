"""Adaptive difficulty rules for SandStudyMate.

Pure Python with no AWS calls, so it is fast and easy to unit test.
"""
from dataclasses import asdict, dataclass, fields, replace

MIN_LEVEL = 1
MAX_LEVEL = 5
STREAK_TO_LEVEL_UP = 2    # correct answers in a row needed to move up
STREAK_TO_LEVEL_DOWN = 2  # wrong answers in a row needed to move down

# Plain-English difficulty descriptions; these go into the Bedrock prompt.
LEVEL_DESCRIPTIONS = {
    1: "very easy warm-up: one step, small whole numbers, everyday words",
    2: "easy: early 5th grade, one step",
    3: "on grade level for 5th grade",
    4: "challenging 5th grade: two steps or a short word problem",
    5: "stretch: multi-step, slightly above 5th grade, still fair",
}

# 5th-grade topics (based on common US standards).
SUBJECT_TOPICS = {
    "math": [
        "place value and rounding decimals",
        "multiplying multi-digit whole numbers",
        "dividing with remainders",
        "adding and subtracting fractions",
        "multiplying fractions",
        "adding and subtracting decimals",
        "volume of rectangular prisms",
        "the coordinate grid",
        "order of operations",
        "converting units of measurement",
    ],
    "science": [
        "states of matter",
        "mixtures and solutions",
        "ecosystems and food webs",
        "what plants need to grow",
        "Earth's four spheres",
        "the water cycle",
        "patterns of the Sun, Earth and Moon",
        "gravity",
        "conservation of matter",
        "properties of materials",
    ],
}


@dataclass
class Progress:
    level: int = MIN_LEVEL
    correct_streak: int = 0
    wrong_streak: int = 0
    total_answered: int = 0
    total_correct: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Progress":
        """Build Progress from a stored item.

        DynamoDB returns numbers as Decimal, so cast each one to int.
        """
        values = {}
        for f in fields(cls):
            if f.name in data:
                values[f.name] = int(data[f.name])
        return cls(**values)


def update_progress(progress: Progress, is_correct: bool) -> tuple[Progress, str]:
    """Return (new_progress, event). event is 'level_up', 'level_down' or 'same'."""
    p = replace(progress)  # a copy: never change the caller's object
    p.total_answered += 1
    event = "same"

    if is_correct:
        p.total_correct += 1
        p.correct_streak += 1
        p.wrong_streak = 0
        if p.correct_streak >= STREAK_TO_LEVEL_UP and p.level < MAX_LEVEL:
            p.level += 1
            p.correct_streak = 0
            event = "level_up"
    else:
        p.wrong_streak += 1
        p.correct_streak = 0
        if p.wrong_streak >= STREAK_TO_LEVEL_DOWN and p.level > MIN_LEVEL:
            p.level -= 1
            p.wrong_streak = 0
            event = "level_down"

    return p, event


def pick_topic(subject: str, question_number: int) -> str:
    """Rotate through the subject's topics so practice stays varied."""
    topics = SUBJECT_TOPICS[subject]
    return topics[question_number % len(topics)]
