"""The model card available-presets read: answered for the card, not the superadmin gate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.model_card import ModelCardEntityType, ModelCardID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.global_scope.validator.superadmin import (
    SuperAdminActionValidator,
)
from ai.backend.manager.actions.v2.single_entity.trigger import SingleEntityActionTriggerMeta
from ai.backend.manager.actions.v2.single_entity.validator.base import (
    SingleEntityActionValidator,
)
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.model_card.types import AvailablePresetsSearchResult
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.model_card.actions.available_presets import (
    AvailablePresetsActionResult,
)
from ai.backend.manager.services.model_card.processors import ModelCardProcessors

READABLE = ModelCardID(uuid4())
DENIED = ModelCardID(uuid4())


@dataclass(frozen=True)
class _CheckedRead:
    entity: EntityIdentifier
    permission: Permission


class _CardReadGate(SingleEntityActionValidator):
    """Lets the readable card through and refuses every other, recording what it saw."""

    seen: list[_CheckedRead]

    def __init__(self) -> None:
        self.seen = []

    @override
    async def validate(self, meta: SingleEntityActionTriggerMeta) -> None:
        self.seen.append(_CheckedRead(meta.entity, meta.operation_type.to_permission()))
        if meta.entity != READABLE:
            raise NotEnoughPermission("no read on this model card")


@pytest.fixture
def regular_user() -> UserData:
    return UserData(
        user_id=uuid4(),
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
        domain_id=DomainID(uuid4()),
    )


@pytest.fixture
def card_gate() -> _CardReadGate:
    return _CardReadGate()


@pytest.fixture
def service() -> MagicMock:
    service = MagicMock()
    service.available_presets = AsyncMock(
        return_value=AvailablePresetsActionResult(
            result=AvailablePresetsSearchResult(
                items=[], total_count=0, has_next_page=False, has_previous_page=False
            )
        )
    )
    return service


@pytest.fixture
def adapter(card_gate: _CardReadGate, service: MagicMock) -> ModelCardAdapter:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(
                single_entity=[card_gate],
                global_scope=[SuperAdminActionValidator()],
            ),
            repository=OpsRepository(MagicMock()),
        )
    )
    processors = ModelCardProcessors(registry.group(GroupMeta(ModelCardEntityType())), service)
    return ModelCardAdapter(processors, MagicMock())


async def test_available_presets_are_answered_for_the_card_reader(
    adapter: ModelCardAdapter,
    card_gate: _CardReadGate,
    regular_user: UserData,
) -> None:
    with with_user(regular_user):
        payload = await adapter.available_presets(READABLE, SearchDeploymentRevisionPresetsInput())

    assert payload.total_count == 0
    assert card_gate.seen == [_CheckedRead(READABLE, Permission.READ)]


async def test_available_presets_are_refused_on_a_card_the_user_cannot_read(
    adapter: ModelCardAdapter,
    service: MagicMock,
    regular_user: UserData,
) -> None:
    with with_user(regular_user), pytest.raises(NotEnoughPermission):
        await adapter.available_presets(DENIED, SearchDeploymentRevisionPresetsInput())

    service.available_presets.assert_not_awaited()
