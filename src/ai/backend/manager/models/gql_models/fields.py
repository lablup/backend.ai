from typing import (
    Any,
)

import graphene
import graphql

from ..rbac import (
    ScopeType,
    deserialize_scope,
)


class ScopeValueField(graphene.Scalar):
    class Meta:
        description = "Added in 24.09.0."

    @staticmethod
    def serialize(val: ScopeType) -> str:
        return val.serialize()

    @staticmethod
    def parse_literal(node: Any, _variables=None):
        if isinstance(node, graphql.language.ast.StringValueNode):
            return deserialize_scope(node.value)

    @staticmethod
    def parse_value(value: str) -> ScopeType:
        return deserialize_scope(value)
