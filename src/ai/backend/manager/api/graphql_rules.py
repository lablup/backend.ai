from __future__ import annotations

from typing import Any

from graphql import GraphQLError, ValidationRule


class CustomIntrospectionRule(ValidationRule):
    """Blocks introspection queries (fields starting with ``__``) except ``__typename``."""

    def enter_field(self, node: Any, *_args: Any) -> None:
        field_name = node.name.value
        if field_name.startswith("__"):
            if field_name == "__typename":
                return
            self.report_error(
                GraphQLError(f"Cannot query '{field_name}': introspection is disabled.", node)
            )
