"""An audit log and its scope entries resolve the entity they record through the entity node loader."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.dto.manager.v2.audit_log.response import (
    AuditLogNode,
    AuditLogScopeEntryNode,
)
from ai.backend.common.dto.manager.v2.audit_log.types import AuditLogStatus
from ai.backend.manager.api.gql.audit_log.types.node import AuditLogV2GQL
from ai.backend.manager.api.gql.audit_log.types.scope_entry import AuditLogScopeEntryGQL
from ai.backend.manager.api.gql.data_loader.data_loaders import DataLoaders


def _audit_log(entity_type: str, target_entity_id: uuid.UUID) -> AuditLogV2GQL:
    log_id = uuid.uuid4()
    return AuditLogV2GQL.from_pydantic(
        AuditLogNode(
            id=log_id,
            field_id=log_id,
            action_id=uuid.uuid4(),
            action_name="deployment:update",
            entity_type=entity_type,
            operation="update",
            target_entity_id=target_entity_id,
            created_at=datetime(2026, 10, 17, tzinfo=UTC),
            description="",
            status=AuditLogStatus.SUCCESS,
        )
    )


def _scope_entry(scope_type: str, scope_id: uuid.UUID) -> AuditLogScopeEntryGQL:
    entry_id = uuid.uuid4()
    return AuditLogScopeEntryGQL.from_pydantic(
        AuditLogScopeEntryNode(
            id=entry_id,
            field_id=entry_id,
            audit_log_id=uuid.uuid4(),
            scope_type=scope_type,
            scope_id=scope_id,
        )
    )


@pytest.fixture
def loaded_node() -> MagicMock:
    return MagicMock()


@pytest.fixture
def entity_loader() -> MagicMock:
    return MagicMock(load=AsyncMock())


class TestAuditLogEntity:
    @pytest.fixture
    def mock_info(self, entity_loader: MagicMock, monkeypatch: pytest.MonkeyPatch) -> MagicMock:
        loaders = DataLoaders(MagicMock())
        monkeypatch.setattr(loaders, "deployment_loader", entity_loader)
        info = MagicMock()
        info.context.data_loaders = loaders
        return info

    async def test_existing_deployment_is_returned(
        self, entity_loader: MagicMock, loaded_node: MagicMock, mock_info: MagicMock
    ) -> None:
        deployment_id = uuid.uuid4()
        entity_loader.load.return_value = loaded_node

        result = await _audit_log("deployment", deployment_id).entity(info=mock_info)

        assert result is loaded_node
        entity_loader.load.assert_awaited_once_with(deployment_id)

    async def test_deleted_deployment_resolves_to_none(
        self, entity_loader: MagicMock, mock_info: MagicMock
    ) -> None:
        entity_loader.load.return_value = None

        result = await _audit_log("deployment", uuid.uuid4()).entity(info=mock_info)

        assert result is None


class TestAuditLogScopeEntryEntity:
    @pytest.fixture
    def mock_info(self, entity_loader: MagicMock, monkeypatch: pytest.MonkeyPatch) -> MagicMock:
        loaders = DataLoaders(MagicMock())
        monkeypatch.setattr(loaders, "project_loader", entity_loader)
        info = MagicMock()
        info.context.data_loaders = loaders
        return info

    async def test_existing_project_is_returned(
        self, entity_loader: MagicMock, loaded_node: MagicMock, mock_info: MagicMock
    ) -> None:
        project_id = uuid.uuid4()
        entity_loader.load.return_value = loaded_node

        result = await _scope_entry("project", project_id).entity(info=mock_info)

        assert result is loaded_node
        entity_loader.load.assert_awaited_once_with(project_id)

    async def test_deleted_project_resolves_to_none(
        self, entity_loader: MagicMock, mock_info: MagicMock
    ) -> None:
        entity_loader.load.return_value = None

        result = await _scope_entry("project", uuid.uuid4()).entity(info=mock_info)

        assert result is None
