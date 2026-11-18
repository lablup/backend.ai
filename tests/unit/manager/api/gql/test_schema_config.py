"""The default resolver of the manager GQL schemas rejects a DTO value left `MISSING`."""

from __future__ import annotations

import enum
import uuid
from typing import Any, cast

import pytest
from pydantic import BaseModel, ConfigDict
from strawberry import Info, Schema
from strawberry.tools import create_type
from strawberry.types.execution import ExecutionResult

from ai.backend.common.meta import BackendAIGQLMeta
from ai.backend.common.tristate.unset import UNSET, Unset
from ai.backend.manager.api.gql.decorators import (
    gql_enum,
    gql_field,
    gql_pydantic_type,
    gql_root_field,
)
from ai.backend.manager.api.gql.extensions.exception_handler import GQLExceptionHandlerExtension
from ai.backend.manager.api.gql.pydantic_compat import (
    MissingKeepingFromPydantic,
    PydanticOutputMixin,
)
from ai.backend.manager.api.gql.schema import public_schema, schema
from ai.backend.manager.api.gql.schema_config import GQLSchemaConfig, MissingRejectingResolver
from ai.backend.manager.errors.api import GraphQLFieldNotSelected

META = BackendAIGQLMeta(added_version="26.9.0", description="Probe type.")


@gql_enum(META, name="ProbeColor")
class ProbeColor(enum.StrEnum):
    RED = "red"
    BLUE = "blue"


