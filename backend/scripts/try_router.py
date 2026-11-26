"""Try the router.  python scripts/try_router.py want to study percentage"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from router import ROUTER_MODEL_ID, understand_request  # noqa: E402

message = " ".join(sys.argv[1:]) or "want to study percentage"
print(f"Model: {ROUTER_MODEL_ID}")
print(json.dumps(understand_request(message), indent=2))