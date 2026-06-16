import logging

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.app_config_fragment.bulk_types import (
    AppConfigFragmentBulkItemError,
)
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentKey
from ai.backend.manager.repositories.app_config_fragment.admin_repository import (
    AppConfigFragmentAdminRepository,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_bulk_create import (
    AdminBulkCreateAppConfigFragmentsAction,
    AdminBulkCreateAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_bulk_purge import (
    AdminBulkPurgeAppConfigFragmentsAction,
    AdminBulkPurgeAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_bulk_update import (
    AdminBulkUpdateAppConfigFragmentsAction,
    AdminBulkUpdateAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentsAction,
    AdminSearchAppConfigFragmentsActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AppConfigFragmentAdminService:
    """Admin-only (superadmin) operations on AppConfigFragment."""

    _admin_repository: AppConfigFragmentAdminRepository

    def __init__(self, admin_repository: AppConfigFragmentAdminRepository) -> None:
        self._admin_repository = admin_repository

    async def admin_search(
        self, action: AdminSearchAppConfigFragmentsAction
    ) -> AdminSearchAppConfigFragmentsActionResult:
        result = await self._admin_repository.admin_search(action.querier)
        return AdminSearchAppConfigFragmentsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    # ── Bulk mutations (per-item transaction) ─────────────────────

    async def admin_bulk_create(
        self, action: AdminBulkCreateAppConfigFragmentsAction
    ) -> AdminBulkCreateAppConfigFragmentsActionResult:
        """Strict insert across any scope; each item in its own
        transaction so failures are collected per-item."""
        created = []
        failed: list[AppConfigFragmentBulkItemError] = []
        for index, item in enumerate(action.items):
            try:
                fragment = await self._admin_repository.create(item.key, item.config)
                created.append(fragment)
            except Exception as e:
                log.warning("admin_bulk_create item {} failed: {}", index, e)
                failed.append(
                    AppConfigFragmentBulkItemError(
                        index=index,
                        scope_type=item.key.scope_type.value,
                        scope_id=item.key.scope_id,
                        name=item.key.name,
                        message=str(e),
                    )
                )
        return AdminBulkCreateAppConfigFragmentsActionResult(created=created, failed=failed)

    async def admin_bulk_update(
        self, action: AdminBulkUpdateAppConfigFragmentsAction
    ) -> AdminBulkUpdateAppConfigFragmentsActionResult:
        """Wholesale JSON replacement; items without an existing row
        are collected as failures (not auto-inserted)."""
        updated = []
        failed: list[AppConfigFragmentBulkItemError] = []
        for index, item in enumerate(action.items):
            try:
                fragment = await self._admin_repository.update(item.key, item.config)
                updated.append(fragment)
            except Exception as e:
                log.warning("admin_bulk_update item {} failed: {}", index, e)
                failed.append(
                    AppConfigFragmentBulkItemError(
                        index=index,
                        scope_type=item.key.scope_type.value,
                        scope_id=item.key.scope_id,
                        name=item.key.name,
                        message=str(e),
                    )
                )
        return AdminBulkUpdateAppConfigFragmentsActionResult(updated=updated, failed=failed)

    async def admin_bulk_purge(
        self, action: AdminBulkPurgeAppConfigFragmentsAction
    ) -> AdminBulkPurgeAppConfigFragmentsActionResult:
        """Cleanup-only deletion; absent keys are no-oped."""
        purged: list[AppConfigFragmentKey] = []
        failed: list[AppConfigFragmentBulkItemError] = []
        for index, key in enumerate(action.keys):
            try:
                ok = await self._admin_repository.purge(key)
                if ok:
                    purged.append(key)
                # Absent keys are intentionally no-oped (no failure entry).
            except Exception as e:
                log.warning("admin_bulk_purge item {} failed: {}", index, e)
                failed.append(
                    AppConfigFragmentBulkItemError(
                        index=index,
                        scope_type=key.scope_type.value,
                        scope_id=key.scope_id,
                        name=key.name,
                        message=str(e),
                    )
                )
        return AdminBulkPurgeAppConfigFragmentsActionResult(purged=purged, failed=failed)
