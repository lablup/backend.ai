"""
Adapter for converting service search DTOs to repository query objects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.endpoint.searchable_fields import DeploymentSearchableFields
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter

if TYPE_CHECKING:
    from ai.backend.common.dto.manager.model_serving.request import ServiceFilterModel


class ServiceSearchAdapter(BaseFilterAdapter):
    """Adapter for converting service search filters to query conditions."""

    def convert_filter(self, filter: ServiceFilterModel) -> list[QueryCondition]:
        """Convert ServiceFilterModel to a list of query conditions."""
        return self.apply_string_filter(filter.name, DeploymentSearchableFields.own.name.filter)
