"""
Adapters to convert export DTOs to repository query objects.
Handles conversion of report-specific filter and order parameters.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import (
    StringInMatchSpec,
    StringMatchSpec,
    UUIDEqualMatchSpec,
    UUIDInMatchSpec,
)
from ai.backend.common.dto.manager.query import DateTimeRangeFilter, StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.export import (
    AuditLogExportFilter,
    AuditLogExportOrder,
    OrderDirection,
    ProjectExportFilter,
    ProjectExportOrder,
    SessionExportFilter,
    SessionExportOrder,
    SessionExportUserNestedFilter,
    UserExportFilter,
    UserExportOrder,
)
from ai.backend.manager.errors.export import InvalidExportFieldKeys
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.repositories.base.export import (
    ExportFieldDef,
    ExportFieldType,
    JoinDef,
    ReportDef,
    StreamingExportQuery,
)
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter

if TYPE_CHECKING:
    from sqlalchemy.orm.attributes import InstrumentedAttribute

__all__ = ("ExportAdapter",)


class ExportAdapter(BaseFilterAdapter):
    """Adapter for converting export request DTOs to query objects.

    Provides report-specific methods to build queries from filter and order DTOs.
    """

    def build_user_query(
        self,
        report: ReportDef,
        fields: list[str] | None,
        filter: UserExportFilter | None,
        order: list[UserExportOrder] | None,
        max_rows: int,
        statement_timeout_sec: int,
    ) -> StreamingExportQuery:
        """Build StreamingExportQuery for user export.

        Dynamically applies JOINs based on selected fields.
        Fields with joins attribute will trigger LEFT JOIN operations.

        Args:
            report: User report definition
            fields: Field keys to include (None = all fields)
            filter: User-specific filter conditions
            order: User-specific order specifications
            max_rows: Maximum rows to export
            statement_timeout_sec: Query timeout in seconds

        Returns:
            StreamingExportQuery ready for execution
        """
        selected_fields = self._select_fields(report, fields)
        conditions = self._build_user_conditions(report, filter)
        orders = self._build_user_orders(report, order)

        # Collect all required JOINs from selected fields
        all_joins = self._collect_joins(selected_fields)

        # Build select_from with dynamic JOINs
        select_from = self._build_select_from_with_joins(report.select_from, all_joins)

        return StreamingExportQuery(
            select_from=select_from,
            fields=selected_fields,
            conditions=conditions,
            orders=orders,
            max_rows=max_rows,
            statement_timeout_sec=statement_timeout_sec,
        )

    def build_session_query(
        self,
        report: ReportDef,
        fields: list[str] | None,
        filter: SessionExportFilter | None,
        order: list[SessionExportOrder] | None,
        max_rows: int,
        statement_timeout_sec: int,
    ) -> StreamingExportQuery:
        """Build StreamingExportQuery for session export.

        Dynamically applies JOINs based on selected fields.
        Fields with joins attribute will trigger LEFT JOIN operations.

        Args:
            report: Session report definition
            fields: Field keys to include (None = all fields)
            filter: Session-specific filter conditions
            order: Session-specific order specifications
            max_rows: Maximum rows to export
            statement_timeout_sec: Query timeout in seconds

        Returns:
            StreamingExportQuery ready for execution
        """
        selected_fields = self._select_fields(report, fields)
        conditions = self._build_session_conditions(report, filter)
        orders = self._build_session_orders(report, order)

        # Collect all required JOINs from selected output fields
        all_joins = self._collect_joins(selected_fields)

        # Build select_from with dynamic JOINs
        select_from = self._build_select_from_with_joins(report.select_from, all_joins)

        return StreamingExportQuery(
            select_from=select_from,
            fields=selected_fields,
            conditions=conditions,
            orders=orders,
            max_rows=max_rows,
            statement_timeout_sec=statement_timeout_sec,
        )

    def build_project_query(
        self,
        report: ReportDef,
        fields: list[str] | None,
        filter: ProjectExportFilter | None,
        order: list[ProjectExportOrder] | None,
        max_rows: int,
        statement_timeout_sec: int,
    ) -> StreamingExportQuery:
        """Build StreamingExportQuery for project export.

        Dynamically applies JOINs based on selected fields.
        Fields with joins attribute will trigger LEFT JOIN operations.

        Args:
            report: Project report definition
            fields: Field keys to include (None = all fields)
            filter: Project-specific filter conditions
            order: Project-specific order specifications
            max_rows: Maximum rows to export
            statement_timeout_sec: Query timeout in seconds

        Returns:
            StreamingExportQuery ready for execution
        """
        selected_fields = self._select_fields(report, fields)
        conditions = self._build_project_conditions(report, filter)
        orders = self._build_project_orders(report, order)

        # Collect all required JOINs from selected fields
        all_joins = self._collect_joins(selected_fields)

        # Build select_from with dynamic JOINs
        select_from = self._build_select_from_with_joins(report.select_from, all_joins)

        return StreamingExportQuery(
            select_from=select_from,
            fields=selected_fields,
            conditions=conditions,
            orders=orders,
            max_rows=max_rows,
            statement_timeout_sec=statement_timeout_sec,
        )

    def build_keypair_query(
        self,
        report: ReportDef,
        fields: list[str] | None,
        filter: None,  # No filter support for keypair export yet
        order: None,  # No order support for keypair export yet
        max_rows: int,
        statement_timeout_sec: int,
    ) -> StreamingExportQuery:
        """Build StreamingExportQuery for keypair export.

        Dynamically applies JOINs based on selected fields.
        Fields with joins attribute will trigger LEFT JOIN operations.

        Args:
            report: Keypair report definition
            fields: Field keys to include (None = all fields)
            filter: Not yet supported for keypair export
            order: Not yet supported for keypair export
            max_rows: Maximum rows to export
            statement_timeout_sec: Query timeout in seconds

        Returns:
            StreamingExportQuery ready for execution
        """
        selected_fields = self._select_fields(report, fields)

        # Collect all required JOINs from selected fields
        all_joins = self._collect_joins(selected_fields)

        # Build select_from with dynamic JOINs
        select_from = self._build_select_from_with_joins(report.select_from, all_joins)

        return StreamingExportQuery(
            select_from=select_from,
            fields=selected_fields,
            conditions=[],  # No filter support yet
            orders=[],  # No order support yet
            max_rows=max_rows,
            statement_timeout_sec=statement_timeout_sec,
        )

    def _collect_joins(
        self,
        fields: list[ExportFieldDef],
    ) -> list[JoinDef]:
        """Collect all required JOINs from selected fields.

        Deduplicates JOINs and returns them in a consistent order
        for deterministic query generation.

        Args:
            fields: Selected field definitions

        Returns:
            List of unique JoinDef in deterministic order
        """
        seen: set[JoinDef] = set()
        result: list[JoinDef] = []

        for field in fields:
            if field.joins:
                for join_def in field.joins:
                    if join_def not in seen:
                        seen.add(join_def)
                        result.append(join_def)

        return result

    def _build_select_from_with_joins(
        self,
        base_table: sa.FromClause,
        joins: list[JoinDef],
    ) -> sa.FromClause:
        """Build select_from clause with dynamic LEFT JOINs.

        Args:
            base_table: Base table (e.g., GroupRow.__table__)
            joins: List of JoinDef to apply

        Returns:
            SQLAlchemy FromClause with all JOINs applied
        """
        result: sa.FromClause = base_table
        for join_def in joins:
            result = result.outerjoin(join_def.table, join_def.condition)
        return result

    def _select_fields(
        self,
        report: ReportDef,
        field_keys: list[str] | None,
    ) -> list[ExportFieldDef]:
        """Select fields from report based on requested field keys.

        Preserves the order specified in field_keys.

        Raises:
            InvalidExportFieldKeys: If a field key is not found in the report.
        """
        if field_keys:
            field_map = {f.key: f for f in report.fields}
            selected: list[ExportFieldDef] = []
            for key in field_keys:
                if key not in field_map:
                    raise InvalidExportFieldKeys([key])
                selected.append(field_map[key])
            return selected
        return list(report.fields)

    # =========================================================================
    # User-specific conditions and orders
    # =========================================================================

    def _build_user_conditions(
        self,
        report: ReportDef,
        filter: UserExportFilter | None,
    ) -> list[QueryCondition]:
        """Convert UserExportFilter to list of QueryCondition."""
        if filter is None:
            return []

        conditions: list[QueryCondition] = []

        # username filter
        if filter.username is not None:
            field = report.get_field("username")
            if field:
                cond = self._build_string_condition(filter.username, field)
                if cond:
                    conditions.append(cond)

        # email filter
        if filter.email is not None:
            field = report.get_field("email")
            if field:
                cond = self._build_string_condition(filter.email, field)
                if cond:
                    conditions.append(cond)

        # domain_name filter
        if filter.domain_name is not None:
            field = report.get_field("domain_name")
            if field:
                cond = self._build_string_condition(filter.domain_name, field)
                if cond:
                    conditions.append(cond)

        # role filter (IN query)
        if filter.role is not None:
            field = report.get_field("role")
            if field:
                cond = self._build_in_condition(filter.role, field)
                conditions.append(cond)

        # status filter (IN query)
        if filter.status is not None:
            field = report.get_field("status")
            if field:
                cond = self._build_in_condition(filter.status, field)
                conditions.append(cond)

        # created_at filter
        if filter.created_at is not None:
            field = report.get_field("created_at")
            if field:
                conditions.extend(self._build_datetime_conditions(filter.created_at, field))

        return conditions

    def _build_user_orders(
        self,
        report: ReportDef,
        orders: list[UserExportOrder] | None,
    ) -> list[QueryOrder]:
        """Convert UserExportOrder list to QueryOrder list."""
        if not orders:
            return []

        result: list[QueryOrder] = []
        for order in orders:
            field_def = report.get_field(order.field.value)
            if field_def is None:
                continue
            if order.direction == OrderDirection.ASC:
                result.append(field_def.column.asc())
            else:
                result.append(field_def.column.desc())

        return result

    # =========================================================================
    # Session-specific conditions and orders
    # =========================================================================

    def _build_session_conditions(
        self,
        report: ReportDef,
        filter: SessionExportFilter | None,
    ) -> list[QueryCondition]:
        """Convert SessionExportFilter to list of QueryCondition."""
        if filter is None:
            return []

        conditions: list[QueryCondition] = []

        # name filter
        if filter.name is not None:
            field = report.get_field("name")
            if field:
                cond = self._build_string_condition(filter.name, field)
                if cond:
                    conditions.append(cond)

        # session_type filter (IN query)
        if filter.session_type is not None:
            field = report.get_field("session_type")
            if field:
                cond = self._build_in_condition(filter.session_type, field)
                conditions.append(cond)

        # domain_name filter
        if filter.domain_name is not None:
            field = report.get_field("domain_name")
            if field:
                cond = self._build_string_condition(filter.domain_name, field)
                if cond:
                    conditions.append(cond)

        # access_key filter
        if filter.access_key is not None:
            field = report.get_field("access_key")
            if field:
                cond = self._build_string_condition(filter.access_key, field)
                if cond:
                    conditions.append(cond)

        # user filter (nested): filter by the owning user's columns without joining users
        # into the main FROM clause.
        if filter.user is not None:
            user_cond = self._build_session_user_filter_condition(report, filter.user)
            if user_cond is not None:
                conditions.append(user_cond)

        # status filter (IN query)
        if filter.status is not None:
            field = report.get_field("status")
            if field:
                cond = self._build_in_condition(filter.status, field)
                conditions.append(cond)

        # scaling_group_name filter
        if filter.scaling_group_name is not None:
            field = report.get_field("scaling_group_name")
            if field:
                cond = self._build_string_condition(filter.scaling_group_name, field)
                if cond:
                    conditions.append(cond)

        # created_at filter
        if filter.created_at is not None:
            field = report.get_field("created_at")
            if field:
                conditions.extend(self._build_datetime_conditions(filter.created_at, field))

        # terminated_at filter
        if filter.terminated_at is not None:
            field = report.get_field("terminated_at")
            if field:
                conditions.extend(self._build_datetime_conditions(filter.terminated_at, field))

        return conditions

    def _build_session_user_filter_condition(
        self,
        report: ReportDef,
        user_filter: SessionExportUserNestedFilter,
    ) -> QueryCondition | None:
        """Build the nested user filter as a correlated EXISTS over the users table.

        Filters sessions by the owning user's columns (email/username) without joining
        users into the main FROM clause — which would risk a cartesian product when the
        user is filtered but not selected. The users table and the correlation condition
        come from the user field's declared joins (ReportDef metadata), so this needs no
        ORM model imports.

        Returns None when the filter contributes no condition.
        """
        user_conditions: list[QueryCondition] = []
        user_joins: set[JoinDef] = set()
        if user_filter.email is not None:
            field = report.get_field("user_email")
            if field:
                user_joins.update(field.joins or ())
                cond = self._build_string_condition(user_filter.email, field)
                if cond:
                    user_conditions.append(cond)
        if user_filter.username is not None:
            field = report.get_field("user_username")
            if field:
                user_joins.update(field.joins or ())
                cond = self._build_string_condition(user_filter.username, field)
                if cond:
                    user_conditions.append(cond)

        if not user_conditions or not user_joins:
            return None

        joins = list(user_joins)

        def owning_user_exists() -> sa.sql.expression.ColumnElement[bool]:
            where_clauses = [join.condition for join in joins]
            where_clauses.extend(cond() for cond in user_conditions)
            # correlate_except keeps the joined table(s) in the subquery's own FROM so that
            # auto-correlation only pulls in the base table. Without it, selecting a user
            # column (which LEFT JOINs users into the outer query) makes the subquery's users
            # auto-correlate out, leaving it with no FROM clause.
            subquery = (
                sa.select(sa.literal(1))
                .select_from(*(join.table for join in joins))
                .where(sa.and_(*where_clauses))
                .correlate_except(*(join.table for join in joins))
            )
            return subquery.exists()

        return owning_user_exists

    def _build_session_orders(
        self,
        report: ReportDef,
        orders: list[SessionExportOrder] | None,
    ) -> list[QueryOrder]:
        """Convert SessionExportOrder list to QueryOrder list."""
        if not orders:
            return []

        result: list[QueryOrder] = []
        for order in orders:
            field_def = report.get_field(order.field.value)
            if field_def is None:
                continue
            if order.direction == OrderDirection.ASC:
                result.append(field_def.column.asc())
            else:
                result.append(field_def.column.desc())

        return result

    # =========================================================================
    # Project-specific conditions and orders
    # =========================================================================

    def _build_project_conditions(
        self,
        report: ReportDef,
        filter: ProjectExportFilter | None,
    ) -> list[QueryCondition]:
        """Convert ProjectExportFilter to list of QueryCondition."""
        if filter is None:
            return []

        conditions: list[QueryCondition] = []

        # name filter
        if filter.name is not None:
            field = report.get_field("name")
            if field:
                cond = self._build_string_condition(filter.name, field)
                if cond:
                    conditions.append(cond)

        # domain_name filter
        if filter.domain_name is not None:
            field = report.get_field("domain_name")
            if field:
                cond = self._build_string_condition(filter.domain_name, field)
                if cond:
                    conditions.append(cond)

        # is_active filter (boolean)
        if filter.is_active is not None:
            field = report.get_field("is_active")
            if field:
                conditions.append(self._build_boolean_condition(filter.is_active, field))

        # created_at filter
        if filter.created_at is not None:
            field = report.get_field("created_at")
            if field:
                conditions.extend(self._build_datetime_conditions(filter.created_at, field))

        return conditions

    def _build_project_orders(
        self,
        report: ReportDef,
        orders: list[ProjectExportOrder] | None,
    ) -> list[QueryOrder]:
        """Convert ProjectExportOrder list to QueryOrder list."""
        if not orders:
            return []

        result: list[QueryOrder] = []
        for order in orders:
            field_def = report.get_field(order.field.value)
            if field_def is None:
                continue
            if order.direction == OrderDirection.ASC:
                result.append(field_def.column.asc())
            else:
                result.append(field_def.column.desc())

        return result

    # =========================================================================
    # Audit Log-specific query builder, conditions and orders
    # =========================================================================

    def build_audit_log_query(
        self,
        report: ReportDef,
        fields: list[str] | None,
        filter: AuditLogExportFilter | None,
        order: list[AuditLogExportOrder] | None,
        max_rows: int,
        statement_timeout_sec: int,
    ) -> StreamingExportQuery:
        """Build StreamingExportQuery for audit log export.

        Args:
            report: Audit log report definition
            fields: Field keys to include (None = all fields)
            filter: Audit log-specific filter conditions
            order: Audit log-specific order specifications
            max_rows: Maximum rows to export
            statement_timeout_sec: Query timeout in seconds

        Returns:
            StreamingExportQuery ready for execution
        """
        selected_fields = self._select_fields(report, fields)
        conditions = self._build_audit_log_conditions(report, filter)
        orders = self._build_audit_log_orders(report, order)

        return StreamingExportQuery(
            select_from=report.select_from,
            fields=selected_fields,
            conditions=conditions,
            orders=orders,
            max_rows=max_rows,
            statement_timeout_sec=statement_timeout_sec,
        )

    def _build_audit_log_conditions(
        self,
        report: ReportDef,
        filter: AuditLogExportFilter | None,
    ) -> list[QueryCondition]:
        """Convert AuditLogExportFilter to list of QueryCondition."""
        if filter is None:
            return []

        conditions: list[QueryCondition] = []

        # entity_type filter
        if filter.entity_type is not None:
            field = report.get_field("entity_type")
            if field:
                cond = self._build_string_condition(filter.entity_type, field)
                if cond:
                    conditions.append(cond)

        # entity_id filter
        if filter.entity_id is not None:
            field = report.get_field("entity_id")
            if field:
                cond = self._build_string_condition(filter.entity_id, field)
                if cond:
                    conditions.append(cond)

        # operation filter
        if filter.operation is not None:
            field = report.get_field("operation")
            if field:
                cond = self._build_string_condition(filter.operation, field)
                if cond:
                    conditions.append(cond)

        # status filter (IN query)
        if filter.status is not None:
            field = report.get_field("status")
            if field:
                cond = self._build_in_condition(filter.status, field)
                conditions.append(cond)

        # triggered_by filter
        if filter.triggered_by is not None:
            field = report.get_field("triggered_by")
            if field:
                cond = self._build_string_condition(filter.triggered_by, field)
                if cond:
                    conditions.append(cond)

        # acted_as filter (UUID)
        if filter.acted_as is not None:
            field = report.get_field("acted_as")
            if field:
                cond = self._build_uuid_condition(filter.acted_as, field)
                if cond:
                    conditions.append(cond)

        # request_id filter
        if filter.request_id is not None:
            field = report.get_field("request_id")
            if field:
                cond = self._build_string_condition(filter.request_id, field)
                if cond:
                    conditions.append(cond)

        # created_at filter
        if filter.created_at is not None:
            field = report.get_field("created_at")
            if field:
                conditions.extend(self._build_datetime_conditions(filter.created_at, field))

        return conditions

    def _build_audit_log_orders(
        self,
        report: ReportDef,
        orders: list[AuditLogExportOrder] | None,
    ) -> list[QueryOrder]:
        """Convert AuditLogExportOrder list to QueryOrder list."""
        if not orders:
            return []

        result: list[QueryOrder] = []
        for order in orders:
            field_def = report.get_field(order.field.value)
            if field_def is None:
                continue
            if order.direction == OrderDirection.ASC:
                result.append(field_def.column.asc())
            else:
                result.append(field_def.column.desc())

        return result

    # =========================================================================
    # Common filter builders
    # =========================================================================

    def _build_in_condition(
        self,
        values: list[str],
        field_def: ExportFieldDef,
    ) -> QueryCondition:
        """Build IN condition for a field.

        If the field type is ENUM, converts string values to enum values.
        """
        column = field_def.column

        if field_def.field_type == ExportFieldType.ENUM:
            enum_cls = column.type._enum_cls
            enum_values = [enum_cls(v) for v in values]
            return lambda: column.in_(enum_values)

        return lambda: column.in_(values)

    def _build_string_condition(
        self,
        string_filter: StringFilter,
        field_def: ExportFieldDef,
    ) -> QueryCondition | None:
        """Convert StringFilter to QueryCondition for the given field."""
        column = field_def.column

        def make_contains_factory(
            col: InstrumentedAttribute[Any],
        ) -> Callable[[StringMatchSpec], QueryCondition]:
            def factory(spec: StringMatchSpec) -> QueryCondition:
                pattern = f"%{spec.value}%"
                if spec.case_insensitive:
                    if spec.negated:
                        return lambda: ~col.ilike(pattern)
                    return lambda: col.ilike(pattern)
                if spec.negated:
                    return lambda: ~col.like(pattern)
                return lambda: col.like(pattern)

            return factory

        def make_equals_factory(
            col: InstrumentedAttribute[Any],
        ) -> Callable[[StringMatchSpec], QueryCondition]:
            def factory(spec: StringMatchSpec) -> QueryCondition:
                if spec.case_insensitive:
                    if spec.negated:
                        return lambda: ~col.ilike(spec.value)
                    return lambda: col.ilike(spec.value)
                if spec.negated:
                    return lambda: col != spec.value
                return lambda: col == spec.value

            return factory

        def make_starts_with_factory(
            col: InstrumentedAttribute[Any],
        ) -> Callable[[StringMatchSpec], QueryCondition]:
            def factory(spec: StringMatchSpec) -> QueryCondition:
                pattern = f"{spec.value}%"
                if spec.case_insensitive:
                    if spec.negated:
                        return lambda: ~col.ilike(pattern)
                    return lambda: col.ilike(pattern)
                if spec.negated:
                    return lambda: ~col.like(pattern)
                return lambda: col.like(pattern)

            return factory

        def make_ends_with_factory(
            col: InstrumentedAttribute[Any],
        ) -> Callable[[StringMatchSpec], QueryCondition]:
            def factory(spec: StringMatchSpec) -> QueryCondition:
                pattern = f"%{spec.value}"
                if spec.case_insensitive:
                    if spec.negated:
                        return lambda: ~col.ilike(pattern)
                    return lambda: col.ilike(pattern)
                if spec.negated:
                    return lambda: ~col.like(pattern)
                return lambda: col.like(pattern)

            return factory

        def make_in_factory(
            col: InstrumentedAttribute[Any],
        ) -> Callable[[StringInMatchSpec], QueryCondition]:
            def factory(spec: StringInMatchSpec) -> QueryCondition:
                if spec.case_insensitive:
                    lowered = [v.lower() for v in spec.values]
                    if spec.negated:
                        return lambda: ~sa.func.lower(col).in_(lowered)
                    return lambda: sa.func.lower(col).in_(lowered)
                if spec.negated:
                    return lambda: ~col.in_(spec.values)
                return lambda: col.in_(spec.values)

            return factory

        return self.convert_string_filter(
            string_filter,
            contains_factory=make_contains_factory(column),
            equals_factory=make_equals_factory(column),
            starts_with_factory=make_starts_with_factory(column),
            ends_with_factory=make_ends_with_factory(column),
            in_factory=make_in_factory(column),
        )

    def _build_uuid_condition(
        self,
        uuid_filter: UUIDFilter,
        field_def: ExportFieldDef,
    ) -> QueryCondition | None:
        """Convert UUIDFilter to QueryCondition for the given field."""
        column = field_def.column

        def make_equals_factory(
            col: InstrumentedAttribute[Any],
        ) -> Callable[[UUIDEqualMatchSpec], QueryCondition]:
            def factory(spec: UUIDEqualMatchSpec) -> QueryCondition:
                value = spec.value
                if spec.negated:
                    return lambda: col != value
                return lambda: col == value

            return factory

        def make_in_factory(
            col: InstrumentedAttribute[Any],
        ) -> Callable[[UUIDInMatchSpec], QueryCondition]:
            def factory(spec: UUIDInMatchSpec) -> QueryCondition:
                values = spec.values
                if spec.negated:
                    return lambda: ~col.in_(values)
                return lambda: col.in_(values)

            return factory

        return self.convert_uuid_filter(
            uuid_filter,
            make_equals_factory(column),
            make_in_factory(column),
        )

    def _build_datetime_conditions(
        self,
        dt_filter: DateTimeRangeFilter,
        field_def: ExportFieldDef,
    ) -> list[QueryCondition]:
        """Convert DateTimeRangeFilter to list of QueryConditions."""
        conditions: list[QueryCondition] = []
        column = field_def.column

        if dt_filter.after is not None:
            after_dt = dt_filter.after
            conditions.append(lambda: column >= after_dt)

        if dt_filter.before is not None:
            before_dt = dt_filter.before
            conditions.append(lambda: column <= before_dt)

        return conditions

    def _build_boolean_condition(
        self,
        value: bool,
        field_def: ExportFieldDef,
    ) -> QueryCondition:
        """Convert a bool value to QueryCondition."""
        column = field_def.column
        return lambda: column == value
