import logging

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.app_config_policy.bulk_types import (
    AppConfigPolicyBulkItemError,
)
from ai.backend.manager.repositories.app_config_policy.admin_repository import (
    AppConfigPolicyAdminRepository,
)
from ai.backend.manager.repositories.app_config_policy.repository import (
    AppConfigPolicyRepository,
)
from ai.backend.manager.services.app_config_policy.actions.admin_bulk_create import (
    AdminBulkCreateAppConfigPoliciesAction,
    AdminBulkCreateAppConfigPoliciesActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.admin_bulk_purge import (
    AdminBulkPurgeAppConfigPoliciesAction,
    AdminBulkPurgeAppConfigPoliciesActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.admin_bulk_update import (
    AdminBulkUpdateAppConfigPoliciesAction,
    AdminBulkUpdateAppConfigPoliciesActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.get import (
    GetAppConfigPolicyAction,
    GetAppConfigPolicyActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.search import (
    SearchAppConfigPoliciesAction,
    SearchAppConfigPoliciesActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AppConfigPolicyService:
    _repository: AppConfigPolicyRepository
    _admin_repository: AppConfigPolicyAdminRepository

    def __init__(
        self,
        repository: AppConfigPolicyRepository,
        admin_repository: AppConfigPolicyAdminRepository,
    ) -> None:
        self._repository = repository
        self._admin_repository = admin_repository

    async def get(self, action: GetAppConfigPolicyAction) -> GetAppConfigPolicyActionResult:
        policy = await self._repository.get(action.config_name)
        return GetAppConfigPolicyActionResult(policy=policy)

    async def search(
        self, action: SearchAppConfigPoliciesAction
    ) -> SearchAppConfigPoliciesActionResult:
        result = await self._admin_repository.search(action.querier)
        return SearchAppConfigPoliciesActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    # ── Bulk mutations ──────────────────────────────────────────

    async def admin_bulk_create(
        self, action: AdminBulkCreateAppConfigPoliciesAction
    ) -> AdminBulkCreateAppConfigPoliciesActionResult:
        """Strict insert per-item; failures collected per-item."""
        created = []
        failed: list[AppConfigPolicyBulkItemError] = []
        for index, item in enumerate(action.items):
            try:
                policy = await self._admin_repository.create(item.config_name, item.scope_sources)
                created.append(policy)
            except Exception as e:
                log.warning("policy admin_bulk_create item {} failed: {}", index, e)
                failed.append(
                    AppConfigPolicyBulkItemError(
                        index=index,
                        config_name=item.config_name,
                        message=str(e),
                    )
                )
        return AdminBulkCreateAppConfigPoliciesActionResult(created=created, failed=failed)

    async def admin_bulk_update(
        self, action: AdminBulkUpdateAppConfigPoliciesAction
    ) -> AdminBulkUpdateAppConfigPoliciesActionResult:
        """Replace `scope_sources`; `config_name` itself is immutable.
        Items referencing a non-existent `config_name` are collected as
        failures (not auto-inserted)."""
        updated = []
        failed: list[AppConfigPolicyBulkItemError] = []
        for index, item in enumerate(action.items):
            try:
                policy = await self._admin_repository.update(item.config_name, item.scope_sources)
                updated.append(policy)
            except Exception as e:
                log.warning("policy admin_bulk_update item {} failed: {}", index, e)
                failed.append(
                    AppConfigPolicyBulkItemError(
                        index=index,
                        config_name=item.config_name,
                        message=str(e),
                    )
                )
        return AdminBulkUpdateAppConfigPoliciesActionResult(updated=updated, failed=failed)

    async def admin_bulk_purge(
        self, action: AdminBulkPurgeAppConfigPoliciesAction
    ) -> AdminBulkPurgeAppConfigPoliciesActionResult:
        """Hard-delete per-item; items whose `config_name` still has
        referencing fragments surface as per-item failures (the
        required-policy invariant)."""
        purged_names: list[str] = []
        failed: list[AppConfigPolicyBulkItemError] = []
        for index, config_name in enumerate(action.typed_entity_ids()):
            try:
                ok = await self._admin_repository.purge(config_name)
                if ok:
                    purged_names.append(config_name)
                # Absent names are no-oped intentionally.
            except Exception as e:
                log.warning("policy admin_bulk_purge item {} failed: {}", index, e)
                failed.append(
                    AppConfigPolicyBulkItemError(
                        index=index,
                        config_name=config_name,
                        message=str(e),
                    )
                )
        return AdminBulkPurgeAppConfigPoliciesActionResult(
            purged_config_names=purged_names,
            failed=failed,
        )
