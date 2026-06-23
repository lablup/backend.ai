"""Tests for the unauthenticated public GraphQL schema (``PublicQueries``).

The public endpoint serves a separate schema that contains only public fields, so private fields
are physically absent and cannot be queried — there is no runtime gate to get wrong.
"""

from __future__ import annotations

from ai.backend.manager.api.gql.schema import public_schema, schema


def test_public_schema_exposes_only_public_fields() -> None:
    public_query = public_schema._schema.query_type
    main_query = schema._schema.query_type
    assert public_query is not None
    assert main_query is not None
    public_fields = set(public_query.fields)
    main_fields = set(main_query.fields)
    # The placeholder public field is present on the public schema.
    assert "publicPing" in public_fields
    # A private root field exists on the authenticated schema...
    assert "node" in main_fields
    # ...but is structurally absent from the public schema (cannot be queried at all).
    assert "node" not in public_fields


def test_public_schema_has_no_mutation_or_subscription() -> None:
    # Anonymous callers cannot mutate or subscribe: those roots do not exist on the public schema.
    assert public_schema._schema.mutation_type is None
    assert public_schema._schema.subscription_type is None
