from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from ai.backend.manager.api.gql.base import StringFilter
from ai.backend.manager.data.agent.types import AgentOrderField, AgentStatus

if TYPE_CHECKING:
    from ai.backend.manager.data.agent.types import AgentFilter, AgentOrderBy


@dataclass
class AgentOrderingOptions:
    """Ordering options for agents."""

    order_by: list[tuple[AgentOrderField, bool]] = field(
        default_factory=lambda: [(AgentOrderField.ID, False)]
    )  # (field, desc)

    @classmethod
    def from_data_ordering(cls, order_by: list[AgentOrderBy]) -> AgentOrderingOptions:
        """
        Convert service-layer AgentOrderBy list to repository-layer AgentOrderingOptions.

        Args:
            order_by: List of AgentOrderBy objects from data layer

        Returns:
            AgentOrderingOptions with converted ordering
        """
        if len(order_by) == 0:
            return cls()  # Uses default ordering

        repo_order_by = []
        for order in order_by:
            # desc is True when ascending=False (inverted logic for repository layer)
            desc = not order.ascending
            repo_order_by.append((order.field, desc))

        return cls(order_by=repo_order_by)


class AgentStatusFilterType(Enum):
    IN = "in"
    EQUALS = "equals"


@dataclass
class AgentStatusFilter:
    type: AgentStatusFilterType
    values: list[AgentStatus]


@dataclass
class AgentFilterOptions:
    """Filtering options for agents."""

    id: Optional[StringFilter] = None
    status: Optional[AgentStatusFilter] = None
    status_changed: Optional[datetime] = None
    region: Optional[StringFilter] = None
    scaling_group: Optional[StringFilter] = None
    schedulable: Optional[bool] = None
    addr: Optional[StringFilter] = None
    first_contact: Optional[datetime] = None
    lost_at: Optional[datetime] = None
    version: Optional[StringFilter] = None

    # Logical operations
    AND: Optional[list["AgentFilterOptions"]] = None
    OR: Optional[list["AgentFilterOptions"]] = None
    NOT: Optional[list["AgentFilterOptions"]] = None

    @classmethod
    def from_data_filter(cls, filter: Optional[AgentFilter]) -> Optional[AgentFilterOptions]:
        """
        Convert service-layer AgentFilter to repository-layer AgentFilterOptions.

        This method encapsulates the conversion logic, avoiding the need for data layer
        objects to have dependencies on repository layer types.

        Args:
            filter: AgentFilter object from data layer (or None)

        Returns:
            AgentFilterOptions with converted filters, or None if input is None
        """
        if filter is None:
            return None

        filter_options = cls()

        # Convert field-specific filters
        # StringFilter fields can be directly copied since they're already StringFilter objects
        if filter.id is not None:
            filter_options.id = filter.id

        if filter.status is not None:
            if filter.status.equals is not None:
                filter_options.status = AgentStatusFilter(
                    type=AgentStatusFilterType.EQUALS,
                    values=[filter.status.equals],
                )
            elif filter.status.in_ is not None:
                filter_options.status = AgentStatusFilter(
                    type=AgentStatusFilterType.IN,
                    values=filter.status.in_,
                )

        if filter.region is not None:
            filter_options.region = filter.region

        if filter.scaling_group is not None:
            filter_options.scaling_group = filter.scaling_group

        if filter.schedulable is not None:
            filter_options.schedulable = filter.schedulable

        if filter.addr is not None:
            filter_options.addr = filter.addr

        if filter.version is not None:
            filter_options.version = filter.version

        # Handle logical operations (AND/OR/NOT)
        if filter.AND is not None:
            converted_and = [cls.from_data_filter(sub_filter) for sub_filter in filter.AND]
            filter_options.AND = [f for f in converted_and if f is not None]
        if filter.OR is not None:
            converted_or = [cls.from_data_filter(sub_filter) for sub_filter in filter.OR]
            filter_options.OR = [f for f in converted_or if f is not None]
        if filter.NOT is not None:
            converted_not = [cls.from_data_filter(sub_filter) for sub_filter in filter.NOT]
            filter_options.NOT = [f for f in converted_not if f is not None]

        return filter_options
