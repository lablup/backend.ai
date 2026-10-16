"""Tests for the per-card answer `ModelCardService.partial_bulk_purge` returns."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.dto.manager.v2.model_card.request import DeleteModelCardOptions
from ai.backend.manager.data.model_card.types import (
    BulkModelCardDeleteFailure,
    BulkModelCardDeleteResultData,
    ModelCardData,
)
from ai.backend.manager.errors.resource import ModelCardNotFound
from ai.backend.manager.repositories.model_card.repository import ModelCardRepository
from ai.backend.manager.services.model_card.actions.partial_bulk_purge_model_cards import (
    PartialBulkPurgeModelCardsAction,
)
from ai.backend.manager.services.model_card.service import ModelCardService


@pytest.fixture
def mock_repository() -> MagicMock:
    return MagicMock(spec=ModelCardRepository)


@pytest.fixture
def model_card_service(mock_repository: MagicMock) -> ModelCardService:
    return ModelCardService(repository=mock_repository, storage_manager=MagicMock())


def _action(*card_ids: ModelCardID) -> PartialBulkPurgeModelCardsAction:
    return PartialBulkPurgeModelCardsAction(ids=list(card_ids), options=DeleteModelCardOptions())


def _card(card_id: ModelCardID) -> ModelCardData:
    return ModelCardData(
        id=card_id,
        name=f"card-{card_id}",
        vfolder_id=VFolderUUID(uuid.uuid4()),
        domain="default",
        project_id=uuid.uuid4(),
        creator_id=uuid.uuid4(),
        author=None,
        title=None,
        model_version=None,
        description=None,
        task=None,
        category=None,
        architecture=None,
        framework=[],
        label=[],
        license=None,
        readme=None,
        access_level="internal",
        created_at=datetime.now(UTC),
        updated_at=None,
    )


class TestPartialBulkPurgeModelCards:
    async def test_every_card_purged_is_answered_for(
        self,
        model_card_service: ModelCardService,
        mock_repository: MagicMock,
    ) -> None:
        first, second = ModelCardID(uuid.uuid4()), ModelCardID(uuid.uuid4())
        cards = [_card(first), _card(second)]
        mock_repository.bulk_delete = AsyncMock(
            return_value=BulkModelCardDeleteResultData(successes=cards, failures=[])
        )

        result = await model_card_service.partial_bulk_purge(_action(first, second))

        assert [item.entity_id for item in result.items] == [first, second]
        assert result.values() == {first: cards[0], second: cards[1]}
        assert result.errors() == {}

    async def test_a_failed_card_carries_the_error_it_raised(
        self,
        model_card_service: ModelCardService,
        mock_repository: MagicMock,
    ) -> None:
        purged, missing = ModelCardID(uuid.uuid4()), ModelCardID(uuid.uuid4())
        card = _card(purged)
        error = ModelCardNotFound()
        mock_repository.bulk_delete = AsyncMock(
            return_value=BulkModelCardDeleteResultData(
                successes=[card],
                failures=[BulkModelCardDeleteFailure(card_id=missing, error=error)],
            )
        )

        result = await model_card_service.partial_bulk_purge(_action(purged, missing))

        assert result.values() == {purged: card}
        assert result.errors() == {missing: error}

    async def test_the_purger_of_every_named_card_reaches_the_repository(
        self,
        model_card_service: ModelCardService,
        mock_repository: MagicMock,
    ) -> None:
        first, second = ModelCardID(uuid.uuid4()), ModelCardID(uuid.uuid4())
        mock_repository.bulk_delete = AsyncMock(
            return_value=BulkModelCardDeleteResultData(
                successes=[_card(first), _card(second)], failures=[]
            )
        )

        await model_card_service.partial_bulk_purge(_action(first, second))

        purgers, options = mock_repository.bulk_delete.call_args.args
        assert [purger.card_id for purger in purgers] == [first, second]
        assert options.delete_associated_vfolder is False


class TestPartialBulkPurgeModelCardsAction:
    def test_narrowing_keeps_the_allowed_cards_in_order(self) -> None:
        first, second, third = (ModelCardID(uuid.uuid4()) for _ in range(3))
        action = _action(first, second, third)

        narrowed = action.narrowed_to([third, first])

        assert list(narrowed.ids) == [first, third]
        assert narrowed.options is action.options
