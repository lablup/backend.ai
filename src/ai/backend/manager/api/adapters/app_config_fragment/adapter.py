"""App config fragment adapter bridging v2 DTOs and the fragment write Processors."""

from __future__ import annotations

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.app_config.types import AppConfigScopeType as AppConfigScopeTypeDTO
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    BulkPurgeAppConfigFragmentInput,
    BulkUpdateAppConfigFragmentInput,
    CreateAppConfigFragmentInput,
    UpdateAppConfigFragmentInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AppConfigFragmentBulkErrorInfo,
    AppConfigFragmentNode,
    BulkPurgeAppConfigFragmentPayload,
    BulkUpdateAppConfigFragmentPayload,
    CreateAppConfigFragmentPayload,
    PurgeAppConfigFragmentPayload,
    UpdateAppConfigFragmentPayload,
)
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
)
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.app_config_fragment.purgers import (
    AppConfigFragmentPurgerSpec,
)
from ai.backend.manager.repositories.app_config_fragment.updaters import (
    AppConfigFragmentUpdaterSpec,
)
from ai.backend.manager.repositories.base import (
    Updater,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_purge import (
    BulkPurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_update import (
    BulkUpdateAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.create import (
    CreateAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.purge import (
    PurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.update import (
    UpdateAppConfigFragmentAction,
)
from ai.backend.manager.types import OptionalState

# Public fragments have no scope owner; the non-null scope_id column stores this empty
# sentinel. Public is identified by scope_type, never by this value.
_PUBLIC_SCOPE_ID = ""


class AppConfigFragmentAdapter(BaseAdapter):
    """Adapter for raw app config fragment write operations."""

    # --- fragment CRUD (RBAC-gated at the processor) ---

    async def create(self, input: CreateAppConfigFragmentInput) -> CreateAppConfigFragmentPayload:
        # scope_id is None only for public (enforced by the DTO validator); persist the empty
        # sentinel since the column is non-null. Domain/user carry the id.
        spec = AppConfigFragmentCreatorSpec(
            config_name=input.config_name,
            scope_type=AppConfigScopeType(input.scope_type.value),
            scope_id=input.scope_id or _PUBLIC_SCOPE_ID,
            config=input.config,
        )
        action_result = await self._processors.app_config_fragment.create.wait_for_complete(
            CreateAppConfigFragmentAction(creator_spec=spec)
        )
        return CreateAppConfigFragmentPayload(
            app_config_fragment=self._fragment_to_node(action_result.fragment),
        )

    async def get(self, fragment_id: AppConfigFragmentID) -> AppConfigFragmentNode:
        action_result = await self._processors.app_config_fragment.get.wait_for_complete(
            GetAppConfigFragmentAction(fragment_id=fragment_id)
        )
        return self._fragment_to_node(action_result.fragment)

    async def update(
        self, fragment_id: AppConfigFragmentID, input: UpdateAppConfigFragmentInput
    ) -> UpdateAppConfigFragmentPayload:
        updater = Updater(
            spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update(input.config)),
            pk_value=fragment_id,
        )
        # No allow-list gate: a fragment row exists only while its entry does (FK with
        # cascade), so an existing fragment is always writable at its own scope.
        action_result = await self._processors.app_config_fragment.update.wait_for_complete(
            UpdateAppConfigFragmentAction(updater=updater)
        )
        return UpdateAppConfigFragmentPayload(
            app_config_fragment=self._fragment_to_node(action_result.fragment),
        )

    async def purge(self, fragment_id: AppConfigFragmentID) -> PurgeAppConfigFragmentPayload:
        purger_spec = AppConfigFragmentPurgerSpec(fragment_id=fragment_id)
        # No allow-list gate — see ``update``.
        action_result = await self._processors.app_config_fragment.purge.wait_for_complete(
            PurgeAppConfigFragmentAction(purger_spec=purger_spec)
        )
        return PurgeAppConfigFragmentPayload(id=action_result.fragment.id)

    async def bulk_update(
        self, input: BulkUpdateAppConfigFragmentInput
    ) -> BulkUpdateAppConfigFragmentPayload:
        updaters = [
            Updater(
                spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update(item.config)),
                pk_value=AppConfigFragmentID(item.id),
            )
            for item in input.items
        ]
        action_result = await self._processors.app_config_fragment.bulk_update.wait_for_complete(
            BulkUpdateAppConfigFragmentAction(updaters=updaters)
        )
        return BulkUpdateAppConfigFragmentPayload(
            succeeded=[self._fragment_to_node(fragment) for fragment in action_result.succeeded],
            failed=[
                AppConfigFragmentBulkErrorInfo(index=error.index, message=error.message)
                for error in action_result.failed
            ],
        )

    async def bulk_purge(
        self, input: BulkPurgeAppConfigFragmentInput
    ) -> BulkPurgeAppConfigFragmentPayload:
        purger_specs = [
            AppConfigFragmentPurgerSpec(fragment_id=AppConfigFragmentID(fragment_id))
            for fragment_id in input.ids
        ]
        action_result = await self._processors.app_config_fragment.bulk_purge.wait_for_complete(
            BulkPurgeAppConfigFragmentAction(purger_specs=purger_specs)
        )
        return BulkPurgeAppConfigFragmentPayload(
            purged_ids=[fragment.id for fragment in action_result.succeeded],
            failed=[
                AppConfigFragmentBulkErrorInfo(index=error.index, message=error.message)
                for error in action_result.failed
            ],
        )

    # --- converters ---

    @staticmethod
    def _fragment_to_node(data: AppConfigFragmentData) -> AppConfigFragmentNode:
        return AppConfigFragmentNode(
            id=data.id,
            config_name=data.config_name,
            scope_type=AppConfigScopeTypeDTO(data.scope_type.value),
            # public has no owner — expose null rather than the stored empty sentinel.
            scope_id=None if data.scope_type is AppConfigScopeType.PUBLIC else data.scope_id,
            config=data.config,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
