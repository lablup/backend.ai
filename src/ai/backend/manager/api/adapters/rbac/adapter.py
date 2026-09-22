"""RBAC domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from functools import lru_cache
from uuid import UUID

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import (
    EntityIdentifier,
    EntityType,
    RuntimeEntityID,
)
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.filter_specs import UUIDInMatchSpec
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.rbac import (
    BulkAddRolePermissionFailureInfo,
    BulkAddRolePermissionsPayload,
    BulkAssignRoleResultPayload,
    BulkRemoveRolePermissionFailureInfo,
    BulkRemoveRolePermissionsPayload,
    BulkRevokeRoleFailureInfo,
    BulkRevokeRoleResultPayload,
    CreateRoleInput,
    CreateRolePayload,
    DeleteRolePayload,
    EntityActionInfo,
    EntityOperationCombinationInfo,
    OperationInfo,
    PermissionNode,
    PurgeRolePayload,
    ReplaceRolePermissionsPayload,
    RoleAssignmentNode,
    RoleNode,
    ScopeEntityCombinationInfo,
    ScopeEntityOperationCombinationInfo,
    UpdateRoleInput,
    UpdateRolePayload,
)
from ai.backend.common.dto.manager.v2.rbac import (
    DeletePermissionPayload as DeletePermissionPayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    AdminSearchPermissionsGQLInput,
    MyAtomicBulkScopePermissionsInput,
    MyScopePermissionsInput,
    PermissionTarget,
    SearchRoleAssignmentsInput,
    SearchRolesInput,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    AssignRoleInput as AssignRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    BulkAddRolePermissionsInput as BulkAddRolePermissionsInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    BulkAssignRoleInput as BulkAssignRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    BulkRemoveRolePermissionsInput as BulkRemoveRolePermissionsInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    BulkRevokeRoleInput as BulkRevokeRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    CreatePermissionInput as CreatePermissionInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    MappedScopeNestedFilter as MappedScopeNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    PermissionFilter as PermissionFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    PermissionNestedFilter as PermissionNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    PermissionOrderBy as PermissionOrderByDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    ReplaceRolePermissionsInput as ReplaceRolePermissionsInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RevokeRoleInput as RevokeRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleAssignmentFilter as RoleAssignmentFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleAssignmentOrderBy as RoleAssignmentOrderByDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleFilter as RoleFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleNestedFilter as RoleNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleOrderBy as RoleOrderByDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleUsage as RoleUsageDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    UpdatePermissionInput as UpdatePermissionInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    UserNestedFilter as UserNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    MyAtomicBulkScopePermissionsPayload,
    MyScopePermissionsPayload,
    ScopeEntityPermission,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    OrderDirection as OrderDirectionV2,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    PermissionBitDTO,
    PermissionBitFilter,
    RoleSourceDTO,
    RoleStatusDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    RoleSourceFilter as RoleSourceFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    RoleStatusFilter as RoleStatusFilterDTO,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.role import (
    AssignedUserData,
    BulkRoleAssignmentResultData,
    BulkRolePermissionReplaceResultData,
    BulkRoleRevocationResultData,
    BulkUserRoleRevocationInput,
    RoleData,
    RoleDetailData,
    UserRoleAssignmentData,
    UserRoleAssignmentInput,
    UserRoleRevocationData,
    UserRoleRevocationInput,
)
from ai.backend.manager.data.permission.status import RoleStatus as InternalRoleStatus
from ai.backend.manager.data.permission.types import GrantableOperation
from ai.backend.manager.data.permission.types import RoleSource as InternalRoleSource
from ai.backend.manager.data.permission.virtual_entity import GovernCheckKey
from ai.backend.manager.errors.base.not_found import NotFoundError
from ai.backend.manager.errors.permission import (
    NotEnoughPermission,
    PermissionAlreadyGranted,
    ReplaceRolePermissionRoleIdMismatch,
)
from ai.backend.manager.errors.repository import RepositoryIntegrityError
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.rbac.exceptions import InvalidScope
from ai.backend.manager.models.rbac_models.permission.creators import RolePermissionCreator
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.searchable_fields import (
    PermissionSearchableFields,
)
from ai.backend.manager.models.rbac_models.permission.searchers import RolePermissionSearcher
from ai.backend.manager.models.rbac_models.permission.updaters import RolePermissionUpdater
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role.creators import RoleCreator
from ai.backend.manager.models.rbac_models.role.deprecated_search import (
    DeprecatedRoleConditions,
)
from ai.backend.manager.models.rbac_models.role.scopes import (
    HeldRoleTarget,
    RoleTarget,
)
from ai.backend.manager.models.rbac_models.role.searchable_fields import (
    RoleSearchableFields,
)
from ai.backend.manager.models.rbac_models.role.searchers import RoleSearcher
from ai.backend.manager.models.rbac_models.role.updaters import RoleSoftDeleteUpdater, RoleUpdater
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.rbac_models.user_role.deprecated_search import (
    DeprecatedRoleAssignmentConditions,
)
from ai.backend.manager.models.rbac_models.user_role.scopes import (
    RoleAssignmentTarget,
    RoleRoleAssignmentTarget,
    UserRoleAssignmentTarget,
)
from ai.backend.manager.models.rbac_models.user_role.searchable_fields import (
    RoleAssignmentSearchableFields,
)
from ai.backend.manager.models.rbac_models.user_role.searchers import RoleAssignmentSearcher
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.specs.permission import PermissionEntry
from ai.backend.manager.models.specs.search.usage import UsedBy
from ai.backend.manager.models.specs.searcher import GlobalSearcher, ScopedSearcher
from ai.backend.manager.models.user.searchable_fields import UserSearchableFields
from ai.backend.manager.services.permission_contoller.actions.add_role_permission import (
    AddRolePermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_get_permissions import (
    BulkGetPermissionsAction,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_get_roles import (
    BulkGetRolesAction,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_lookup_role_assignment_ends import (
    BulkLookupRoleAssignmentRolesAction,
    BulkLookupRoleAssignmentUsersAction,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_remove_role_permissions import (
    BulkRemoveRolePermissionsAction,
)
from ai.backend.manager.services.permission_contoller.actions.create_role import CreateRoleAction
from ai.backend.manager.services.permission_contoller.actions.delete_permission import (
    DeletePermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.delete_role import DeleteRoleAction
from ai.backend.manager.services.permission_contoller.actions.get_held_permissions import (
    ScopedGetHeldPermissionsAction,
)
from ai.backend.manager.services.permission_contoller.actions.get_permission_matrix import (
    PublicGetPermissionMatrixAction,
)
from ai.backend.manager.services.permission_contoller.actions.get_role_detail import (
    GetRoleDetailAction,
)
from ai.backend.manager.services.permission_contoller.actions.purge_role import PurgeRoleAction
from ai.backend.manager.services.permission_contoller.actions.replace_role_permissions import (
    ReplaceRolePermissionsAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_my_role_assignments import (
    ScopedSearchRoleAssignmentsAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_permissions import (
    GlobalSearchPermissionsAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_role_permissions import (
    SearchRolePermissionsAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles import (
    GlobalSearchRolesAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles_in_scope import (
    SearchRolesInScopeAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_users_assigned_to_role import (
    GlobalSearchRoleAssignmentsAction,
)
from ai.backend.manager.services.permission_contoller.actions.update_permission import (
    UpdatePermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.update_role import UpdateRoleAction
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.manager.services.rbac.actions.role.assign import AssignRoleAction
from ai.backend.manager.services.rbac.actions.role.bulk_assign import (
    BulkAssignRoleAction,
)
from ai.backend.manager.services.rbac.actions.role.bulk_revoke import (
    BulkRevokeRoleAction,
)
from ai.backend.manager.services.rbac.actions.role.revoke import RevokeRoleAction
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.manager.types import OptionalState, TriState

# ------------------------------------------------------------------ pagination specs


@lru_cache(maxsize=1)
def _permission_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=PermissionSearchableFields.own.created_at.order.apply(ascending=False),
        cursor_column=PermissionRow.id,
    )


@lru_cache(maxsize=1)
def _role_gql_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RoleSearchableFields.own.created_at.order.apply(ascending=False),
        cursor_column=RoleRow.id,
    )


@lru_cache(maxsize=1)
def _assignment_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RoleAssignmentSearchableFields.own.granted_at.order.apply(ascending=False),
        cursor_column=UserRoleRow.id,
    )


class RBACAdapter(BaseAdapter):
    """Adapter for RBAC domain operations.

    Exposes: create, admin_search, get, update, delete, purge.
    assign/revoke/bulk operations require specialized inputs not
    yet bridged through this adapter.
    """

    _rbac: RbacProcessors
    _permission_controller: PermissionControllerProcessors

    def __init__(
        self,
        rbac: RbacProcessors,
        permission_controller: PermissionControllerProcessors,
    ) -> None:
        self._rbac = rbac
        self._permission_controller = permission_controller

    def _validate_scope_id(self, scope_type: EntityType, scope_id: str) -> None:
        """Raise InvalidScope if scope_id is not a valid UUID for scope types that require one."""
        match scope_type:
            case UserEntityType() | ProjectEntityType() | DomainEntityType():
                self._scope_uuid(scope_type, scope_id)
            case _:
                pass

    def _scope_uuid(self, scope_type: EntityType, scope_id: str) -> UUID:
        try:
            return UUID(scope_id)
        except ValueError:
            raise InvalidScope(
                f"scope_id must be a valid UUID for scope_type '{scope_type}', got '{scope_id}'"
            ) from None

    def _scope_identifier(self, scope_type: EntityType, scope_id: str) -> EntityIdentifier:
        value = self._scope_uuid(scope_type, scope_id)
        match scope_type:
            case DomainEntityType():
                return DomainID(value)
            case ProjectEntityType():
                return ProjectID(value)
            case UserEntityType():
                return UserID(value)
            case _:
                return RuntimeEntityID(scope_type, value)

    # ------------------------------------------------------------------ batch load (DataLoader)

    async def batch_load_roles_by_ids(self, role_ids: Sequence[RoleID]) -> list[RoleNode | None]:
        """Batch load roles by ID for DataLoader use.

        Returns RoleNode DTOs in the same order as the input role_ids list.
        """
        if not role_ids:
            return []
        got = await self._permission_controller.bulk_get_roles.run(
            BulkGetRolesAction(ids=list(role_ids))
        )
        role_map = {
            entity_id: self._role_data_to_node(data) for entity_id, data in got.values().items()
        }
        return [role_map.get(role_id) for role_id in role_ids]

    async def batch_load_permissions_by_ids(
        self, permission_ids: Sequence[PermissionID]
    ) -> list[PermissionNode | None]:
        """Batch load permissions by ID for DataLoader use.

        Returns PermissionNode DTOs in the same order as the input permission_ids list.
        """
        if not permission_ids:
            return []
        got = await self._permission_controller.bulk_get_permissions.run(
            BulkGetPermissionsAction(permission_ids=[PermissionID(pid) for pid in permission_ids])
        )
        permission_map = {
            field_id: self._permission_data_to_node(data)
            for field_id, data in got.successes.items()
        }
        return [permission_map.get(PermissionID(pid)) for pid in permission_ids]

    async def batch_load_role_assignments_by_ids(
        self, assignment_ids: Sequence[UUID]
    ) -> list[RoleAssignmentNode | None]:
        """Batch load role assignments by ID for DataLoader use.

        Returns RoleAssignmentNode DTOs in the same order as the input assignment_ids list.
        """
        if not assignment_ids:
            return []
        roles = await self._permission_controller.bulk_lookup_role_assignment_roles.run(
            BulkLookupRoleAssignmentRolesAction(assignment_ids=assignment_ids)
        )
        users = await self._permission_controller.bulk_lookup_role_assignment_users.run(
            BulkLookupRoleAssignmentUsersAction(assignment_ids=assignment_ids)
        )
        found: dict[UUID, RoleAssignmentNode] = {}
        by_role: dict[RoleID, list[UUID]] = defaultdict(list)
        for aid, role_id in roles.resolved.items():
            by_role[role_id].append(aid)
        for role_id, aids in by_role.items():
            found.update(
                await self._read_assignments_in_scope(
                    RoleRoleAssignmentTarget(role_id=role_id), aids
                )
            )
        by_user: dict[UserID, list[UUID]] = defaultdict(list)
        for aid, user_id in users.resolved.items():
            if aid not in found:
                by_user[user_id].append(aid)
        for user_id, aids in by_user.items():
            found.update(
                await self._read_assignments_in_scope(
                    UserRoleAssignmentTarget(user_id=user_id), aids
                )
            )
        return [found.get(aid) for aid in assignment_ids]

    async def _read_assignments_in_scope(
        self, target: RoleAssignmentTarget, assignment_ids: Sequence[UUID]
    ) -> dict[UUID, RoleAssignmentNode]:
        """Read the named assignment rows from one of the ends they join.

        A caller barred from the end answers for none of its rows, so the loader falls
        through to the other end and leaves the rest of the batch alone.
        """
        searcher = RoleAssignmentSearcher(
            pagination=NoPagination(),
            conditions=[
                RoleAssignmentSearchableFields.own.id.filter.in_(
                    UUIDInMatchSpec(values=assignment_ids, negated=False)
                )
            ],
        )
        try:
            result = await self._permission_controller.scoped_search_role_assignments.run(
                ScopedSearchRoleAssignmentsAction(targets=[target], searcher=searcher)
            )
        except NotEnoughPermission:
            return {}
        return {data.id: self._assignment_data_to_node(data) for data in result.result.items}

    async def batch_load_permissions_by_role_ids(
        self, role_ids: Sequence[RoleID]
    ) -> list[list[PermissionNode]]:
        """Batch load permissions grouped by role_id for DataLoader use.

        Returns a list of permission lists, one per role_id (empty list if no permissions).
        """
        if not role_ids:
            return []
        found = await self._permission_controller.search_role_permissions.run(
            SearchRolePermissionsAction(
                role_ids=list(role_ids), searcher=RolePermissionSearcher(pagination=NoPagination())
            )
        )
        result_map: dict[UUID, list[PermissionNode]] = defaultdict(list)
        for item in found.items:
            result_map[item.role_id].append(self._permission_data_to_node(item))
        return [result_map.get(role_id, []) for role_id in role_ids]

    # ------------------------------------------------------------------ held permissions

    async def my_scope_permissions(
        self, input: MyScopePermissionsInput
    ) -> MyScopePermissionsPayload:
        """The bits the current user holds on one entity type within one scope."""
        items = await self._scope_permissions([input.target])
        return MyScopePermissionsPayload(item=items[0])

    async def my_atomic_bulk_scope_permissions(
        self, input: MyAtomicBulkScopePermissionsInput
    ) -> MyAtomicBulkScopePermissionsPayload:
        """The same answer for several targets, resolved in one grouped pass."""
        return MyAtomicBulkScopePermissionsPayload(
            items=await self._scope_permissions(input.targets)
        )

    async def _scope_permissions(
        self, targets: Sequence[PermissionTarget]
    ) -> list[ScopeEntityPermission]:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        user_id = UserID(me.user_id)
        keys = [self._govern_check_key(user_id, target) for target in targets]
        action_result = await self._permission_controller.scoped_get_held_permissions.run(
            ScopedGetHeldPermissionsAction(user_id=user_id, keys=keys)
        )
        granted = action_result.granted
        return [
            ScopeEntityPermission(
                scope_type=target.scope_type,
                scope_id=target.scope_id,
                entity_type=target.entity_type,
                permissions=[PermissionBitDTO.of(bit) for bit in granted.get(key, Permission.NONE)],
            )
            for target, key in zip(targets, keys, strict=True)
        ]

    def _govern_check_key(self, user_id: UserID, target: PermissionTarget) -> GovernCheckKey:
        scope_type = EntityType.from_name(target.scope_type)
        return GovernCheckKey(
            user_id=user_id,
            scope=self._scope_identifier(scope_type, str(target.scope_id)),
            entity_type=EntityType.from_name(target.entity_type),
        )

    # ------------------------------------------------------------------ permission catalog

    async def _permission_matrix(
        self,
    ) -> Mapping[EntityType, Mapping[EntityType, Sequence[GrantableOperation]]]:
        action_result = await self._permission_controller.public_get_permission_matrix.run(
            PublicGetPermissionMatrixAction()
        )
        return action_result.matrix

    async def get_permission_matrix(self) -> list[ScopeEntityOperationCombinationInfo]:
        """Return the complete RBAC scope-entity-operation permission matrix."""
        matrix = await self._permission_matrix()
        return [
            ScopeEntityOperationCombinationInfo(
                scope_type=scope,
                entities=self._entity_actions(entity_map),
            )
            for scope, entity_map in sorted(matrix.items())
        ]

    async def get_entity_operation_combinations(self) -> list[EntityOperationCombinationInfo]:
        """Return every entity a role may permit and the operations it may permit on it."""
        matrix = await self._permission_matrix()
        return [
            EntityOperationCombinationInfo(
                entity_type=entity.entity_type,
                operations=entity.actions,
            )
            for entity in self._entity_actions(self._any_entity_map(matrix))
        ]

    async def get_scope_entity_combinations(self) -> list[ScopeEntityCombinationInfo]:
        """Return, per scope a role sits in, the entities a permission there may name."""
        matrix = await self._permission_matrix()
        return [
            ScopeEntityCombinationInfo(
                scope_type=scope,
                valid_entity_types=sorted(entity_map),
            )
            for scope, entity_map in sorted(matrix.items())
        ]

    @staticmethod
    def _any_entity_map(
        matrix: Mapping[EntityType, Mapping[EntityType, Sequence[GrantableOperation]]],
    ) -> Mapping[EntityType, Sequence[GrantableOperation]]:
        """The entities of any one scope. A permission row names no scope, so every
        scope carries the same ones."""
        for entity_map in matrix.values():
            return entity_map
        return {}

    @staticmethod
    def _entity_actions(
        entity_map: Mapping[EntityType, Sequence[GrantableOperation]],
    ) -> list[EntityActionInfo]:
        return sorted(
            [
                EntityActionInfo(
                    entity_type=entity,
                    actions=[
                        OperationInfo(
                            operation=op.name,
                            description=op.description,
                            required_permission=PermissionBitDTO.of(op.permission),
                        )
                        for op in operations
                    ],
                )
                for entity, operations in entity_map.items()
            ],
            key=lambda e: e.entity_type,
        )

    # ------------------------------------------------------------------ create

    async def create(self, input: CreateRoleInput) -> CreateRolePayload:
        """Create a new role in the one scope the input names."""
        scope_input = input.scope_input()
        result = await self._permission_controller.create_role.run(
            CreateRoleAction(
                creator=RoleCreator(
                    name=input.name,
                    scope=self._scope_identifier(scope_input.scope_type, scope_input.scope_id),
                    description=input.description,
                    auto_assign=input.auto_assign,
                )
            )
        )
        return CreateRolePayload(role=self._role_data_to_node(result.data))

    # ------------------------------------------------------------------ GQL search

    async def admin_search_permissions_gql(
        self,
        input: AdminSearchPermissionsGQLInput,
        base_conditions: Sequence[QueryCondition] | None = None,
    ) -> SearchResult[PermissionNode]:
        """Search scoped permissions with cursor/offset pagination."""
        conditions = self._convert_permission_filter(input.filter) if input.filter else []
        orders = self._convert_permission_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_permission_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=base_conditions,
        )
        raw = await self._permission_controller.global_search_permissions.run(
            GlobalSearchPermissionsAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=RolePermissionSearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )
        return SearchResult(
            items=[self._permission_data_to_node(item) for item in raw.items],
            total_count=raw.total_count,
            has_next_page=raw.has_next_page,
            has_previous_page=raw.has_previous_page,
        )

    async def admin_search_roles_gql(
        self,
        input: SearchRolesInput,
    ) -> SearchResult[RoleNode]:
        """Search roles with cursor/offset pagination."""
        conditions = self._convert_role_filter_gql(input.filter) if input.filter else []
        orders = self._convert_role_orders_gql(input.order) if input.order else []
        searcher = self._build_searcher(
            RoleSearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=_role_gql_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        raw = await self._permission_controller.global_search_roles.run(
            GlobalSearchRolesAction(
                searcher=GlobalSearcher(used_by=self._role_usage(input.usage), searcher=searcher)
            )
        )
        return SearchResult(
            items=[self._role_data_to_node(item) for item in raw.items],
            total_count=raw.total_count,
            has_next_page=raw.has_next_page,
            has_previous_page=raw.has_previous_page,
        )

    async def my_search_roles(self, input: SearchRolesInput) -> SearchResult[RoleNode]:
        """The roles the current authenticated user holds."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        return await self.search_roles_in_scope([HeldRoleTarget(user_id=UserID(me.user_id))], input)

    async def search_roles_in_scope(
        self,
        targets: Sequence[RoleTarget],
        input: SearchRolesInput,
    ) -> SearchResult[RoleNode]:
        """Search the roles the named scopes reach."""
        conditions = self._convert_role_filter_gql(input.filter) if input.filter else []
        orders = self._convert_role_orders_gql(input.order) if input.order else []
        searcher = self._build_searcher(
            RoleSearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=_role_gql_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        raw = await self._permission_controller.search_roles_in_scope.run(
            SearchRolesInScopeAction(
                searcher=ScopedSearcher(
                    scopes=targets,
                    used_by=self._role_usage(input.usage),
                    searcher=searcher,
                )
            )
        )
        return SearchResult(
            items=[self._role_data_to_node(item) for item in raw.items],
            total_count=raw.total_count,
            has_next_page=raw.has_next_page,
            has_previous_page=raw.has_previous_page,
        )

    async def my_search_role_assignments(
        self,
        input: SearchRoleAssignmentsInput,
    ) -> SearchResult[RoleAssignmentNode]:
        """Search role assignments for the current authenticated user."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        return await self.search_role_assignments_in_scope(
            [UserRoleAssignmentTarget(user_id=UserID(me.user_id))], input
        )

    async def search_role_assignments_in_scope(
        self,
        targets: Sequence[RoleAssignmentTarget],
        input: SearchRoleAssignmentsInput,
    ) -> SearchResult[RoleAssignmentNode]:
        """Search the role assignments the named scopes reach."""
        searcher = self._build_searcher(
            RoleAssignmentSearcher,
            conditions=self._convert_assignment_filter(input.filter) if input.filter else [],
            orders=self._convert_assignment_orders(input.order) if input.order else [],
            pagination_spec=_assignment_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        found = await self._permission_controller.scoped_search_role_assignments.run(
            ScopedSearchRoleAssignmentsAction(targets=targets, searcher=searcher)
        )
        raw = found.result
        return SearchResult(
            items=[self._assignment_data_to_node(item) for item in raw.items],
            total_count=raw.total_count,
            has_next_page=raw.has_next_page,
            has_previous_page=raw.has_previous_page,
        )

    async def search_role_permissions(
        self,
        role_id: RoleID,
        input: AdminSearchPermissionsGQLInput,
    ) -> SearchResult[PermissionNode]:
        """Search the permission entries one role holds."""
        searcher = self._build_searcher(
            RolePermissionSearcher,
            conditions=self._convert_permission_filter(input.filter) if input.filter else [],
            orders=self._convert_permission_orders(input.order) if input.order else [],
            pagination_spec=_permission_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        found = await self._permission_controller.search_role_permissions.run(
            SearchRolePermissionsAction(role_ids=[role_id], searcher=searcher)
        )
        return SearchResult(
            items=[self._permission_data_to_node(item) for item in found.items],
            total_count=found.total_count,
            has_next_page=found.has_next_page,
            has_previous_page=found.has_previous_page,
        )

    async def admin_search_role_assignments(
        self,
        input: SearchRoleAssignmentsInput,
    ) -> SearchResult[RoleAssignmentNode]:
        """Search role assignments with cursor/offset pagination (admin)."""
        searcher = self._build_searcher(
            RoleAssignmentSearcher,
            conditions=self._convert_assignment_filter(input.filter) if input.filter else [],
            orders=self._convert_assignment_orders(input.order) if input.order else [],
            pagination_spec=_assignment_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._permission_controller.global_search_role_assignments.run(
            GlobalSearchRoleAssignmentsAction(searcher=searcher)
        )
        raw = action_result.result
        return SearchResult(
            items=[self._assignment_data_to_node(item) for item in raw.items],
            total_count=raw.total_count,
            has_next_page=raw.has_next_page,
            has_previous_page=raw.has_previous_page,
        )

    async def get(self, role_id: UUID) -> RoleNode:
        """Get a role by ID."""
        action_result = await self._permission_controller.get_role_detail.run(
            GetRoleDetailAction(role_id=RoleID(role_id))
        )
        return self._role_detail_to_node(action_result.role)

    # ------------------------------------------------------------------ update

    async def update(self, role_id: UUID, input: UpdateRoleInput) -> UpdateRolePayload:
        """Update an existing role."""
        updater = self._build_updater(role_id, input)
        result = await self._permission_controller.update_role.run(
            UpdateRoleAction(updater=updater)
        )
        return UpdateRolePayload(role=self._role_data_to_node(result.data))

    # ------------------------------------------------------------------ delete

    async def delete(self, role_id: UUID) -> DeleteRolePayload:
        """Soft-delete a role (marks status as DELETED)."""
        result = await self._permission_controller.delete_role.run(
            DeleteRoleAction(updater=RoleSoftDeleteUpdater(role_id=RoleID(role_id)))
        )
        return DeleteRolePayload(id=result.data.id)

    # ------------------------------------------------------------------ purge

    async def purge(self, role_id: UUID) -> PurgeRolePayload:
        """Hard-delete a role from the database."""
        result = await self._permission_controller.purge_role.run(
            PurgeRoleAction(role_id=RoleID(role_id))
        )
        return PurgeRolePayload(id=result.data.id)

    # ------------------------------------------------------------------ delete_permission

    async def delete_permission(self, permission_id: UUID) -> DeletePermissionPayloadDTO:
        """Hard-delete a scoped permission."""
        await self._permission_controller.delete_permission.run(
            DeletePermissionAction(permission_id=PermissionID(permission_id))
        )
        return DeletePermissionPayloadDTO(id=permission_id)

    # ------------------------------------------------------------------ create_permission / update_permission

    async def create_permission(self, input: CreatePermissionInputDTO) -> PermissionNode:
        """Create a permission on the role; it holds in the scope the role sits in."""
        creator = RolePermissionCreator(
            entity_type=input.entity_type,
            permission=input.permission_bit(),
        )
        action_result = await self._permission_controller.add_role_permission.run(
            AddRolePermissionAction(role_id=RoleID(input.role_id), creator=creator)
        )
        return self._permission_data_to_node(action_result.data)

    async def update_permission(self, input: UpdatePermissionInputDTO) -> PermissionNode:
        """Update an existing permission."""
        updater = RolePermissionUpdater(
            permission_id=PermissionID(input.id),
            entity_type=OptionalState.from_unset(input.entity_type),
            permission=OptionalState.from_unset(input.permission_bit()),
        )
        action_result = await self._permission_controller.update_permission.run(
            UpdatePermissionAction(permission_id=PermissionID(input.id), updater=updater)
        )
        return self._permission_data_to_node(action_result.data)

    # ------------------------------------------------------------------ assign_role / revoke_role

    async def assign_role(self, input: AssignRoleInputDTO) -> RoleAssignmentNode:
        """Assign a role to a user."""
        action_result = await self._rbac.assign_role.run(
            AssignRoleAction(
                input=UserRoleAssignmentInput(
                    user_id=input.user_id,
                    role_id=input.role_id,
                    project_id=input.project_id,
                )
            )
        )
        data: UserRoleAssignmentData = action_result.data
        return RoleAssignmentNode(
            id=data.id,
            user_id=data.user_id,
            role_id=data.role_id,
            granted_by=data.granted_by,
            granted_at=datetime.now(tz=UTC),
        )

    async def revoke_role(self, input: RevokeRoleInputDTO) -> RoleAssignmentNode:
        """Revoke a role from a user."""
        action_result = await self._rbac.revoke_role.run(
            RevokeRoleAction(
                input=UserRoleRevocationInput(user_id=input.user_id, role_id=input.role_id)
            )
        )
        data: UserRoleRevocationData = action_result.data
        return RoleAssignmentNode(
            id=data.user_role_id,
            user_id=data.user_id,
            role_id=data.role_id,
            granted_by=None,
            granted_at=datetime.now(tz=UTC),
        )

    # ------------------------------------------------------------------ bulk_assign_role / bulk_revoke_role

    async def bulk_assign_role(self, input: BulkAssignRoleInputDTO) -> BulkAssignRoleResultPayload:
        """Bulk-assign a role to multiple users."""
        action_result = await self._rbac.bulk_assign_role.run(
            BulkAssignRoleAction(
                role_id=RoleID(input.role_id),
                user_ids=[UserID(uid) for uid in input.user_ids],
                project_id=input.project_id,
            )
        )
        result: BulkRoleAssignmentResultData = action_result.data
        now = datetime.now(tz=UTC)
        return BulkAssignRoleResultPayload(
            assigned=[
                RoleAssignmentNode(
                    id=s.id,
                    user_id=s.user_id,
                    role_id=s.role_id,
                    granted_by=s.granted_by,
                    granted_at=now,
                )
                for s in result.successes
            ],
            failed=[],
        )

    async def bulk_add_role_permissions(
        self,
        input: BulkAddRolePermissionsInputDTO,
    ) -> BulkAddRolePermissionsPayload:
        """Insert scoped permission rows across one or more roles, one entry at a time,
        each answered for by its role; an entry the database refuses is reported
        beside the ones that landed."""
        items: list[PermissionNode] = []
        failed: list[BulkAddRolePermissionFailureInfo] = []
        for entry in input.permissions:
            try:
                result = await self._permission_controller.add_role_permission.run(
                    AddRolePermissionAction(
                        role_id=RoleID(entry.role_id),
                        creator=self._role_permission_creator(entry),
                    )
                )
            except (PermissionAlreadyGranted, RepositoryIntegrityError) as e:
                failed.append(
                    BulkAddRolePermissionFailureInfo(
                        role_id=entry.role_id,
                        entity_type=entry.entity_type,
                        permission=entry.permission,
                        message=str(e),
                    )
                )
                continue
            items.append(self._permission_data_to_node(result.data))
        return BulkAddRolePermissionsPayload(items=items, failed=failed)

    async def bulk_remove_role_permissions(
        self,
        input: BulkRemoveRolePermissionsInputDTO,
    ) -> BulkRemoveRolePermissionsPayload:
        """Delete permission rows by primary key, each answered for by its role. An id
        matching no row is left out of the answer rather than reported."""
        if not input.permission_ids:
            return BulkRemoveRolePermissionsPayload(items=[], failed=[])
        try:
            result = await self._permission_controller.bulk_remove_role_permissions.run(
                BulkRemoveRolePermissionsAction(
                    permission_ids=[PermissionID(pid) for pid in input.permission_ids]
                )
            )
        except NotFoundError:
            return BulkRemoveRolePermissionsPayload(items=[], failed=[])
        return BulkRemoveRolePermissionsPayload(
            items=[self._permission_data_to_node(item) for item in result.successes.values()],
            failed=[
                BulkRemoveRolePermissionFailureInfo(
                    permission_id=permission_id,
                    message=str(exception),
                )
                for permission_id, exception in result.errors.items()
                if not isinstance(exception, NotFoundError)
            ],
        )

    async def replace_role_permissions(
        self,
        input: ReplaceRolePermissionsInputDTO,
    ) -> ReplaceRolePermissionsPayload:
        """Replace one role's entire scoped-permission set."""
        for entry in input.permissions:
            if entry.role_id != input.role_id:
                raise ReplaceRolePermissionRoleIdMismatch(
                    f"entry role_id {entry.role_id} does not match request role_id {input.role_id}",
                )
        action_result = await self._permission_controller.replace_role_permissions.run(
            ReplaceRolePermissionsAction(
                role_id=RoleID(input.role_id),
                entries=self._permission_entries(input.permissions),
            )
        )
        result: BulkRolePermissionReplaceResultData = action_result.data
        return ReplaceRolePermissionsPayload(
            items=[self._permission_data_to_node(item) for item in result.successes],
            failed=[],
        )

    def _permission_entries(
        self, entries: Sequence[CreatePermissionInputDTO]
    ) -> list[PermissionEntry]:
        """One entry per entity type; an input names a single operation, and an entity
        type named more than once holds every operation named on it."""
        held: dict[EntityType, Permission] = {}
        for entry in entries:
            entity_type = entry.entity_type
            held[entity_type] = held.get(entity_type, Permission.NONE) | entry.permission_bit()
        return [
            PermissionEntry(entity_type=entity_type, permission=permission)
            for entity_type, permission in held.items()
        ]

    def _role_permission_creator(self, entry: CreatePermissionInputDTO) -> RolePermissionCreator:
        return RolePermissionCreator(
            entity_type=entry.entity_type,
            permission=entry.permission_bit(),
        )

    async def bulk_revoke_role(self, input: BulkRevokeRoleInputDTO) -> BulkRevokeRoleResultPayload:
        """Bulk-revoke a role from multiple users."""
        action_result = await self._rbac.bulk_revoke_role.run(
            BulkRevokeRoleAction(
                input=BulkUserRoleRevocationInput(role_id=input.role_id, user_ids=input.user_ids)
            )
        )
        result: BulkRoleRevocationResultData = action_result.data
        now = datetime.now(tz=UTC)
        return BulkRevokeRoleResultPayload(
            revoked=[
                RoleAssignmentNode(
                    id=s.user_role_id,
                    user_id=s.user_id,
                    role_id=s.role_id,
                    granted_by=None,
                    granted_at=now,
                )
                for s in result.successes
            ],
            failed=[
                BulkRevokeRoleFailureInfo(user_id=f.user_id, message=f.message)
                for f in result.failures
            ],
        )

    # ------------------------------------------------------------------ helpers (GQL layer)

    def _role_usage(self, usage: RoleUsageDTO | None) -> list[UsedBy]:
        """The uses narrowing the roles read."""
        if usage is None or usage.uses is None:
            return []
        linked = RoleSearchableFields.linked.usage
        return [
            linked.role_presets.uses(RolePresetID(preset_id))
            for preset_id in usage.uses.role_preset or ()
        ]

    def _convert_permission_bit_filter(
        self,
        f: PermissionBitFilter,
        conditions: EnumConditions[Permission],
    ) -> list[QueryCondition]:
        """Each operation the caller set, on the entry's one permission bit."""
        applied: list[QueryCondition] = []
        if f.equals is not None:
            applied.append(conditions.equals(f.equals.to_permission()))
        if f.not_equals is not None:
            applied.append(conditions.not_equals(f.not_equals.to_permission()))
        if f.in_:
            applied.append(conditions.in_([v.to_permission() for v in f.in_]))
        if f.not_in:
            applied.append(conditions.not_in([v.to_permission() for v in f.not_in]))
        return applied

    def _convert_permission_filter(self, f: PermissionFilterDTO) -> list[QueryCondition]:
        fields = PermissionSearchableFields.own
        conditions = [
            *self.apply_uuid_filter(f.role_id, fields.role_id.filter),
            *self.apply_string_filter(f.entity_type, fields.entity_type.filter),
            *self.apply_datetime_filter(f.created_at, fields.created_at.filter),
        ]
        if f.permission is not None:
            conditions.extend(
                self._convert_permission_bit_filter(f.permission, fields.permission.filter)
            )
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_permission_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_permission_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_permission_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_permission_orders(self, orders: list[PermissionOrderByDTO]) -> list[QueryOrder]:
        fields = PermissionSearchableFields.own
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirectionV2.ASC
            if o.field == "id":
                result.append(fields.id.order.apply(ascending))
            elif o.field == "entity_type":
                result.append(fields.entity_type.order.apply(ascending))
            elif o.field == "created_at":
                result.append(fields.created_at.order.apply(ascending))
        return result

    def _convert_role_filter_gql(self, f: RoleFilterDTO) -> list[QueryCondition]:
        fields = RoleSearchableFields.own
        conditions = [
            *self.apply_string_filter(f.name, fields.name.filter),
            *self._convert_role_source_filter(f.source, fields.source.filter),
            *self._convert_role_status_filter(f.status, fields.status.filter),
            *self._convert_assigned_user_nested_filter(f.assigned_user),
            *self._convert_mapped_scope_nested_filter(f.mapped_scope),
            *self.apply_to_many_filter(
                f.permissions,
                RoleSearchableFields.nested.permissions.correlation,
                self._convert_permission_filter,
            ),
        ]
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_role_filter_gql(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_role_filter_gql(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_role_filter_gql(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_role_source_filter(
        self, f: RoleSourceFilterDTO | None, conditions: EnumConditions[InternalRoleSource]
    ) -> list[QueryCondition]:
        """The request-side source names carry the same values as the stored ones."""
        if f is None:
            return []
        applied: list[QueryCondition] = []
        if f.equals is not None:
            applied.append(conditions.equals(InternalRoleSource(f.equals)))
        if f.in_:
            applied.append(conditions.in_([InternalRoleSource(s) for s in f.in_]))
        if f.not_equals is not None:
            applied.append(conditions.not_equals(InternalRoleSource(f.not_equals)))
        if f.not_in:
            applied.append(conditions.not_in([InternalRoleSource(s) for s in f.not_in]))
        return applied

    def _convert_role_status_filter(
        self, f: RoleStatusFilterDTO | None, conditions: EnumConditions[InternalRoleStatus]
    ) -> list[QueryCondition]:
        """The request-side status names carry the same values as the stored ones."""
        if f is None:
            return []
        applied: list[QueryCondition] = []
        if f.equals is not None:
            applied.append(conditions.equals(InternalRoleStatus(f.equals)))
        if f.in_:
            applied.append(conditions.in_([InternalRoleStatus(s) for s in f.in_]))
        if f.not_equals is not None:
            applied.append(conditions.not_equals(InternalRoleStatus(f.not_equals)))
        if f.not_in:
            applied.append(conditions.not_in([InternalRoleStatus(s) for s in f.not_in]))
        return applied

    def _convert_assigned_user_nested_filter(
        self, f: UserNestedFilterDTO | None
    ) -> list[QueryCondition]:
        """Deprecated. Every condition lands in one EXISTS over one assignment row."""
        if f is None:
            return []
        row_conditions = self.apply_uuid_filter(
            f.user_id, RoleAssignmentSearchableFields.own.user_id.filter
        )
        conditions: list[QueryCondition] = []
        if row_conditions:
            conditions.append(DeprecatedRoleConditions.exists_assignment_combined(row_conditions))
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_assigned_user_nested_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_assigned_user_nested_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_assigned_user_nested_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_mapped_scope_nested_filter(
        self, f: MappedScopeNestedFilterDTO | None
    ) -> list[QueryCondition]:
        """The scope a role is registered in sits in the role's own two columns."""
        if f is None:
            return []
        fields = RoleSearchableFields.own
        conditions = [
            *self.apply_string_filter(f.scope_type, fields.scope_type.filter),
            *self.apply_uuid_filter(f.scope_id, fields.scope_id.filter),
        ]
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_mapped_scope_nested_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_mapped_scope_nested_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_mapped_scope_nested_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_role_orders_gql(self, orders: list[RoleOrderByDTO]) -> list[QueryOrder]:
        fields = RoleSearchableFields.own
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirectionV2.ASC
            if o.field == "name":
                result.append(fields.name.order.apply(ascending))
            elif o.field == "created_at":
                result.append(fields.created_at.order.apply(ascending))
            elif o.field == "updated_at":
                result.append(fields.updated_at.order.apply(ascending))
        return result

    def _convert_role_nested_filter(self, f: RoleNestedFilterDTO) -> list[QueryCondition]:
        """Deprecated. Every condition lands in one EXISTS over the assignment's role."""
        fields = RoleSearchableFields.own
        row_conditions = [
            *self.apply_string_filter(f.name, fields.name.filter),
            *self._convert_role_source_filter(f.source, fields.source.filter),
            *self._convert_role_status_filter(f.status, fields.status.filter),
        ]
        conditions: list[QueryCondition] = []
        if row_conditions:
            conditions.append(
                DeprecatedRoleAssignmentConditions.exists_role_combined(row_conditions)
            )
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_role_nested_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_role_nested_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_role_nested_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_permission_nested_filter(
        self, f: PermissionNestedFilterDTO
    ) -> list[QueryCondition]:
        """Deprecated. Every condition lands in one EXISTS over one permission entry."""
        fields = PermissionSearchableFields.own
        row_conditions = [
            *self.apply_string_filter(f.entity_type, fields.entity_type.filter),
            *(
                self._convert_permission_bit_filter(f.permission, fields.permission.filter)
                if f.permission is not None
                else []
            ),
        ]
        conditions: list[QueryCondition] = []
        if row_conditions:
            conditions.append(
                DeprecatedRoleAssignmentConditions.exists_permission_combined(row_conditions)
            )
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_permission_nested_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_permission_nested_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_permission_nested_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_assignment_filter(self, f: RoleAssignmentFilterDTO) -> list[QueryCondition]:
        """The searcher joins the assignment row to its user, so the user's columns
        carry plain conditions rather than a subquery."""
        fields = RoleAssignmentSearchableFields.own
        user_fields = UserSearchableFields.own
        conditions = [
            *self.apply_uuid_filter(f.role_id, fields.role_id.filter),
            *(self._convert_role_nested_filter(f.role) if f.role is not None else []),
            *(
                self._convert_permission_nested_filter(f.permission)
                if f.permission is not None
                else []
            ),
            *self.apply_string_filter(f.username, user_fields.username.filter),
            *self.apply_string_filter(f.email, user_fields.email.filter),
        ]
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_assignment_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_assignment_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_assignment_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_assignment_orders(
        self, orders: list[RoleAssignmentOrderByDTO]
    ) -> list[QueryOrder]:
        fields = RoleAssignmentSearchableFields.own
        user_fields = UserSearchableFields.own
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirectionV2.ASC
            if o.field == "username":
                result.append(user_fields.username.order.apply(ascending))
            elif o.field == "email":
                result.append(user_fields.email.order.apply(ascending))
            elif o.field == "granted_at":
                result.append(fields.granted_at.order.apply(ascending))
        return result

    def _build_updater(self, role_id: UUID, input: UpdateRoleInput) -> RoleUpdater:
        return RoleUpdater(
            role_id=RoleID(role_id),
            name=OptionalState.from_unset(input.name),
            description=TriState.from_unset(input.description),
            auto_assign=OptionalState.from_unset(input.auto_assign),
        )

    @staticmethod
    def _role_data_to_node(data: RoleData) -> RoleNode:
        return RoleNode(
            id=data.id,
            entity_id=data.entity_id(),
            name=data.name,
            description=data.description,
            source=RoleSourceDTO(data.source.value),
            status=RoleStatusDTO(data.status.value),
            auto_assign=data.auto_assign,
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
            scope_type=data.scope_type,
            scope_id=data.scope_id,
        )

    @staticmethod
    def _role_detail_to_node(data: RoleDetailData) -> RoleNode:
        return RoleNode(
            id=data.id,
            entity_id=data.id,
            name=data.name,
            description=data.description,
            source=RoleSourceDTO(data.source.value),
            status=RoleStatusDTO(data.status.value),
            auto_assign=data.auto_assign,
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
            scope_type=data.scope_type,
            scope_id=data.scope_id,
        )

    @staticmethod
    def _permission_data_to_node(data: PermissionData) -> PermissionNode:
        return PermissionNode(
            id=data.id,
            field_id=data.id,
            role_id=data.role_id,
            entity_type=EntityType(data.entity_type),
            permission=PermissionBitDTO.of(data.permission),
            created_at=data.created_at,
        )

    @staticmethod
    def _assignment_data_to_node(data: AssignedUserData) -> RoleAssignmentNode:
        return RoleAssignmentNode(
            id=data.id,
            user_id=data.user_id,
            role_id=data.role_id,
            granted_by=data.granted_by,
            granted_at=data.granted_at,
        )
