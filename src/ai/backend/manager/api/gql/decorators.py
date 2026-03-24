"""Custom Strawberry GQL type decorators with enforced BackendAI metadata.

Use these instead of @strawberry.type, @strawberry.experimental.pydantic.type/input,
@strawberry.field, @strawberry.enum, and @strawberry.mutation so that every GQL
element carries consistent version and description metadata.

Decorator roles:
    gql_node_type          — PydanticNodeMixin subclasses (Relay Node types with from_pydantic).
    gql_connection_type    — Connection[T] and Edge[T] subclasses.
    gql_pydantic_type      — Output types backed by a v2 Pydantic DTO; Strawberry
                             auto-generates from_pydantic() / to_pydantic().
    gql_pydantic_input     — Input types backed by a v2 Pydantic DTO via PydanticInputMixin.
    gql_pydantic_interface — Interface types backed by a v2 Pydantic DTO.
    gql_field              — Fields introduced with the parent type (no separate version).
    gql_added_field        — Fields added after the parent type (own version via meta).
    gql_root_field         — Root query fields (always have their own version via meta).
    gql_enum               — Enum types with version metadata.
    gql_mutation           — Mutation resolvers with version metadata.
    gql_subscription       — Subscription resolvers with version metadata.
    gql_federation_type    — Federation types with version metadata and keys.
"""

from __future__ import annotations

import enum
from collections.abc import Callable, Sequence
from typing import Any, TypeVar, dataclass_transform, overload

import strawberry
import strawberry.experimental.pydantic
import strawberry.federation
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
    "gql_added_field",
    "gql_connection_type",
    "gql_enum",
    "gql_field",
    "gql_mutation",
    "gql_node_type",
    "gql_pydantic_input",
    "gql_pydantic_interface",
    "gql_pydantic_type",
    "gql_root_field",
    "gql_subscription",
    "gql_federation_type",
)

T = TypeVar("T", bound="PydanticNodeMixin[Any]")
T_conn = TypeVar("T_conn", bound="Connection[Any]")
T_input = TypeVar("T_input", bound="PydanticInputMixin[Any]")


def _build_description(meta: BackendAIGQLMeta) -> str:
    """Build a GQL description string from BackendAIGQLMeta."""
    description = f"Added in {meta.added_version}. {meta.description}"
    if meta.deprecated_version is not None:
        hint = f" Use {meta.deprecation_hint}." if meta.deprecation_hint else ""
        description += f" Deprecated since {meta.deprecated_version}.{hint}"
    return description


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
    return strawberry.type(
        name=name,
        description=_build_description(meta),
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
    return strawberry.type(
        name=name,
        description=_build_description(meta),
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

    When ``one_of=True``, injects the ``@oneOf`` directive so exactly one field
    must be provided (mirrors ``@strawberry.input(one_of=True)`` behaviour).
    """
    if one_of:
        directives = (*directives, OneOf())
    return strawberry.input(
        name=name,
        description=_build_description(meta),
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
    return strawberry.experimental.pydantic.interface(
        model=model,
        fields=fields,
        name=name,
        description=_build_description(meta),
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
    return strawberry.experimental.pydantic.type(
        model=model,
        fields=fields,
        name=name,
        description=_build_description(meta),
        directives=directives,
        all_fields=all_fields,
        use_pydantic_alias=use_pydantic_alias,
    )


def gql_field(
    *,
    description: str,
    name: str | None = None,
    default: Any = strawberry.UNSET,
    deprecation_reason: str | None = None,
) -> Any:
    """Field introduced with the parent type (shares the parent's version).

    Use for fields that do not need their own ``added_version``.
    For fields added after the parent type, use ``gql_added_field`` instead.
    """
    return strawberry.field(
        description=description,
        name=name,
        default=default,
        deprecation_reason=deprecation_reason,
    )


def gql_added_field(
    meta: BackendAIGQLMeta,
    *,
    name: str | None = None,
    default: Any = strawberry.UNSET,
    deprecation_reason: str | None = None,
) -> Any:
    """Field added after the parent type was released (has its own version).

    Automatically prefixes the description with "Added in {version}."
    """
    return strawberry.field(
        description=_build_description(meta),
        name=name,
        default=default,
        deprecation_reason=deprecation_reason,
    )


def gql_root_field(
    meta: BackendAIGQLMeta,
    *,
    name: str | None = None,
    deprecation_reason: str | None = None,
) -> Any:
    """Root query/subscription field on the Query type (always has its own version).

    Use for top-level fields on the Query type that are independently versioned.
    """
    return strawberry.field(
        description=_build_description(meta),
        name=name,
        deprecation_reason=deprecation_reason,
    )


@overload
def gql_enum[T_enum: enum.Enum](
    meta: BackendAIGQLMeta,
    enum_cls: type[T_enum],
    *,
    name: str | None = ...,
) -> type[T_enum]: ...


@overload
def gql_enum[T_enum: enum.Enum](
    meta: BackendAIGQLMeta,
    enum_cls: None = ...,
    *,
    name: str | None = ...,
) -> Callable[[type[T_enum]], type[T_enum]]: ...


def gql_enum(
    meta: BackendAIGQLMeta,
    enum_cls: type[enum.Enum] | None = None,
    *,
    name: str | None = None,
) -> Any:
    """Enum type with version metadata.

    Can be used as a decorator or as a function call for DTO wrapping::

        # As decorator
        @gql_enum(BackendAIGQLMeta(...))
        class StatusGQL(StrEnum): ...

        # As function (DTO wrapping)
        StatusGQL = gql_enum(BackendAIGQLMeta(...), StatusDTO, name="Status")
    """
    description = _build_description(meta)
    if enum_cls is not None:
        if name is not None:
            return strawberry.enum(enum_cls, description=description, name=name)
        return strawberry.enum(enum_cls, description=description)
    if name is not None:
        return strawberry.enum(description=description, name=name)
    return strawberry.enum(description=description)


def gql_mutation(
    meta: BackendAIGQLMeta,
    *,
    name: str | None = None,
    deprecation_reason: str | None = None,
) -> Any:
    """Mutation resolver with version metadata."""
    return strawberry.mutation(
        description=_build_description(meta),
        name=name,
        deprecation_reason=deprecation_reason,
    )


def gql_subscription(
    meta: BackendAIGQLMeta,
    *,
    name: str | None = None,
    deprecation_reason: str | None = None,
) -> Any:
    """Subscription resolver with version metadata."""
    return strawberry.subscription(
        description=_build_description(meta),
        name=name,
        deprecation_reason=deprecation_reason,
    )


@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(strawberry_field, StrawberryField),
)
def gql_federation_type(
    meta: BackendAIGQLMeta,
    *,
    name: str | None = None,
    keys: list[str] | None = None,
    extend: bool = False,
    directives: Sequence[object] = (),
) -> Any:
    """Federation type with version metadata and keys.

    Wraps ``strawberry.federation.type`` for federation entity types.
    Use for types that participate in Apollo Federation with ``@key`` directives.
    """
    # GraphQL spec forbids descriptions on `extend type` declarations
    description = None if extend else _build_description(meta)
    return strawberry.federation.type(
        name=name,
        keys=keys or [],
        description=description,
        extend=extend,
        directives=directives,
    )
