from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.repositories.ops.repository import OpsRepository


@pytest.fixture
def processor_registry() -> ProcessorRegistry[Any]:
    """A registry these tests wire nothing into; its catalog answers what was wired."""
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(),
            repository=OpsRepository(MagicMock()),
        )
    )
