"""Test for the unauthenticated public GraphQL schema (``PublicQueries``).

The public endpoint serves a separate schema, so private fields must not leak into it. This
asserts the durable structural property rather than the (placeholder) public fields themselves.
"""

from __future__ import annotations

from ai.backend.manager.api.gql.schema import public_schema, schema


def test_public_schema_excludes_private_fields() -> None:
    public_query = public_schema._schema.query_type
    main_query = schema._schema.query_type
    assert public_query is not None
    assert main_query is not None
    # `node` is a private root field on the authenticated schema; it must be absent from the
    # public schema, which exposes only explicitly-public fields.
    assert "node" in main_query.fields
    assert "node" not in public_query.fields
