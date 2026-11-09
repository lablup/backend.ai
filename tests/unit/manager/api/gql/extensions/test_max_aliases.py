from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from graphql import GraphQLSchema, build_schema, parse, validate

from ai.backend.manager.api.gql.extensions.max_aliases import GQLMaxAliasesExtension


@dataclass(frozen=True)
class _AliasCountCase:
    description: str
    document: str
    expected_errors: list[str] = field(default_factory=list)


class TestGQLMaxAliasesExtension:
    @pytest.fixture
    def schema(self) -> GraphQLSchema:
        return build_schema("type Query { node(id: ID!): Item } type Item { id: ID! }")

    @pytest.fixture
    def extension(self) -> GQLMaxAliasesExtension:
        return GQLMaxAliasesExtension(max_alias_count=20)

    @pytest.mark.parametrize(
        "case",
        [
            _AliasCountCase(
                description="router-batched-15-root-fields",
                document="{ "
                + " ".join(
                    f'_v{i}___typename: __typename _v{i}_node: node(id: "{i}") {{ id }}'
                    for i in range(15)
                )
                + " }",
            ),
            _AliasCountCase(
                description="20-aliases-at-limit",
                document="{ "
                + " ".join(f'a{i}: node(id: "{i}") {{ id }}' for i in range(20))
                + " }",
            ),
            _AliasCountCase(
                description="30-typename-aliases-only",
                document="{ " + " ".join(f"t{i}: __typename" for i in range(30)) + " }",
            ),
            _AliasCountCase(
                description="21-aliases-over-limit",
                document="{ "
                + " ".join(f'a{i}: node(id: "{i}") {{ id }}' for i in range(21))
                + " }",
                expected_errors=["21 aliases found. Allowed: 20"],
            ),
            _AliasCountCase(
                description="aliases-in-inline-and-named-fragments-add-up",
                document="{ "
                + " ".join(f'a{i}: node(id: "{i}") {{ id }}' for i in range(7))
                + ' node(id: "x") { ... on Item { '
                + " ".join(f"b{i}: id" for i in range(7))
                + " } ...ItemIds } } fragment ItemIds on Item { "
                + " ".join(f"c{i}: id" for i in range(7))
                + " }",
                expected_errors=["21 aliases found. Allowed: 20"],
            ),
        ],
        ids=lambda case: case.description,
    )
    def test_counts_aliases_except_typename(
        self,
        schema: GraphQLSchema,
        extension: GQLMaxAliasesExtension,
        case: _AliasCountCase,
    ) -> None:
        errors = validate(schema, parse(case.document), extension.validation_rules)

        assert [error.message for error in errors] == case.expected_errors
