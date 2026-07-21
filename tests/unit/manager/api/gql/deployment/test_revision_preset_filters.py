from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
import sqlalchemy as sa

from ai.backend.manager.api.adapters.deployment_revision_preset.adapter import (
    DeploymentRevisionPresetAdapter,
)
from ai.backend.manager.api.gql.base import StringFilter as StringFilterGQL
from ai.backend.manager.api.gql.base import UUIDFilter as UUIDFilterGQL
from ai.backend.manager.api.gql.deployment.types.revision_preset import (
    DeploymentRevisionPresetFilterGQL,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.deployment_revision_preset.conditions import (
    DeploymentRevisionPresetConditions,
)
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow


class TestDeploymentRevisionPresetFilterCombinators:
    def test_empty(self) -> None:
        dto = DeploymentRevisionPresetFilterGQL().to_pydantic()
        assert dto.AND is None and dto.OR is None and dto.NOT is None

    def test_and(self) -> None:
        f = DeploymentRevisionPresetFilterGQL(
            AND=[
                DeploymentRevisionPresetFilterGQL(name=StringFilterGQL(contains="a")),
                DeploymentRevisionPresetFilterGQL(name=StringFilterGQL(contains="b")),
            ]
        )
        dto = f.to_pydantic()
        assert dto.AND is not None
        assert len(dto.AND) == 2

    def test_or(self) -> None:
        f = DeploymentRevisionPresetFilterGQL(
            OR=[DeploymentRevisionPresetFilterGQL(name=StringFilterGQL(contains="a"))]
        )
        assert f.to_pydantic().OR is not None

    def test_not(self) -> None:
        f = DeploymentRevisionPresetFilterGQL(
            NOT=[DeploymentRevisionPresetFilterGQL(name=StringFilterGQL(equals="x"))]
        )
        assert f.to_pydantic().NOT is not None


def _compiled_sql(condition: QueryCondition) -> str:
    query = sa.select(DeploymentRevisionPresetRow.id).where(condition())
    return str(query.compile())


class TestCompatibleWithModelCardIdFilter:
    """The `compatibleWithModelCardId` filter accepts a `UUIDFilter` (per issue #12976
    acceptance: `{ equals: <cardId> }`) and must return the same subset as
    `ModelCardV2.availablePresets` — i.e. reuse `by_model_card_compatible`."""

    def test_gql_to_dto_carries_equals_operand(self) -> None:
        card_id = uuid4()
        dto = DeploymentRevisionPresetFilterGQL(
            compatible_with_model_card_id=UUIDFilterGQL(equals=card_id)
        ).to_pydantic()
        assert dto.compatible_with_model_card_id is not None
        assert dto.compatible_with_model_card_id.equals == card_id

    def test_convert_filter_reuses_model_card_compatible_condition(self) -> None:
        # Structural parity: the adapter path and the ModelCardV2.availablePresets
        # path must compile to identical SQL so the two cannot drift.
        card_id = uuid4()
        adapter = DeploymentRevisionPresetAdapter(processors=MagicMock())
        dto = DeploymentRevisionPresetFilterGQL(
            compatible_with_model_card_id=UUIDFilterGQL(equals=card_id)
        ).to_pydantic()

        conditions = adapter._convert_filter(dto)

        assert len(conditions) == 1
        expected = DeploymentRevisionPresetConditions.by_model_card_compatible(card_id)
        assert _compiled_sql(conditions[0]) == _compiled_sql(expected)

    def test_convert_filter_rejects_unsupported_operators(self) -> None:
        adapter = DeploymentRevisionPresetAdapter(processors=MagicMock())
        dto = DeploymentRevisionPresetFilterGQL(
            compatible_with_model_card_id=UUIDFilterGQL(in_=[uuid4(), uuid4()])
        ).to_pydantic()

        with pytest.raises(InvalidAPIParameters):
            adapter._convert_filter(dto)
