from collections.abc import Mapping, Sequence
from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.bulk.validator.base import (
    AtomicBulkActionValidator,
    PartialBulkActionValidator,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.virtual_scope import EntityPermissionCheckKey
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)


class VirtualScopeBulkPermissionCheck:
    """Which of a run's named entities the caller lacks the run's permission on.

    The check itself, kept apart from what a shape does with the answer: one shape
    refuses the whole run, the other carries the denials into its result.
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

    async def denied(self, meta: BulkActionTriggerMeta) -> Sequence[EntityIdentifier]:
        if not self._config_provider.config.manager.rbac.enforcement_enabled:
            return ()

        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return ()

        keys = [
            EntityPermissionCheckKey(
                user_id=UserID(user.user_id),
                entity=entity_id,
            )
            for entity_id in meta.entity_ids
        ]
        permission = meta.operation_type.to_permission()
        permission_map = await self._repository.check_bulk_permission_via_virtual_scope(
            keys, permission
        )
        return [key.entity for key in keys if not permission_map.get(key, False)]


class VirtualScopeAtomicBulkActionRBACValidator(AtomicBulkActionValidator):
    """The check applied to the run: one target lacking the permission rejects it all.

    For the per-entity answer see :class:`VirtualScopePartialBulkActionRBACValidator`; both
    ask the same question of the virtual-scope chain.
    """

    _check: VirtualScopeBulkPermissionCheck

    def __init__(
        self,
        repository: PermissionControllerRepository,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._check = VirtualScopeBulkPermissionCheck(repository, config_provider)

    @override
    async def validate(self, meta: BulkActionTriggerMeta) -> None:
        denied = await self._check.denied(meta)
        if denied:
            raise NotEnoughPermission(
                f"The caller lacks the permission this run asks for on entities {list(denied)}"
            )


class VirtualScopePartialBulkActionRBACValidator(PartialBulkActionValidator):
    """The check answered per entity, so the run keeps going without the denied ones.

    A denied entity becomes one failed item of the result, told apart from an id that
    matched no row by the error it carries.
    """

    _check: VirtualScopeBulkPermissionCheck

    def __init__(
        self,
        repository: PermissionControllerRepository,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._check = VirtualScopeBulkPermissionCheck(repository, config_provider)

    @override
    async def validate(self, meta: BulkActionTriggerMeta) -> Mapping[EntityIdentifier, Exception]:
        return {
            entity_id: NotEnoughPermission(
                f"The caller lacks the permission this run asks for on entity {entity_id}"
            )
            for entity_id in await self._check.denied(meta)
        }
