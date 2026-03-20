"""Custom Strawberry GQL type decorators with enforced BackendAI metadata.

Use these instead of @strawberry.type and @strawberry.experimental.pydantic.type/input
so that every GQL type carries consistent version and description metadata.

Decorator roles:
    gql_node_type        — PydanticNodeMixin subclasses and complex output types
                           that cannot use @strawberry.experimental.pydantic.type
                           (e.g. types with strawberry.Private fields or interface
                           implementations).
    gql_connection_type  — Connection[T] and Edge[T] subclasses.
    gql_pydantic_type    — Output types backed by a v2 Pydantic DTO; Strawberry
                           auto-generates from_pydantic() / to_pydantic().
    gql_pydantic_input   — Input types backed by a v2 Pydantic DTO; Strawberry
                           auto-generates from_pydantic() / to_pydantic().
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar, dataclass_transform

import strawberry
import strawberry.experimental.pydantic
from pydantic import BaseModel
from strawberry.experimental.pydantic.conversion_types import StrawberryTypeFromPydantic
from strawberry.schema_directives import OneOf
from strawberry.types.field import StrawberryField
from strawberry.types.field import field as strawberry_field

from ai.backend.common.meta import BackendAIGQLMeta

__all__ = (
    "BackendAIGQLMeta",
    "gql_connection_type",
    "gql_node_type",
    "gql_pydantic_input",
    "gql_pydantic_interface",
    "gql_pydantic_type",
)

T = TypeVar("T")


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
    """Decorator for GQL node types.

    Use for PydanticNodeMixin subclasses and any complex output type that
    cannot use gql_pydantic_type (e.g. types with strawberry.Private fields,
    interface implementations, or types requiring custom from_pydantic logic).
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
) -> Callable[[type[T]], type[T]]:
    """Decorator for GQL Connection and Edge types."""
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
def gql_pydantic_input[PydanticModel: BaseModel](
    meta: BackendAIGQLMeta,
    *,
    model: type[PydanticModel],
    fields: list[str] | None = None,
    name: str | None = None,
    directives: Sequence[object] = (),
    use_pydantic_alias: bool = True,
    description: str | None = None,
    one_of: bool = False,
) -> Callable[..., type[StrawberryTypeFromPydantic[PydanticModel]]]:
    """Decorator for GQL input types backed by a v2 Pydantic DTO.

    Strawberry auto-generates to_pydantic() for simple types where all GQL field
    types map directly to the pydantic model fields (same scalar types).

    When explicit conversion is required — e.g., strawberry.ID → uuid.UUID,
    UNSET/SENTINEL mapping, or enum type coercion — define to_pydantic() in the
    class body. A user-defined to_pydantic() takes precedence over Strawberry's
    auto-generated one.

    Always declare fields explicitly in the class body. Using all_fields=True is
    not supported because it prevents mypy from seeing the attributes and causes
    strawberry to use pydantic field defaults (including SENTINEL) verbatim in the
    GQL schema, which breaks schema printing for non-scalar default types.

    The description param is accepted for backward compatibility but the
    canonical description is always built from BackendAIGQLMeta.

    When one_of=True, injects the @oneOf directive so exactly one field must
    be provided (mirrors @strawberry.input(one_of=True) behaviour).
    """
    desc = f"Added in {meta.added_version}. {meta.description or (description or '')}"
    if meta.deprecated_version is not None:
        hint = f" Use {meta.deprecation_hint}." if meta.deprecation_hint else ""
        desc += f" Deprecated since {meta.deprecated_version}.{hint}"
    if one_of:
        directives = (*directives, OneOf())
    return strawberry.experimental.pydantic.input(
        model=model,
        fields=fields,
        name=name,
        description=desc,
        directives=directives,
        use_pydantic_alias=use_pydantic_alias,
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
