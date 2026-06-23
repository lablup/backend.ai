"""Tests for the anonymous public GraphQL gate (``@public`` directive + PublicFieldGateRule)."""

from __future__ import annotations

from graphql import (
    GraphQLField,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
    parse,
    validate,
)

from ai.backend.common.meta import BackendAIGQLMeta
from ai.backend.manager.api.gql.decorators import gql_root_field
from ai.backend.manager.api.gql.directives import Public
from ai.backend.manager.api.graphql_rules import PublicFieldGateRule

# --- Part A: a root field declared with directives=[Public()] carries the @public marker ---


def test_gql_root_field_carries_public_directive() -> None:
    field = gql_root_field(
        BackendAIGQLMeta(description="d", added_version="26.4.4"), directives=[Public()]
    )
    assert any(isinstance(d, Public) for d in field.directives)


def test_gql_root_field_without_public_directive_is_unmarked() -> None:
    field = gql_root_field(BackendAIGQLMeta(description="d", added_version="26.4.4"))
    assert not any(isinstance(d, Public) for d in field.directives)


# --- Part B: PublicFieldGateRule enforces the marker at validation time ---
#
# The schema is built with graphql-core directly (Strawberry's type/field constructors are banned
# in this repo). The ``strawberry-definition`` extension holds a real ``StrawberryField`` produced
# by ``gql_root_field(..., directives=[Public()])``, so the rule reads ``@public`` exactly as it
# does on the production schema.

_public_marker = gql_root_field(
    BackendAIGQLMeta(description="d", added_version="26.4.4"), directives=[Public()]
)
_info_type = GraphQLObjectType("Info", {"version": GraphQLField(GraphQLString)})
_schema = GraphQLSchema(
    query=GraphQLObjectType(
        "Query",
        {
            "serverConfig": GraphQLField(
                _info_type,
                extensions={"strawberry-definition": _public_marker},
            ),
            "secretData": GraphQLField(GraphQLString),
        },
    ),
    mutation=GraphQLObjectType("Mutation", {"doThing": GraphQLField(GraphQLString)}),
)


def _gate(query: str) -> list[str]:
    return [e.message for e in validate(_schema, parse(query), [PublicFieldGateRule])]


def test_public_marked_root_field_passes() -> None:
    assert _gate("{ serverConfig { version } }") == []


def test_unmarked_root_field_rejected() -> None:
    errors = _gate("{ secretData }")
    assert len(errors) == 1
    assert "secretData" in errors[0]


def test_nested_field_under_public_root_is_reachable() -> None:
    # Only the root entry point is gated; the whole sub-selection is allowed.
    assert _gate("{ serverConfig { version } }") == []


def test_mutation_always_rejected() -> None:
    errors = _gate("mutation { doThing }")
    assert len(errors) == 1
    assert "read-only" in errors[0]


def test_typename_allowed_at_root() -> None:
    assert _gate("{ __typename }") == []


def test_introspection_rejected() -> None:
    errors = _gate("{ __schema { types { name } } }")
    assert len(errors) == 1
    assert "__schema" in errors[0]


def test_fragment_cannot_bypass_gate() -> None:
    errors = _gate("{ ...F } fragment F on Query { secretData }")
    assert len(errors) == 1
    assert "secretData" in errors[0]
