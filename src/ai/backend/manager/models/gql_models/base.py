from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

import graphene
import graphql
from graphene.types import Scalar
from graphene.types.scalars import MAX_INT, MIN_INT
from graphql.language.ast import IntValueNode

from ...api.exceptions import ObjectNotFound
from ..gql_relay import AsyncNode

SAFE_MIN_INT = -9007199254740991
SAFE_MAX_INT = 9007199254740991


class ResourceLimit(graphene.ObjectType):
    key = graphene.String()
    min = graphene.String()
    max = graphene.String()


class KVPair(graphene.ObjectType):
    key = graphene.String()
    value = graphene.String()


class ResourceLimitInput(graphene.InputObjectType):
    key = graphene.String()
    min = graphene.String()
    max = graphene.String()


class KVPairInput(graphene.InputObjectType):
    key = graphene.String()
    value = graphene.String()


class BigInt(Scalar):
    """
    BigInt is an extension of the regular graphene.Int scalar type
    to support integers outside the range of a signed 32-bit integer.
    """

    @staticmethod
    def coerce_bigint(value):
        num = int(value)
        if not (SAFE_MIN_INT <= num <= SAFE_MAX_INT):
            raise ValueError("Cannot serialize integer out of the safe range.")
        if not (MIN_INT <= num <= MAX_INT):
            # treat as float
            return float(int(num))
        return num

    serialize = coerce_bigint
    parse_value = coerce_bigint

    @staticmethod
    def parse_literal(node):
        if isinstance(node, IntValueNode):
            num = int(node.value)
            if not (SAFE_MIN_INT <= num <= SAFE_MAX_INT):
                raise ValueError("Cannot parse integer out of the safe range.")
            if not (MIN_INT <= num <= MAX_INT):
                # treat as float
                return float(int(num))
            return num


class Bytes(Scalar):
    class Meta:
        description = "Added in 24.09.1."

    @staticmethod
    def serialize(val: bytes) -> str:
        return val.hex()

    @staticmethod
    def parse_literal(node: Any, _variables=None) -> Optional[bytes]:
        if isinstance(node, graphql.language.ast.StringValueNode):
            assert isinstance(node, str)
            return bytes.fromhex(node)
        return None

    @staticmethod
    def parse_value(value: str) -> bytes:
        return bytes.fromhex(value)


class ImageRefType(graphene.InputObjectType):
    name = graphene.String(required=True)
    registry = graphene.String()
    architecture = graphene.String()


def extract_object_uuid(info: graphene.ResolveInfo, global_id: str, object_name: str) -> UUID:
    """
    Converts a GraphQL global ID to its corresponding UUID.
    If the global ID is not valid, raises an error using the provided object name.
    """

    _, raw_id = AsyncNode.resolve_global_id(info, global_id)
    if not raw_id:
        raw_id = global_id

    try:
        return UUID(raw_id)
    except ValueError:
        raise ObjectNotFound(object_name)
