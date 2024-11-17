from typing import (
    Any,
    Optional,
)

import graphene
import graphql

from ..rbac import (
    ScopeType,
    deserialize_scope,
)
from ..rbac.permission_defs import AgentPermission


class ScopeField(graphene.Scalar):
    class Meta:
        description = (
            "Added in 24.12.0. A string value in the format '<SCOPE_TYPE>:<SCOPE_ID>'. "
            "<SCOPE_TYPE> should be one of [system, domain, project, user]. "
            "<SCOPE_ID> should be the ID value of the scope. "
            "e.g. `domain:default`, `user:123e4567-e89b-12d3-a456-426614174000`."
        )

    @staticmethod
    def serialize(val: ScopeType) -> str:
        return val.serialize()

    @staticmethod
    def parse_literal(node: Any, _variables=None) -> Optional[ScopeType]:
        if isinstance(node, graphql.language.ast.StringValueNode):
            return deserialize_scope(node.value)
        return None

    @staticmethod
    def parse_value(value: str) -> ScopeType:
        return deserialize_scope(value)


class AgentPermissionField(graphene.Scalar):
    class Meta:
        description = f"Added in 24.12.0. One of {[val.value for val in AgentPermission]}."

    @staticmethod
    def serialize(val: AgentPermission) -> str:
        return val.value

    @staticmethod
    def parse_literal(node: Any, _variables=None):
        if isinstance(node, graphql.language.ast.StringValueNode):
            return AgentPermission(node.value)

    @staticmethod
    def parse_value(value: str) -> AgentPermission:
        return AgentPermission(value)
