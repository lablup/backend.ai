"""Tests for the per-card answer `ModelCardService.bulk_delete` returns."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.dto.manager.v2.model_card.request import DeleteModelCardOptions
from ai.backend.manager.data.model_card.types import (
    BulkModelCardDeleteFailure,
    BulkModelCardDeleteResultData,
)
from ai.backend.manager.errors.resource import ModelCardNotFound
from ai.backend.manager.repositories.model_card.repository import ModelCardRepository
from ai.backend.manager.services.model_card.actions.bulk_delete import BulkDeleteModelCardAction
from ai.backend.manager.services.model_card.service import ModelCardService


@pytest.fixture
def mock_repository() -> MagicMock:
    return MagicMock(spec=ModelCardRepository)


@pytest.fixture
def model_card_service(mock_repository: MagicMock) -> ModelCardService:
    return ModelCardService(repository=mock_repository, storage_manager=MagicMock())


def _action(*card_ids: ModelCardID) -> BulkDeleteModelCardAction:
    return BulkDeleteModelCardAction(ids=list(card_ids), options=DeleteModelCardOptions())


class TestBulkDeleteModelCard:
    async def test_every_card_deleted_is_answered_for(
        self,
        model_card_service: ModelCardService,
        mock_repository: MagicMock,
    ) -> None:
        first, second = ModelCardID(uuid.uuid4()), ModelCardID(uuid.uuid4())
        mock_repository.bulk_delete = AsyncMock(
            return_value=BulkModelCardDeleteResultData(successes=[first, second], failures=[])
        )

        result = await model_card_service.bulk_delete(_action(first, second))

        assert [item.entity_id for item in result.items] == [first, second]
        assert result.values() == {first: first, second: second}
        assert result.errors() == {}

    async def test_a_failed_card_carries_the_error_it_raised(
        self,
        model_card_service: ModelCardService,
        mock_repository: MagicMock,
    ) -> None:
        deleted, missing = ModelCardID(uuid.uuid4()), ModelCardID(uuid.uuid4())
        error = ModelCardNotFound()
        mock_repository.bulk_delete = AsyncMock(
            return_value=BulkModelCardDeleteResultData(
                successes=[deleted],
                failures=[BulkModelCardDeleteFailure(card_id=missing, error=error)],
            )
        )

        result = await model_card_service.bulk_delete(_action(deleted, missing))

        assert result.values() == {deleted: deleted}
        assert result.errors() == {missing: error}

    async def test_the_purger_of_every_named_card_reaches_the_repository(
        self,
        model_card_service: ModelCardService,
        mock_repository: MagicMock,
    ) -> None:
        first, second = ModelCardID(uuid.uuid4()), ModelCardID(uuid.uuid4())
        mock_repository.bulk_delete = AsyncMock(
            return_value=BulkModelCardDeleteResultData(successes=[first, second], failures=[])
        )

        await model_card_service.bulk_delete(_action(first, second))

        purgers, options = mock_repository.bulk_delete.call_args.args
        assert [purger.card_id for purger in purgers] == [first, second]
        assert options.delete_associated_vfolder is False


class TestBulkDeleteModelCardAction:
    def test_narrowing_keeps_the_allowed_cards_in_order(self) -> None:
        first, second, third = (ModelCardID(uuid.uuid4()) for _ in range(3))
        action = _action(first, second, third)

        narrowed = action.narrowed_to([third, first])

        assert list(narrowed.ids) == [first, third]
        assert narrowed.options is action.options
