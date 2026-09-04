from __future__ import annotations

import json

from pydantic import BaseModel, ConfigDict, Field

from ai.backend.common.api_handlers import (
    UNDEFINED,
    BaseRequestModel,
    Undefined,
)


class UpdateSampleInput(BaseRequestModel):
    id: int
    region: str | Undefined | None = Field(default=UNDEFINED)
    nickname: str | Undefined | None = Field(default=UNDEFINED, alias="nickName")
    count: int | None = Field(default=1)


class CreateSampleInput(BaseRequestModel):
    name: str
    description: str | None = None


class OuterSampleInput(BaseRequestModel):
    outer_id: int
    inner: UpdateSampleInput


class PlainEquivalentModel(BaseModel):
    name: str
    description: str | None = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_by_name=True,
    )


def test_omitted_field_mode_python_no_key() -> None:
    """Omitted field: model_dump(mode='python') has no region key."""
    model = UpdateSampleInput(id=1)
    dumped = model.model_dump(mode="python")
    assert "region" not in dumped
    assert dumped["id"] == 1


def test_omitted_field_mode_json_no_key() -> None:
    """Omitted field: model_dump(mode='json') has no region key."""
    model = UpdateSampleInput(id=1)
    dumped = model.model_dump(mode="json")
    assert "region" not in dumped
    assert dumped["id"] == 1


def test_omitted_field_with_none_includes_key() -> None:
    """Omitted field: None value includes 'region': None."""
    model = UpdateSampleInput(id=1, region=None)
    dumped = model.model_dump(mode="python")
    assert "region" in dumped
    assert dumped["region"] is None


def test_omitted_field_with_value_includes_value() -> None:
    """Omitted field: a value includes the value."""
    model = UpdateSampleInput(id=1, region="us-west")
    dumped = model.model_dump(mode="python")
    assert "region" in dumped
    assert dumped["region"] == "us-west"


def test_explicit_undefined_behaves_same_as_omitted() -> None:
    """Explicit UNDEFINED: model_dump() has no region key (same as omitting)."""
    model = UpdateSampleInput(id=1, region=UNDEFINED)
    dumped = model.model_dump(mode="python")
    assert "region" not in dumped


def test_exclude_unset_true_drops_undefined_field() -> None:
    """exclude_unset=True still drops UNDEFINED field."""
    model = UpdateSampleInput(id=1)
    dumped = model.model_dump(mode="python", exclude_unset=True)
    assert "region" not in dumped


def test_by_alias_true_drops_undefined_field_under_alias() -> None:
    """by_alias=True: aliased UNDEFINED field dropped under both nickname and nickName."""
    model = UpdateSampleInput(id=1)
    dumped = model.model_dump(mode="python", by_alias=True)
    assert "nickname" not in dumped
    assert "nickName" not in dumped


def test_by_alias_and_exclude_unset_drops_undefined() -> None:
    """by_alias=True + exclude_unset=True: UNDEFINED field dropped."""
    model = UpdateSampleInput(id=1)
    dumped = model.model_dump(mode="python", by_alias=True, exclude_unset=True)
    assert "nickname" not in dumped
    assert "nickName" not in dumped


def test_model_dump_json_no_region_key() -> None:
    """model_dump_json(): output has no region key."""
    model = UpdateSampleInput(id=1)
    json_str = model.model_dump_json()
    data = json.loads(json_str)
    assert "region" not in data


def test_model_dump_json_no_enum_leak() -> None:
    """model_dump_json(): no enum value leak (1 would be the enum's internal value)."""
    model = UpdateSampleInput(id=1)
    json_str = model.model_dump_json()
    # The entire JSON output should not contain the enum's numeric value
    assert '"1"' not in json_str or '"id": 1' in json_str  # id is 1, but not as a string enum


def test_model_validate_omitted_field_is_undefined() -> None:
    """model_validate: omitted field gives UNDEFINED."""
    model = UpdateSampleInput.model_validate({"id": 1})
    assert model.region is UNDEFINED


