"""Strawberry-Pydantic compatibility utilities.

Provides mixins for converting between Pydantic DTO v2 models and Strawberry types:

- PydanticNodeMixin  — for Relay Node types (carries the Node interface, handles ``id`` field).
- PydanticOutputMixin — for non-Node output types (payloads, nested structs, no id handling).
  DEPRECATED: prefer ``@gql_pydantic_type(model=...)`` for new types.
- PydanticInputMixin — for input types with auto ``to_pydantic()`` via reflection.

Usage::

    # Relay Node type
    @gql_node_type(meta)
    class FooGQL(PydanticNodeMixin[FooNode]):
        id: NodeID[str]
        name: str = strawberry.field(description="...")

    # Non-Node output type (payload, nested struct)
    @gql_pydantic_type(meta, model=FooPayloadDTO)
    class FooPayloadGQL(PydanticOutputMixin[FooPayloadDTO]):
        result_id: strawberry.ID
        name: str = strawberry.field(description="...")

    # Input type with auto to_pydantic()
    @gql_pydantic_input(meta)
    class CreateFooInputGQL(PydanticInputMixin[CreateFooInputDTO]):
        name: str

    # Convert from DTO:
    node = FooGQL.from_pydantic(foo_dto, id_field="id")
    payload = FooPayloadGQL.from_pydantic(foo_payload_dto)

    # Convert to DTO:
    dto = create_input_gql.to_pydantic()
"""

from __future__ import annotations

import dataclasses
import types
from decimal import Decimal
from enum import Enum
from typing import Any, ClassVar, Self, Union, cast, final, get_args, get_origin, get_type_hints
from uuid import UUID

from pydantic import BaseModel
from strawberry import ID as StrawberryID
from strawberry import UNSET
from strawberry.relay import Node
from strawberry.types.base import StrawberryObjectDefinition


