from typing import List


def generate_questions(topic: str, difficulty: str = "medium", count: int = 5) -> List[str]:
    """Generate mock study questions for a topic."""
    return [
        f"What is the key concept behind {topic}?",
        f"Explain the main challenge in {topic} at {difficulty} level.",
        f"Give an example related to {topic} and describe its importance.",
        f"How would you break down {topic} into smaller components?",
        f"What evidence supports a strong understanding of {topic}?",
    ][:count]
