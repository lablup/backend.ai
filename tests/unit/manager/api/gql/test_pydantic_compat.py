"""Tests for PydanticNodeMixin and strawberry.experimental.pydantic compatibility.

Verifies:
- PydanticNodeMixin converts Pydantic DTOs to Strawberry types correctly
- Enum mapping via value-based conversion
- Nested Pydantic model recursive conversion
- PASSWORD_PLACEHOLDER-style extra overrides
- Sentinel/UNSET bridging for experimental.pydantic.input
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, cast
from uuid import uuid4

import strawberry
from pydantic import BaseModel, Field
from strawberry.relay import Node, NodeID

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.dto.manager.v2.container_registry.response import (
    ContainerRegistryNode,
)
from ai.backend.manager.api.adapters.container_registry import ContainerRegistryAdapter
from ai.backend.manager.api.adapters.registry import Adapters
from ai.backend.manager.api.gql.container_registry.types import (
    ContainerRegistryGQL,
    ContainerRegistryTypeGQL,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.defs import PASSWORD_PLACEHOLDER

# ---- Test fixtures: Pydantic DTOs ----


class ItemType(StrEnum):
    BOOK = "book"
    TOOL = "tool"


class SubInfo(BaseModel):
    label: str = Field(description="A label")
    count: int = Field(default=0, description="Count")


class ItemNode(BaseModel):
    id: str = Field(description="Unique ID")
    name: str = Field(description="Item name")
    type: ItemType = Field(description="Item type")
    sub: SubInfo | None = Field(default=None, description="Optional sub-info")
    tags: list[str] | None = Field(default=None, description="Tags")
    extra_data: dict[str, Any] | None = Field(default=None, description="Extra JSON")


# ---- Test fixtures: Strawberry types ----


@strawberry.enum(name="ItemType")
class ItemTypeGQL(StrEnum):
    BOOK = "book"
    TOOL = "tool"


@strawberry.type(name="SubInfo")
class SubInfoGQL:
    label: str = strawberry.field(description="A label")
    count: int = strawberry.field(description="Count", default=0)

    @classmethod
    def from_pydantic(cls, dto: SubInfo) -> SubInfoGQL:
        return cls(label=dto.label, count=dto.count)


@strawberry.type(name="ItemV2")
class ItemGQL(PydanticNodeMixin[Any]):
    id: NodeID[str] = strawberry.field(description="Relay ID")
    name: str = strawberry.field(description="Item name")
    type: ItemTypeGQL = strawberry.field(description="Item type")
    sub: SubInfoGQL | None = strawberry.field(description="Sub info", default=None)
    tags: list[str] | None = strawberry.field(description="Tags", default=None)
    extra_data: strawberry.scalars.JSON | None = strawberry.field(
        description="Extra JSON", default=None
    )


class TestPydanticNodeMixin:
    def test_basic_conversion(self) -> None:
        item_id = "test-id-123"
        dto = ItemNode(id=item_id, name="My Book", type=ItemType.BOOK)

        gql = ItemGQL.from_pydantic(dto)

        assert gql.id == item_id
        assert gql.name == "My Book"
        assert gql.type == ItemTypeGQL.BOOK
        assert gql.sub is None
        assert gql.tags is None

    def test_enum_conversion(self) -> None:
        dto = ItemNode(id="e1", name="Wrench", type=ItemType.TOOL)

        gql = ItemGQL.from_pydantic(dto)

        assert gql.type == ItemTypeGQL.TOOL
        assert isinstance(gql.type, ItemTypeGQL)

    def test_nested_model_conversion(self) -> None:
        dto = ItemNode(
            id="n1",
            name="Tagged Book",
            type=ItemType.BOOK,
            sub=SubInfo(label="chapter-1", count=42),
        )

        gql = ItemGQL.from_pydantic(dto)

        assert gql.sub is not None
        assert isinstance(gql.sub, SubInfoGQL)
        assert gql.sub.label == "chapter-1"
        assert gql.sub.count == 42

    def test_none_nested_model(self) -> None:
        dto = ItemNode(id="n2", name="No Sub", type=ItemType.BOOK, sub=None)

        gql = ItemGQL.from_pydantic(dto)

        assert gql.sub is None

    def test_list_field(self) -> None:
        dto = ItemNode(
            id="l1",
            name="Tagged",
            type=ItemType.BOOK,
            tags=["python", "graphql"],
        )

        gql = ItemGQL.from_pydantic(dto)

        assert gql.tags == ["python", "graphql"]

    def test_extra_overrides(self) -> None:
        dto = ItemNode(
            id="x1",
            name="Secret Item",
            type=ItemType.TOOL,
        )

        gql = ItemGQL.from_pydantic(dto, extra={"name": "MASKED"})

        assert gql.name == "MASKED"

    def test_custom_id_field(self) -> None:
        """from_pydantic with id_field pointing to a different field."""

        class NameKeyNode(BaseModel):
            key: str = Field(description="Primary key is name")
            value: int = Field(description="Some value")

        @strawberry.type(name="NameKeyV2")
        class NameKeyGQL(PydanticNodeMixin[Any]):
            id: NodeID[str] = strawberry.field(description="Relay ID")
            value: int = strawberry.field(description="Some value")

        dto = NameKeyNode(key="my-domain", value=99)
        gql = NameKeyGQL.from_pydantic(dto, id_field="key")

        assert gql.id == "my-domain"
        assert gql.value == 99

    def test_dict_passthrough(self) -> None:
        dto = ItemNode(
            id="d1",
            name="With Extra",
            type=ItemType.BOOK,
            extra_data={"foo": "bar", "nested": [1, 2, 3]},
        )

        gql = ItemGQL.from_pydantic(dto)

        assert cast(dict[str, Any], gql.extra_data) == {"foo": "bar", "nested": [1, 2, 3]}

    def test_inherits_node(self) -> None:
        """PydanticNodeMixin inherits Node, so concrete types only need one parent."""
        assert issubclass(PydanticNodeMixin, Node)
        assert issubclass(ItemGQL, Node)

    def test_mro_does_not_duplicate_node(self) -> None:
        """Node appears exactly once in MRO despite PydanticNodeMixin inheriting it."""
        mro = ItemGQL.__mro__
        node_count = sum(1 for cls in mro if cls is Node)
        assert node_count == 1

    def test_strawberry_definition_accessible(self) -> None:
        """Strawberry field introspection should work on mixin types."""
        assert hasattr(ItemGQL, "__strawberry_definition__")
        field_names = {f.name for f in ItemGQL.__strawberry_definition__.fields}
        assert "name" in field_names
        assert "type" in field_names
        assert "id" in field_names


class TestExperimentalPydanticInput:
    """Verify strawberry.experimental.pydantic.input works with our Pydantic models."""

    def test_simple_input_all_fields(self) -> None:
        """All fields from Pydantic model are mapped to GQL input."""

        class CreateItemInput(BaseModel):
            name: str = Field(description="Item name")
            type: str = Field(description="Item type")

        @strawberry.experimental.pydantic.input(
            model=CreateItemInput,
            all_fields=True,
            name="CreateItemInput",
        )
        class CreateItemInputGQL:
            pass

        gql_input = CreateItemInputGQL(name="Test", type="book")
        pydantic_obj = gql_input.to_pydantic()

        assert isinstance(pydantic_obj, CreateItemInput)
        assert pydantic_obj.name == "Test"
        assert pydantic_obj.type == "book"

    def test_optional_field_default_none(self) -> None:
        """Optional fields with None default work correctly."""

        class UpdateSimpleInput(BaseModel):
            name: str | None = Field(default=None, description="Updated name")
            count: int | None = Field(default=None, description="Updated count")

        @strawberry.experimental.pydantic.input(
            model=UpdateSimpleInput,
            all_fields=True,
            name="UpdateSimpleInput",
        )
        class UpdateSimpleInputGQL:
            pass

        # Only set one field
        gql_input = UpdateSimpleInputGQL(name="New Name")
        pydantic_obj = gql_input.to_pydantic()

        assert pydantic_obj.name == "New Name"
        assert pydantic_obj.count is None

    def test_field_set_to_null_passes_none(self) -> None:
        """Explicitly setting a field to None passes None to Pydantic."""

        class ClearableInput(BaseModel):
            description: str | None = Field(default=None, description="Description")

        @strawberry.experimental.pydantic.input(
            model=ClearableInput,
            all_fields=True,
            name="ClearableInput",
        )
        class ClearableInputGQL:
            pass

        gql_input = ClearableInputGQL(description=None)
        pydantic_obj = gql_input.to_pydantic()

        assert pydantic_obj.description is None

    def test_from_pydantic_roundtrip(self) -> None:
        """from_pydantic and to_pydantic form a roundtrip."""

        class RoundtripModel(BaseModel):
            name: str = Field(description="Name")
            active: bool = Field(default=True, description="Active")

        @strawberry.experimental.pydantic.input(
            model=RoundtripModel,
            all_fields=True,
            name="RoundtripInput",
        )
        class RoundtripInputGQL:
            pass

        original = RoundtripModel(name="foo", active=False)
        gql = RoundtripInputGQL.from_pydantic(original)
        back = gql.to_pydantic()

        assert back.name == "foo"
        assert back.active is False


class TestContainerRegistryGQLFromPydantic:
    """Verify ContainerRegistryGQL.from_pydantic() with real DTO types."""

    def test_from_pydantic_basic(self) -> None:
        reg_id = uuid4()
        dto = ContainerRegistryNode(
            id=reg_id,
            url="https://registry.example.com",
            registry_name="test-registry",
            type=ContainerRegistryType.DOCKER,
            project="my-project",
            username="admin",
            ssl_verify=True,
            is_global=False,
            extra={"key": "value"},
        )

        gql = ContainerRegistryGQL.from_pydantic(dto)

        assert gql.id == str(reg_id)
        assert gql.url == "https://registry.example.com"
        assert gql.registry_name == "test-registry"
        assert gql.type == ContainerRegistryTypeGQL.DOCKER
        assert gql.project == "my-project"
        assert gql.username == "admin"
        assert gql.password is None  # DTO has no password field
        assert gql.ssl_verify is True
        assert gql.is_global is False
        assert cast(dict[str, Any], gql.extra) == {"key": "value"}

    def test_from_pydantic_with_password_extra(self) -> None:
        dto = ContainerRegistryNode(
            id=uuid4(),
            url="https://registry.example.com",
            registry_name="test",
            type=ContainerRegistryType.HARBOR2,
        )

        gql = ContainerRegistryGQL.from_pydantic(dto, extra={"password": PASSWORD_PLACEHOLDER})

        assert gql.password == PASSWORD_PLACEHOLDER

    def test_only_inherits_pydantic_node_mixin(self) -> None:
        """ContainerRegistryGQL inherits only PydanticNodeMixin (which carries Node)."""
        assert issubclass(ContainerRegistryGQL, PydanticNodeMixin)
        assert issubclass(ContainerRegistryGQL, Node)

    def test_mro_no_duplicate_node(self) -> None:
        mro = ContainerRegistryGQL.__mro__
        node_count = sum(1 for cls in mro if cls is Node)
        assert node_count == 1

    def test_strawberry_definition_intact(self) -> None:
        assert hasattr(ContainerRegistryGQL, "__strawberry_definition__")
        field_names = {f.name for f in ContainerRegistryGQL.__strawberry_definition__.fields}
        assert "url" in field_names
        assert "type" in field_names
        assert "password" in field_names


class TestAdaptersRegistry:
    """Verify Adapters registry can be created."""

    def test_create_registry(self) -> None:
        adapters = Adapters.create(processors=None, auth_config=None)  # type: ignore[arg-type]
        assert isinstance(adapters, Adapters)

    def test_container_registry_adapter_available(self) -> None:
        adapters = Adapters.create(processors=None, auth_config=None)  # type: ignore[arg-type]
        assert isinstance(adapters.container_registry, ContainerRegistryAdapter)
