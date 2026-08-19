"""Tests for shared GQL types in ai.backend.manager.api.gql.common_types."""

from __future__ import annotations

from typing import Any, cast

from ai.backend.common.dto.manager.v2.common import BinarySizeInfo
from ai.backend.manager.api.gql.common_types import BinarySizeInfoGQL


class TestBinarySizeInfoGQL:
    """BinarySizeInfoGQL.expr must map to GraphQL String, not the 32-bit Int scalar.

    Regression guard: exposing the byte count as Int made sizes over 2 GiB fail
    response serialization with "Int cannot represent non 32-bit signed integer".
    Strawberry maps a ``str`` field to String and an ``int`` field to Int, so the
    field's Python type is the invariant that decides the GraphQL scalar.
    """

    def test_expr_field_maps_to_string(self) -> None:
        definition = cast(Any, BinarySizeInfoGQL).__strawberry_definition__
        fields = {f.name: f for f in definition.fields}
        assert fields["expr"].type is str

    def test_from_pydantic_preserves_string_expr(self) -> None:
        gql = BinarySizeInfoGQL.from_pydantic(BinarySizeInfo(expr="1234000000000", display="1.1t"))
        assert cast(Any, gql).expr == "1234000000000"
