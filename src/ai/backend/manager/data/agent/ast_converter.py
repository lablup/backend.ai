from __future__ import annotations

from typing import override

from ..base import BaseCombineOperator, BaseFilterConverter, FilterGroup, LeafFilterCondition
from .types import (
    AgentFilter,
    AgentFilterCondition,
    AgentFilterField,
    AgentStatus,
    AgentStatusFilter,
)


class AgentFilterConverter(
    BaseFilterConverter[
        AgentFilterField,
        AgentFilter,
    ]
):
    """
    Converter class for transforming Lark AST to AgentFilter structures.

    This class handles the conversion from minilang AST (from QueryFilterParser)
    to structured filter objects that can be used by the Service and Repository layers.

    Uses BaseFilterOperator and BaseCombineOperator from the base module,
    reducing generic complexity.
    """

    @override
    def _parse_field(self, field_name: str) -> AgentFilterField:
        """
        Parse field name string to AgentFilterField enum.

        Args:
            field_name: Raw field name from filter expression (case-insensitive)

        Returns:
            AgentFilterField enum value

        Raises:
            ValueError: If field name is unknown
        """
        # Convert to lowercase to match DB column names
        try:
            return AgentFilterField(field_name.lower())
        except ValueError:
            raise ValueError(f"Unknown filter field: {field_name}")

    @override
    def _convert_filter_group(
        self,
        filter_group: FilterGroup[AgentFilterField],
    ) -> AgentFilter:
        """
        Convert generic FilterGroup to Strawberry-compatible AgentFilter.

        This is an internal method called by convert() to transform
        the intermediate FilterGroup structure into the final AgentFilter format.

        Args:
            filter_group: The parsed filter group

        Returns:
            AgentFilter object compatible with Strawberry pattern
        """
        agent_filter = AgentFilter()

        # Single condition
        if len(filter_group.conditions) == 1:
            condition = filter_group.conditions[0]
            if isinstance(condition, LeafFilterCondition):
                return self._apply_condition_to_filter(agent_filter, condition)
            # Nested group with single condition - recursively convert
            return self._convert_filter_group(condition)

        # Multiple conditions or nested - use logical operators
        converted_children: list[AgentFilter] = []
        for condition in filter_group.conditions:
            if isinstance(condition, LeafFilterCondition):
                # Leaf condition - wrap in AgentFilter
                child_filter = AgentFilter()
                converted_children.append(self._apply_condition_to_filter(child_filter, condition))
            else:
                # Nested group - recursively convert
                converted_children.append(self._convert_filter_group(condition))

        # Assign to appropriate logical operation
        match filter_group.operator:
            case BaseCombineOperator.AND:
                agent_filter.AND = converted_children
            case BaseCombineOperator.OR:
                agent_filter.OR = converted_children

        return agent_filter

    @staticmethod
    def _create_string_filter_from_operator(operator, value: str):
        """
        Create a StringFilter based on the operator and value.
        Handles LIKE/ILIKE patterns by detecting % wildcards and converting to appropriate filter type.
        """
        from ai.backend.manager.api.gql.base import StringFilter

        from ..base import BaseFilterOperator

        str_value = str(value)

        match operator:
            case BaseFilterOperator.EQ:
                return StringFilter(equals=str_value)
            case BaseFilterOperator.NE:
                return StringFilter(not_equals=str_value)
            case BaseFilterOperator.CONTAINS:
                return StringFilter(contains=str_value)
            case BaseFilterOperator.LIKE:
                # Parse LIKE pattern: %value% -> contains, value% -> starts_with, %value -> ends_with
                if str_value.startswith("%") and str_value.endswith("%"):
                    return StringFilter(contains=str_value[1:-1])
                elif str_value.endswith("%"):
                    return StringFilter(starts_with=str_value[:-1])
                elif str_value.startswith("%"):
                    return StringFilter(ends_with=str_value[1:])
                else:
                    return StringFilter(equals=str_value)
            case BaseFilterOperator.ILIKE:
                # Parse ILIKE pattern (case-insensitive)
                if str_value.startswith("%") and str_value.endswith("%"):
                    return StringFilter(i_contains=str_value[1:-1])
                elif str_value.endswith("%"):
                    return StringFilter(i_starts_with=str_value[:-1])
                elif str_value.startswith("%"):
                    return StringFilter(i_ends_with=str_value[1:])
                else:
                    return StringFilter(i_equals=str_value)
            case _:
                # Default to equals for unknown operators
                return StringFilter(equals=str_value)

    @staticmethod
    def _apply_condition_to_filter(
        agent_filter: AgentFilter,
        condition: AgentFilterCondition,
    ) -> AgentFilter:
        """
        Apply a single leaf condition to an AgentFilter object and return the modified filter.

        Args:
            agent_filter: The AgentFilter object to modify
            condition: Typed condition with field, operator, and value

        Returns:
            The modified AgentFilter object
        """
        field = condition.field
        operator = condition.operator
        value = condition.value

        match field:
            case AgentFilterField.ID:
                agent_filter.id = AgentFilterConverter._create_string_filter_from_operator(
                    operator, value
                )
            case AgentFilterField.STATUS:
                # Status needs special handling
                if isinstance(value, AgentStatus):
                    agent_filter.status = AgentStatusFilter(equals=value)
                elif isinstance(value, str):
                    try:
                        status = AgentStatus[value.upper()]
                        agent_filter.status = AgentStatusFilter(equals=status)
                    except (KeyError, AttributeError):
                        pass
            case AgentFilterField.STATUS_CHANGED:
                agent_filter.status_changed = value
            case AgentFilterField.REGION:
                agent_filter.region = AgentFilterConverter._create_string_filter_from_operator(
                    operator, value
                )
            case AgentFilterField.SCALING_GROUP:
                agent_filter.scaling_group = (
                    AgentFilterConverter._create_string_filter_from_operator(operator, value)
                )
            case AgentFilterField.SCHEDULABLE:
                agent_filter.schedulable = bool(value)
            case AgentFilterField.ADDR:
                agent_filter.addr = AgentFilterConverter._create_string_filter_from_operator(
                    operator, value
                )
            case AgentFilterField.FIRST_CONTACT:
                agent_filter.first_contact = value
            case AgentFilterField.LOST_AT:
                agent_filter.lost_at = value
            case AgentFilterField.VERSION:
                agent_filter.version = AgentFilterConverter._create_string_filter_from_operator(
                    operator, value
                )

        return agent_filter
