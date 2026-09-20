"""Project adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from typing import assert_never
from uuid import UUID

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.group.request import (
    AdminSearchProjectsInput,
    AssignUsersToProjectInput,
    CreateProjectInput,
    DeleteProjectInput,
    ProjectFilter,
    ProjectOrder,
    PurgeProjectInput,
    RestoreProjectInput,
    ScopedSearchProjectsInput,
    UnassignUsersFromProjectInput,
    UpdateProjectInput,
)
from ai.backend.common.dto.manager.v2.group.response import (
    AdminSearchGroupsPayload,
    AssignUsersToProjectPayload,
    DeleteProjectPayload,
    ProjectBasicInfo,
    ProjectLifecycleInfo,
    ProjectNode,
    ProjectOrganizationInfo,
    ProjectPayload,
    ProjectStorageInfo,
    PurgeProjectPayload,
    RestoreProjectPayload,
    UnassignUserError,
    UnassignUsersFromProjectPayload,
    VFolderHostPermissionEntry,
)
from ai.backend.common.dto.manager.v2.group.types import (
    OrderDirection,
    ProjectDomainFilter,
    ProjectOrderField,
    ProjectScope,
    ProjectType,
    ProjectTypeFilter,
    ProjectUserFilter,
)
from ai.backend.common.dto.manager.v2.user.response import UserNode
from ai.backend.common.exception import UnreachableError
from ai.backend.common.types import AccessKey
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.project.types import ProjectType as DataProjectType
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.domain.searchable_fields import DomainSearchableFields
from ai.backend.manager.models.project.creators import ProjectCreator
from ai.backend.manager.models.project.deprecated_search import (
    DeprecatedProjectConditions,
    DeprecatedProjectOrders,
)
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.scopes import (
    DomainProjectTarget,
    ProjectTarget,
    UserProjectTarget,
)
from ai.backend.manager.models.project.searchable_fields import ProjectSearchableFields
from ai.backend.manager.models.project.searchers import ProjectSearcher
from ai.backend.manager.models.project.updaters import (
    ProjectRestoreUpdater,
    ProjectSoftDeleteUpdater,
    ProjectUpdater,
)
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.models.user.searchable_fields import UserSearchableFields
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.project.actions.bulk_get import BulkGetProjectsAction
from ai.backend.manager.services.project.actions.create_project import CreateProjectAction
from ai.backend.manager.services.project.actions.delete_project import DeleteProjectAction
from ai.backend.manager.services.project.actions.purge_project import PurgeProjectAction
from ai.backend.manager.services.project.actions.restore_project import RestoreProjectAction
from ai.backend.manager.services.project.actions.scoped_search import (
    ScopedSearchProjectsAction,
)
from ai.backend.manager.services.project.actions.search_projects import (
    GetProjectAction,
    GlobalSearchProjectsAction,
)
from ai.backend.manager.services.project.actions.update_project import UpdateProjectAction
from ai.backend.manager.services.project.processors import ProjectProcessors
from ai.backend.manager.services.rbac.actions.roster.join_project import (
    JoinProjectAction,
)
from ai.backend.manager.services.rbac.actions.roster.leave_project import (
    LeaveProjectAction,
)
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.manager.services.user.actions.keypair_ops import GetDefaultKeypairsAction
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.types import OptionalState, TriState

_PROJECT_PAGINATION_SPEC = PaginationSpec(
    forward_order=ProjectSearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=ProjectRow.id,
)


class ProjectAdapter(BaseAdapter):
    """Adapter for project (group) operations."""

    _project: ProjectProcessors
    _rbac: RbacProcessors
    _domain: DomainProcessors
    _user: UserProcessors

    def __init__(
        self,
        project: ProjectProcessors,
        rbac: RbacProcessors,
        domain: DomainProcessors,
        user: UserProcessors,
    ) -> None:
        self._project = project
        self._rbac = rbac
        self._domain = domain
        self._user = user

    async def _resolve_domain_id(self, domain_name: str) -> DomainID:
        result = await self._domain.lookup.run(LookupDomainAction(name=DomainName(domain_name)))
        return result.entity_id()

    # ------------------------------------------------------------------ batch load (DataLoader)

    async def batch_load_by_ids(
        self, group_ids: Sequence[ProjectID]
    ) -> list[ProjectNode | Exception | None]:
        """Batch load projects by UUID for DataLoader use, checked per project."""
        if not group_ids:
            return []
        result = await self._project.bulk_get.run(BulkGetProjectsAction(ids=list(group_ids)))
        return [
            self._group_data_to_node(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    # ------------------------------------------------------------------ get

    async def get(self, project_id: UUID) -> ProjectNode:
        """Retrieve a single project by UUID."""
        action_result = await self._project.get_project.run(
            GetProjectAction(project_id=ProjectID(project_id))
        )
        return self._group_data_to_node(action_result.data)

    async def admin_search(
        self,
        input: AdminSearchProjectsInput,
    ) -> AdminSearchGroupsPayload:
        """Search projects (admin, no scope) with filters, orders, and pagination."""
        conditions = self._convert_group_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            ProjectSearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=_PROJECT_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

        result = await self._project.global_search.run(
            GlobalSearchProjectsAction(searcher=GlobalSearcher(used_by=(), searcher=searcher))
        )

        return AdminSearchGroupsPayload(
            items=[self._group_data_to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def admin_create(self, input: CreateProjectInput) -> ProjectPayload:
        """Create a new project (superadmin only)."""
        domain_id = await self._resolve_domain_id(input.domain_name)
        result = await self._project.create_project.run(
            CreateProjectAction(
                domain_id=domain_id,
                creator=ProjectCreator(
                    name=input.name,
                    domain_id=domain_id,
                    domain_name=input.domain_name,
                    type=DataProjectType(input.type.value) if input.type else None,
                    description=input.description,
                    integration_name=input.integration_name,
                    resource_policy=input.resource_policy,
                ),
            )
        )
        return ProjectPayload(project=self._group_data_to_node(result.data))

    async def admin_update(self, project_id: UUID, input: UpdateProjectInput) -> ProjectPayload:
        """Update an existing project (superadmin only)."""
        updater = ProjectUpdater(
            project_id=ProjectID(project_id),
            name=OptionalState.from_unset(input.name),
            description=TriState.from_unset(input.description),
            is_active=OptionalState.from_unset(input.is_active),
            integration_name=TriState.from_unset(input.integration_name),
            resource_policy=OptionalState.from_unset(input.resource_policy),
        )
        result = await self._project.update_project.run(UpdateProjectAction(updater=updater))
        if result.data is None:
            raise UnreachableError("modify_group must return data")
        return ProjectPayload(project=self._group_data_to_node(result.data))

    async def admin_delete(self, input: DeleteProjectInput) -> DeleteProjectPayload:
        """Soft-delete a project (superadmin only)."""
        project_id = ProjectID(input.group_id)
        await self._project.delete_project.run(
            DeleteProjectAction(updater=ProjectSoftDeleteUpdater(project_id=project_id))
        )
        return DeleteProjectPayload(deleted=True)

    async def admin_restore(self, input: RestoreProjectInput) -> RestoreProjectPayload:
        """Restore a soft-deleted project (superadmin only)."""
        project_id = ProjectID(input.group_id)
        await self._project.restore_project.run(
            RestoreProjectAction(updater=ProjectRestoreUpdater(project_id=project_id))
        )
        return RestoreProjectPayload(restored=True)

    async def admin_purge(self, input: PurgeProjectInput) -> PurgeProjectPayload:
        """Permanently purge a project (superadmin only)."""
        await self._project.purge_project.run(
            PurgeProjectAction(project_id=ProjectID(input.group_id))
        )
        return PurgeProjectPayload(purged=True)

    async def unassign_users(
        self, project_id: UUID, input: UnassignUsersFromProjectInput
    ) -> UnassignUsersFromProjectPayload:
        """Unassign users from a project."""
        result = await self._rbac.leave_project.run(
            LeaveProjectAction(
                project_id=ProjectID(project_id),
                user_ids=[UserID(uid) for uid in input.user_ids],
            )
        )
        return UnassignUsersFromProjectPayload(
            unassigned_users=await self._user_nodes(result.members),
            failed=[
                UnassignUserError(user_id=f.user_id, message=f.reason) for f in result.failures
            ],
        )

    async def search_by_domain_name(
        self,
        domain_name: DomainName,
        input: AdminSearchProjectsInput,
    ) -> AdminSearchGroupsPayload:
        """Search projects within a domain."""
        domain_id = await self._resolve_domain_id(domain_name)
        conditions = self._convert_group_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            ProjectSearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=_PROJECT_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

        result = await self._project.scoped_search.run(
            ScopedSearchProjectsAction(
                targets=[DomainProjectTarget(domain_id=domain_id)], searcher=searcher
            )
        )

        return AdminSearchGroupsPayload(
            items=[self._group_data_to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    def _scope_targets(self, scope: ProjectScope) -> list[ProjectTarget]:
        """The scope targets the request named, in the order the input lists them."""
        targets: list[ProjectTarget] = [
            DomainProjectTarget(domain_id=DomainID(entry.value)) for entry in scope.domain or ()
        ]
        targets.extend(UserProjectTarget(user_id=UserID(entry.value)) for entry in scope.user or ())
        return targets

    async def scoped_search(
        self,
        input: ScopedSearchProjectsInput,
    ) -> AdminSearchGroupsPayload:
        """Search the projects the named scopes reach, combined with OR."""
        conditions = self._convert_group_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            ProjectSearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=_PROJECT_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._project.scoped_search.run(
            ScopedSearchProjectsAction(targets=self._scope_targets(input.scope), searcher=searcher)
        )
        return AdminSearchGroupsPayload(
            items=[self._group_data_to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_by_user(
        self,
        user_id: UserID,
        input: AdminSearchProjectsInput,
    ) -> AdminSearchGroupsPayload:
        """Search projects a user is a member of."""
        conditions = self._convert_group_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            ProjectSearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=_PROJECT_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

        result = await self._project.scoped_search.run(
            ScopedSearchProjectsAction(
                targets=[UserProjectTarget(user_id=user_id)], searcher=searcher
            )
        )

        return AdminSearchGroupsPayload(
            items=[self._group_data_to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def assign_users(
        self,
        project_id: UUID,
        input: AssignUsersToProjectInput,
    ) -> AssignUsersToProjectPayload:
        """Assign users to a project."""
        result = await self._rbac.join_project.run(
            JoinProjectAction(
                project_id=ProjectID(project_id),
                user_ids=[UserID(uid) for uid in input.user_ids],
                role_id=RoleID(input.role_id),
            )
        )
        return AssignUsersToProjectPayload(
            items=await self._user_nodes(result.members),
        )

    async def _user_nodes(self, users: Sequence[UserData]) -> list[UserNode]:
        """Convert users, reading the key each authorizes with for all of them at once."""
        if not users:
            return []
        result = await self._user.get_default_keypairs.run(
            GetDefaultKeypairsAction(user_ids=[UserID(user.id) for user in users])
        )
        keys = {owner: AccessKey(kp.access_key) for owner, kp in result.designated.items()}
        return [UserAdapter._user_data_to_node(user, keys.get(UserID(user.id))) for user in users]

    def _convert_group_filter(self, filter: ProjectFilter) -> list[QueryCondition]:
        fields = ProjectSearchableFields.own
        conditions = [
            *self.apply_uuid_filter(filter.id, fields.id.filter),
            *self.apply_string_filter(filter.name, fields.name.filter),
            *self.apply_string_filter(filter.domain_name, fields.domain_name.filter),
            *self.apply_string_filter(filter.description, fields.description.filter),
            *self.apply_string_filter(filter.integration_name, fields.integration_name.filter),
            *self._convert_type_filter(filter.type),
            *self.apply_bool_filter(filter.is_active, fields.is_active.filter),
            *self.apply_datetime_filter(filter.created_at, fields.created_at.filter),
            *self.apply_datetime_filter(filter.modified_at, fields.modified_at.filter),
            *self._convert_domain_nested_filter(filter.domain),
            *self._convert_user_nested_filter(filter.user),
        ]

        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_group_filter(sub_filter))

        if filter.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_sub_conditions.extend(self._convert_group_filter(sub_filter))
            if or_sub_conditions:
                conditions.append(combine_conditions_or(or_sub_conditions))

        if filter.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_sub_conditions.extend(self._convert_group_filter(sub_filter))
            if not_sub_conditions:
                conditions.append(negate_conditions(not_sub_conditions))

        return conditions

    def _convert_type_filter(self, type_filter: ProjectTypeFilter | None) -> list[QueryCondition]:
        if type_filter is None:
            return []
        conditions: list[QueryCondition] = []
        type_conditions = ProjectSearchableFields.own.type.filter
        if type_filter.equals is not None:
            conditions.append(type_conditions.equals(DataProjectType(type_filter.equals.value)))
        if type_filter.in_ is not None:
            conditions.append(
                type_conditions.in_([DataProjectType(t.value) for t in type_filter.in_])
            )
        if type_filter.not_equals is not None:
            conditions.append(
                type_conditions.not_equals(DataProjectType(type_filter.not_equals.value))
            )
        if type_filter.not_in is not None:
            conditions.append(
                type_conditions.not_in([DataProjectType(t.value) for t in type_filter.not_in])
            )
        return conditions

    def _convert_domain_nested_filter(
        self, domain_filter: ProjectDomainFilter | None
    ) -> list[QueryCondition]:
        """The domain conditions, gathered into one EXISTS on the holding domain row."""
        if domain_filter is None:
            return []
        fields = DomainSearchableFields.own
        raw_conditions = [
            *self.apply_string_filter(domain_filter.name, fields.name.filter),
            *self.apply_bool_filter(domain_filter.is_active, fields.is_active.filter),
        ]
        if not raw_conditions:
            return []
        return [DeprecatedProjectConditions.exists_domain_combined(raw_conditions)]

    def _convert_user_nested_filter(
        self, user_filter: ProjectUserFilter | None
    ) -> list[QueryCondition]:
        """Deprecated. Every condition lands in one EXISTS over one enrolled member."""
        if user_filter is None:
            return []
        fields = UserSearchableFields.own
        conditions = [
            *self.apply_uuid_filter(user_filter.id, fields.uuid.filter),
            *self.apply_string_filter(user_filter.username, fields.username.filter),
            *self.apply_string_filter(user_filter.email, fields.email.filter),
            *self._convert_member_active_filter(user_filter.is_active),
        ]
        if not conditions:
            return []
        return [DeprecatedProjectConditions.exists_user_combined(conditions)]

    def _convert_member_active_filter(self, is_active: bool | None) -> list[QueryCondition]:
        """Active means the member's account status is ACTIVE."""
        if is_active is None:
            return []
        status = UserSearchableFields.own.status.filter
        if is_active:
            return [status.equals(UserStatus.ACTIVE)]
        return [status.not_equals(UserStatus.ACTIVE)]

    def _convert_orders(self, order: list[ProjectOrder]) -> list[QueryOrder]:
        return [self._convert_order(o) for o in order]

    def _convert_order(self, order: ProjectOrder) -> QueryOrder:
        """The query order one requested order field names."""
        fields = ProjectSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case ProjectOrderField.NAME:
                return fields.name.order.apply(ascending)
            case ProjectOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case ProjectOrderField.MODIFIED_AT:
                return fields.modified_at.order.apply(ascending)
            case ProjectOrderField.IS_ACTIVE:
                return fields.is_active.order.apply(ascending)
            case ProjectOrderField.TYPE:
                return fields.type.order.apply(ascending)
            case ProjectOrderField.DOMAIN_NAME:
                return fields.domain_name.order.apply(ascending)
            case ProjectOrderField.ID:
                return fields.id.order.apply(ascending)
            case ProjectOrderField.DESCRIPTION:
                return fields.description.order.apply(ascending)
            case ProjectOrderField.INTEGRATION_NAME:
                return fields.integration_name.order.apply(ascending)
            case ProjectOrderField.USER_USERNAME:
                return DeprecatedProjectOrders.by_user_username(ascending)
            case ProjectOrderField.USER_EMAIL:
                return DeprecatedProjectOrders.by_user_email(ascending)
            case _:
                assert_never(order.field)

    @staticmethod
    def _group_data_to_node(data: ProjectData) -> ProjectNode:
        """Convert data layer type to Pydantic DTO."""
        vfolder_host_entries = [
            VFolderHostPermissionEntry(
                host=host,
                permissions=[perm.value for perm in perms],
            )
            for host, perms in data.allowed_vfolder_hosts.items()
        ]

        return ProjectNode(
            id=data.id,
            entity_id=data.entity_id(),
            basic_info=ProjectBasicInfo(
                name=data.name,
                description=data.description,
                type=ProjectType(data.type.value),
                integration_name=data.integration_name,
            ),
            organization=ProjectOrganizationInfo(
                domain_name=data.domain_name,
                resource_policy=data.resource_policy,
            ),
            storage=ProjectStorageInfo(
                allowed_vfolder_hosts=vfolder_host_entries,
            ),
            lifecycle=ProjectLifecycleInfo(
                is_active=data.is_active,
                created_at=data.created_at,
                modified_at=data.modified_at,
            ),
        )
