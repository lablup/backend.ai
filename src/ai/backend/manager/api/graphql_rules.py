from __future__ import annotations

from typing import Any

from graphql import GraphQLError, GraphQLField, ValidationRule
from strawberry.types.field import StrawberryField

from ai.backend.manager.api.gql.directives import Public


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


class PublicFieldGateRule(ValidationRule):
    """Restricts anonymous (unauthenticated) public queries to ``@public``-marked root fields.

    Applied only on the public GraphQL endpoint. A root ``Query`` field is accepted only when its
    definition carries the ``@public`` directive (see ``api.gql.directives.Public``); every other
    root query field, and every mutation/subscription root field, is rejected. ``__typename`` is
    always allowed.

    Gating happens at the operation root only: once a root query field is allowed, its whole
    sub-selection is reachable. Parent-type tracking is delegated to graphql-core's ``TypeInfo``,
    so fragments and inline fragments cannot be used to bypass the gate.
    """

    @staticmethod
    def _is_public_field(field_def: GraphQLField | None) -> bool:
        """Return True if the resolved GraphQL field carries the ``@public`` schema directive.

        Strawberry stores its own field definition under the ``strawberry-definition`` key of the
        graphql-core field's ``extensions``; that object is a ``StrawberryField`` whose
        ``directives`` list holds the applied schema directives.
        """
        if field_def is None:
            return False
        definition = (field_def.extensions or {}).get("strawberry-definition")
        if not isinstance(definition, StrawberryField):
            return False
        return any(isinstance(directive, Public) for directive in definition.directives)

    def enter_field(self, node: Any, *_args: Any) -> None:
        parent_type = self.context.get_parent_type()
        if parent_type is None:
            return
        schema = self.context.schema
        field_name = node.name.value
        if parent_type is schema.query_type:
            if field_name == "__typename" or self._is_public_field(self.context.get_field_def()):
                return
            self.report_error(
                GraphQLError(
                    f"Cannot query '{field_name}': not available for anonymous public access.",
                    node,
                )
            )
        elif schema.mutation_type is not None and parent_type is schema.mutation_type:
            self.report_error(
                GraphQLError(
                    f"Cannot perform mutation '{field_name}': "
                    "anonymous public access is read-only.",
                    node,
                )
            )
        elif schema.subscription_type is not None and parent_type is schema.subscription_type:
            self.report_error(
                GraphQLError(
                    f"Cannot subscribe to '{field_name}': anonymous public access is read-only.",
                    node,
                )
            )
