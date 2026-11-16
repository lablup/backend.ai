from __future__ import annotations

from typing import Any

import pytest

_IDLE_CHECKERS: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000f001",
        "name": "session-lifetime",
        "description": "Terminates sessions running longer than a day.",
        "target_session_types": ["interactive", "batch"],
        "spec": {"type": "session_lifetime", "session_lifetime": {"max_lifetime_seconds": 86400}},
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000f002",
        "name": "network-timeout",
        "target_session_types": ["interactive"],
        "initial_grace_period_seconds": 300,
        "spec": {
            "type": "network_timeout",
            "network": {"max_network_inactivity_seconds": 3600},
        },
    },
]


@pytest.fixture
def idle_checker_ids() -> list[str]:
    return [str(checker["id"]) for checker in _IDLE_CHECKERS]
