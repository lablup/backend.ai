"""Strawberry-Pydantic compatibility utilities.

Provides PydanticNodeMixin for converting Pydantic DTO v2 response models
to Strawberry Relay Node types.  Concrete GQL types inherit only this mixin;
it carries the Node interface through to the subclass.

Usage::

    @strawberry.type(name="FooV2")
    class FooGQL(PydanticNodeMixin):
        id: NodeID[str]
        name: str = strawberry.field(description="...")

    # Convert from DTO:
    node = FooGQL.from_pydantic(foo_dto, id_field="id")
"""

from __future__ import annotations

import dataclasses
import types
from enum import Enum
from typing import Any, Self, Union, get_args, get_origin, get_type_hints

from pydantic import BaseModel
from strawberry.relay import Node
from strawberry.types.base import StrawberryObjectDefinition


class PydanticNodeMixin(Node):
    """Relay Node mixin with ``from_pydantic()`` conversion.

    Inherits ``Node`` so that concrete types only need::

        class FooGQL(PydanticNodeMixin): ...

    Strawberry's ``_get_interfaces()`` walks the MRO and appends every class
    whose ``__strawberry_definition__.is_interface`` is ``True``.  Without the
    override below, both ``PydanticNodeMixin`` and ``Node`` would contribute
    the Node interface, causing a schema validation error
    (``"Type X can only implement Node once."``).

    By giving this class its own ``__strawberry_definition__`` with
    ``is_interface=False``, the MRO scan skips it and only picks up
    ``Node`` itself — so the interface is registered exactly once.
    """

    __strawberry_definition__ = StrawberryObjectDefinition(
        name="PydanticNodeMixin",
        is_input=False,
        is_interface=False,
        origin=object,
        interfaces=[],
        extend=False,
        description=None,
        directives=(),
        is_type_of=None,
        resolve_type=None,
        fields=[],
    )

    @classmethod
    def from_pydantic(
        cls,
        dto: BaseModel,
        *,
        id_field: str = "id",
        extra: dict[str, Any] | None = None,
    ) -> Self:
        """Convert a Pydantic DTO instance to this Strawberry Node type.

        Args:
            dto: Pydantic model instance (e.g. ``ContainerRegistryNode``).
            id_field: Name of the field on *dto* to use as the relay ``id``.
                The value is converted to ``str`` for ``NodeID[str]``.
            extra: Additional keyword arguments to pass to the constructor,
                overriding any auto-mapped fields.  Useful for fields that
                require special handling (e.g. PASSWORD_PLACEHOLDER masking).

        Returns:
            An instance of the Strawberry type (``cls``).

        Mapping rules:
            * ``id`` ← ``str(getattr(dto, id_field))``
            * Pydantic sub-models with a corresponding Strawberry type that has
              ``from_pydantic`` → recursively converted.
            * Enums → mapped via GQL enum's ``from_enum()`` if available,
              otherwise passed through (Strawberry handles stdlib enums).
            * Fields not present on the DTO are skipped (left to their
              Strawberry default, typically ``UNSET`` or resolver-provided).
        """
        extra = extra or {}

        # Resolve string annotations (from `from __future__ import annotations`)
        # into actual types. include_extras preserves Annotated wrappers.
        resolved_hints = get_type_hints(cls, include_extras=True)

        kwargs: dict[str, Any] = {}
        for field in dataclasses.fields(cls):  # type: ignore[arg-type]
            field_name = field.name
            # Extra overrides take priority
            if field_name in extra:
                kwargs[field_name] = extra[field_name]
                continue

            # The ``id`` field is always sourced from id_field
            if field_name == "id":
                kwargs["id"] = str(getattr(dto, id_field))
                continue

            # Skip fields that don't exist on the DTO
            if not hasattr(dto, field_name):
                continue

            value = getattr(dto, field_name)
            hint = resolved_hints.get(field_name)
            kwargs[field_name] = _convert_value(value, hint)

        return cls(**kwargs)


def _convert_value(value: Any, type_hint: Any) -> Any:
    """Convert a single value from Pydantic domain to Strawberry domain."""
    if value is None:
        return None

    # Enum: if the strawberry field type has from_enum, use it
    if isinstance(value, Enum):
        field_type = _unwrap_optional(type_hint)
        if (
            field_type is not None
            and isinstance(field_type, type)
            and hasattr(field_type, "from_enum")
        ):
            return field_type.from_enum(value)
        return value

    # Nested Pydantic model: recursively convert if strawberry type has from_pydantic
    if isinstance(value, BaseModel):
        field_type = _unwrap_optional(type_hint)
        if (
            field_type is not None
            and isinstance(field_type, type)
            and hasattr(field_type, "from_pydantic")
        ):
            return field_type.from_pydantic(value)
        return value

    # List of Pydantic models or enums
    if isinstance(value, list) and value:
        first = value[0]
        item_type = _unwrap_list_item(type_hint)
        if isinstance(first, BaseModel):
            if (
                item_type is not None
                and isinstance(item_type, type)
                and hasattr(item_type, "from_pydantic")
            ):
                return [item_type.from_pydantic(item) for item in value]
        elif isinstance(first, Enum):
            if (
                item_type is not None
                and isinstance(item_type, type)
                and hasattr(item_type, "from_enum")
            ):
                return [item_type.from_enum(item) for item in value]

    return value


def _unwrap_optional(type_hint: Any) -> Any:
    """Unwrap Optional[X] / X | None to get X."""
    if type_hint is None:
        return None

    origin = get_origin(type_hint)

    # Union (Optional[X] = Union[X, None] or X | None)
    # Python 3.10+ `X | None` produces types.UnionType, not typing.Union
    if origin is Union or isinstance(type_hint, types.UnionType):
        args = get_args(type_hint)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
        return None

    return type_hint


def _unwrap_list_item(type_hint: Any) -> Any:
    """Unwrap Optional[list[X]] or list[X] to get X."""
    if type_hint is None:
        return None

    inner = _unwrap_optional(type_hint)
    if inner is None:
        return None

    origin = get_origin(inner)
    if origin is list:
        args = get_args(inner)
        if args:
            return args[0]

    return None
