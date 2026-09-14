from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.audit_log import AuditLogFieldType
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    Concern,
    ConcernMeta,
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.scope.monitor.audit_log import ScopeActionAuditLogMonitor
from ai.backend.manager.actions.v2.scope.validator.rbac import VirtualEntityScopeActionRBACValidator
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.data.permission.virtual_entity import GovernCheckKey
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.base.export import StreamingExportQuery
from ai.backend.manager.repositories.client_ip_masking.repository import ClientIPMaskingRepository
from ai.backend.manager.repositories.export.repository import ExportRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.services.export.actions.export_my_keypairs_csv import (
    ExportMyKeypairsCSVAction,
)
from ai.backend.manager.services.export.processors import ExportProcessors
from ai.backend.manager.services.export.service import ExportService


@pytest.fixture
def query() -> StreamingExportQuery:
    return StreamingExportQuery(
        select_from=sa.table("export_test"),
        fields=[],
        conditions=[],
        orders=[],
        max_rows=100,
        statement_timeout_sec=30,
    )


@pytest.fixture
def actor() -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


@pytest.fixture
def permission_repository() -> MagicMock:
    repository = MagicMock(spec=PermissionControllerRepository)
    repository.governed_permissions.return_value = {}
    return repository


@pytest.fixture
def export_repository() -> MagicMock:
    return MagicMock(spec=ExportRepository)


@pytest.fixture
def audit_repository() -> MagicMock:
    return MagicMock(spec=OpsRepository)


@pytest.fixture
def registry(
    permission_repository: MagicMock,
    audit_repository: MagicMock,
) -> ProcessorRegistry[Any]:
    config = MagicMock(spec=ManagerConfigProvider)
    config.config.manager.rbac.enforcement_enabled = True
    masking = MagicMock(spec=ClientIPMaskingRepository)
    masking.mask.return_value = None
    policy = AuditLogPolicy([ActionOperationType.SEARCH])
    return ProcessorRegistry(
        ProcessorDependencies(
            repository=OpsRepository(MagicMock()),
            monitors=ActionMonitors(
                scope=[ScopeActionAuditLogMonitor(audit_repository, policy, masking)],
            ),
            validators=ActionValidators(
                scope=[VirtualEntityScopeActionRBACValidator(permission_repository, config)]
            ),
        )
    )


@pytest.fixture
def processors(registry: ProcessorRegistry[Any], export_repository: MagicMock) -> ExportProcessors:
    groups = registry.concern(ConcernMeta(Concern.VISIBILITY))
    return ExportProcessors(
        groups.group(GroupMeta(UserEntityType())),
        groups.group(GroupMeta(SessionEntityType())),
        groups.group(GroupMeta(ProjectEntityType())),
        groups.group(GroupMeta(GlobalEntityType())),
        groups.dangling_field_group(FieldGroupMeta(AuditLogFieldType()), AuditLogData),
        ExportService(export_repository),
    )


class TestScopedExportPermissions:
    async def test_my_keypairs_requires_read_on_the_target_within_its_scope(
        self,
        processors: ExportProcessors,
        actor: UserData,
        query: StreamingExportQuery,
        permission_repository: MagicMock,
        audit_repository: MagicMock,
    ) -> None:
        scope = UserID(actor.user_id)
        permission_repository.governed_permissions.return_value = {
            GovernCheckKey(
                user_id=UserID(actor.user_id), scope=scope, entity_type=UserEntityType()
            ): Permission.READ,
        }
        with with_user(actor):
            await processors.export_my_keypairs_csv.run(
                ExportMyKeypairsCSVAction(user_uuid=UserID(actor.user_id), query=query)
            )
        specs, scopes = audit_repository.atomic_create_dangling_fields_with_nested.call_args.args
        record = specs[0]
        assert record.entity_type == UserEntityType()
        assert record.operation == ActionOperationType.SEARCH
        assert [(item.scope_type, item.scope_id) for item in scopes] == [
            (str(scope.entity_type()), scope)
        ]

    async def test_my_keypairs_without_read_permission_are_denied_before_export(
        self,
        processors: ExportProcessors,
        actor: UserData,
        query: StreamingExportQuery,
        export_repository: MagicMock,
        audit_repository: MagicMock,
    ) -> None:
        with with_user(actor), pytest.raises(NotEnoughPermission):
            await processors.export_my_keypairs_csv.run(
                ExportMyKeypairsCSVAction(user_uuid=UserID(actor.user_id), query=query)
            )
        export_repository.execute_export.assert_not_called()
        specs, _ = audit_repository.atomic_create_dangling_fields_with_nested.call_args.args
        record = specs[0]
        assert record.entity_type == UserEntityType()
        assert record.status == OperationStatus.DENIED
