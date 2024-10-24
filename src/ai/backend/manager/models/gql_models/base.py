from __future__ import annotations

import graphene
from graphene.types import Scalar
from graphene.types.scalars import MAX_INT, MIN_INT
from graphql.language.ast import IntValueNode

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


class ImageRefType(graphene.InputObjectType):
    name = graphene.String(required=True)
    registry = graphene.String()
    architecture = graphene.String()
