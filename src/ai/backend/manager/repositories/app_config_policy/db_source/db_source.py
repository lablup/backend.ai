"""Database source for app config policy repository operations.

Each public method only executes the spec/wrapper handed in by the caller —
no raw sessions or SQLAlchemy statements are touched. All DB access goes
through the session-bound ops handed out by :class:`DBOpsProvider`.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.common.identifier.app_config_policy import AppConfigPolicyID
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.repositories.app_config_policy.creators import (
    AppConfigPolicyCreatorSpec,
)
from ai.backend.manager.repositories.app_config_policy.types import (
    AppConfigPolicySearchResult,
)
from ai.backend.manager.repositories.app_config_policy.updaters import (
    AppConfigPolicyUpdaterSpec,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    Purger,
    Querier,
    SearchScope,
    Updater,
)
from ai.backend.manager.repositories.ops import DBOpsProvider

__all__ = (
    "AppConfigPolicyCreatorSpec",
    "AppConfigPolicyDBSource",
    "AppConfigPolicyUpdaterSpec",
)


class AppConfigPolicyDBSource:
    """Database operations for `app_config_policies`.

    Mutations go through the shared Creator / Updater / Purger specs so the
    ``integrity_error_checks`` wired into the specs translate DB constraint
    violations into typed domain errors (see
    :mod:`ai.backend.manager.repositories.app_config_policy.creators`).
    """

    _ops: DBOpsProvider

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._ops = ops_provider

    async def get_by_id(self, id: AppConfigPolicyID) -> AppConfigPolicyData | None:
        """Look up a policy by row id."""
        async with self._ops.read_ops() as r:
            result = await r.query(Querier(row_class=AppConfigPolicyRow, pk_value=id))
            return result.row.to_data() if result is not None else None

    async def create(self, creator: Creator[AppConfigPolicyRow]) -> AppConfigPolicyData:
        """Insert a new policy via the shared Creator spec.

        Duplicate `config_name` surfaces as :class:`AppConfigPolicyConflict`
        via the spec's ``integrity_error_checks``.
        """
        async with self._ops.write_ops() as w:
            result = await w.create(creator)
            return result.row.to_data()

    async def update(self, updater: Updater[AppConfigPolicyRow]) -> AppConfigPolicyData | None:
        """Apply a pre-built Updater. Returns ``None`` when the row vanished
        between PK resolution and write; the caller maps this to
        :class:`AppConfigPolicyNotFound`."""
        async with self._ops.write_ops() as w:
            result = await w.update(updater)
            return result.row.to_data() if result is not None else None

    async def purge(self, purger: Purger[AppConfigPolicyRow]) -> bool:
        """Apply a pre-built Purger. The DB-side FK from
        `app_config_fragments.name` (NO ACTION) blocks the delete while
        fragments still reference this policy — the service layer is expected
        to reject earlier with a friendlier error. Returns ``True`` only when
        a row was actually removed."""
        async with self._ops.write_ops() as w:
            result = await w.purge(purger)
            return result is not None

    async def search(self, querier: BatchQuerier) -> AppConfigPolicySearchResult:
        """Paginated search across all policies, with no scope filter
        (superadmin / system-wide path)."""
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(AppConfigPolicyRow), querier)
            items = [row.AppConfigPolicyRow.to_data() for row in result.rows]
            return AppConfigPolicySearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def scoped_search(
        self,
        querier: BatchQuerier,
        scopes: Sequence[SearchScope],
    ) -> AppConfigPolicySearchResult:
        """Paginated search over policy rows matching any of ``scopes`` (OR),
        narrowed by ``querier``."""
        async with self._ops.read_ops() as r:
            result = await r.batch_query_with_scopes(sa.select(AppConfigPolicyRow), querier, scopes)
            items = [row.AppConfigPolicyRow.to_data() for row in result.rows]
            return AppConfigPolicySearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
