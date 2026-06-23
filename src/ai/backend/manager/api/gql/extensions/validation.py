from __future__ import annotations

from collections.abc import Iterator

from graphql import ValidationRule
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.extensions.query_depth_limiter import create_validator as create_depth_validator

from ai.backend.manager.api.gql.types import PublicGQLContext, StrawberryGQLContext
from ai.backend.manager.api.graphql_rules import CustomIntrospectionRule, PublicFieldGateRule


class GQLValidationExtension(SchemaExtension):
    """Assembles per-request GraphQL validation rules.

    Reads configuration from ``StrawberryGQLContext.config_provider`` to decide which validation
    rules to add at request time (introspection blocking, query depth limiting). For the
    unauthenticated public endpoint — identified by a ``PublicGQLContext`` — it also applies
    ``PublicFieldGateRule`` so anonymous callers reach only ``@public``-marked root fields.
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
        if isinstance(ctx, PublicGQLContext):
            additional_rules.append(PublicFieldGateRule)

        if additional_rules:
            self.execution_context.validation_rules = (
                self.execution_context.validation_rules + tuple(additional_rules)
            )
        yield
