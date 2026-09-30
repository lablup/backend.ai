"""Actors, grants, and the production gates and audit trail for the per-shape ops tests.

Each shape's test file wires its representative action through :class:`OpsHarness`,
seeds its rows, grants the actors with :func:`grant`, and reads the trail back with
:meth:`OpsHarness.audit`.
"""

from __future__ import annotations

import enum
import uuid
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, override
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.contexts.user import with_user_context
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID, DomainName
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.exception import BackendAIError, ErrorDetail
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.bulk.monitor.audit_log import BulkActionAuditLogMonitor
from ai.backend.manager.actions.v2.global_scope.monitor.audit_log import (
    GlobalActionAuditLogMonitor,
)
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction
from ai.backend.manager.actions.v2.lookup.bulk_monitor.audit_log import (
    BulkLookupActionAuditLogMonitor,
)
from ai.backend.manager.actions.v2.lookup.monitor.audit_log import LookupActionAuditLogMonitor
from ai.backend.manager.actions.v2.lookup.monitor.base import LookupActionMonitor
from ai.backend.manager.actions.v2.lookup.result import (
    LookupActionProcessResult,
    LookupActionResultMeta,
)
from ai.backend.manager.actions.v2.scope.monitor.audit_log import ScopeActionAuditLogMonitor
from ai.backend.manager.actions.v2.single_entity.monitor.audit_log import (
    SingleEntityActionAuditLogMonitor,
)
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta
from ai.backend.manager.actions.validators.build import build_action_validators
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.project.types import ProjectStatus, ProjectType
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy.row import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.client_ip_masking.repository import (
    ClientIPMaskingRepository,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.testutils.db import TableOrORM
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

__all__ = (
    "ANONYMOUS_NOT_REFUSED",
    "ANONYMOUS_RECORDED_AS_ERROR",
    "FIELD_WRITE_NEEDS_OWNER_READ",
    "ANONYMOUS_RUNS_UNENFORCED",
    "BASE_TABLES",
    "MONITOR_READ_REFUSED",
    "Actor",
    "Actors",
    "AuditRecord",
    "OpsHarness",
    "assert_refused",
    "entity_key",
    "grant",
    "provision",
    "seed_actors",
)

# Row imports above and here ensure mapper initialization (FK dependency order).
BASE_TABLES: list[TableOrORM] = [
    DomainRow,
    ResourceGroupRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    RoleRow,
    UserRoleRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    ContainerRegistryRow,
    ImageRow,
    VFolderRow,
    EndpointRow,
    DeploymentPolicyRow,
    DeploymentAutoScalingPolicyRow,
    RuntimeVariantRow,
    DeploymentRevisionPresetRow,
    DeploymentRevisionRow,
    SessionRow,
    AgentRow,
    KernelRow,
    ReplicaGroupRow,
    RoutingRow,
    ResourcePresetRow,
    PermissionRow,
    VirtualEntityRow,
    ScopeBindingRow,
    EntityLabelRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
    ModelCardRow,
    EntityShareRow,
    AuditLogRow,
    AuditLogScopeRow,
    ClientIPMaskingPolicyRow,
]

# Where the expectation table and the code part ways; each is a separate Bug.
MONITOR_READ_REFUSED = pytest.mark.xfail(
    strict=True, reason="a monitor passes reads only at the global gate"
)
ANONYMOUS_RECORDED_AS_ERROR = pytest.mark.xfail(
    strict=True, reason="a caller with no user is recorded as ERROR, not DENIED"
)
ANONYMOUS_NOT_REFUSED = pytest.mark.xfail(
    strict=True, reason="a caller with no user fails with an error that is not a refusal"
)
FIELD_WRITE_NEEDS_OWNER_READ = pytest.mark.xfail(
    strict=True, reason="a field write needs READ on the owner to pass the owner lookup"
)
ANONYMOUS_RUNS_UNENFORCED = pytest.mark.xfail(
    strict=True,
    reason="with enforcement off the single-entity and scope gates pass a caller with no user",
)


class Actor(enum.StrEnum):
    SUPERADMIN = "superadmin"
    MONITOR = "monitor"
    GRANTED = "granted"
    READ_ONLY = "read_only"
    UNGRANTED = "ungranted"
    ANONYMOUS = "anonymous"


_ROLES: dict[Actor, UserRole] = {
    Actor.SUPERADMIN: UserRole.SUPERADMIN,
    Actor.MONITOR: UserRole.MONITOR,
    Actor.GRANTED: UserRole.USER,
    Actor.READ_ONLY: UserRole.USER,
    Actor.UNGRANTED: UserRole.USER,
}


@dataclass(frozen=True)
class Actors:
    """The actors every shape is run as, all in one domain the graph knows."""

    domain_id: DomainID
    domain_name: DomainName
    users: dict[Actor, UserID]

    def user_id(self, actor: Actor) -> UserID:
        return self.users[actor]

    def user_data(self, actor: Actor) -> UserData | None:
        if actor is Actor.ANONYMOUS:
            return None
        role = _ROLES[actor]
        return UserData(
            user_id=self.users[actor],
            is_authorized=True,
            is_admin=role is UserRole.SUPERADMIN,
            is_superadmin=role is UserRole.SUPERADMIN,
            role=role,
            domain_name=self.domain_name,
            domain_id=self.domain_id,
        )

    @contextmanager
    def acting_as(self, actor: Actor) -> Iterator[None]:
        with with_user_context(self.user_data(actor)):
            yield


async def seed_actors(db: ExtendedAsyncSAEngine) -> Actors:
    """A domain and one user per actor, each with a node in the graph and no role."""
    seeder = VirtualEntitySeeder()
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"actors-{domain_id.hex[:8]}")
    policy = f"actors-policy-{domain_id.hex[:8]}"
    users = {actor: UserID(uuid.uuid4()) for actor in _ROLES}
    async with db.begin_session() as sess:
        sess.add(DomainRow(id=domain_id, name=domain_name, total_resource_slots=ResourceSlot()))
        sess.add(
            UserResourcePolicyRow(
                name=policy,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
        )
        await sess.flush()
        sess.add_all([
            UserRow(
                uuid=user_id,
                username=f"{actor}-{user_id.hex[:8]}",
                email=f"{actor}-{user_id.hex[:8]}@test.com",
                resource_policy=policy,
                status=UserStatus.ACTIVE,
                need_password_change=False,
                sudo_session_enabled=False,
                domain_name=domain_name,
                domain_id=domain_id,
                role=_ROLES[actor],
            )
            for actor, user_id in users.items()
        ])
        await sess.flush()
        await seeder.provision(sess, DomainEntityType(), domain_id)
        for user_id in users.values():
            await seeder.provision(sess, UserEntityType(), user_id)
        await sess.commit()
    return Actors(domain_id=domain_id, domain_name=domain_name, users=users)


async def provision(
    db: ExtendedAsyncSAEngine,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    scopes: Sequence[tuple[EntityType, uuid.UUID]] = (),
) -> None:
    """Give an entity its node, created in the given scopes."""
    seeder = VirtualEntitySeeder()
    async with db.begin_session() as sess:
        if scopes:
            await seeder.create_in(sess, entity_type, entity_id, scopes)
        else:
            await seeder.provision(sess, entity_type, entity_id)
        await sess.commit()


async def grant(
    db: ExtendedAsyncSAEngine,
    user_id: UserID,
    scope_type: EntityType,
    scope_id: uuid.UUID,
    entity_type: EntityType,
    permission: Permission,
) -> None:
    """A role at the scope holding ``permission`` on ``entity_type``, assigned to the user.

    Granting at the entity itself reaches that entity alone: its node governs itself.
    """
    seeder = VirtualEntitySeeder()
    async with db.begin_session() as sess:
        await seeder.provision(sess, scope_type, scope_id)
        role = RoleRow(
            name=f"grant-{uuid.uuid4().hex[:12]}",
            status=RoleStatus.ACTIVE,
            scope_type=scope_type,
            scope_id=scope_id,
        )
        sess.add(role)
        await sess.flush()
        sess.add_all([
            PermissionRow(role_id=role.id, entity_type=entity_type, permission=bit)
            for bit in Permission
            if bit and permission & bit
        ])
        sess.add(UserRoleRow(user_id=user_id, role_id=role.id))
        await sess.commit()


async def seed_project(
    db: ExtendedAsyncSAEngine,
    actors: Actors,
    *,
    project_type: ProjectType = ProjectType.GENERAL,
    status: ProjectStatus = ProjectStatus.ACTIVE,
) -> ProjectID:
    """A project in the actors' domain, created there in the graph."""
    project_id = ProjectID(uuid.uuid4())
    policy = f"project-policy-{project_id.hex[:8]}"
    async with db.begin_session() as sess:
        sess.add(
            ProjectResourcePolicyRow(
                name=policy,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=0,
            )
        )
        await sess.flush()
        sess.add(
            ProjectRow(
                id=project_id,
                name=f"project-{project_id.hex[:8]}",
                description=None,
                is_active=status is ProjectStatus.ACTIVE,
                status=status,
                domain_name=actors.domain_name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                integration_id=None,
                resource_policy=policy,
                type=project_type,
            )
        )
        await sess.flush()
        await VirtualEntitySeeder().create_in(
            sess, ProjectEntityType(), project_id, [(DomainEntityType(), actors.domain_id)]
        )
        await sess.commit()
    return project_id


async def project_status(db: ExtendedAsyncSAEngine, project_id: ProjectID) -> ProjectStatus:
    async with db.begin_readonly_session() as sess:
        return (
            await sess.execute(sa.select(ProjectRow.status).where(ProjectRow.id == project_id))
        ).scalar_one()


@dataclass(frozen=True)
class AuditRecord:
    """One audit row as the tests compare it."""

    entity_type: str | None
    entity_id: str | None
    operation: str
    status: OperationStatus
    description: str
    lookup_kind: str | None
    lookup_key: str | None
    scopes: frozenset[tuple[str, str]]


class _LookupRecorder(LookupActionMonitor):
    results: list[LookupActionResultMeta]

    def __init__(self) -> None:
        self.results = []

    @override
    async def prepare(self, action: BaseLookupAction, meta: ActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, action: BaseLookupAction, result: LookupActionProcessResult) -> None:
        self.results.append(result.meta)


def assert_refused(error: BaseException) -> None:
    """The run was refused, as opposed to failing on the server."""
    if not isinstance(error, BackendAIError):
        raise AssertionError(f"not a refusal: {error!r}")
    detail = error.error_code().error_detail
    if detail not in (ErrorDetail.FORBIDDEN, ErrorDetail.UNAUTHORIZED):
        raise AssertionError(f"not a refusal: {error!r} ({detail})")


class OpsHarness:
    """The production gates and audit monitors over one database.

    RBAC enforcement starts on and can be switched per test; whether successful reads
    are recorded is fixed per harness, as the configuration fixes it per server.
    """

    _db: ExtendedAsyncSAEngine
    _config_provider: MagicMock
    _registry: ProcessorRegistry[Any]
    _lookup_recorder: _LookupRecorder

    def __init__(self, db: ExtendedAsyncSAEngine, *, record_reads: bool = True) -> None:
        self._db = db
        self._config_provider = MagicMock()
        self._config_provider.config.manager.rbac.enforcement_enabled = True
        check = RbacPermissionCheckRepository(PermissionOpsProvider(db), self._config_provider)
        audit_repository: OpsRepository[AuditLogData] = OpsRepository(V2DBOpsProvider(db))
        policy = AuditLogPolicy(ActionOperationType.read_operations() if record_reads else ())
        masking = ClientIPMaskingRepository(db)
        self._lookup_recorder = _LookupRecorder()
        monitors = ActionMonitors(
            single_entity=[SingleEntityActionAuditLogMonitor(audit_repository, policy, masking)],
            bulk=[BulkActionAuditLogMonitor(audit_repository, policy, masking)],
            scope=[ScopeActionAuditLogMonitor(audit_repository, policy, masking)],
            global_scope=[GlobalActionAuditLogMonitor(audit_repository, policy, masking)],
            lookup=[
                LookupActionAuditLogMonitor(audit_repository, policy, masking),
                self._lookup_recorder,
            ],
            bulk_lookup=[BulkLookupActionAuditLogMonitor(audit_repository, policy, masking)],
        )
        self._registry = ProcessorRegistry(
            ProcessorDependencies(
                monitors=monitors,
                validators=build_action_validators(check, self._config_provider),
                repository=OpsRepository(V2DBOpsProvider(db)),
            )
        )

    @property
    def registry(self) -> ProcessorRegistry[Any]:
        """For the groups a domain reaches through ``registry.concern(...)``."""
        return self._registry

    @property
    def lookup_results(self) -> list[LookupActionResultMeta]:
        """What every lookup run ended with, error codes included."""
        return self._lookup_recorder.results

    def group(self, entity_type: EntityType) -> ProcessorGroup[Any]:
        return self._registry.group(GroupMeta(entity_type))

    def enforce(self, enabled: bool) -> None:
        self._config_provider.config.manager.rbac.enforcement_enabled = enabled

    async def audit(self, action_name: str) -> list[AuditRecord]:
        async with self._db.begin_readonly_session() as sess:
            rows = (
                await sess.scalars(
                    sa.select(AuditLogRow).where(AuditLogRow.action_name == action_name)
                )
            ).all()
            scope_rows = (
                await sess.execute(
                    sa.select(
                        AuditLogScopeRow.audit_log_id,
                        AuditLogScopeRow.scope_type,
                        AuditLogScopeRow.scope_id,
                    ).where(AuditLogScopeRow.audit_log_id.in_([row.id for row in rows]))
                )
            ).all()
        scopes: dict[Any, set[tuple[str, str]]] = {}
        for audit_log_id, scope_type, scope_id in scope_rows:
            scopes.setdefault(audit_log_id, set()).add((scope_type, scope_id))
        return [
            AuditRecord(
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                operation=row.operation,
                status=row.status,
                description=row.description,
                lookup_kind=row.lookup_kind,
                lookup_key=row.lookup_key,
                scopes=frozenset(scopes.get(row.id, ())),
            )
            for row in rows
        ]


def entity_key(entity_id: EntityIdentifier) -> tuple[str, str]:
    """The ``(entity_type, entity_id)`` pair an audit row names an entity by."""
    return (str(entity_id.entity_type()), str(entity_id))
