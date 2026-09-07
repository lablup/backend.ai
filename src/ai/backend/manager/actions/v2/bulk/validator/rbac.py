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
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.virtual_entity import OwnCheckKey
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)


class BulkOwnCheck:
    """The own check on every entity a run names, answered per entity.

    The check itself, kept apart from what a shape does with the answer: one shape
    refuses the whole run on any entity not owned, the other carries those into its
    result. Enforcement off or a superadmin answers every entity as owned.
    """

    _repository: PermissionControllerRepository
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        repository: PermissionControllerRepository,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._repository = repository
        self._config_provider = config_provider

    async def held(
        self, entity_ids: Sequence[EntityIdentifier]
    ) -> Mapping[EntityIdentifier, Permission]:
        """The bits the caller holds on each entity, as this check sees them.

        Enforcement off or a superadmin holds everything; anyone else holds what the
        own check answers. What a domain shows as the caller's permissions is read
        from here, so it cannot disagree with what the check would allow.
        """
        if not self._config_provider.config.manager.rbac.enforcement_enabled:
            return dict.fromkeys(entity_ids, Permission.full())

        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return dict.fromkeys(entity_ids, Permission.full())

        keys = [
            OwnCheckKey(
                user_id=UserID(user.user_id),
                entity=entity_id,
            )
            for entity_id in entity_ids
        ]
        owned = await self._repository.owned_permissions(keys)
        return {key.entity: owned.get(key, Permission.NONE) for key in keys}

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

    def __init__(
        self,
        repository: PermissionControllerRepository,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._check = BulkOwnCheck(repository, config_provider)

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
    matched no row by the error it carries.
    """

    _check: BulkOwnCheck

    def __init__(
        self,
        repository: PermissionControllerRepository,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._check = BulkOwnCheck(repository, config_provider)

    @override
    async def validate(self, meta: BulkActionTriggerMeta) -> Mapping[EntityIdentifier, Exception]:
        owned = await self._check.check(meta)
        return {
            entity_id: NotEnoughPermission(
                f"The caller lacks the permission this run asks for on entity {entity_id}"
            )
            for entity_id, is_owned in owned.items()
            if not is_owned
        }
