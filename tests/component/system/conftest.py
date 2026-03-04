from __future__ import annotations

import pytest

from ai.backend.manager.api.rest.types import ModuleRegistrar


@pytest.fixture()
def server_module_registrars() -> list[ModuleRegistrar]:
    """No modules needed — the hello() handler is on the root app."""
    return []
