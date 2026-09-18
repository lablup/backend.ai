"""Every paginated GQL resolver must emit a cursor its own ``after`` accepts. (BA-7985)"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.role_permission_preset import RolePermissionPresetID
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.vfolder import VFolderEntityType, VFolderUUID
from ai.backend.common.data.model_deployment.types import (
    ActivenessStatus,
    LivenessStatus,
    ReadinessStatus,
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.common.data.user.types import UserData
from ai.backend.common.dto.manager.v2.deployment.response import (
    ReplicaNode,
    SearchReplicasPayload,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    DeploymentRevisionPresetNode,
    PresetClusterSpec,
    PresetDeploymentDefaults,
    PresetExecutionSpec,
    PresetResourceAllocation,
    SearchDeploymentRevisionPresetsPayload,
)
from ai.backend.common.dto.manager.v2.entity_share.response import (
    EntityShareNode,
    SearchEntitySharesPayload,
)
from ai.backend.common.dto.manager.v2.entity_share.types import EntityShareStatusDTO
from ai.backend.common.dto.manager.v2.model_card.response import (
    ModelCardMetadata,
    ModelCardNode,
    SearchModelCardsPayload,
)
from ai.backend.common.dto.manager.v2.model_card.types import ModelCardAccessLevel
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
from ai.backend.common.dto.manager.v2.retention_policy.response import (
    RetentionPolicyNode,
    SearchRetentionPoliciesPayload,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    RolePermissionPresetNode,
    SearchRolePermissionPresetsPayload,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    RolePresetNode,
    SearchRolePresetsPayload,
)
from ai.backend.common.dto.manager.v2.runtime_variant.response import (
    RuntimeVariantModelDefinitionInfo,
    RuntimeVariantNode,
    SearchRuntimeVariantsPayload,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    PresetTargetSpec,
    RuntimeVariantPresetNode,
    SearchRuntimeVariantPresetsPayload,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
)
from ai.backend.manager.api.gql.base import decode_cursor, encode_cursor
from ai.backend.manager.api.gql.deployment.resolver.replica import replicas as replicas_resolver
from ai.backend.manager.api.gql.deployment.resolver.revision_preset import (
    deployment_revision_presets,
)
from ai.backend.manager.api.gql.deployment.types.deployment import ModelDeployment
from ai.backend.manager.api.gql.entity_share.resolver import my_entity_shares
from ai.backend.manager.api.gql.model_card.resolver import (
    admin_model_cards_v2,
    model_card_available_presets,
)
from ai.backend.manager.api.gql.model_card.types import ModelCardAvailablePresetsScopeGQL
from ai.backend.manager.api.gql.retention_policy.resolver import admin_retention_policies
from ai.backend.manager.api.gql.role_preset.resolver.query import admin_role_presets
from ai.backend.manager.api.gql.role_preset.types.node import RolePresetGQL
from ai.backend.manager.api.gql.runtime_variant.resolver import runtime_variants
from ai.backend.manager.api.gql.runtime_variant_preset.resolver import runtime_variant_presets
from ai.backend.manager.api.gql.vfolder_v2.types.node import VFolderGQL
from ai.backend.manager.models.user import UserRole

_NOW = datetime(2026, 1, 1, tzinfo=UTC)
_PAGE_SIZE = 2
_ITEM_COUNT = 4


def _superadmin() -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=True,
        is_superadmin=True,
        role=UserRole.SUPERADMIN,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


class _InMemorySearch:
    """Adapter stand-in that pages an in-memory list by decoding the ``after`` cursor."""

    _items: list[Any]
    _payload_type: type[Any]

    def __init__(self, items: list[Any], payload_type: type[Any]) -> None:
        self._items = items
        self._payload_type = payload_type

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        search_input = next(a for a in (*args, *kwargs.values()) if hasattr(a, "after"))
        start = 0
        if search_input.after is not None:
            row_id = decode_cursor(search_input.after)
            start = next(i for i, it in enumerate(self._items) if str(it.id) == row_id) + 1
        page = self._items[start : start + (search_input.first or len(self._items))]
        return self._payload_type(
            items=page,
            total_count=len(self._items),
            has_next_page=start + len(page) < len(self._items),
            has_previous_page=start > 0,
        )


@dataclass(frozen=True)
class ConnectionCase:
    name: str
    items: list[Any]
    payload_type: type[Any]
    adapter_owner: str
    adapter_method: str
    call: Callable[[MagicMock, int, str | None], Awaitable[Any]]


def _runtime_variants() -> list[RuntimeVariantNode]:
    return [
        RuntimeVariantNode(
            id=uuid.uuid4(),
            entity_id=uuid.uuid4(),
            name=f"variant-{n}",
            reads_vfolder_config_files=False,
            default_model_definition=RuntimeVariantModelDefinitionInfo(),
            created_at=_NOW,
        )
        for n in range(_ITEM_COUNT)
    ]


def _runtime_variant_presets() -> list[RuntimeVariantPresetNode]:
    return [
        RuntimeVariantPresetNode(
            id=uuid.uuid4(),
            entity_id=uuid.uuid4(),
            runtime_variant_id=uuid.uuid4(),
            name=f"preset-{n}",
            rank=n,
            target_spec=PresetTargetSpec(
                preset_target=PresetTarget.ENV,
                value_type=PresetValueType.STR,
                key="KEY",
            ),
            required=False,
            created_at=_NOW,
        )
        for n in range(_ITEM_COUNT)
    ]


def _retention_policies() -> list[RetentionPolicyNode]:
    return [
        RetentionPolicyNode(
            id=uuid.uuid4(),
            entity_id=uuid.uuid4(),
            category=RetentionCategory.LOGS,
            retention_period_days=30,
            enabled=True,
            created_at=_NOW,
            updated_at=_NOW,
        )
        for _ in range(_ITEM_COUNT)
    ]


def _role_presets() -> list[RolePresetNode]:
    return [
        RolePresetNode(
            id=RolePresetID(uuid.uuid4()),
            entity_id=uuid.uuid4(),
            name=f"role-preset-{n}",
            scope_type=DomainEntityType(),
            auto_assign=False,
            deleted=False,
            created_at=_NOW,
            updated_at=_NOW,
        )
        for n in range(_ITEM_COUNT)
    ]


def _role_permission_presets() -> list[RolePermissionPresetNode]:
    return [
        RolePermissionPresetNode(
            id=RolePermissionPresetID(uuid.uuid4()),
            field_id=uuid.uuid4(),
            role_preset_id=RolePresetID(uuid.uuid4()),
            entity_type=VFolderEntityType(),
            permission=PermissionBitDTO.READ,
            created_at=_NOW,
        )
        for _ in range(_ITEM_COUNT)
    ]


def _revision_presets() -> list[DeploymentRevisionPresetNode]:
    return [
        DeploymentRevisionPresetNode(
            id=uuid.uuid4(),
            entity_id=uuid.uuid4(),
            runtime_variant_id=RuntimeVariantID(uuid.uuid4()),
            name=f"revision-preset-{n}",
            description=None,
            rank=n,
            cluster=PresetClusterSpec(cluster_mode="single-node", cluster_size=1),
            resource=PresetResourceAllocation(resource_opts=[]),
            execution=PresetExecutionSpec(
                image_id=None,
                startup_command=None,
                bootstrap_script=None,
                environ=[],
            ),
            deployment_defaults=PresetDeploymentDefaults(),
            model_definition=None,
            preset_values=[],
            created_at=_NOW,
            updated_at=None,
        )
        for n in range(_ITEM_COUNT)
    ]


def _model_cards() -> list[ModelCardNode]:
    return [
        ModelCardNode(
            id=uuid.uuid4(),
            entity_id=uuid.uuid4(),
            name=f"card-{n}",
            vfolder_id=VFolderUUID(uuid.uuid4()),
            domain_name="default",
            project_id=uuid.uuid4(),
            creator_id=uuid.uuid4(),
            metadata=ModelCardMetadata(),
            access_level=ModelCardAccessLevel.PUBLIC,
            created_at=_NOW,
        )
        for n in range(_ITEM_COUNT)
    ]


def _entity_shares() -> list[EntityShareNode]:
    return [
        EntityShareNode(
            id=EntityShareID(uuid.uuid4()),
            entity_id=uuid.uuid4(),
            target_entity_type=VFolderEntityType(),
            target_entity_id=uuid.uuid4(),
            permissions=[PermissionBitDTO.READ],
            status=EntityShareStatusDTO.PENDING,
            created_at=_NOW,
            updated_at=_NOW,
        )
        for _ in range(_ITEM_COUNT)
    ]


def _replicas() -> list[ReplicaNode]:
    return [
        ReplicaNode(
            id=uuid.uuid4(),
            field_id=uuid.uuid4(),
            deployment_id=uuid.uuid4(),
            revision_id=uuid.uuid4(),
            readiness_status=ReadinessStatus.HEALTHY,
            liveness_status=LivenessStatus.HEALTHY,
            activeness_status=ActivenessStatus.ACTIVE,
            status=RouteStatus.RUNNING,
            traffic_status=RouteTrafficStatus.ACTIVE,
            health_status=RouteHealthStatus.HEALTHY,
            created_at=_NOW,
        )
        for _ in range(_ITEM_COUNT)
    ]


CASES: list[ConnectionCase] = [
    ConnectionCase(
        name="runtime_variants",
        items=_runtime_variants(),
        payload_type=SearchRuntimeVariantsPayload,
        adapter_owner="runtime_variant",
        adapter_method="search",
        call=lambda info, first, after: runtime_variants.base_resolver(
            info, first=first, after=after
        ),
    ),
    ConnectionCase(
        name="runtime_variant_presets",
        items=_runtime_variant_presets(),
        payload_type=SearchRuntimeVariantPresetsPayload,
        adapter_owner="runtime_variant_preset",
        adapter_method="search",
        call=lambda info, first, after: runtime_variant_presets.base_resolver(
            info, first=first, after=after
        ),
    ),
    ConnectionCase(
        name="admin_retention_policies",
        items=_retention_policies(),
        payload_type=SearchRetentionPoliciesPayload,
        adapter_owner="retention_policy",
        adapter_method="search",
        call=lambda info, first, after: admin_retention_policies.base_resolver(
            info, first=first, after=after
        ),
    ),
    ConnectionCase(
        name="admin_role_presets",
        items=_role_presets(),
        payload_type=SearchRolePresetsPayload,
        adapter_owner="role_preset",
        adapter_method="search",
        call=lambda info, first, after: admin_role_presets.base_resolver(
            info, first=first, after=after
        ),
    ),
    ConnectionCase(
        name="role_preset.permission_presets",
        items=_role_permission_presets(),
        payload_type=SearchRolePermissionPresetsPayload,
        adapter_owner="role_preset",
        adapter_method="search_permission_presets",
        call=lambda info, first, after: RolePresetGQL.permission_presets(
            SimpleNamespace(id=str(uuid.uuid4())), info, first=first, after=after
        ),
    ),
    ConnectionCase(
        name="deployment_revision_presets",
        items=_revision_presets(),
        payload_type=SearchDeploymentRevisionPresetsPayload,
        adapter_owner="deployment_revision_preset",
        adapter_method="search",
        call=lambda info, first, after: deployment_revision_presets.base_resolver(
            info, first=first, after=after
        ),
    ),
    ConnectionCase(
        name="model_card_available_presets",
        items=_revision_presets(),
        payload_type=SearchDeploymentRevisionPresetsPayload,
        adapter_owner="model_card",
        adapter_method="available_presets",
        call=lambda info, first, after: model_card_available_presets.base_resolver(
            info,
            ModelCardAvailablePresetsScopeGQL(model_card_id=uuid.uuid4()),
            first=first,
            after=after,
        ),
    ),
    ConnectionCase(
        name="admin_model_cards_v2",
        items=_model_cards(),
        payload_type=SearchModelCardsPayload,
        adapter_owner="model_card",
        adapter_method="admin_search",
        call=lambda info, first, after: admin_model_cards_v2.base_resolver(
            info, first=first, after=after
        ),
    ),
    ConnectionCase(
        name="vfolder.model_cards",
        items=_model_cards(),
        payload_type=SearchModelCardsPayload,
        adapter_owner="model_card",
        adapter_method="search_by_vfolder",
        call=lambda info, first, after: VFolderGQL.model_cards(
            SimpleNamespace(id=str(uuid.uuid4())), info, first=first, after=after
        ),
    ),
    ConnectionCase(
        name="my_entity_shares",
        items=_entity_shares(),
        payload_type=SearchEntitySharesPayload,
        adapter_owner="entity_share",
        adapter_method="my_search",
        call=lambda info, first, after: my_entity_shares.base_resolver(
            info, first=first, after=after
        ),
    ),
    ConnectionCase(
        name="replicas",
        items=_replicas(),
        payload_type=SearchReplicasPayload,
        adapter_owner="deployment",
        adapter_method="admin_search_replicas",
        call=lambda info, first, after: replicas_resolver.base_resolver(
            info, first=first, after=after
        ),
    ),
    ConnectionCase(
        name="deployment.replicas",
        items=_replicas(),
        payload_type=SearchReplicasPayload,
        adapter_owner="deployment",
        adapter_method="search_replicas",
        call=lambda info, first, after: ModelDeployment.replicas(
            SimpleNamespace(id=str(uuid.uuid4())), info, first=first, after=after
        ),
    ),
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
async def test_end_cursor_is_accepted_as_after(case: ConnectionCase) -> None:
    info = MagicMock()
    setattr(
        getattr(info.context.adapters, case.adapter_owner),
        case.adapter_method,
        _InMemorySearch(case.items, case.payload_type),
    )

    with with_user(_superadmin()):
        first_page = await case.call(info, _PAGE_SIZE, None)
        assert first_page is not None
        assert [edge.cursor for edge in first_page.edges] == [
            encode_cursor(item.id) for item in case.items[:_PAGE_SIZE]
        ]

        second_page = await case.call(info, _PAGE_SIZE, first_page.page_info.end_cursor)

    assert second_page is not None
    assert [str(edge.node.id) for edge in second_page.edges] == [
        str(item.id) for item in case.items[_PAGE_SIZE:]
    ]
