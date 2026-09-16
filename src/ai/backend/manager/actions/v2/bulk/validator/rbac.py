from collections.abc import Mapping, Sequence
from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.bulk.validator.base import (
    AtomicBulkActionValidator,
    PartialBulkActionValidator,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)


class BulkOwnCheck:
    """The own check on every entity a run names, answered per entity.

    The check itself, kept apart from what a shape does with the answer: one shape
    refuses the whole run on any entity not owned, the other carries those into its
    result.
    """

    _repository: RbacPermissionCheckRepository

    def __init__(self, repository: RbacPermissionCheckRepository) -> None:
        self._repository = repository

    async def held(
        self, entity_ids: Sequence[EntityIdentifier]
    ) -> Mapping[EntityIdentifier, Permission]:
        """The bits the caller holds on each entity, as this check sees them.

        What a domain shows as the caller's permissions is read from here, so it cannot
        disagree with what the check would allow.
        """
        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        return await self._repository.held_permissions(UserID(user.user_id), entity_ids)

    async def check(self, meta: BulkActionTriggerMeta) -> Mapping[EntityIdentifier, bool]:
        permission = meta.operation_type.to_permission()
        held = await self.held(meta.entity_ids)
        return {entity_id: mask.covers(permission) for entity_id, mask in held.items()}


class VirtualEntityAtomicBulkActionRBACValidator(AtomicBulkActionValidator):
    """The check applied to the run: one target lacking the permission rejects it all.

    For the per-entity answer see :class:`VirtualEntityPartialBulkActionRBACValidator`; both
    ask the same own check.
    """

    _check: BulkOwnCheck

    def __init__(self, repository: RbacPermissionCheckRepository) -> None:
        self._check = BulkOwnCheck(repository)

    @override
    async def validate(self, meta: BulkActionTriggerMeta) -> None:
        owned = await self._check.check(meta)
        denied = [entity_id for entity_id, is_owned in owned.items() if not is_owned]
        if denied:
            raise NotEnoughPermission(
                f"The caller lacks the permission this run asks for on entities {denied}"
            )


class VirtualEntityPartialBulkActionRBACValidator(PartialBulkActionValidator):
    """The check answered per entity, so the run keeps going without the denied ones.

    A denied entity becomes one failed item of the result, told apart from an id that
    matched no row by the error it carries. A superadmin is denied nothing, so an id
    that matched no row reaches the operation and comes back as the miss it is.
    """

    _check: BulkOwnCheck

    def __init__(self, repository: RbacPermissionCheckRepository) -> None:
        self._check = BulkOwnCheck(repository)

    @override
    async def validate(self, meta: BulkActionTriggerMeta) -> Mapping[EntityIdentifier, Exception]:
        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return {}
        owned = await self._check.check(meta)
        return {
            entity_id: NotEnoughPermission(
                f"The caller lacks the permission this run asks for on entity {entity_id}"
            )
            for entity_id, is_owned in owned.items()
            if not is_owned
        }
