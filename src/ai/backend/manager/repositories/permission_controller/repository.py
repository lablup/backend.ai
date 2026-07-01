from __future__ import annotations

import uuid
from collections.abc import Collection, Mapping
from typing import cast

from ai.backend.common.data.permission.types import OperationType, RBACElementType
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.actions.action.rbac_role_invitation import (
    CreateRoleInvitationResult,
)
from ai.backend.manager.data.permission.entity import ElementAssociationListResult, EntityListResult
from ai.backend.manager.data.permission.id import ObjectId
from ai.backend.manager.data.permission.permission import (
    PermissionData,
    PermissionListResult,
)
from ai.backend.manager.data.permission.role import (
    AssignedUserListResult,
    BatchEntityPermissionCheckInput,
    BulkPermissionCheckInput,
    BulkRoleAssignmentFailure,
    BulkRoleAssignmentResultData,
    BulkRolePermissionAddFailure,
    BulkRolePermissionAddResultData,
    BulkRolePermissionRemoveFailure,
    BulkRolePermissionRemoveResultData,
    BulkRolePermissionReplaceResultData,
    BulkRoleRevocationResultData,
    BulkUserRoleRevocationInput,
    PermissionResolutionKey,
    RoleData,
    RoleDetailData,
    RoleListResult,
    RolePermissionsUpdateInput,
    RoleRevocationResult,
    ScopeChainPermissionCheckInput,
    ScopePermissionCheckInput,
    SingleEntityPermissionCheckInput,
    UserRoleAssignmentData,
    UserRoleAssignmentInput,
    UserRoleRevocationInput,
)
from ai.backend.manager.data.permission.types import (
    EntityType,
    ScopeListResult,
    ScopeType,
)
from ai.backend.manager.data.role_invitation.types import RoleInvitationData
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import (
    BulkCreator,
    Creator,
)
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.permission_controller.creators import (
    PermissionCreatorSpec,
    UserRoleCreatorSpec,
)
from ai.backend.manager.repositories.permission_controller.types import (
    PermissionSearchScope,
    ScopedRoleSearchScope,
)
from ai.backend.manager.repositories.role_invitation.types import (
    InviteeSearchScope,
    InviterSearchScope,
    RoleInvitationSearchResult,
    RoleInvitationSearchScope,
)

from .db_source.db_source import CreateRoleInput, PermissionDBSource

