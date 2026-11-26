import pytest

import app


@pytest.fixture(autouse=True)
def no_aws(monkeypatch):
    """Unit tests never call AWS: swap cloud calls for fakes."""
    monkeypatch.setattr(app, "retrieve", lambda query, subject=None: [])
    monkeypatch.setattr(app, "check_input", lambda text: (True, ""))
