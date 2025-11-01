from __future__ import annotations

from typing import override

from ai.backend.common.exception import AgentOrderingFieldNotSupportedError

from ..base import BaseOrderConverter
from .types import AgentOrderBy, AgentOrderField


class AgentOrderConverter(BaseOrderConverter[AgentOrderField, AgentOrderBy]):
    """
    Parser for Agent ordering expressions.
    Parses order strings like "+id" or "-status" into AgentOrderingOptions objects.
    """

    @override
    def _convert_field(self, parsed_expr: dict[str, bool]) -> dict[AgentOrderField, bool]:
        try:
            result = {}
            for field_name, ascending in parsed_expr.items():
                field_enum = AgentOrderField(field_name.lower())
                result[field_enum] = ascending
            return result

        except ValueError:
            field_names = ",".join(parsed_expr.keys())
            raise AgentOrderingFieldNotSupportedError(field_names)

    @override
    def _create_order_by(self, order_by: dict[AgentOrderField, bool]) -> list[AgentOrderBy]:
        return [
            AgentOrderBy(field=field, ascending=ascending) for field, ascending in order_by.items()
        ]
