from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from graphql import GraphQLError, ValidationRule
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.extensions.query_depth_limiter import create_validator as create_depth_validator

from ai.backend.manager.api.gql.types import StrawberryGQLContext


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


class GQLValidationExtension(SchemaExtension):
    """Conditionally applies introspection blocking and query depth limiting.

    Reads configuration from ``StrawberryGQLContext.config_provider`` to decide
    which validation rules to add at request time.
    """

    def on_validate(self) -> Iterator[None]:
        ctx: StrawberryGQLContext = self.execution_context.context
        config = ctx.config_provider.config

        additional_rules: list[type[ValidationRule]] = []
        if not config.api.allow_graphql_schema_introspection:
            additional_rules.append(CustomIntrospectionRule)
        max_depth = config.api.max_gql_query_depth
        if max_depth is not None:
            additional_rules.append(create_depth_validator(max_depth, None, None))

        if additional_rules:
            self.execution_context.validation_rules = (
                self.execution_context.validation_rules + tuple(additional_rules)
            )
        yield
