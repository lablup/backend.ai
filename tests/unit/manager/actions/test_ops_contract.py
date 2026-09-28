"""The behaviour every ``group.*_ops`` shape shares, checked once against the project.

A domain scenario wires its operation through the same shape, so it writes one success
and one failure row; the actor, target, duplicate, page and scope combinations live here.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass, replace
from typing import Any, Self, override
from unittest.mock import MagicMock

import pytest

from ai.backend.common.contexts.user import with_user_context
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID, DomainName
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction, BasePartialBulkAction
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.bulk.processor import (
    BulkActionProcessor,
    PartialEntityResultJudge,
)
from ai.backend.manager.actions.v2.bulk.result import (
    BasePartialBulkActionResult,
    BulkEntityResult,
    PartialBulkEntityResult,
    PartialBulkResult,
)
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.actions.validators.build import build_action_validators
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
    build_orders,
    build_pagination,
)
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.project.types import ProjectData, ProjectType
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.base.not_found import NotFoundError
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.agent.row import AgentRow
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
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.scopes import DomainProjectTarget
from ai.backend.manager.models.project.searchable_fields import ProjectSearchableFields
from ai.backend.manager.models.project.searchers import ProjectSearcher
from ai.backend.manager.models.project.updaters import ProjectSoftDeleteUpdater
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
from ai.backend.manager.models.specs.searcher import GlobalSearcher, ScopedSearcher
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
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.domain.actions.bulk_lookup import BulkLookupDomainsAction
from ai.backend.manager.services.project.actions.bulk_get import BulkGetProjectsAction
from ai.backend.manager.services.project.actions.delete_project import DeleteProjectAction
from ai.backend.manager.services.project.actions.lookup import LookupProjectAction
from ai.backend.manager.services.project.actions.scoped_search import ScopedSearchProjectsAction
from ai.backend.manager.services.project.actions.search_projects import (
    GetProjectAction,
    GlobalSearchProjectsAction,
)
from ai.backend.testutils.db import TableOrORM, with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

# Row imports above ensure mapper initialization (FK dependency order).
_WITH_TABLES: list[TableOrORM] = [
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
]

_PAGINATION_SPEC = PaginationSpec(
    forward_order=ProjectSearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=ProjectRow.id,
)


@dataclass(frozen=True)
class _Domain:
    id: DomainID
    name: DomainName


@dataclass(frozen=True)
class _World:
    """Four domains and the projects in them, and the user granted two of the domains.

    ``granted_a`` / ``granted_b`` are where the granted user holds every bit on projects;
    ``ungranted`` is in the graph with no role on it; ``outside`` has a row and no node.
    """

    granted_a: _Domain
    granted_b: _Domain
    ungranted: _Domain
    outside: _Domain
    projects_a: tuple[ProjectID, ...]
    projects_b: tuple[ProjectID, ...]
    project_ungranted: ProjectID
    project_outside: ProjectID
    granted_user: UserID
    ungranted_user: UserID

    def every_project(self) -> set[ProjectID]:
        return {
            *self.projects_a,
            *self.projects_b,
            self.project_ungranted,
            self.project_outside,
        }


@dataclass(frozen=True)
class _Processors:
    get: Any
    bulk_get: Any
    lookup: Any
    bulk_lookup_domains: Any
    global_search: Any
    scoped_search: Any
    delete: Any
    validators: ActionValidators


@pytest.fixture
async def db(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(global_entity_ids, _WITH_TABLES):
        yield global_entity_ids


def _project_row(project_id: ProjectID, domain: _Domain, policy_name: str) -> ProjectRow:
    return ProjectRow(
        id=project_id,
        name=f"project-{project_id.hex[:8]}",
        description=None,
        is_active=True,
        domain_name=domain.name,
        total_resource_slots=ResourceSlot(),
        allowed_vfolder_hosts=VFolderHostPermissionMap(),
        integration_id=None,
        resource_policy=policy_name,
        type=ProjectType.GENERAL,
    )


def _user_row(user_id: UserID, domain: _Domain, policy_name: str) -> UserRow:
    return UserRow(
        uuid=user_id,
        username=f"user-{user_id.hex[:8]}",
        email=f"user-{user_id.hex[:8]}@test.com",
        resource_policy=policy_name,
        status=UserStatus.ACTIVE,
        need_password_change=False,
        sudo_session_enabled=False,
        domain_name=domain.name,
        domain_id=domain.id,
        role=UserRole.USER,
    )


@pytest.fixture
async def world(db: ExtendedAsyncSAEngine) -> _World:
    seeder = VirtualEntitySeeder()
    domains = [
        _Domain(id=DomainID(uuid.uuid4()), name=DomainName(f"{label}-{uuid.uuid4().hex[:8]}"))
        for label in ("granted-a", "granted-b", "ungranted", "outside")
    ]
    granted_a, granted_b, ungranted, outside = domains
    projects_a = tuple(ProjectID(uuid.uuid4()) for _ in range(3))
    projects_b = (ProjectID(uuid.uuid4()),)
    project_ungranted = ProjectID(uuid.uuid4())
    project_outside = ProjectID(uuid.uuid4())
    granted_user = UserID(uuid.uuid4())
    ungranted_user = UserID(uuid.uuid4())
    user_policy = f"user-policy-{uuid.uuid4().hex[:8]}"
    project_policy = f"project-policy-{uuid.uuid4().hex[:8]}"

    async with db.begin_session() as sess:
        sess.add_all([
            DomainRow(id=domain.id, name=domain.name, total_resource_slots=ResourceSlot())
            for domain in domains
        ])
        sess.add(
            UserResourcePolicyRow(
                name=user_policy,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
        )
        sess.add(
            ProjectResourcePolicyRow(
                name=project_policy,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=0,
            )
        )
        await sess.flush()
        placed: list[tuple[ProjectID, _Domain]] = [
            *((project_id, granted_a) for project_id in projects_a),
            *((project_id, granted_b) for project_id in projects_b),
            (project_ungranted, ungranted),
        ]
        sess.add_all([
            _project_row(project_id, domain, project_policy) for project_id, domain in placed
        ])
        sess.add(_project_row(project_outside, outside, project_policy))
        sess.add_all([
            _user_row(granted_user, granted_a, user_policy),
            _user_row(ungranted_user, granted_a, user_policy),
        ])
        await sess.flush()

        for domain in (granted_a, granted_b, ungranted):
            await seeder.provision(sess, DomainEntityType(), domain.id)
        for project_id, domain in placed:
            await seeder.create_in(
                sess, ProjectEntityType(), project_id, [(DomainEntityType(), domain.id)]
            )
        await seeder.provision(sess, UserEntityType(), granted_user)
        await seeder.provision(sess, UserEntityType(), ungranted_user)

        for domain in (granted_a, granted_b):
            role = RoleRow(
                name=f"project-admin-{domain.id.hex[:8]}",
                status=RoleStatus.ACTIVE,
                scope_type=DomainEntityType(),
                scope_id=domain.id,
            )
            sess.add(role)
            await sess.flush()
            sess.add_all([
                PermissionRow(role_id=role.id, entity_type=ProjectEntityType(), permission=bit)
                for bit in Permission
                if bit and Permission.full() & bit
            ])
            sess.add(UserRoleRow(user_id=granted_user, role_id=role.id))
        await sess.commit()

    return _World(
        granted_a=granted_a,
        granted_b=granted_b,
        ungranted=ungranted,
        outside=outside,
        projects_a=projects_a,
        projects_b=projects_b,
        project_ungranted=project_ungranted,
        project_outside=project_outside,
        granted_user=granted_user,
        ungranted_user=ungranted_user,
    )


@pytest.fixture
def processors(db: ExtendedAsyncSAEngine) -> _Processors:
    """Each shape wired the way a domain wires it, with the production validators."""
    config_provider = MagicMock()
    config_provider.config.manager.rbac.enforcement_enabled = True
    check = RbacPermissionCheckRepository(PermissionOpsProvider(db), config_provider)
    validators = build_action_validators(check, config_provider)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=validators,
            repository=OpsRepository(V2DBOpsProvider(db)),
        )
    )
    projects = registry.group(GroupMeta(ProjectEntityType()))
    domains = registry.group(GroupMeta(DomainEntityType()))
    return _Processors(
        get=projects.single_get_ops(GetProjectAction),
        bulk_get=projects.partial_bulk_get_ops(BulkGetProjectsAction),
        lookup=projects.public_lookup_ops(LookupProjectAction),
        bulk_lookup_domains=domains.public_bulk_lookup_ops(BulkLookupDomainsAction),
        global_search=projects.global_searcher_ops(GlobalSearchProjectsAction),
        scoped_search=projects.scoped_search_ops(ScopedSearchProjectsAction),
        delete=projects.single_delete_ops(DeleteProjectAction),
        validators=validators,
    )


def _user(user_id: UserID, domain: _Domain) -> UserData:
    return UserData(
        user_id=user_id,
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name=domain.name,
        domain_id=domain.id,
    )


def _granted(world: _World) -> UserData:
    return _user(world.granted_user, world.granted_a)


def _ungranted(world: _World) -> UserData:
    return _user(world.ungranted_user, world.granted_a)


def _superadmin(world: _World) -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=True,
        is_superadmin=True,
        role=UserRole.SUPERADMIN,
        domain_name=world.granted_a.name,
        domain_id=world.granted_a.id,
    )


def _actor(world: _World, name: str) -> UserData:
    match name:
        case "granted":
            return _granted(world)
        case "ungranted":
            return _ungranted(world)
        case "superadmin":
            return _superadmin(world)
    raise ValueError(name)


def _searcher(options: PaginationOptions) -> ProjectSearcher:
    return ProjectSearcher(
        pagination=build_pagination(options, _PAGINATION_SPEC),
        orders=build_orders(options, _PAGINATION_SPEC, []),
    )


class TestPartialBulkGetOps:
    """``partial_bulk_get_ops``."""

    async def test_bulk_get_lets_a_superadmin_read_an_entity_outside_the_graph(
        self, processors: _Processors, world: _World
    ) -> None:
        ids = [world.projects_a[0], world.project_outside]

        with with_user_context(_superadmin(world)):
            result: PartialBulkResult[ProjectData] = await processors.bulk_get.run(
                BulkGetProjectsAction(ids=ids)
            )

        assert [item.entity_id for item in result.items] == ids
        assert {entity_id: data.id for entity_id, data in result.values().items()} == {
            entity_id: entity_id for entity_id in ids
        }

    async def test_bulk_get_answers_a_repeated_id_the_same_at_every_place(
        self, processors: _Processors, world: _World
    ) -> None:
        repeated, other = world.projects_a[0], world.projects_b[0]
        ids = [repeated, other, repeated]

        with with_user_context(_granted(world)):
            result: PartialBulkResult[ProjectData] = await processors.bulk_get.run(
                BulkGetProjectsAction(ids=ids)
            )

        assert [item.entity_id for item in result.items] == ids
        first, _, second = result.items
        assert first.error is None and second.error is None
        assert first.value is not None and second.value is not None
        assert first.value.id == second.value.id == repeated

    async def test_bulk_get_denies_a_repeated_id_at_every_place(
        self, processors: _Processors, world: _World
    ) -> None:
        repeated, other = world.projects_a[0], world.projects_b[0]
        ids = [repeated, other, repeated]

        with with_user_context(_ungranted(world)):
            result: PartialBulkResult[ProjectData] = await processors.bulk_get.run(
                BulkGetProjectsAction(ids=ids)
            )

        assert [item.entity_id for item in result.items] == ids
        assert all(item.is_denied for item in result.items)
        assert all(isinstance(item.error, NotEnoughPermission) for item in result.items)

    @pytest.mark.parametrize("actor", ["granted", "ungranted", "superadmin"])
    async def test_bulk_get_of_no_ids_answers_nothing(
        self, processors: _Processors, world: _World, actor: str
    ) -> None:
        with with_user_context(_actor(world, actor)):
            result: PartialBulkResult[ProjectData] = await processors.bulk_get.run(
                BulkGetProjectsAction(ids=[])
            )

        assert result.items == []


class TestPublicLookupOps:
    """``public_lookup_ops`` and ``public_bulk_lookup_ops``."""

    async def test_lookup_refuses_a_caller_with_no_user(
        self, processors: _Processors, world: _World
    ) -> None:
        project = world.projects_a[0]

        with pytest.raises(UserNotFound):
            await processors.lookup.run(
                LookupProjectAction(
                    domain_name=world.granted_a.name, project_name=f"project-{project.hex[:8]}"
                )
            )

    async def test_lookup_refuses_an_unauthorized_caller(
        self, processors: _Processors, world: _World
    ) -> None:
        project = world.projects_a[0]
        caller = replace(_granted(world), is_authorized=False)

        with with_user_context(caller):
            with pytest.raises(GenericForbidden):
                await processors.lookup.run(
                    LookupProjectAction(
                        domain_name=world.granted_a.name, project_name=f"project-{project.hex[:8]}"
                    )
                )

    @pytest.mark.parametrize("actor", ["granted", "ungranted", "superadmin"])
    async def test_bulk_lookup_answers_every_key_it_was_given(
        self, processors: _Processors, world: _World, actor: str
    ) -> None:
        present = world.granted_a
        missing = DomainName(f"missing-{uuid.uuid4().hex[:8]}")
        names = [present.name, missing, present.name]

        with with_user_context(_actor(world, actor)):
            result = await processors.bulk_lookup_domains.run(BulkLookupDomainsAction(names=names))

        assert [(r.status, r.entity_id) for r in result.key_results()] == [
            (OperationStatus.SUCCESS, present.id),
            (OperationStatus.ERROR, None),
            (OperationStatus.SUCCESS, present.id),
        ]


_SINGLE_EXPECTATIONS: list[tuple[str, bool, type[Exception] | None]] = [
    ("granted", True, None),
    ("ungranted", True, NotEnoughPermission),
    ("superadmin", True, None),
    ("granted", False, NotEnoughPermission),
    ("ungranted", False, NotEnoughPermission),
    ("superadmin", False, NotFoundError),
]


def _single_ids(expectation: tuple[str, bool, type[Exception] | None]) -> str:
    actor, exists, _ = expectation
    return f"{actor}-{'present' if exists else 'missing'}"


class TestSingleEntityOps:
    """``single_get_ops`` and ``single_delete_ops``."""

    @pytest.mark.parametrize("expectation", _SINGLE_EXPECTATIONS, ids=_single_ids)
    async def test_single_get_by_actor_and_target(
        self,
        processors: _Processors,
        world: _World,
        expectation: tuple[str, bool, type[Exception] | None],
    ) -> None:
        actor, exists, error = expectation
        target = world.projects_a[0] if exists else ProjectID(uuid.uuid4())

        with with_user_context(_actor(world, actor)):
            if error is None:
                result = await processors.get.run(GetProjectAction(project_id=target))
                assert result.data.id == target
            else:
                with pytest.raises(error):
                    await processors.get.run(GetProjectAction(project_id=target))

    @pytest.mark.parametrize("expectation", _SINGLE_EXPECTATIONS, ids=_single_ids)
    async def test_single_delete_by_actor_and_target(
        self,
        processors: _Processors,
        world: _World,
        expectation: tuple[str, bool, type[Exception] | None],
    ) -> None:
        actor, exists, error = expectation
        target = world.projects_a[0] if exists else ProjectID(uuid.uuid4())
        action = DeleteProjectAction(updater=ProjectSoftDeleteUpdater(project_id=target))

        with with_user_context(_actor(world, actor)):
            if error is None:
                result = await processors.delete.run(action)
                assert result.data.id == target
            else:
                with pytest.raises(error):
                    await processors.delete.run(action)


class TestGlobalSearcherOps:
    """``global_searcher_ops``."""

    async def test_global_search_cursor_pages_neither_overlap_nor_skip(
        self, processors: _Processors, world: _World
    ) -> None:
        """Every project is created in one transaction, so the order column ties throughout."""
        seen: list[uuid.UUID] = []
        after: str | None = None
        with with_user_context(_superadmin(world)):
            while True:
                searcher = _searcher(PaginationOptions(first=2, after=after))
                page = await processors.global_search.run(
                    GlobalSearchProjectsAction(
                        searcher=GlobalSearcher(used_by=(), searcher=searcher)
                    )
                )
                seen.extend(item.id for item in page.items)
                if not page.has_next_page:
                    break
                after = encode_cursor(page.items[-1].id)

        assert len(seen) == len(set(seen))
        assert set(seen) == world.every_project()

    async def test_global_search_offset_pages_neither_overlap_nor_skip(
        self, processors: _Processors, world: _World
    ) -> None:
        seen: list[uuid.UUID] = []
        offset = 0
        with with_user_context(_superadmin(world)):
            while True:
                searcher = _searcher(PaginationOptions(limit=2, offset=offset))
                page = await processors.global_search.run(
                    GlobalSearchProjectsAction(
                        searcher=GlobalSearcher(used_by=(), searcher=searcher)
                    )
                )
                seen.extend(item.id for item in page.items)
                if not page.has_next_page:
                    break
                offset += 2

        assert len(seen) == len(set(seen))
        assert set(seen) == world.every_project()

    async def test_global_search_refuses_a_caller_granted_only_in_scopes(
        self, processors: _Processors, world: _World
    ) -> None:
        searcher = _searcher(PaginationOptions(limit=10))

        with with_user_context(_granted(world)):
            with pytest.raises(InsufficientPrivilege):
                await processors.global_search.run(
                    GlobalSearchProjectsAction(
                        searcher=GlobalSearcher(used_by=(), searcher=searcher)
                    )
                )


def _scoped(domains: Sequence[_Domain]) -> ScopedSearchProjectsAction:
    return ScopedSearchProjectsAction(
        searcher=ScopedSearcher(
            scopes=[DomainProjectTarget(domain_id=domain.id) for domain in domains],
            used_by=(),
            searcher=_searcher(PaginationOptions(limit=100)),
        )
    )


class TestScopedSearchOps:
    """``scoped_search_ops``."""

    async def test_scoped_search_over_two_granted_scopes_reads_their_union_once(
        self, processors: _Processors, world: _World
    ) -> None:
        with with_user_context(_granted(world)):
            result = await processors.scoped_search.run(_scoped([world.granted_a, world.granted_b]))

        ids = [item.id for item in result.items]
        assert len(ids) == len(set(ids))
        assert set(ids) == {*world.projects_a, *world.projects_b}

    async def test_scoped_search_naming_one_ungranted_scope_is_refused_whole(
        self, processors: _Processors, world: _World
    ) -> None:
        with with_user_context(_granted(world)):
            with pytest.raises(NotEnoughPermission):
                await processors.scoped_search.run(_scoped([world.granted_a, world.ungranted]))

    async def test_scoped_search_lets_a_superadmin_name_a_scope_outside_the_graph(
        self, processors: _Processors, world: _World
    ) -> None:
        with with_user_context(_superadmin(world)):
            result = await processors.scoped_search.run(_scoped([world.outside]))

        assert result.total_count == len(result.items)


@dataclass
class _PurgeProjectsPartially(BasePartialBulkAction):
    ids: Sequence[ProjectID]

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "purge_projects_partially"


@dataclass
class _PurgeProjectsAtomically(BaseBulkAction):
    ids: Sequence[ProjectID]

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "purge_projects_atomically"


@dataclass
class _AtomicResult(BasePartialBulkActionResult):
    results: Sequence[BulkEntityResult]

    @override
    def entity_results(self) -> Sequence[BulkEntityResult]:
        return self.results


class TestManyRowWrites:
    """A partial shape answers a mixed run per entity; an atomic one refuses it whole."""

    async def test_partial_bulk_write_answers_a_mixed_run_per_entity(
        self, processors: _Processors, world: _World
    ) -> None:
        granted, ungranted = world.projects_a[0], world.project_ungranted
        written: list[EntityIdentifier] = []

        async def purge(action: _PurgeProjectsPartially) -> PartialBulkResult[str]:
            written.extend(action.entity_ids())
            return PartialBulkResult(
                items=[
                    PartialBulkEntityResult[str].succeeded(entity_id, "purged")
                    for entity_id in action.entity_ids()
                ]
            )

        processor = PartialBulkActionProcessor[_PurgeProjectsPartially, str](
            purge, partial_validators=processors.validators.partial_bulk
        )

        with with_user_context(_granted(world)):
            result = await processor.run(_PurgeProjectsPartially(ids=[granted, ungranted]))

        assert written == [granted]
        assert result.values() == {granted: "purged"}
        assert isinstance(result.errors()[ungranted], NotEnoughPermission)

    async def test_atomic_bulk_write_refuses_a_mixed_run_whole(
        self, processors: _Processors, world: _World
    ) -> None:
        granted, ungranted = world.projects_a[0], world.project_ungranted
        written: list[EntityIdentifier] = []

        async def purge(action: _PurgeProjectsAtomically) -> _AtomicResult:
            written.extend(action.entity_ids())
            return _AtomicResult(results=[])

        processor = BulkActionProcessor[_PurgeProjectsAtomically, _AtomicResult](
            func=purge,
            judge=PartialEntityResultJudge(),
            validators=processors.validators.atomic_bulk,
        )

        with with_user_context(_granted(world)):
            with pytest.raises(NotEnoughPermission):
                await processor.run(_PurgeProjectsAtomically(ids=[granted, ungranted]))

        assert written == []
