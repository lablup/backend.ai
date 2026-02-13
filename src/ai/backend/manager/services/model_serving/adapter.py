"""
Adapter for converting service search DTOs to repository query objects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.repositories.deployment.options import DeploymentConditions

if TYPE_CHECKING:
    from ai.backend.manager.api.service import ServiceFilterModel


class ServiceSearchAdapter(BaseFilterAdapter):
    """Adapter for converting service search filters to query conditions."""

    def convert_filter(self, filter: ServiceFilterModel) -> list[QueryCondition]:
        """Convert ServiceFilterModel to a list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=DeploymentConditions.by_name_contains,
                equals_factory=DeploymentConditions.by_name_equals,
                starts_with_factory=DeploymentConditions.by_name_starts_with,
                ends_with_factory=DeploymentConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions
