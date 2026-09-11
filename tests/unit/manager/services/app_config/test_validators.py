"""Tests for the fragment owner check with a mocked ops repository."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.exception import UserNotFound
from ai.backend.manager.actions.action.base import BaseActionTriggerMeta
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.app_config.actions.fragment.bulk_upsert import (
    BulkUpsertAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config.validators import FragmentOwnerExistsValidator


@dataclass(frozen=True)
class _OwnerCase:
    owner: EntityIdentifier
    refused_as: type[Exception]


@pytest.fixture
def mock_repository() -> MagicMock:
    return MagicMock(spec=OpsRepository)


@pytest.fixture
def validator(mock_repository: MagicMock) -> FragmentOwnerExistsValidator:
    return FragmentOwnerExistsValidator(mock_repository)


@pytest.fixture
def meta() -> BaseActionTriggerMeta:
    return BaseActionTriggerMeta(action_id=uuid.uuid4(), started_at=datetime.now(UTC))


@pytest.fixture
def owner_missing(mock_repository: MagicMock) -> None:
    mock_repository.get = AsyncMock(
        side_effect=EntityNotFoundError(
            entity_type=UserEntityType(), operation=ActionOperationType.GET
        )
    )


@pytest.fixture
def owner_present(mock_repository: MagicMock) -> None:
    mock_repository.get = AsyncMock(return_value=MagicMock())


class TestFragmentOwnerExistsValidator:
    @pytest.mark.parametrize(
        "case",
        [
            _OwnerCase(owner=DomainID(uuid.uuid4()), refused_as=DomainNotFound),
            _OwnerCase(owner=UserID(uuid.uuid4()), refused_as=UserNotFound),
        ],
        ids=lambda case: case.owner.entity_type().name(),
    )
    async def test_a_missing_owner_is_refused_as_not_found(
        self,
        validator: FragmentOwnerExistsValidator,
        meta: BaseActionTriggerMeta,
        owner_missing: None,
        case: _OwnerCase,
    ) -> None:
        action = BulkUpsertAppConfigFragmentsAction(owner=case.owner, upserters=[])

        with pytest.raises(case.refused_as):
            await validator.validate(action, meta)

    @pytest.mark.parametrize(
        "owner",
        [DomainID(uuid.uuid4()), UserID(uuid.uuid4())],
        ids=lambda owner: owner.entity_type().name(),
    )
    async def test_an_existing_owner_passes(
        self,
        validator: FragmentOwnerExistsValidator,
        meta: BaseActionTriggerMeta,
        owner_present: None,
        owner: EntityIdentifier,
    ) -> None:
        action = BulkUpsertAppConfigFragmentsAction(owner=owner, upserters=[])

        await validator.validate(action, meta)
