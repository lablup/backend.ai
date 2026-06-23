"""Strawberry schema directives for the manager GraphQL schema."""

from __future__ import annotations

import strawberry
from strawberry.schema_directive import Location


@strawberry.schema_directive(
    locations=[Location.FIELD_DEFINITION],
    name="public",
    description=(
        "Marks a root Query field as accessible without authentication via the public "
        "GraphQL endpoint (POST /admin/gql/strawberry/public). Fields without this directive "
        "are rejected for anonymous callers. Only mark fields whose resolvers are safe to run "
        "without an authenticated user."
    ),
)
class Public:
    """Field-definition directive declaring a root Query field publicly accessible."""
