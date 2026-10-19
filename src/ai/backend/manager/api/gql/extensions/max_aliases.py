from __future__ import annotations

from typing import Any

from graphql import FieldNode, GraphQLError, ValidationContext, ValidationRule
from strawberry.extensions import AddValidationRules


class GQLMaxAliasesExtension(AddValidationRules):
    """Caps aliased fields per document, skipping aliased ``__typename``: Hive Gateway adds a
    ``_vN___typename: __typename`` beside every root field it batches into a subgraph request.
    """

    def __init__(self, max_alias_count: int) -> None:
        super().__init__([_max_aliases_rule(max_alias_count)])


def _max_aliases_rule(max_alias_count: int) -> type[ValidationRule]:
    class MaxAliasesRule(ValidationRule):
        _alias_count: int

        def __init__(self, context: ValidationContext) -> None:
            super().__init__(context)
            self._alias_count = 0

        def enter_field(self, node: FieldNode, *_args: Any) -> None:
            if node.alias is not None and node.name.value != "__typename":
                self._alias_count += 1

        def leave_document(self, *_args: Any) -> None:
            if self._alias_count > max_alias_count:
                self.report_error(
                    GraphQLError(f"{self._alias_count} aliases found. Allowed: {max_alias_count}")
                )

    return MaxAliasesRule
