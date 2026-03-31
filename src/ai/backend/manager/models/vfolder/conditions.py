"""Query conditions for vfolder rows."""

from __future__ import annotations

from collections.abc import Collection
from datetime import datetime
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

if TYPE_CHECKING:
    from ai.backend.common.data.filter_specs import StringMatchSpec

from ai.backend.common.data.user.types import UserData
from ai.backend.common.types import VFolderHostPermission, VFolderUsageMode
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus
from ai.backend.manager.repositories.base import QueryCondition

from .row import VFolderRow


class VFolderConditions:
    """Query conditions for vfolders."""

    # ── name string filter factories ──

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = VFolderRow.name.ilike(f"%{spec.value}%")
            else:
                condition = VFolderRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(VFolderRow.name) == spec.value.lower()
            else:
                condition = VFolderRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = VFolderRow.name.ilike(f"{spec.value}%")
            else:
                condition = VFolderRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = VFolderRow.name.ilike(f"%{spec.value}")
            else:
                condition = VFolderRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # ── host string filter factories ──

    @staticmethod
    def by_host_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = VFolderRow.host.ilike(f"%{spec.value}%")
            else:
                condition = VFolderRow.host.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_host_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(VFolderRow.host) == spec.value.lower()
            else:
                condition = VFolderRow.host == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_host_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = VFolderRow.host.ilike(f"{spec.value}%")
            else:
                condition = VFolderRow.host.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_host_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = VFolderRow.host.ilike(f"%{spec.value}")
            else:
                condition = VFolderRow.host.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # ── boolean filter factories ──

    @staticmethod
    def by_cloneable(value: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.cloneable == value

        return inner

    # ── enum filter factories ──

    @staticmethod
    def by_status_in(statuses: Collection[VFolderOperationStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_status_not_in(statuses: Collection[VFolderOperationStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.status.notin_(statuses)

        return inner

    @staticmethod
    def by_usage_mode_in(modes: Collection[VFolderUsageMode]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.usage_mode.in_(modes)

        return inner

    @staticmethod
    def by_usage_mode_not_in(modes: Collection[VFolderUsageMode]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.usage_mode.notin_(modes)

        return inner

    # ── datetime filter factories ──

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.created_at == dt

        return inner

    # ── host permission filter factory ──

    @staticmethod
    def by_host_permission(
        requester: UserData,
        *,
        permissions: Collection[VFolderHostPermission],
        negate: bool = False,
    ) -> QueryCondition:
        """Filter vfolders by storage host accessibility.

        Builds a SQL subquery that extracts host names from
        ``allowed_vfolder_hosts`` JSONB columns in domains, groups, and
        keypair_resource_policies, filtering to hosts that contain **all**
        requested *permissions*.

        Args:
            requester: The user whose host permissions are evaluated.
            permissions: Host permissions to check.  A host must have
                **all** listed permissions to match.
            negate: When ``True``, returns vfolders on hosts that
                **lack** the requested permissions (``NOT IN``).
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            from ai.backend.manager.models.domain.row import DomainRow
            from ai.backend.manager.models.group.row import AssocGroupUserRow, GroupRow
            from ai.backend.manager.models.keypair.row import KeyPairRow
            from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow

            perm_values = [p.value for p in permissions]

            def _build_source_query(
                table_col: Any,
                from_clause: sa.FromClause,
                where_clause: sa.ColumnElement[bool],
            ) -> sa.Select[tuple[str, str]]:
                """Extract (host_key, permission) pairs from a JSONB column."""
                j = sa.func.jsonb_each(table_col).table_valued("key", "value")
                # jsonb_array_elements_text returns a single-column set-returning
                # function.  Use render_derived=True so PostgreSQL names the column.
                elem = sa.func.jsonb_array_elements_text(
                    sa.type_coerce(j.c.value, JSONB)
                ).table_valued(sa.column("value", sa.Text), with_ordinality=False)
                return (
                    sa.select(j.c.key, elem.c.value)
                    .select_from(from_clause.join(j, sa.true()).join(elem, sa.true()))
                    .where(where_clause)
                )

            # 1. Domain hosts
            domain_pairs = _build_source_query(
                DomainRow.allowed_vfolder_hosts,
                DomainRow.__table__,
                (DomainRow.name == requester.domain_name) & (DomainRow.is_active.is_(True)),
            )

            # 2. User's group hosts
            group_from = GroupRow.__table__.join(
                AssocGroupUserRow.__table__,
                GroupRow.id == AssocGroupUserRow.group_id,
            )
            group_pairs = _build_source_query(
                GroupRow.allowed_vfolder_hosts,
                group_from,
                (AssocGroupUserRow.user_id == requester.user_id)
                & (GroupRow.domain_name == requester.domain_name)
                & (GroupRow.is_active.is_(True)),
            )

            # 3. Keypair resource policy hosts
            krp_from = KeyPairResourcePolicyRow.__table__.join(
                KeyPairRow.__table__,
                KeyPairRow.resource_policy == KeyPairResourcePolicyRow.name,
            )
            keypair_pairs = _build_source_query(
                KeyPairResourcePolicyRow.allowed_vfolder_hosts,
                krp_from,
                (KeyPairRow.user == requester.user_id) & (KeyPairRow.is_active.is_(True)),
            )

            # UNION ALL (host, perm) from all sources, then GROUP BY host
            # and check the merged permission set contains all requested perms.
            # This matches the Python-side union semantics of
            # get_allowed_vfolder_hosts_by_user() where permissions from
            # different sources are merged per host.
            all_pairs = sa.union_all(domain_pairs, group_pairs, keypair_pairs).subquery()
            # Use literal_column to embed the array directly in SQL, avoiding
            # asyncpg parameter binding issues with array/JSONB type coercion.
            perm_array_literal: sa.ColumnElement[list[str]] = sa.literal_column(
                "ARRAY[" + ",".join(f"'{v}'" for v in perm_values) + "]::text[]"
            )
            hosts_with_perms = (
                sa.select(all_pairs.c[0].label("host_key"))
                .group_by(all_pairs.c[0])
                .having(
                    sa.type_coerce(
                        sa.func.array_agg(sa.distinct(all_pairs.c[1])),
                        ARRAY(sa.Text),
                    ).contains(perm_array_literal)
                )
            )

            host_in_allowed = VFolderRow.host.in_(hosts_with_perms)

            if negate:
                return ~host_in_allowed
            return host_in_allowed

        return inner

    # ── cursor pagination factories ──

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(VFolderRow.created_at).where(VFolderRow.id == cursor_id).scalar_subquery()
            )
            return VFolderRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(VFolderRow.created_at).where(VFolderRow.id == cursor_id).scalar_subquery()
            )
            return VFolderRow.created_at > subquery

        return inner
