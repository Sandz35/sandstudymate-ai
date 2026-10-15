from typing import Dict


def evaluate_answer(question: str, answer: str) -> Dict[str, float]:
    """Return a simple mock evaluation payload for an answer."""
    score = 0.0
    if answer and len(answer.strip()) > 20:
        score = 0.85
    if question.lower() in answer.lower():
        score += 0.1
    return {"score": min(score, 1.0), "feedback": "Answer reviewed. Add more detail or examples to improve clarity."}