def test_model_validate_explicit_none_gives_none() -> None:
    """model_validate: explicit None gives None."""
    model = UpdateSampleInput.model_validate({"id": 1, "region": None})
    assert model.region is None


def test_model_json_schema_no_undefined_in_json() -> None:
    """model_json_schema(): json.dumps(schema) contains no 'Undefined'."""
    schema = UpdateSampleInput.model_json_schema()
    schema_str = json.dumps(schema)
    assert "Undefined" not in schema_str


def test_model_json_schema_region_property_clean() -> None:
    """model_json_schema(): properties.region has no Undefined ref and no default."""
    schema = UpdateSampleInput.model_json_schema()
    region_prop = schema["properties"]["region"]
    # Should be simplified to {"anyOf": [{"type": "string"}, {"type": "null"}], ...}
    # or just the innermost structure
    schema_str = json.dumps(region_prop)
    assert "Undefined" not in schema_str
    assert "$ref" not in schema_str  # No Undefined ref


def test_model_json_schema_no_default_on_undefined_field() -> None:
    """model_json_schema(): region field has no default key."""
    schema = UpdateSampleInput.model_json_schema()
    region_prop = schema["properties"]["region"]
    assert "default" not in region_prop


def test_model_json_schema_count_preserves_legitimate_default() -> None:
    """model_json_schema(): count field with default=1 still has 'default': 1."""
    schema = UpdateSampleInput.model_json_schema()
    count_prop = schema["properties"]["count"]
    assert count_prop.get("default") == 1


def test_model_json_schema_with_components_ref_template() -> None:
    """model_json_schema(ref_template='#/components/schemas/{model}'): no Undefined."""
    schema = UpdateSampleInput.model_json_schema(ref_template="#/components/schemas/{model}")
    schema_str = json.dumps(schema)
    assert "Undefined" not in schema_str


def test_create_model_dump_equals_plain_basemodel() -> None:
    """CreateSampleInput model_dump() equals identical plain BaseModel's."""
    create_input = CreateSampleInput(name="test", description="desc")
    plain_model = PlainEquivalentModel(name="test", description="desc")

    create_dump = create_input.model_dump(mode="python")
    plain_dump = plain_model.model_dump(mode="python")

    assert create_dump == plain_dump


def test_create_model_json_schema_equals_plain_basemodel() -> None:
    """CreateSampleInput model_json_schema() equals identical plain BaseModel's (excluding title)."""
    create_schema = CreateSampleInput.model_json_schema()
    plain_schema = PlainEquivalentModel.model_json_schema()

    # Remove titles and compare (they differ by class name but structure should be same)
    create_schema_copy = dict(create_schema)
    plain_schema_copy = dict(plain_schema)
    create_schema_copy.pop("title", None)
    plain_schema_copy.pop("title", None)
    assert create_schema_copy == plain_schema_copy


def test_nested_outer_dumps_without_inner_undefined() -> None:
    """Nested case: outer model_dump() drops inner UNDEFINED fields."""
    inner = UpdateSampleInput(id=1)  # region is UNDEFINED
    outer = OuterSampleInput(outer_id=10, inner=inner)

    dumped = outer.model_dump(mode="python")

    # The outer should be present
    assert dumped["outer_id"] == 10

    # The inner dict should be present
    assert "inner" in dumped
    inner_dict = dumped["inner"]

    # The inner's UNDEFINED field (region) should not be in the dumped dict
    assert "region" not in inner_dict
    assert inner_dict["id"] == 1


def test_serialization_mode_schema_keeps_fields() -> None:
    """model_json_schema(mode='serialization') keeps the model's properties (not {})."""
    schema = UpdateSampleInput.model_json_schema(mode="serialization")
    assert set(schema["properties"]) == {"id", "region", "nickName", "count"}
    assert "Undefined" not in json.dumps(schema)