def _from_pydantic_kwargs(
    cls: type,
    dto: BaseModel,
    extra: dict[str, Any],
    skip_fields: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """Build constructor kwargs by mapping DTO fields to GQL class fields.

    Shared by both PydanticNodeMixin and PydanticOutputMixin.
    Recursively converts nested Pydantic models and enums via _convert_value.
    """
    resolved_hints = get_type_hints(cls, include_extras=True)
    kwargs: dict[str, Any] = {}
    for field in dataclasses.fields(cls):
        field_name = field.name
        if field_name in skip_fields:
            continue
        if field_name in extra:
            kwargs[field_name] = extra[field_name]
            continue
        if not hasattr(dto, field_name):
            continue
        value = getattr(dto, field_name)
        hint = resolved_hints.get(field_name)
        kwargs[field_name] = _convert_value(value, hint)
    return kwargs


class PydanticNodeMixin[T_DTO: BaseModel](Node):
    """Relay Node mixin with ``from_pydantic()`` conversion.

    Inherits ``Node`` so that concrete types only need::

        class FooGQL(PydanticNodeMixin[FooDTONode]): ...

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

    @final
    @classmethod
    def from_pydantic(
        cls,
        dto: T_DTO,
        extra: dict[str, Any] | None = None,
        *,
        id_field: str = "id",
    ) -> Self:
        """Convert a Pydantic DTO instance to this Strawberry Node type.

        This method is ``@final``: subclasses must NOT override it.
        Use the ``extra`` parameter at the call site to override individual
        fields (e.g. masking, resolver-provided values).

        Args:
            dto: Pydantic model instance (e.g. ``ContainerRegistryNode``).
            id_field: Name of the field on *dto* to use as the relay ``id``.
                The value is converted to ``str`` for ``NodeID[str]``.
            extra: Additional keyword arguments to pass to the constructor,
                overriding any auto-mapped fields.

        Returns:
            An instance of the Strawberry type (``cls``).

        Mapping rules:
            * ``id`` ← ``str(getattr(dto, id_field))``
            * ``uuid.UUID`` → ``strawberry.ID`` when the GQL field is typed as
              ``strawberry.ID``.
            * Pydantic sub-models → recursively converted via ``from_pydantic``
              on the corresponding GQL field type.
            * Enums → converted via ``GQLEnumType(dto_enum.value)`` when types differ,
              or passed through when the types match.
            * Fields not present on the DTO are skipped (left to their
              Strawberry default, typically ``UNSET`` or resolver-provided).
        """
        combined_extra = dict(extra or {})
        kwargs = _from_pydantic_kwargs(cls, dto, combined_extra, skip_fields=frozenset({"id"}))

        # Always set the relay ``id`` first.  Strawberry's Node interface may
        # remove NodeID[str] from dataclasses.fields(), so we cannot rely on
        # the field loop to encounter it.
        if "id" in combined_extra:
            kwargs["id"] = combined_extra["id"]
        else:
            kwargs["id"] = str(getattr(dto, id_field))

        return cls(**kwargs)


class PydanticOutputMixin[T_DTO: BaseModel]:
    """Non-Node GQL output type mixin with ``from_pydantic()`` conversion.

    DEPRECATED: Do not use in new code.
    For non-Node output types backed by a Pydantic DTO, use
    ``@gql_pydantic_type(model=...)`` instead.

    Use for non-Relay-Node output types (mutation payloads, nested structs)
    that are backed by a v2 Pydantic DTO.  Unlike PydanticNodeMixin this class
    does NOT inherit ``Node`` and does NOT handle the Relay ``id`` field.

    Mapping rules are identical to PydanticNodeMixin.from_pydantic() except
    there is no ``id`` field bootstrapping.
    """

    @final
    @classmethod
    def from_pydantic(
        cls,
        dto: T_DTO,
        extra: dict[str, Any] | None = None,
    ) -> Self:
        """Convert a Pydantic DTO instance to this Strawberry output type.

        This method is ``@final``: subclasses must NOT override it.
        Use the ``extra`` parameter at the call site to override individual
        fields.

        Args:
            dto: Pydantic model instance.
            extra: Additional keyword arguments, overriding auto-mapped fields.

        Returns:
            An instance of the Strawberry type (``cls``).

        Mapping rules are identical to ``PydanticNodeMixin.from_pydantic()``
        except there is no ``id`` field bootstrapping.
        """
        combined_extra = dict(extra or {})
        kwargs = _from_pydantic_kwargs(cls, dto, combined_extra)
        return cls(**kwargs)


class PydanticInputMixin[T_DTO: BaseModel]:
    """Input type mixin with auto ``to_pydantic()`` conversion via reflection.

    Use with ``@gql_pydantic_input(meta)`` (``model=None``) to get automatic
    ``to_pydantic()`` without Strawberry's pydantic input machinery. This avoids
    the Strawberry issue where ``@strawberry.experimental.pydantic.input``
    overwrites any inherited ``to_pydantic()`` via ``__qualname__`` check.

    Usage::

        @gql_pydantic_input(meta)
        class CreateFooInputGQL(PydanticInputMixin[CreateFooInputDTO]):
            name: str
            count: int
            # No manual to_pydantic() needed

    Conversion rules (GQL → DTO):
        * ``strawberry.UNSET`` → field is skipped (DTO default is used).
        * ``strawberry.ID`` / ``str`` → ``uuid.UUID`` when the DTO field is UUID.
        * GQL enum → DTO enum via ``.value`` coercion.
        * Nested ``PydanticInputMixin`` → recursively calls ``.to_pydantic()``.
        * ``list`` → list comprehension with per-item recursive conversion.
        * All other values → passed through unchanged.
    """

    __dto_type__: ClassVar[type]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        for base in getattr(cls, "__orig_bases__", ()):
            if get_origin(base) is PydanticInputMixin:
                args = get_args(base)
                if args and isinstance(args[0], type):
                    cls.__dto_type__ = args[0]
                    return

    @final
    def to_pydantic(self) -> T_DTO:
        """Convert this GQL input to the corresponding Pydantic DTO.

        This method is ``@final``: subclasses must NOT override it.
        The DTO type is inferred from the generic parameter ``T_DTO``.
        """
        dto_cls = self.__class__.__dto_type__
        kwargs = _to_pydantic_kwargs(self, dto_cls)
        return cast(T_DTO, dto_cls(**kwargs))


def _convert_value(value: Any, type_hint: Any) -> Any:
    """Convert a single value from Pydantic domain to Strawberry domain."""
    if value is None:
        return None

    # uuid.UUID → strawberry.ID when the GQL field is typed as strawberry.ID
    if isinstance(value, UUID):
        field_type = _unwrap_optional(type_hint)
        if field_type is StrawberryID:
            return StrawberryID(str(value))
        return value

    # Enum → GQL enum: handles same-type, cross-type Enum, and str/int → Enum.
    field_type = _unwrap_optional(type_hint)
    if field_type is not None and isinstance(field_type, type) and issubclass(field_type, Enum):
        if isinstance(value, field_type):
            return value  # already the correct enum type
        if isinstance(value, Enum):
            # Different Enum types (e.g. ProjectTypeDTO → ProjectTypeEnum) — convert by value.
            try:
                return field_type(value.value)
            except (ValueError, KeyError):
                return value
        # str/int → Enum (DTO stores raw value, GQL field expects an enum)
        try:
            return field_type(value)
        except (ValueError, KeyError):
            return value

    # str/int/float → Decimal when the GQL field expects Decimal
    field_type = _unwrap_optional(type_hint)
    if field_type is Decimal and isinstance(value, (str, int, float)):
        return Decimal(str(value))

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

    # List of Pydantic models, enums, or raw values needing enum conversion
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
        elif item_type is not None and isinstance(item_type, type) and issubclass(item_type, Enum):
            # list[Enum] or list[str/int] → list[GQL enum]
            def _to_enum(item: Any) -> Any:
                if isinstance(item, item_type):
                    return item
                raw = item.value if isinstance(item, Enum) else item
                try:
                    return item_type(raw)
                except (ValueError, KeyError):
                    return item

            return [_to_enum(item) for item in value]

    return value


def _to_pydantic_kwargs(gql_instance: Any, dto_cls: type) -> dict[str, Any]:
    """Build DTO constructor kwargs from a GQL input instance.

    Skips UNSET values and GQL-only fields not present in the DTO.
    Converts strawberry.ID → UUID, enums, and nested PydanticInputMixin
    instances recursively.
    """
    dto_hints = get_type_hints(dto_cls, include_extras=True)
    kwargs: dict[str, Any] = {}
    for field in dataclasses.fields(gql_instance.__class__):
        field_name = field.name
        value = getattr(gql_instance, field_name)
        if value is UNSET:
            continue
        if field_name not in dto_hints:
            continue
        dto_hint = dto_hints.get(field_name)
        kwargs[field_name] = _convert_input_value(value, dto_hint)
    return kwargs


def _convert_input_value(value: Any, dto_hint: Any) -> Any:
    """Convert a single value from Strawberry GQL input to Pydantic domain."""
    if value is None:
        return None

    dto_field_type = _unwrap_optional(dto_hint)

    # strawberry.ID is NewType("ID", str) — at runtime it is just a str.
    # Convert str → UUID when the DTO field expects UUID.
    if isinstance(value, str) and dto_field_type is UUID:
        return UUID(value)

    # GQL enum → DTO enum via .value coercion
    if isinstance(value, Enum):
        if (
            dto_field_type is not None
            and isinstance(dto_field_type, type)
            and issubclass(dto_field_type, Enum)
        ):
            if isinstance(value, dto_field_type):
                return value
            try:
                return dto_field_type(value.value)
            except (ValueError, KeyError):
                return value
        return value

    # Nested PydanticInputMixin → to_pydantic() recursively
    if isinstance(value, PydanticInputMixin):
        return value.to_pydantic()

    # list → convert each item
    if isinstance(value, list):
        item_type = _unwrap_list_item(dto_hint)
        return [_convert_input_value(item, item_type) for item in value]

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
