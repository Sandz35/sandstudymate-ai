from typing import Any, Dict


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Sample Lambda entrypoint for the StudyMate API."""
    return {
        "statusCode": 200,
        "body": "StudyMate AI backend is running.",
        "headers": {"Content-Type": "application/json"},
    }
