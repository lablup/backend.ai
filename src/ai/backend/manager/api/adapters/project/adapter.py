"""Project adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.filter_specs import UUIDInMatchSpec
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.group.request import (
    AdminSearchProjectsInput,
    AssignUsersToProjectInput,
    CreateProjectInput,
    DeleteProjectInput,
    ProjectFilter,
    ProjectOrder,
    PurgeProjectInput,
    RestoreProjectInput,
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
    ProjectOrderField,
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
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.domain.conditions import DomainConditions
from ai.backend.manager.models.project.conditions import ProjectConditions
from ai.backend.manager.models.project.creators import ProjectCreator
from ai.backend.manager.models.project.orders import ProjectOrders
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.scopes import (
    DomainProjectOperationScope,
    UserProjectOperationScope,
)
from ai.backend.manager.models.project.searchers import ProjectSearcher
from ai.backend.manager.models.project.updaters import (
    ProjectRestoreUpdater,
    ProjectSoftDeleteUpdater,
    ProjectUpdater,
)
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.repositories.project.scope_binders import UserProjectEntityUnbinder
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.manager.services.project.actions.assign_users_to_project import (
    AssignUsersToProjectAction,
)
from ai.backend.manager.services.project.actions.create_project import CreateProjectAction
from ai.backend.manager.services.project.actions.delete_project import DeleteProjectAction
from ai.backend.manager.services.project.actions.purge_project import PurgeProjectAction
from ai.backend.manager.services.project.actions.restore_project import RestoreProjectAction
from ai.backend.manager.services.project.actions.search_projects import (
    GetProjectAction,
    GlobalSearchProjectsAction,
    SearchProjectsByDomainAction,
    SearchProjectsByUserAction,
)
from ai.backend.manager.services.project.actions.unassign_users import (
    UnassignUsersFromProjectAction,
)
from ai.backend.manager.services.project.actions.update_project import UpdateProjectAction
from ai.backend.manager.services.user.actions.keypair_ops import GetDefaultKeypairsAction
from ai.backend.manager.types import OptionalState, TriState

_PROJECT_PAGINATION_SPEC = PaginationSpec(
    forward_order=ProjectOrders.created_at(ascending=False),
    backward_order=ProjectOrders.created_at(ascending=True),
    forward_condition_factory=lambda cursor_id: ProjectConditions.by_cursor_forward(
        UUID(cursor_id)
    ),
    backward_condition_factory=lambda cursor_id: ProjectConditions.by_cursor_backward(
        UUID(cursor_id)
    ),
    tiebreaker_order=ProjectRow.id.asc(),
)


class ProjectAdapter(BaseAdapter):
    """Adapter for project (group) operations."""

    async def _resolve_domain_id(self, domain_name: str) -> DomainID:
        result = await self._processors.domain.lookup.run(
            LookupDomainAction(name=DomainName(domain_name))
        )
        return result.entity_id()

    # ------------------------------------------------------------------ batch load (DataLoader)

    async def batch_load_by_ids(self, group_ids: Sequence[UUID]) -> list[ProjectNode | None]:
        """Batch load projects by UUID for DataLoader use.

        Returns ProjectNode DTOs in the same order as the input group_ids list.
        """
        if not group_ids:
            return []
        searcher = ProjectSearcher(
            pagination=NoPagination(),
            conditions=[
                ProjectConditions.by_id_in(UUIDInMatchSpec(values=list(group_ids), negated=False))
            ],
        )
        result = await self._processors.project.global_search.run(
            GlobalSearchProjectsAction(searcher=searcher)
        )
        project_map = {group.id: self._group_data_to_node(group) for group in result.items}
        return [project_map.get(group_id) for group_id in group_ids]

    # ------------------------------------------------------------------ get

    async def get(self, project_id: UUID) -> ProjectNode:
        """Retrieve a single project by UUID."""
        action_result = await self._processors.project.get_project.run(
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

        result = await self._processors.project.global_search.run(
            GlobalSearchProjectsAction(searcher=searcher)
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
        result = await self._processors.project.create_project.run(
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
            name=(
                OptionalState.update(input.name) if input.name is not None else OptionalState.nop()
            ),
            description=(
                TriState.nop()
                if isinstance(input.description, Sentinel)
                else TriState.nullify()
                if input.description is None
                else TriState.update(input.description)
            ),
            is_active=(
                OptionalState.update(input.is_active)
                if input.is_active is not None
                else OptionalState.nop()
            ),
            integration_name=(
                TriState.nop()
                if isinstance(input.integration_name, Sentinel)
                else TriState.nullify()
                if input.integration_name is None
                else TriState.update(input.integration_name)
            ),
            resource_policy=(
                OptionalState.update(input.resource_policy)
                if input.resource_policy is not None
                else OptionalState.nop()
            ),
        )
        result = await self._processors.project.update_project.run(
            UpdateProjectAction(updater=updater)
        )
        if result.data is None:
            raise UnreachableError("modify_group must return data")
        return ProjectPayload(project=self._group_data_to_node(result.data))

    async def admin_delete(self, input: DeleteProjectInput) -> DeleteProjectPayload:
        """Soft-delete a project (superadmin only)."""
        project_id = ProjectID(input.group_id)
        await self._processors.project.delete_project.run(
            DeleteProjectAction(updater=ProjectSoftDeleteUpdater(project_id=project_id))
        )
        return DeleteProjectPayload(deleted=True)

    async def admin_restore(self, input: RestoreProjectInput) -> RestoreProjectPayload:
        """Restore a soft-deleted project (superadmin only)."""
        project_id = ProjectID(input.group_id)
        await self._processors.project.restore_project.run(
            RestoreProjectAction(updater=ProjectRestoreUpdater(project_id=project_id))
        )
        return RestoreProjectPayload(restored=True)

    async def admin_purge(self, input: PurgeProjectInput) -> PurgeProjectPayload:
        """Permanently purge a project (superadmin only)."""
        await self._processors.project.purge_project.run(
            PurgeProjectAction(project_id=ProjectID(input.group_id))
        )
        return PurgeProjectPayload(purged=True)

    async def unassign_users(
        self, project_id: UUID, input: UnassignUsersFromProjectInput
    ) -> UnassignUsersFromProjectPayload:
        """Unassign users from a project."""
        result = await self._processors.project.unassign_users_from_project.run(
            UnassignUsersFromProjectAction(
                project_id=ProjectID(project_id),
                unbinder=UserProjectEntityUnbinder(
                    user_uuids=input.user_ids, project_id=project_id
                ),
            )
        )
        return UnassignUsersFromProjectPayload(
            unassigned_users=await self._user_nodes(result.unassigned_users),
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
        scope = DomainProjectOperationScope(domain_id=domain_id)
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

        result = await self._processors.project.search_projects_by_domain.run(
            SearchProjectsByDomainAction(domain_id=scope.domain_id, searcher=searcher)
        )

        return AdminSearchGroupsPayload(
            items=[self._group_data_to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_by_user(
        self,
        scope: UserProjectOperationScope,
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

        result = await self._processors.project.search_projects_by_user.run(
            SearchProjectsByUserAction(user_id=UserID(scope.user_uuid), searcher=searcher)
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
        result = await self._processors.project.assign_users_to_project.run(
            AssignUsersToProjectAction(
                project_id=ProjectID(project_id), user_ids=input.user_ids, role_id=input.role_id
            )
        )
        return AssignUsersToProjectPayload(
            items=await self._user_nodes(result.assigned_users),
        )

    async def _user_nodes(self, users: Sequence[UserData]) -> list[UserNode]:
        """Convert users, reading the key each authorizes with for all of them at once."""
        if not users:
            return []
        result = await self._processors.user.get_default_keypairs.run(
            GetDefaultKeypairsAction(user_ids=[UserID(user.id) for user in users])
        )
        keys = {owner: AccessKey(kp.access_key) for owner, kp in result.designated.items()}
        return [UserAdapter._user_data_to_node(user, keys.get(UserID(user.id))) for user in users]

    def _convert_group_filter(self, filter: ProjectFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter.id is not None:
            condition = self._convert_id_filter(filter.id)
            if condition is not None:
                conditions.append(condition)

        if filter.name is not None:
            condition = self._convert_name_filter(filter.name)
            if condition is not None:
                conditions.append(condition)

        if filter.domain_name is not None:
            condition = self._convert_domain_name_filter(filter.domain_name)
            if condition is not None:
                conditions.append(condition)

        if filter.type is not None:
            conditions.extend(self._convert_type_filter(filter.type))

        if filter.is_active is not None:
            conditions.append(ProjectConditions.by_is_active(filter.is_active))

        if filter.created_at is not None:
            condition = self._convert_created_at_filter(filter.created_at)
            if condition is not None:
                conditions.append(condition)

        if filter.modified_at is not None:
            condition = self._convert_modified_at_filter(filter.modified_at)
            if condition is not None:
                conditions.append(condition)

        if filter.domain is not None:
            conditions.extend(
                self._convert_domain_nested_filter(filter.domain.name, filter.domain.is_active)
            )

        if filter.user is not None:
            conditions.extend(self._convert_user_nested_filter(filter.user))

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

    def _convert_id_filter(self, uuid_filter: UUIDFilter) -> QueryCondition | None:
        return self.convert_uuid_filter(
            uuid_filter,
            equals_factory=ProjectConditions.by_id_equals,
            in_factory=ProjectConditions.by_id_in,
        )

    def _convert_name_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=ProjectConditions.by_name_contains,
            equals_factory=ProjectConditions.by_name_equals,
            starts_with_factory=ProjectConditions.by_name_starts_with,
            ends_with_factory=ProjectConditions.by_name_ends_with,
            in_factory=ProjectConditions.by_name_in,
        )

    def _convert_domain_name_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=ProjectConditions.by_domain_name_contains,
            equals_factory=ProjectConditions.by_domain_name_equals,
            starts_with_factory=ProjectConditions.by_domain_name_starts_with,
            ends_with_factory=ProjectConditions.by_domain_name_ends_with,
            in_factory=ProjectConditions.by_domain_name_in,
        )

    @staticmethod
    def _convert_type_filter(type_filter: ProjectTypeFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if type_filter.equals is not None:
            conditions.append(
                ProjectConditions.by_type_equals(DataProjectType(type_filter.equals.value))
            )
        if type_filter.in_ is not None:
            conditions.append(
                ProjectConditions.by_type_in([DataProjectType(t.value) for t in type_filter.in_])
            )
        if type_filter.not_equals is not None:
            conditions.append(
                negate_conditions([
                    ProjectConditions.by_type_equals(DataProjectType(type_filter.not_equals.value))
                ])
            )
        if type_filter.not_in is not None:
            conditions.append(
                negate_conditions([
                    ProjectConditions.by_type_in([
                        DataProjectType(t.value) for t in type_filter.not_in
                    ])
                ])
            )
        return conditions

    @staticmethod
    def _convert_created_at_filter(dt_filter: DateTimeFilter) -> QueryCondition | None:
        return dt_filter.build_query_condition(
            before_factory=ProjectConditions.by_created_at_before,
            after_factory=ProjectConditions.by_created_at_after,
            equals_factory=ProjectConditions.by_created_at_equals,
        )

    @staticmethod
    def _convert_modified_at_filter(dt_filter: DateTimeFilter) -> QueryCondition | None:
        return dt_filter.build_query_condition(
            before_factory=ProjectConditions.by_modified_at_before,
            after_factory=ProjectConditions.by_modified_at_after,
            equals_factory=ProjectConditions.by_modified_at_equals,
        )

    @staticmethod
    def _convert_domain_nested_filter(
        name_filter: StringFilter | None,
        is_active: bool | None,
    ) -> list[QueryCondition]:
        raw_conditions: list[QueryCondition] = []
        if name_filter is not None:
            condition = name_filter.build_query_condition(
                contains_factory=DomainConditions.by_name_contains,
                equals_factory=DomainConditions.by_name_equals,
                starts_with_factory=DomainConditions.by_name_starts_with,
                ends_with_factory=DomainConditions.by_name_ends_with,
                in_factory=DomainConditions.by_name_in,
            )
            if condition is not None:
                raw_conditions.append(condition)
        if is_active is not None:
            raw_conditions.append(DomainConditions.by_is_active(is_active))
        if not raw_conditions:
            return []
        return [ProjectConditions.exists_domain_combined(raw_conditions)]

    @staticmethod
    def _convert_user_nested_filter(user_filter: ProjectUserFilter) -> list[QueryCondition]:
        raw_conditions: list[QueryCondition] = []
        if user_filter.id is not None:
            condition = user_filter.id.build_query_condition(
                equals_factory=ProjectConditions.by_user_id_equals,
                in_factory=ProjectConditions.by_user_id_in,
            )
            if condition is not None:
                raw_conditions.append(condition)
        if user_filter.username is not None:
            condition = user_filter.username.build_query_condition(
                contains_factory=ProjectConditions.by_user_username_contains,
                equals_factory=ProjectConditions.by_user_username_equals,
                starts_with_factory=ProjectConditions.by_user_username_starts_with,
                ends_with_factory=ProjectConditions.by_user_username_ends_with,
                in_factory=ProjectConditions.by_user_username_in,
            )
            if condition is not None:
                raw_conditions.append(condition)
        if user_filter.email is not None:
            condition = user_filter.email.build_query_condition(
                contains_factory=ProjectConditions.by_user_email_contains,
                equals_factory=ProjectConditions.by_user_email_equals,
                starts_with_factory=ProjectConditions.by_user_email_starts_with,
                ends_with_factory=ProjectConditions.by_user_email_ends_with,
                in_factory=ProjectConditions.by_user_email_in,
            )
            if condition is not None:
                raw_conditions.append(condition)
        if user_filter.is_active is not None:
            raw_conditions.append(ProjectConditions.by_user_is_active(user_filter.is_active))
        if not raw_conditions:
            return []
        return [ProjectConditions.exists_user_combined(raw_conditions)]

    @staticmethod
    def _convert_orders(order: list[ProjectOrder]) -> list[QueryOrder]:
        return [_resolve_order(o.field, o.direction) for o in order]

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


def _resolve_order(field: ProjectOrderField, direction: OrderDirection) -> QueryOrder:
    """Resolve a ProjectOrderField + OrderDirection pair to a QueryOrder."""
    ascending = direction == OrderDirection.ASC
    match field:
        case ProjectOrderField.NAME:
            return ProjectOrders.name(ascending)
        case ProjectOrderField.CREATED_AT:
            return ProjectOrders.created_at(ascending)
        case ProjectOrderField.MODIFIED_AT:
            return ProjectOrders.modified_at(ascending)
        case ProjectOrderField.IS_ACTIVE:
            return ProjectOrders.is_active(ascending)
        case ProjectOrderField.TYPE:
            return ProjectOrders.type(ascending)
        case ProjectOrderField.DOMAIN_NAME:
            return ProjectOrders.by_domain_name(ascending)
        case ProjectOrderField.USER_USERNAME:
            return ProjectOrders.by_user_username(ascending)
        case ProjectOrderField.USER_EMAIL:
            return ProjectOrders.by_user_email(ascending)
