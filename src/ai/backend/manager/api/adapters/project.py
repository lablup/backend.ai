"""Project adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.api_handlers import Sentinel
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
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapters.pagination import PaginationSpec
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.data.group.types import ProjectType as DataProjectType
from ai.backend.manager.models.domain.conditions import DomainConditions
from ai.backend.manager.models.group.conditions import GroupConditions
from ai.backend.manager.models.group.orders import GroupOrders
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    NoPagination,
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.group.creators import GroupCreatorSpec
from ai.backend.manager.repositories.group.scope_binders import UserProjectEntityUnbinder
from ai.backend.manager.repositories.group.types import (
    DomainProjectSearchScope,
    UserProjectSearchScope,
)
from ai.backend.manager.repositories.group.updaters import GroupUpdaterSpec
from ai.backend.manager.services.group.actions.assign_users_to_project import (
    AssignUsersToProjectAction,
)
from ai.backend.manager.services.group.actions.create_group import CreateGroupAction
from ai.backend.manager.services.group.actions.delete_group import DeleteGroupAction
from ai.backend.manager.services.group.actions.modify_group import ModifyGroupAction
from ai.backend.manager.services.group.actions.purge_group import PurgeGroupAction
from ai.backend.manager.services.group.actions.search_projects import (
    GetProjectAction,
    SearchProjectsAction,
    SearchProjectsByDomainAction,
    SearchProjectsByUserAction,
)
from ai.backend.manager.services.group.actions.unassign_users import (
    UnassignUsersFromProjectAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter
from .user import UserAdapter

_PROJECT_PAGINATION_SPEC = PaginationSpec(
    forward_order=GroupOrders.created_at(ascending=False),
    backward_order=GroupOrders.created_at(ascending=True),
    forward_condition_factory=lambda cursor_id: GroupConditions.by_cursor_forward(UUID(cursor_id)),
    backward_condition_factory=lambda cursor_id: GroupConditions.by_cursor_backward(
        UUID(cursor_id)
    ),
    tiebreaker_order=GroupRow.id.asc(),
)


class ProjectAdapter(BaseAdapter):
    """Adapter for project (group) operations."""

    # ------------------------------------------------------------------ batch load (DataLoader)

    async def batch_load_by_ids(self, group_ids: Sequence[UUID]) -> list[ProjectNode | None]:
        """Batch load projects by UUID for DataLoader use.

        Returns ProjectNode DTOs in the same order as the input group_ids list.
        """
        if not group_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[
                GroupConditions.by_id_in(UUIDInMatchSpec(values=list(group_ids), negated=False))
            ],
        )
        action_result = await self._processors.group.search_projects.wait_for_complete(
            SearchProjectsAction(querier=querier)
        )
        project_map = {group.id: self._group_data_to_node(group) for group in action_result.items}
        return [project_map.get(group_id) for group_id in group_ids]

    # ------------------------------------------------------------------ get

    async def get(self, project_id: UUID) -> ProjectNode:
        """Retrieve a single project by UUID."""
        action_result = await self._processors.group.get_project.wait_for_complete(
            GetProjectAction(project_id=project_id)
        )
        return self._group_data_to_node(action_result.data)

    async def admin_search(
        self,
        input: AdminSearchProjectsInput,
    ) -> AdminSearchGroupsPayload:
        """Search projects (admin, no scope) with filters, orders, and pagination."""
        conditions = self._convert_group_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
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

        action_result = await self._processors.group.search_projects.wait_for_complete(
            SearchProjectsAction(querier=querier)
        )

        return AdminSearchGroupsPayload(
            items=[self._group_data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def admin_create(self, input: CreateProjectInput) -> ProjectPayload:
        """Create a new project (superadmin only)."""
        spec = GroupCreatorSpec(
            name=input.name,
            domain_name=input.domain_name,
            type=DataProjectType(input.type.value) if input.type else None,
            description=input.description,
            integration_id=input.integration_id,
            resource_policy=input.resource_policy,
        )
        result = await self._processors.group.create_group.wait_for_complete(
            CreateGroupAction(creator=Creator(spec=spec), _domain_name=input.domain_name)
        )
        if result.data is None:
            raise UnreachableError("create_group must return data")
        return ProjectPayload(project=self._group_data_to_node(result.data))

    async def admin_update(self, project_id: UUID, input: UpdateProjectInput) -> ProjectPayload:
        """Update an existing project (superadmin only)."""
        spec = GroupUpdaterSpec(
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
            integration_id=(
                OptionalState.nop()
                if isinstance(input.integration_id, Sentinel)
                else OptionalState.nop()
                if input.integration_id is None
                else OptionalState.update(input.integration_id)
            ),
            resource_policy=(
                OptionalState.update(input.resource_policy)
                if input.resource_policy is not None
                else OptionalState.nop()
            ),
        )
        updater: Updater[GroupRow] = Updater(spec=spec, pk_value=project_id)
        result = await self._processors.group.modify_group.wait_for_complete(
            ModifyGroupAction(updater=updater)
        )
        if result.data is None:
            raise UnreachableError("modify_group must return data")
        return ProjectPayload(project=self._group_data_to_node(result.data))

    async def admin_delete(self, input: DeleteProjectInput) -> DeleteProjectPayload:
        """Soft-delete a project (superadmin only)."""
        await self._processors.group.delete_group.wait_for_complete(
            DeleteGroupAction(group_id=input.group_id)
        )
        return DeleteProjectPayload(deleted=True)

    async def admin_purge(self, input: PurgeProjectInput) -> PurgeProjectPayload:
        """Permanently purge a project (superadmin only)."""
        await self._processors.group.purge_group.wait_for_complete(
            PurgeGroupAction(group_id=input.group_id)
        )
        return PurgeProjectPayload(purged=True)

    async def unassign_users(
        self, project_id: UUID, input: UnassignUsersFromProjectInput
    ) -> UnassignUsersFromProjectPayload:
        """Unassign users from a project."""
        result = await self._processors.group.unassign_users_from_project.wait_for_complete(
            UnassignUsersFromProjectAction(
                unbinder=UserProjectEntityUnbinder(
                    user_uuids=input.user_ids, project_id=project_id
                ),
            )
        )
        return UnassignUsersFromProjectPayload(
            unassigned_users=[
                UserAdapter._user_data_to_node(user_data) for user_data in result.unassigned_users
            ],
            failed=[
                UnassignUserError(user_id=f.user_id, message=f.reason) for f in result.failures
            ],
        )

    async def search_by_domain(
        self,
        scope: DomainProjectSearchScope,
        input: AdminSearchProjectsInput,
    ) -> AdminSearchGroupsPayload:
        """Search projects within a domain."""
        conditions = self._convert_group_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        base_conditions: list[QueryCondition] = [scope.to_condition()]
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_PROJECT_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=base_conditions,
        )

        action_result = await self._processors.group.search_projects_by_domain.wait_for_complete(
            SearchProjectsByDomainAction(scope=scope, querier=querier)
        )

        return AdminSearchGroupsPayload(
            items=[self._group_data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def search_by_user(
        self,
        scope: UserProjectSearchScope,
        input: AdminSearchProjectsInput,
    ) -> AdminSearchGroupsPayload:
        """Search projects a user is a member of."""
        conditions = self._convert_group_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        base_conditions: list[QueryCondition] = [scope.to_condition()]
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_PROJECT_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=base_conditions,
        )

        action_result = await self._processors.group.search_projects_by_user.wait_for_complete(
            SearchProjectsByUserAction(scope=scope, querier=querier)
        )

        return AdminSearchGroupsPayload(
            items=[self._group_data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def assign_users(
        self,
        project_id: UUID,
        input: AssignUsersToProjectInput,
    ) -> AssignUsersToProjectPayload:
        """Assign users to a project."""
        result = await self._processors.group.assign_users_to_project.wait_for_complete(
            AssignUsersToProjectAction(project_id=project_id, user_ids=input.user_ids)
        )
        return AssignUsersToProjectPayload(
            items=[UserAdapter._user_data_to_node(u) for u in result.assigned_users],
        )

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
            conditions.append(GroupConditions.by_is_active(filter.is_active))

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
            equals_factory=GroupConditions.by_id_equals,
            in_factory=GroupConditions.by_id_in,
        )

    def _convert_name_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=GroupConditions.by_name_contains,
            equals_factory=GroupConditions.by_name_equals,
            starts_with_factory=GroupConditions.by_name_starts_with,
            ends_with_factory=GroupConditions.by_name_ends_with,
        )

    def _convert_domain_name_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=GroupConditions.by_domain_name_contains,
            equals_factory=GroupConditions.by_domain_name_equals,
            starts_with_factory=GroupConditions.by_domain_name_starts_with,
            ends_with_factory=GroupConditions.by_domain_name_ends_with,
        )

    @staticmethod
    def _convert_type_filter(type_filter: ProjectTypeFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if type_filter.equals is not None:
            conditions.append(
                GroupConditions.by_type_equals(DataProjectType(type_filter.equals.value))
            )
        if type_filter.in_ is not None:
            conditions.append(
                GroupConditions.by_type_in([DataProjectType(t.value) for t in type_filter.in_])
            )
        if type_filter.not_equals is not None:
            conditions.append(
                negate_conditions([
                    GroupConditions.by_type_equals(DataProjectType(type_filter.not_equals.value))
                ])
            )
        if type_filter.not_in is not None:
            conditions.append(
                negate_conditions([
                    GroupConditions.by_type_in([
                        DataProjectType(t.value) for t in type_filter.not_in
                    ])
                ])
            )
        return conditions

    @staticmethod
    def _convert_created_at_filter(dt_filter: DateTimeFilter) -> QueryCondition | None:
        return dt_filter.build_query_condition(
            before_factory=GroupConditions.by_created_at_before,
            after_factory=GroupConditions.by_created_at_after,
            equals_factory=GroupConditions.by_created_at_equals,
        )

    @staticmethod
    def _convert_modified_at_filter(dt_filter: DateTimeFilter) -> QueryCondition | None:
        return dt_filter.build_query_condition(
            before_factory=GroupConditions.by_modified_at_before,
            after_factory=GroupConditions.by_modified_at_after,
            equals_factory=GroupConditions.by_modified_at_equals,
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
            )
            if condition is not None:
                raw_conditions.append(condition)
        if is_active is not None:
            raw_conditions.append(DomainConditions.by_is_active(is_active))
        if not raw_conditions:
            return []
        return [GroupConditions.exists_domain_combined(raw_conditions)]

    @staticmethod
    def _convert_user_nested_filter(user_filter: ProjectUserFilter) -> list[QueryCondition]:
        raw_conditions: list[QueryCondition] = []
        if user_filter.username is not None:
            condition = user_filter.username.build_query_condition(
                contains_factory=GroupConditions.by_user_username_contains,
                equals_factory=GroupConditions.by_user_username_equals,
                starts_with_factory=GroupConditions.by_user_username_starts_with,
                ends_with_factory=GroupConditions.by_user_username_ends_with,
            )
            if condition is not None:
                raw_conditions.append(condition)
        if user_filter.email is not None:
            condition = user_filter.email.build_query_condition(
                contains_factory=GroupConditions.by_user_email_contains,
                equals_factory=GroupConditions.by_user_email_equals,
                starts_with_factory=GroupConditions.by_user_email_starts_with,
                ends_with_factory=GroupConditions.by_user_email_ends_with,
            )
            if condition is not None:
                raw_conditions.append(condition)
        if user_filter.is_active is not None:
            raw_conditions.append(GroupConditions.by_user_is_active(user_filter.is_active))
        if not raw_conditions:
            return []
        return [GroupConditions.exists_user_combined(raw_conditions)]

    @staticmethod
    def _convert_orders(order: list[ProjectOrder]) -> list[QueryOrder]:
        return [_resolve_order(o.field, o.direction) for o in order]

    @staticmethod
    def _group_data_to_node(data: GroupData) -> ProjectNode:
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
                integration_id=data.integration_id,
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
            return GroupOrders.name(ascending)
        case ProjectOrderField.CREATED_AT:
            return GroupOrders.created_at(ascending)
        case ProjectOrderField.MODIFIED_AT:
            return GroupOrders.modified_at(ascending)
        case ProjectOrderField.IS_ACTIVE:
            return GroupOrders.is_active(ascending)
        case ProjectOrderField.TYPE:
            return GroupOrders.type(ascending)
        case ProjectOrderField.DOMAIN_NAME:
            return GroupOrders.by_domain_name(ascending)
        case ProjectOrderField.USER_USERNAME:
            return GroupOrders.by_user_username(ascending)
        case ProjectOrderField.USER_EMAIL:
            return GroupOrders.by_user_email(ascending)
