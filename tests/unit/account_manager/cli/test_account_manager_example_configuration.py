from __future__ import annotations

import tomllib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from pydantic import Field, create_model

from ai.backend.account_manager.cli.__main__ import main
from ai.backend.account_manager.config import (
    BaseSchema,
    ServerConfig,
    UnsupportedTypeError,
    generate_example_json,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed

_MISSING_HOST_PATH_ERROR_TYPES = {"path_not_directory", "path_not_file"}


class _SectionWithFieldExample(BaseSchema):
    port: int = Field(examples=[20])


class _RequiredFieldWithoutExample(BaseSchema):
    value: str


@dataclass(frozen=True)
class _FieldWithoutExampleCase:
    description: str
    field_definition: Any
    expected_example: dict[str, Any]


class TestGenerateExampleJson:
    @pytest.fixture
    def schema_without_field_example(self, case: _FieldWithoutExampleCase) -> type[BaseSchema]:
        return create_model(
            "SchemaWithoutFieldExample",
            __base__=BaseSchema,
            value=case.field_definition,
        )

    @pytest.mark.parametrize(
        "case",
        [
            _FieldWithoutExampleCase(
                description="default_is_used",
                field_definition=(int, 5),
                expected_example={"value": 5},
            ),
            _FieldWithoutExampleCase(
                description="default_factory_is_called",
                field_definition=(list[str], Field(default_factory=lambda: ["a"])),
                expected_example={"value": ["a"]},
            ),
            _FieldWithoutExampleCase(
                description="none_default_is_left_out",
                field_definition=(int | None, None),
                expected_example={},
            ),
            _FieldWithoutExampleCase(
                description="optional_section_is_described",
                field_definition=(_SectionWithFieldExample | None, None),
                expected_example={"value": {"port": 20}},
            ),
            _FieldWithoutExampleCase(
                description="list_of_sections_is_described",
                field_definition=(list[_SectionWithFieldExample], Field(default_factory=list)),
                expected_example={"value": [{"port": 20}]},
            ),
        ],
        ids=lambda case: case.description,
    )
    def test_field_without_example(
        self,
        case: _FieldWithoutExampleCase,
        schema_without_field_example: type[BaseSchema],
    ) -> None:
        assert generate_example_json(schema_without_field_example) == case.expected_example

    def test_required_field_without_example_raises(self) -> None:
        with pytest.raises(UnsupportedTypeError):
            generate_example_json(_RequiredFieldWithoutExample)


class TestGenerateExampleConfigurationCommand:
    @pytest.fixture
    def auto_directories_left_uncreated(self) -> Iterator[None]:
        with patch("pathlib.Path.mkdir"):
            yield

    @pytest.fixture
    def example_output_file(self, tmp_path: Path) -> Path:
        return tmp_path / "example.toml"

    @pytest.mark.usefixtures("auto_directories_left_uncreated")
    def test_stdout_example_passes_server_config_validation_apart_from_host_paths(self) -> None:
        result = CliRunner().invoke(main, ["generate-example-configuration"])

        assert result.exit_code == 0, result.output
        validation_errors: list[dict[str, Any]] = []
        try:
            ServerConfig.model_validate(tomllib.loads(result.stdout))
        except BackendAISchemaValidationFailed as e:
            assert e.extra_data is not None
            validation_errors = e.extra_data["errors"]
        assert [
            error
            for error in validation_errors
            if error["type"] not in _MISSING_HOST_PATH_ERROR_TYPES
        ] == []

    def test_output_option_writes_the_same_example_as_stdout(
        self, example_output_file: Path
    ) -> None:
        stdout_result = CliRunner().invoke(main, ["generate-example-configuration"])
        file_result = CliRunner().invoke(
            main, ["generate-example-configuration", "--output", str(example_output_file)]
        )

        assert file_result.exit_code == 0, file_result.output
        assert tomllib.loads(example_output_file.read_text()) == tomllib.loads(stdout_result.stdout)
