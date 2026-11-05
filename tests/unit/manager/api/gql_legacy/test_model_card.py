from __future__ import annotations

import uuid
from collections.abc import Callable, Generator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import graphene
import pytest
import sqlalchemy as sa
from graphql_relay import to_global_id

from ai.backend.common.config import ModelDefinition
from ai.backend.manager.api.gql_legacy.vfolder import ModelCard
from ai.backend.manager.models.resource_group.row import ResourceGroupForProjectRow
from ai.backend.manager.models.user.row import UserRole
from ai.backend.manager.models.vfolder.row import VFolderRow

# Reachable only through string relationships of the vfolder row's eager loads.
_ORM_CLUSTER = (ResourceGroupForProjectRow,)


class TestModelCardParseModelModifiedAt:
    """Tests for ModelCard.parse_model modified_at fallback chain."""

    @pytest.fixture
    def graph_ctx(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def vfolder_row(self) -> MagicMock:
        row = MagicMock()
        row.id = uuid.uuid4()
        row.name = "test-model"
        row.creator = "testuser"
        row.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        row.last_used = datetime(2025, 6, 15, tzinfo=UTC)
        return row

    @pytest.fixture
    def model_def_with_metadata(self) -> Callable[[dict[str, Any]], ModelDefinition]:
        def _build(metadata: dict[str, Any]) -> ModelDefinition:
            return ModelDefinition.model_validate({
                "models": [
                    {
                        "name": "test-model",
                        "model_path": "/models/test-model",
                        "metadata": metadata,
                    }
                ]
            })

        return _build

    @pytest.fixture(autouse=True)
    def _mock_vfolder_helpers(self) -> Generator[None]:
        with (
            patch(
                "ai.backend.manager.api.gql_legacy.vfolder.VirtualFolderNode.from_row",
                return_value=MagicMock(),
            ),
            patch(
                "ai.backend.manager.api.gql_legacy.vfolder.VirtualFolder.from_orm_row",
                return_value=MagicMock(),
            ),
        ):
            yield

    async def test_modified_at_uses_metadata_last_modified_when_present(
        self,
        graph_ctx: MagicMock,
        vfolder_row: MagicMock,
        model_def_with_metadata: Callable[[dict[str, Any]], ModelDefinition],
    ) -> None:
        expected = "2025-12-25T00:00:00Z"
        model_def = model_def_with_metadata({"last_modified": expected})

        card = ModelCard.parse_model(graph_ctx, vfolder_row, model_def=model_def)

        assert card.modified_at == expected

    async def test_modified_at_falls_back_to_last_used_when_metadata_missing(
        self,
        graph_ctx: MagicMock,
        vfolder_row: MagicMock,
        model_def_with_metadata: Callable[[dict[str, Any]], ModelDefinition],
    ) -> None:
        model_def = model_def_with_metadata({})

        card = ModelCard.parse_model(graph_ctx, vfolder_row, model_def=model_def)

        assert card.modified_at == vfolder_row.last_used

    async def test_modified_at_is_none_when_both_metadata_and_last_used_missing(
        self,
        graph_ctx: MagicMock,
        vfolder_row: MagicMock,
        model_def_with_metadata: Callable[[dict[str, Any]], ModelDefinition],
    ) -> None:
        vfolder_row.last_used = None
        model_def = model_def_with_metadata({})

        card = ModelCard.parse_model(graph_ctx, vfolder_row, model_def=model_def)

        assert card.modified_at is None


class TestModelCardGetNode:
    """modelCard(id:) reads a vfolder only within the requester's vfolder permissions."""

    @pytest.fixture
    def db_session(self) -> MagicMock:
        session = MagicMock()
        session.scalar = AsyncMock(return_value=None)
        return session

    @pytest.fixture
    def info(self, db_session: MagicMock) -> graphene.ResolveInfo:
        ctx = MagicMock()
        ctx.user = {"role": UserRole.USER, "domain_name": "default", "uuid": uuid.uuid4()}
        ctx.db.connect = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=MagicMock()),
                __aexit__=AsyncMock(return_value=None),
            )
        )
        ctx.db.begin_readonly_session = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=db_session),
                __aexit__=AsyncMock(return_value=None),
            )
        )
        info = MagicMock(spec=graphene.ResolveInfo)
        info.context = ctx
        return info

    @pytest.fixture
    def model_card_id(self) -> str:
        return to_global_id("ModelCard", str(uuid.uuid4()))

    async def test_a_requester_reaching_no_vfolder_gets_null_without_a_read(
        self, info: graphene.ResolveInfo, db_session: MagicMock, model_card_id: str
    ) -> None:
        permission_ctx = MagicMock(query_condition=None)
        with patch(
            "ai.backend.manager.api.gql_legacy.vfolder.get_permission_ctx",
            AsyncMock(return_value=permission_ctx),
        ):
            assert await ModelCard.get_node(info, model_card_id) is None
        db_session.scalar.assert_not_called()

    async def test_the_read_is_bounded_by_the_permission_condition(
        self, info: graphene.ResolveInfo, db_session: MagicMock, model_card_id: str
    ) -> None:
        permission_ctx = MagicMock(query_condition=VFolderRow.domain_name == "default")
        with patch(
            "ai.backend.manager.api.gql_legacy.vfolder.get_permission_ctx",
            AsyncMock(return_value=permission_ctx),
        ):
            assert await ModelCard.get_node(info, model_card_id) is None
        stmt: sa.Select[tuple[object]] = db_session.scalar.await_args.args[0]
        where = str(stmt.whereclause)
        assert "vfolders.domain_name" in where
        assert "vfolders.id" in where