permission_controller_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY, layer=LayerType.PERMISSION_CONTROLLER_REPOSITORY
            )
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class PermissionControllerRepository:
    _db_source: PermissionDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = PermissionDBSource(db)

    @permission_controller_repository_resilience.apply()
    async def create_role(self, input_data: CreateRoleInput) -> RoleData:
        """
        Create a new role in the database.

        Returns the created role data.
        """
        role_row = await self._db_source.create_role(input_data)
        return role_row.to_data()

    @permission_controller_repository_resilience.apply()
    async def create_permission(
        self,
        creator: Creator[PermissionRow],
    ) -> PermissionData:
        """
        Create a new permission in the database.

        Returns the created permission data.
        """
        row = await self._db_source.create_permission(creator)
        return row.to_data()

    @permission_controller_repository_resilience.apply()
    async def delete_permission(
        self,
        purger: Purger[PermissionRow],
    ) -> PermissionData:
        """
        Delete a permission from the database.

        Returns the deleted permission data.

        Raises:
            ObjectNotFound: If permission does not exist.
        """
        row = await self._db_source.delete_permission(purger)
        return row.to_data()

    @permission_controller_repository_resilience.apply()
    async def update_permission(
        self,
        updater: Updater[PermissionRow],
    ) -> PermissionData:
        """
        Update a permission in the database.

        Returns the updated permission data.

        Raises:
            ObjectNotFound: If permission does not exist.
        """
        row = await self._db_source.update_permission(updater)
        return row.to_data()

    @permission_controller_repository_resilience.apply()
    async def update_role(self, updater: Updater[RoleRow]) -> RoleData:
        result = await self._db_source.update_role(updater)
        return result.to_data()

    @permission_controller_repository_resilience.apply()
    async def update_role_permissions(
        self, input_data: RolePermissionsUpdateInput
    ) -> RoleDetailData:
        """Update role permissions using batch update."""
        result = await self._db_source.update_role_permissions(input_data=input_data)
        return result.to_detail_data_without_users()

    @permission_controller_repository_resilience.apply()
    async def bulk_add_role_permissions(
        self,
        creator: BulkCreator[PermissionRow],
    ) -> BulkRolePermissionAddResultData:
        result = await self._db_source.bulk_add_role_permissions(creator)
        failures = [
            BulkRolePermissionAddFailure(
                role_id=(spec := cast(PermissionCreatorSpec, error.spec)).role_id,
                scope_type=ScopeType(spec.scope_type.value),
                scope_id=spec.scope_id,
                entity_type=EntityType(spec.entity_type.value),
                operation=spec.operation,
                message=str(error.exception),
            )
            for error in result.errors
        ]
        return BulkRolePermissionAddResultData(
            successes=[row.to_data() for row in result.successes],
            failures=failures,
        )

    @permission_controller_repository_resilience.apply()
    async def bulk_remove_role_permissions(
        self,
        purgers: list[Purger[PermissionRow]],
    ) -> BulkRolePermissionRemoveResultData:
        result = await self._db_source.bulk_remove_role_permissions(purgers)
        failures = [
            BulkRolePermissionRemoveFailure(
                permission_id=cast(uuid.UUID, error.purger.pk_value),
                message=str(error.exception),
            )
            for error in result.errors
        ]
        return BulkRolePermissionRemoveResultData(
            successes=[row.to_data() for row in result.successes],
            failures=failures,
        )

    @permission_controller_repository_resilience.apply()
    async def replace_role_permissions(
        self,
        role_id: uuid.UUID,
        creator: BulkCreator[PermissionRow],
    ) -> BulkRolePermissionReplaceResultData:
        result = await self._db_source.replace_role_permissions(role_id=role_id, creator=creator)
        failures = [
            BulkRolePermissionAddFailure(
                role_id=(spec := cast(PermissionCreatorSpec, error.spec)).role_id,
                scope_type=ScopeType(spec.scope_type.value),
                scope_id=spec.scope_id,
                entity_type=EntityType(spec.entity_type.value),
                operation=spec.operation,
                message=str(error.exception),
            )
            for error in result.errors
        ]
        return BulkRolePermissionReplaceResultData(
            role_id=role_id,
            successes=[row.to_data() for row in result.successes],
            failures=failures,
        )

    @permission_controller_repository_resilience.apply()
    async def delete_role(self, updater: Updater[RoleRow]) -> RoleData:
        result = await self._db_source.delete_role(updater)
        return result.to_data()

    @permission_controller_repository_resilience.apply()
    async def purge_role(self, purger: Purger[RoleRow]) -> RoleData:
        result = await self._db_source.purge_role(purger)
        return result.to_data()

    @permission_controller_repository_resilience.apply()
    async def assign_role(self, data: UserRoleAssignmentInput) -> UserRoleAssignmentData:
        result = await self._db_source.assign_role(data)
        return result.to_data()

    @permission_controller_repository_resilience.apply()
    async def revoke_role(self, data: UserRoleRevocationInput) -> RoleRevocationResult:
        return await self._db_source.revoke_role(data)

    @permission_controller_repository_resilience.apply()
    async def bulk_assign_role(
        self, bulk_creator: BulkCreator[UserRoleRow]
    ) -> BulkRoleAssignmentResultData:
        result = await self._db_source.bulk_assign_role(bulk_creator)
        failures = [
            BulkRoleAssignmentFailure(
                user_id=cast(UserRoleCreatorSpec, error.spec).user_id,
                message=str(error.exception),
            )
            for error in result.errors
        ]
        return BulkRoleAssignmentResultData(
            successes=[row.to_data() for row in result.successes],
            failures=failures,
        )

    @permission_controller_repository_resilience.apply()
    async def bulk_revoke_role(
        self, data: BulkUserRoleRevocationInput
    ) -> BulkRoleRevocationResultData:
        return await self._db_source.bulk_revoke_role(data)

    @permission_controller_repository_resilience.apply()
    async def get_role(self, role_id: uuid.UUID) -> RoleData | None:
        result = await self._db_source.get_role(role_id)
        return result.to_data() if result else None

    @permission_controller_repository_resilience.apply()
    async def check_permission_of_entity(self, data: SingleEntityPermissionCheckInput) -> bool:
        target_object_id = data.target_object_id
        roles = await self._db_source.get_user_roles(data.user_id)
        for role in roles:
            for object_perm in role.object_permission_rows:
                if object_perm.operation != data.operation:
                    continue
                if object_perm.object_id() == target_object_id:
                    return True
        return False

    @permission_controller_repository_resilience.apply()
    async def check_permission_in_scope(self, data: ScopePermissionCheckInput) -> bool:
        return await self._db_source.check_scope_permission_exist(
            data.user_id, data.target_scope_id, data.operation
        )

    @permission_controller_repository_resilience.apply()
    async def check_permission_of_entities(
        self,
        data: BatchEntityPermissionCheckInput,
    ) -> Mapping[ObjectId, bool]:
        """
        Check if the user has the requested operation permission on the given entity IDs.
        Returns a mapping of entity ID to a boolean indicating permission.
        """
        return await self._db_source.check_batch_object_permission_exist(
            data.user_id, data.target_object_ids, data.operation
        )

    @permission_controller_repository_resilience.apply()
    async def search_roles(
        self,
        querier: BatchQuerier,
    ) -> RoleListResult:
        """Searches roles with pagination and filtering."""
        return await self._db_source.search_roles(querier=querier)

    @permission_controller_repository_resilience.apply()
    async def search_roles_in_scope(
        self,
        querier: BatchQuerier,
        scope: ScopedRoleSearchScope,
    ) -> RoleListResult:
        """Search roles registered in a project scope."""
        return await self._db_source.search_roles_in_scope(querier=querier, scope=scope)

    @permission_controller_repository_resilience.apply()
    async def search_permissions(
        self,
        querier: BatchQuerier,
        scope: PermissionSearchScope | None = None,
    ) -> PermissionListResult:
        """Searches permissions with pagination and filtering."""
        return await self._db_source.search_permissions(querier=querier, scope=scope)

    @permission_controller_repository_resilience.apply()
    async def get_role_with_permissions(self, role_id: uuid.UUID) -> RoleDetailData:
        """Get role with all permission details (without users)."""
        result = await self._db_source.get_role_with_permissions(role_id)
        return result.to_detail_data_without_users()

    @permission_controller_repository_resilience.apply()
    async def search_users_assigned_to_role(
        self,
        querier: BatchQuerier,
    ) -> AssignedUserListResult:
        """Searches users assigned to a specific role with pagination and filtering."""
        return await self._db_source.search_users_assigned_to_role(
            querier=querier,
        )

    @permission_controller_repository_resilience.apply()
    async def search_scopes(
        self,
        element_type: RBACElementType,
        querier: BatchQuerier,
    ) -> ScopeListResult:
        """Search scopes based on element type.

        Args:
            element_type: The RBAC element type of scope to search.
            querier: BatchQuerier with conditions, orders, and pagination.

        Returns:
            ScopeListResult with matching scopes.
        """
        match element_type:
            case RBACElementType.DOMAIN:
                return await self._db_source.search_domain_scopes(querier)
            case RBACElementType.PROJECT:
                return await self._db_source.search_project_scopes(querier)
            case RBACElementType.USER:
                return await self._db_source.search_user_scopes(querier)
            case _:
                raise NotImplementedError(
                    "This function will be deprecated and new repository functions will be implemented for each scope"
                )

    @permission_controller_repository_resilience.apply()
    async def search_entities(
        self,
        querier: BatchQuerier,
    ) -> EntityListResult:
        """Search entities within a scope.

        Args:
            querier: BatchQuerier with scope conditions and pagination settings.

        Returns:
            EntityListResult with matching entities.
        """
        return await self._db_source.search_entities_in_scope(querier)

    @permission_controller_repository_resilience.apply()
    async def search_element_associations(
        self,
        querier: BatchQuerier,
    ) -> ElementAssociationListResult:
        """Search element associations (full association rows) within a scope.

        Args:
            querier: BatchQuerier with scope conditions and pagination settings.

        Returns:
            ElementAssociationListResult with full association row data.
        """
        return await self._db_source.search_element_associations_in_scope(querier)

    @permission_controller_repository_resilience.apply()
    async def check_permission_with_scope_chain(
        self,
        data: ScopeChainPermissionCheckInput,
    ) -> bool:
        """Permission check that traverses the scope chain via AUTO edges only.

        Walks the association_scopes_entities hierarchy upward from the target
        entity, checking if the user has the requested operation at any ancestor
        scope. REF edges are not traversed.
        """
        return await self._db_source.check_permission_with_scope_chain(data)

    @permission_controller_repository_resilience.apply()
    async def check_bulk_permission_with_scope_chain(
        self,
        data: BulkPermissionCheckInput,
    ) -> Mapping[PermissionResolutionKey, bool]:
        """Batch permission check that traverses the scope chain via AUTO edges.

        Same semantics as check_permission_with_scope_chain but for an
        arbitrary collection of per-target keys in a single query.
        """
        return await self._db_source.check_bulk_permission_with_scope_chain(data)

    @permission_controller_repository_resilience.apply()
    async def resolve_effective_permissions(
        self,
        keys: Collection[PermissionResolutionKey],
    ) -> Mapping[PermissionResolutionKey, frozenset[OperationType]]:
        """Resolve the set of permitted operations per target key.

        Each input key represents one ``(user_id, element_type, entity_id,
        subject_entity_type)`` combination. For each key, traverses the scope
        chain (AUTO edges) and self-scope permissions to collect all operations
        the user can perform.
        """
        return await self._db_source.resolve_effective_permissions(keys)

    # -- role invitation --

    @permission_controller_repository_resilience.apply()
    async def create_invitation_by_email(
        self,
        *,
        invitee_emails: list[str],
        inviter_user_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> CreateRoleInvitationResult:
        return await self._db_source.create_invitation_by_email(
            invitee_emails=invitee_emails,
            inviter_user_id=inviter_user_id,
            role_id=role_id,
        )

    @permission_controller_repository_resilience.apply()
    async def search_invitations_by_invitee(
        self,
        querier: BatchQuerier,
        scope: InviteeSearchScope,
    ) -> RoleInvitationSearchResult:
        return await self._db_source.search_invitations_by_invitee(querier, scope)

    @permission_controller_repository_resilience.apply()
    async def search_invitations_by_inviter(
        self,
        querier: BatchQuerier,
        scope: InviterSearchScope,
    ) -> RoleInvitationSearchResult:
        return await self._db_source.search_invitations_by_inviter(querier, scope)

    @permission_controller_repository_resilience.apply()
    async def search_invitations_by_role(
        self,
        querier: BatchQuerier,
        scope: RoleInvitationSearchScope,
    ) -> RoleInvitationSearchResult:
        return await self._db_source.search_invitations_by_role(querier, scope)

    @permission_controller_repository_resilience.apply()
    async def admin_search_invitations(
        self,
        querier: BatchQuerier,
    ) -> RoleInvitationSearchResult:
        return await self._db_source.admin_search_invitations(querier)

    @permission_controller_repository_resilience.apply()
    async def accept_invitation(
        self,
        invitation_id: uuid.UUID,
    ) -> RoleInvitationData:
        return await self._db_source.accept_invitation(invitation_id)

    @permission_controller_repository_resilience.apply()
    async def reject_invitation(
        self,
        invitation_id: uuid.UUID,
    ) -> RoleInvitationData:
        return await self._db_source.reject_invitation(invitation_id)

    @permission_controller_repository_resilience.apply()
    async def cancel_invitation(
        self,
        invitation_id: uuid.UUID,
    ) -> RoleInvitationData:
        return await self._db_source.cancel_invitation(invitation_id)
