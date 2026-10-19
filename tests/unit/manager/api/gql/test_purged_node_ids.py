"""Tests for the purged Node ids on delete and purge payloads."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from strawberry.relay import GlobalID

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.dto.manager.v2.domain.response import (
    DeleteDomainPayload as DeleteDomainPayloadDTO,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DomainBasicInfo,
    DomainLifecycleInfo,
    DomainNode,
    DomainRegistryInfo,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
    EntityLabelNode,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
    PurgeEntityLabelPayload as PurgeEntityLabelPayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    PurgeRolePayload as PurgeRolePayloadDTO,
)
from ai.backend.manager.api.gql.domain_v2.resolver import mutation as domain_resolver
from ai.backend.manager.api.gql.entity_label.resolver import mutation as entity_label_resolver
from ai.backend.manager.api.gql.rbac.resolver import role as role_resolver


class TestPurgeRole:
    @pytest.fixture
    def role_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def info(self, role_id: uuid.UUID) -> MagicMock:
        info = MagicMock()
        info.context.adapters.rbac.purge = AsyncMock(
            return_value=PurgeRolePayloadDTO(id=role_id, entity_id=role_id)
        )
        return info

    async def test_purged_id_is_role_global_id(self, info: MagicMock, role_id: uuid.UUID) -> None:
        resolver_fn = cast(Any, role_resolver.purge_role).base_resolver
        result = await resolver_fn(info, role_id)

        assert result.purged_id == str(GlobalID("Role", str(role_id)))
        assert result.entity_id == role_id
        assert result.id == role_id


class TestPurgeEntityLabel:
    @pytest.fixture
    def label(self) -> EntityLabelNode:
        label_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        return EntityLabelNode(
            id=label_id,
            field_id=label_id,
            entity_type="vfolder",
            entity_id=uuid.uuid4(),
            key="team",
            value="ml",
            created_at=now,
            updated_at=now,
        )

    @pytest.fixture
    def info(self, label: EntityLabelNode) -> MagicMock:
        info = MagicMock()
        info.context.adapters.entity_label.purge = AsyncMock(
            return_value=PurgeEntityLabelPayloadDTO(label=label, field_id=label.field_id)
        )
        return info

    async def test_purged_id_is_label_global_id(
        self, info: MagicMock, label: EntityLabelNode
    ) -> None:
        resolver_fn = cast(Any, entity_label_resolver.purge_entity_label).base_resolver
        result = await resolver_fn(info, str(label.id))

        assert result.purged_id == str(GlobalID("EntityLabel", str(label.id)))
        assert result.field_id == label.field_id
        assert result.label.field_id == label.field_id


class TestDeleteDomainV2:
    @pytest.fixture
    def domain(self) -> DomainNode:
        domain_id = DomainID(uuid.uuid4())
        now = datetime.now(tz=UTC)
        return DomainNode(
            id=domain_id,
            entity_id=domain_id,
            basic_info=DomainBasicInfo(name="to-delete", description=None, integration_name=None),
            registry=DomainRegistryInfo(allowed_docker_registries=[]),
            lifecycle=DomainLifecycleInfo(
                is_active=True, is_default=False, created_at=now, modified_at=now
            ),
        )

    @pytest.fixture
    def info(self, domain: DomainNode) -> MagicMock:
        info = MagicMock()
        info.context.adapters.domain.delete = AsyncMock(
            return_value=DeleteDomainPayloadDTO(deleted=True, domain=domain)
        )
        return info

    async def test_returns_soft_deleted_domain_node(
        self, info: MagicMock, domain: DomainNode
    ) -> None:
        resolver_fn = cast(Any, domain_resolver.delete_domain_v2).base_resolver
        result = await resolver_fn(info, domain.id)

        assert result.domain.id == str(domain.id)
        assert result.domain.entity_id == domain.entity_id
        assert result.deleted is True
