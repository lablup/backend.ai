"""The session lifecycle handler adapter, assembled for one row."""

from __future__ import annotations

import pytest

from ai.backend.manager.api.adapters.session_lifecycle_handler.adapter import (
    SessionLifecycleHandlerAdapter,
)


@pytest.fixture
def adapter() -> SessionLifecycleHandlerAdapter:
    return SessionLifecycleHandlerAdapter()
