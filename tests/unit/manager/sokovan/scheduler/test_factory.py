from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.manager.sokovan.scheduler.factory import (
    SESSION_LIFECYCLE_HANDLER_TYPES,
    CoordinatorHandlersArgs,
    create_coordinator_handlers,
)


@pytest.fixture
def coordinator_handlers_args() -> CoordinatorHandlersArgs:
    return CoordinatorHandlersArgs(
        provisioner=MagicMock(),
        launcher=MagicMock(),
        terminator=MagicMock(),
        repository=MagicMock(),
        valkey_schedule=MagicMock(),
        scheduling_controller=MagicMock(),
        fair_share_aggregator=MagicMock(),
        fair_share_calculator=MagicMock(),
        resource_usage_repository=MagicMock(),
        fair_share_repository=MagicMock(),
    )


class TestSessionLifecycleHandlerTypes:
    def test_names_the_classes_the_coordinator_is_built_with(
        self, coordinator_handlers_args: CoordinatorHandlersArgs
    ) -> None:
        handlers = create_coordinator_handlers(coordinator_handlers_args)

        assert {type(handler) for handler in handlers.lifecycle_handlers.values()} == set(
            SESSION_LIFECYCLE_HANDLER_TYPES
        )
