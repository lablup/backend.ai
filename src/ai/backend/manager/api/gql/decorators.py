"""Custom Strawberry GQL type decorators with enforced BackendAI metadata.

Use these instead of @strawberry.type and @strawberry.experimental.pydantic.type/input
so that every GQL type carries consistent version and description metadata.

Decorator roles:
    gql_node_type        — PydanticNodeMixin subclasses (Relay Node types with from_pydantic).
    gql_connection_type  — Connection[T] and Edge[T] subclasses.
    gql_pydantic_type    — Output types backed by a v2 Pydantic DTO; Strawberry
                           auto-generates from_pydantic() / to_pydantic().
    gql_pydantic_input   — Input types backed by a v2 Pydantic DTO via PydanticInputMixin.
    gql_type             — Plain output types not backed by Pydantic DTOs (e.g. subscription
                           event payloads). Use only when no suitable Pydantic DTO exists.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, TypeVar, dataclass_transform

import strawberry
import strawberry.experimental.pydantic
from pydantic import BaseModel
from strawberry.experimental.pydantic.conversion_types import StrawberryTypeFromPydantic
from strawberry.relay import Connection
from strawberry.schema_directives import OneOf
from strawberry.types.field import StrawberryField
from strawberry.types.field import field as strawberry_field

from ai.backend.common.meta import BackendAIGQLMeta
from ai.backend.manager.api.gql.pydantic_compat import (
    PydanticInputMixin,
    PydanticNodeMixin,
)

__all__ = (
    "BackendAIGQLMeta",
    "PydanticInputMixin",
    "gql_connection_type",
    "gql_node_type",
    "gql_pydantic_input",
    "gql_pydantic_interface",
    "gql_pydantic_type",
    "gql_type",
)

T = TypeVar("T", bound="PydanticNodeMixin[Any]")
T_any = TypeVar("T_any")
T_conn = TypeVar("T_conn", bound="Connection[Any]")
T_input = TypeVar("T_input", bound="PydanticInputMixin[Any]")


@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(strawberry_field, StrawberryField),
)
def gql_node_type(
    meta: BackendAIGQLMeta,
    *,
    name: str | None = None,
    directives: Sequence[object] = (),
    extend: bool = False,
) -> Callable[[type[T]], type[T]]:
    """Decorator for GQL Relay Node types (PydanticNodeMixin subclasses).

    Use for types that inherit PydanticNodeMixin and implement the Relay Node interface.
    For non-node output types backed by a Pydantic DTO, use gql_pydantic_type instead.
    """
    description = f"Added in {meta.added_version}. {meta.description}"
    if meta.deprecated_version is not None:
        hint = f" Use {meta.deprecation_hint}." if meta.deprecation_hint else ""
        description += f" Deprecated since {meta.deprecated_version}.{hint}"
    return strawberry.type(
        name=name,
        description=description,
        directives=directives,
        extend=extend,
    )


@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(strawberry_field, StrawberryField),
)
def gql_connection_type(
    meta: BackendAIGQLMeta,
    *,
    name: str | None = None,
    directives: Sequence[object] = (),
    extend: bool = False,
) -> Callable[[type[T_conn]], type[T_conn]]:
    """Decorator for GQL Connection types (Connection[T] subclasses)."""
    description = f"Added in {meta.added_version}. {meta.description}"
    if meta.deprecated_version is not None:
        hint = f" Use {meta.deprecation_hint}." if meta.deprecation_hint else ""
        description += f" Deprecated since {meta.deprecated_version}.{hint}"
    return strawberry.type(
        name=name,
        description=description,
        directives=directives,
        extend=extend,
    )


@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(strawberry_field, StrawberryField),
)
def gql_pydantic_input(
    meta: BackendAIGQLMeta,
    *,
    name: str | None = None,
    directives: Sequence[object] = (),
    description: str | None = None,
    one_of: bool = False,
) -> Callable[[type[T_input]], type[T_input]]:
    """Decorator for GQL input types backed by a Pydantic DTO via PydanticInputMixin.

    Wraps the class with ``@strawberry.input`` and relies on ``PydanticInputMixin[DTO]``
    inheritance for automatic ``to_pydantic()`` conversion.  Strawberry does not touch
    inherited methods on plain ``@strawberry.input`` types, so the mixin's
    ``to_pydantic()`` is preserved.

    Example::

        @gql_pydantic_input(meta)
        class CreateFooInputGQL(PydanticInputMixin[CreateFooInputDTO]):
            name: str

    Always declare fields explicitly in the class body.

    The ``description`` param is accepted for additional context but the
    canonical description is always built from ``BackendAIGQLMeta``.

    When ``one_of=True``, injects the ``@oneOf`` directive so exactly one field
    must be provided (mirrors ``@strawberry.input(one_of=True)`` behaviour).
    """
    desc = f"Added in {meta.added_version}. {meta.description or (description or '')}"
    if meta.deprecated_version is not None:
        hint = f" Use {meta.deprecation_hint}." if meta.deprecation_hint else ""
        desc += f" Deprecated since {meta.deprecated_version}.{hint}"
    if one_of:
        directives = (*directives, OneOf())
    return strawberry.input(
        name=name,
        description=desc,
        directives=directives,
    )


@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(strawberry_field, StrawberryField),
)
def gql_pydantic_interface[PydanticModel: BaseModel](
    meta: BackendAIGQLMeta,
    *,
    model: type[PydanticModel],
    fields: list[str] | None = None,
    name: str | None = None,
    directives: Sequence[object] = (),
    use_pydantic_alias: bool = True,
) -> Callable[..., type[StrawberryTypeFromPydantic[PydanticModel]]]:
    """Decorator for GQL interface types backed by a v2 Pydantic DTO.

    Wraps strawberry.experimental.pydantic.interface so that every GQL
    interface type carries consistent version and description metadata.
    Use for interface types where all implementors share a common Pydantic
    model structure.
    """
    description = f"Added in {meta.added_version}. {meta.description}"
    if meta.deprecated_version is not None:
        hint = f" Use {meta.deprecation_hint}." if meta.deprecation_hint else ""
        description += f" Deprecated since {meta.deprecated_version}.{hint}"
    return strawberry.experimental.pydantic.interface(
        model=model,
        fields=fields,
        name=name,
        description=description,
        directives=directives,
        use_pydantic_alias=use_pydantic_alias,
    )


@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(strawberry_field, StrawberryField),
)
def gql_pydantic_type[PydanticModel: BaseModel](
    meta: BackendAIGQLMeta,
    *,
    model: type[PydanticModel],
    fields: list[str] | None = None,
    name: str | None = None,
    all_fields: bool = False,
    directives: Sequence[object] = (),
    use_pydantic_alias: bool = True,
) -> Callable[..., type[StrawberryTypeFromPydantic[PydanticModel]]]:
    """Decorator for GQL types backed by a v2 Pydantic DTO.

    Strawberry auto-generates from_pydantic() and to_pydantic() methods.
    Use all_fields=True for scalar-only types, or declare fields explicitly
    for types with nested GQL node fields.
    """
    description = f"Added in {meta.added_version}. {meta.description}"
    if meta.deprecated_version is not None:
        hint = f" Use {meta.deprecation_hint}." if meta.deprecation_hint else ""
        description += f" Deprecated since {meta.deprecated_version}.{hint}"
    return strawberry.experimental.pydantic.type(
        model=model,
        fields=fields,
        name=name,
        description=description,
        directives=directives,
        all_fields=all_fields,
        use_pydantic_alias=use_pydantic_alias,
    )


@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(strawberry_field, StrawberryField),
)
def gql_type(
    meta: BackendAIGQLMeta,
    *,
    name: str | None = None,
    directives: Sequence[object] = (),
    extend: bool = False,
) -> Callable[[type[T_any]], type[T_any]]:
    """Decorator for plain GQL output types not backed by Pydantic DTOs.

    Use only for types that cannot use gql_node_type or gql_pydantic_type,
    such as subscription event payloads that are constructed directly from
    event objects rather than from Pydantic DTOs.
    """
    description = f"Added in {meta.added_version}. {meta.description}"
    if meta.deprecated_version is not None:
        hint = f" Use {meta.deprecation_hint}." if meta.deprecation_hint else ""
        description += f" Deprecated since {meta.deprecated_version}.{hint}"
    return strawberry.type(
        name=name,
        description=description,
        directives=directives,
        extend=extend,
    )
