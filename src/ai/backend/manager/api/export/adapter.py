"""
Adapters to convert export DTOs to repository query objects.
Handles conversion of report-specific filter and order parameters.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa

from ai.backend.common.dto.manager.export import (
    AuditLogExportFilter,
    AuditLogExportOrder,
    BooleanFilter,
    DateTimeRangeFilter,
    OrderDirection,
    ProjectExportFilter,
    ProjectExportOrder,
    SessionExportFilter,
    SessionExportOrder,
    UserExportFilter,
    UserExportOrder,
)
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.errors.export import InvalidExportFieldKeys
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.base.export import (
    ExportFieldDef,
    ExportFieldType,
    JoinDef,
    ReportDef,
    StreamingExportQuery,
)

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

        return StreamingExportQuery(
            select_from=report.select_from,
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

        return StreamingExportQuery(
            select_from=report.select_from,
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

        return self.convert_string_filter(
            string_filter,
            contains_factory=make_contains_factory(column),
            equals_factory=make_equals_factory(column),
            starts_with_factory=make_starts_with_factory(column),
            ends_with_factory=make_ends_with_factory(column),
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
        bool_filter: BooleanFilter,
        field_def: ExportFieldDef,
    ) -> QueryCondition:
        """Convert BooleanFilter to QueryCondition."""
        column = field_def.column
        value = bool_filter.equals
        return lambda: column == value
