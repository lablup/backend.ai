from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.manager.api.adapters.resource_allocation.adapter import ResourceAllocationAdapter
from ai.backend.manager.errors.auth import AuthenticationRequired


@dataclass(frozen=True)
class _CallWithoutCurrentUserCase:
    method_name: str
    call_adapter: Callable[[ResourceAllocationAdapter], Awaitable[Any]]


class TestCallWithoutCurrentUser:
    @pytest.fixture
    def adapter_without_current_user(self) -> ResourceAllocationAdapter:
        return ResourceAllocationAdapter(
            session=MagicMock(),
            domain=MagicMock(),
            config_provider=None,
        )

    @pytest.mark.parametrize(
        "case",
        [
            _CallWithoutCurrentUserCase(
                method_name="effective_allocation_for_current_user",
                call_adapter=lambda adapter: adapter.effective_allocation_for_current_user(
                    input=MagicMock(),
                ),
            ),
            _CallWithoutCurrentUserCase(
                method_name="check_preset_availability_for_current_user",
                call_adapter=lambda adapter: adapter.check_preset_availability_for_current_user(
                    input=MagicMock(),
                ),
            ),
            _CallWithoutCurrentUserCase(
                method_name="effective_allocation",
                call_adapter=lambda adapter: adapter.effective_allocation(
                    input=MagicMock(),
                    access_key="access-key",
                    resource_policy={},
                ),
            ),
            _CallWithoutCurrentUserCase(
                method_name="check_preset_availability",
                call_adapter=lambda adapter: adapter.check_preset_availability(
                    input=MagicMock(),
                    access_key="access-key",
                    resource_policy={},
                ),
            ),
        ],
        ids=lambda case: case.method_name,
    )
    async def test_raises_authentication_required(
        self,
        adapter_without_current_user: ResourceAllocationAdapter,
        case: _CallWithoutCurrentUserCase,
    ) -> None:
        with pytest.raises(AuthenticationRequired):
            await case.call_adapter(adapter_without_current_user)