class InnerDTO(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    label: str | Unset = UNSET


class ProbeDTO(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str | None | Unset = UNSET
    id: uuid.UUID | Unset = UNSET
    color: ProbeColor | Unset = UNSET
    count: int | Unset = UNSET
    required_name: str | Unset = UNSET
    inner: InnerDTO | Unset = UNSET
    tags: list[str] | Unset = UNSET
    items: list[InnerDTO] | Unset = UNSET
    required_tags: list[str] | Unset = UNSET


@gql_pydantic_type(META, model=InnerDTO, name="ProbeInner")
class InnerGQL(PydanticOutputMixin[InnerDTO]):
    label: str | None = gql_field(description="Label.")


@gql_pydantic_type(META, model=ProbeDTO, name="Probe")
class ProbeGQL(PydanticOutputMixin[ProbeDTO]):
    name: str | None = gql_field(description="Name.")
    id: uuid.UUID | None = gql_field(description="ID.")
    color: ProbeColor | None = gql_field(description="Color.")
    count: int | None = gql_field(description="Count.")
    required_name: str = gql_field(description="Non-null name.")
    inner: InnerGQL | None = gql_field(description="Nested object.")
    tags: list[str] | None = gql_field(description="Scalar list.")
    items: list[InnerGQL] | None = gql_field(description="Object list.")
    required_tags: list[str] = gql_field(description="Non-null scalar list.")


class PlainDTO(BaseModel):
    label: str


@gql_pydantic_type(META, model=PlainDTO, name="ProbePlain")
class PlainGQL(PydanticOutputMixin[PlainDTO]):
    label: str = gql_field(description="Label.")


@gql_root_field(META)
def probe(info: Info) -> ProbeGQL | None:
    return ProbeGQL.from_pydantic(info.context["dto"])


@gql_root_field(META)
def required_probe(info: Info) -> ProbeGQL:
    return ProbeGQL.from_pydantic(info.context["dto"])


_FULL = ProbeDTO(
    name="alpha",
    id=uuid.UUID("11111111-2222-3333-4444-555555555555"),
    color=ProbeColor.BLUE,
    count=7,
    required_name="beta",
    inner=InnerDTO(label="gamma"),
    tags=["t"],
    items=[InnerDTO(label="i")],
    required_tags=["r"],
)
_NOT_SELECTED_CODE = str(GraphQLFieldNotSelected().error_code())


@pytest.fixture
def probe_schema() -> Schema:
    return Schema(
        query=create_type("Query", [cast(Any, probe), cast(Any, required_probe)]),
        config=GQLSchemaConfig(auto_camel_case=True),
        extensions=[GQLExceptionHandlerExtension],
    )


async def _execute(probe_schema: Schema, query: str, dto: ProbeDTO) -> ExecutionResult:
    return await probe_schema.execute(query, context_value={"dto": dto})


def _error_paths(result: ExecutionResult) -> list[list[str | int]]:
    return [error.path or [] for error in result.errors or []]


class TestFromPydantic:
    @pytest.mark.parametrize(
        "field", ["name", "id", "color", "count", "required_name", "inner", "tags", "items"]
    )
    def test_a_missing_value_is_kept_on_the_gql_object(self, field: str) -> None:
        converted = ProbeGQL.from_pydantic(_FULL.model_copy(update={field: UNSET}))
        assert getattr(converted, field) is UNSET

    def test_a_dto_without_missing_converts_as_before(self) -> None:
        converted = ProbeGQL.from_pydantic(_FULL)
        assert converted.inner == InnerGQL(label="gamma")
        assert converted.items == [InnerGQL(label="i")]
        assert converted.tags == ["t"]

    def test_a_type_without_unset_fields_keeps_strawberry_conversion(self) -> None:
        assert not isinstance(cast(Any, PlainGQL).from_pydantic, MissingKeepingFromPydantic)


class TestMissingFieldIsRejected:
    async def test_a_missing_field_is_null_with_an_error_and_siblings_stay(
        self, probe_schema: Schema
    ) -> None:
        dto = _FULL.model_copy(update={"name": UNSET})
        result = await _execute(probe_schema, "{ probe { name count } }", dto)
        assert result.data == {"probe": {"name": None, "count": 7}}
        assert result.errors is not None
        assert _error_paths(result) == [["probe", "name"]]
        assert result.errors[0].extensions == {"code": _NOT_SELECTED_CODE}
        assert "name" in result.errors[0].message

    @pytest.mark.parametrize("field", ["name", "id", "color", "count"])
    async def test_every_scalar_kind_is_rejected(self, probe_schema: Schema, field: str) -> None:
        dto = _FULL.model_copy(update={field: UNSET})
        result = await _execute(probe_schema, "{ probe { name id color count } }", dto)
        assert result.data is not None
        assert result.data["probe"][field] is None
        assert _error_paths(result) == [["probe", field]]


class TestSelectedValuesAreUnchanged:
    async def test_values_resolve_as_before(self, probe_schema: Schema) -> None:
        result = await _execute(
            probe_schema,
            "{ probe { name id color count requiredName inner { label } tags items { label }"
            " requiredTags } }",
            _FULL,
        )
        assert result.errors is None
        assert result.data == {
            "probe": {
                "name": "alpha",
                "id": "11111111-2222-3333-4444-555555555555",
                "color": "BLUE",
                "count": 7,
                "requiredName": "beta",
                "inner": {"label": "gamma"},
                "tags": ["t"],
                "items": [{"label": "i"}],
                "requiredTags": ["r"],
            }
        }

    async def test_none_stays_null_without_an_error(self, probe_schema: Schema) -> None:
        dto = _FULL.model_copy(update={"name": None})
        result = await _execute(probe_schema, "{ probe { name } }", dto)
        assert result.errors is None
        assert result.data == {"probe": {"name": None}}

    async def test_an_unqueried_missing_field_raises_nothing(self, probe_schema: Schema) -> None:
        dto = _FULL.model_copy(update={"name": UNSET})
        result = await _execute(probe_schema, "{ probe { count } }", dto)
        assert result.errors is None
        assert result.data == {"probe": {"count": 7}}


class TestNestedObject:
    async def test_a_missing_field_inside_a_nested_object(self, probe_schema: Schema) -> None:
        dto = _FULL.model_copy(update={"inner": InnerDTO()})
        result = await _execute(probe_schema, "{ probe { count inner { label } } }", dto)
        assert result.data == {"probe": {"count": 7, "inner": {"label": None}}}
        assert _error_paths(result) == [["probe", "inner", "label"]]

    @pytest.mark.parametrize(
        ("field", "query"),
        [("inner", "inner { label }"), ("items", "items { label }"), ("tags", "tags")],
    )
    async def test_a_missing_object_or_list(
        self, probe_schema: Schema, field: str, query: str
    ) -> None:
        dto = _FULL.model_copy(update={field: UNSET})
        result = await _execute(probe_schema, f"{{ probe {{ count {query} }} }}", dto)
        assert result.data == {"probe": {"count": 7, field: None}}
        assert _error_paths(result) == [["probe", field]]


class TestNonNullField:
    async def test_null_moves_up_to_the_nullable_parent(self, probe_schema: Schema) -> None:
        dto = _FULL.model_copy(update={"required_name": UNSET})
        result = await _execute(probe_schema, "{ probe { count requiredName } }", dto)
        assert result.data == {"probe": None}
        assert _error_paths(result) == [["probe", "requiredName"]]

    async def test_a_non_null_list_moves_null_up_too(self, probe_schema: Schema) -> None:
        dto = _FULL.model_copy(update={"required_tags": UNSET})
        result = await _execute(probe_schema, "{ probe { count requiredTags } }", dto)
        assert result.data == {"probe": None}
        assert _error_paths(result) == [["probe", "requiredTags"]]

    async def test_null_reaches_data_under_a_non_null_root(self, probe_schema: Schema) -> None:
        dto = _FULL.model_copy(update={"required_name": UNSET})
        result = await _execute(probe_schema, "{ requiredProbe { count requiredName } }", dto)
        assert result.data is None
        assert _error_paths(result) == [["requiredProbe", "requiredName"]]


class TestManagerSchemasUseTheResolver:
    @pytest.mark.parametrize("built", [schema, public_schema], ids=["schema", "public_schema"])
    def test_the_default_resolver_rejects_missing(self, built: Schema) -> None:
        assert isinstance(built.config.default_resolver, MissingRejectingResolver)
