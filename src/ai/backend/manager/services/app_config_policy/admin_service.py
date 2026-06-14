import logging

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyBulkItemError
from ai.backend.manager.repositories.app_config_policy.admin_repository import (
    AppConfigPolicyAdminRepository,
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
from ai.backend.manager.services.app_config_policy.actions.admin_search import (
    AdminSearchAppConfigPoliciesAction,
    AdminSearchAppConfigPoliciesActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AppConfigPolicyAdminService:
    """Admin-only (superadmin) operations on AppConfigPolicy."""

    _admin_repository: AppConfigPolicyAdminRepository

    def __init__(self, admin_repository: AppConfigPolicyAdminRepository) -> None:
        self._admin_repository = admin_repository

    async def admin_search(
        self, action: AdminSearchAppConfigPoliciesAction
    ) -> AdminSearchAppConfigPoliciesActionResult:
        result = await self._admin_repository.search(action.querier)
        return AdminSearchAppConfigPoliciesActionResult(
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
                failed.append(AppConfigPolicyBulkItemError(index=index, message=str(e)))
        return AdminBulkCreateAppConfigPoliciesActionResult(created=created, failed=failed)

    async def admin_bulk_update(
        self, action: AdminBulkUpdateAppConfigPoliciesAction
    ) -> AdminBulkUpdateAppConfigPoliciesActionResult:
        """Replace `scope_sources` by id; `config_name` itself is
        immutable. Items targeting non-existent ids are collected as
        failures."""
        updated = []
        failed: list[AppConfigPolicyBulkItemError] = []
        for index, item in enumerate(action.items):
            try:
                policy = await self._admin_repository.update(item.id, item.scope_sources)
                updated.append(policy)
            except Exception as e:
                log.warning("policy admin_bulk_update item {} failed: {}", index, e)
                failed.append(AppConfigPolicyBulkItemError(index=index, message=str(e)))
        return AdminBulkUpdateAppConfigPoliciesActionResult(updated=updated, failed=failed)

    async def admin_bulk_purge(
        self, action: AdminBulkPurgeAppConfigPoliciesAction
    ) -> AdminBulkPurgeAppConfigPoliciesActionResult:
        """Hard-delete per-item; items whose policy still has
        referencing fragments surface as per-item failures (the
        required-policy invariant)."""
        purged_ids = []
        failed: list[AppConfigPolicyBulkItemError] = []
        for index, policy_id in enumerate(action.ids):
            try:
                ok = await self._admin_repository.purge(policy_id)
                if ok:
                    purged_ids.append(policy_id)
                # Absent ids are no-oped intentionally.
            except Exception as e:
                log.warning("policy admin_bulk_purge item {} failed: {}", index, e)
                failed.append(AppConfigPolicyBulkItemError(index=index, message=str(e)))
        return AdminBulkPurgeAppConfigPoliciesActionResult(
            purged_ids=purged_ids,
            failed=failed,
        )
