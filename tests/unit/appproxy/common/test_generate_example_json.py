from __future__ import annotations

import tomllib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner
from pydantic import Field, FilePath, create_model

from ai.backend.appproxy.common.config import UnsupportedTypeError, generate_example_json
from ai.backend.appproxy.common.types import DigestModType
from ai.backend.appproxy.coordinator.cli.__main__ import main as coordinator_cli
from ai.backend.appproxy.coordinator.config import ServerConfig as CoordinatorServerConfig
from ai.backend.appproxy.worker.cli.__main__ import main as worker_cli
from ai.backend.appproxy.worker.config import ServerConfig as WorkerServerConfig
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.meta import BackendAIConfigMeta, ConfigExample
from ai.backend.common.types import BackendAISchema

_MISSING_HOST_PATH_ERROR_TYPES = {"path_not_directory", "path_not_file"}


class _SectionWithConfigExample(BackendAISchema):
    port: Annotated[
        int,
        BackendAIConfigMeta(
            description="A port.",
            added_version="26.11.0",
            example=ConfigExample(local="10", prod="20"),
        ),
    ]


class _RequiredFieldWithoutExample(BackendAISchema):
    value: str


@dataclass(frozen=True)
class _ConfigExampleConversionCase:
    description: str
    annotation: Any
    example_text: str
    expected_value: Any


@dataclass(frozen=True)
class _FieldWithoutUsableConfigExampleCase:
    description: str
    field_definition: Any
    expected_example: dict[str, Any]


@dataclass(frozen=True)
class _ExampleCommandCase:
    description: str
    cli: click.Group
    server_config: type[BackendAISchema]


class TestGenerateExampleJson:
    @pytest.fixture
    def schema_with_config_example(
        self, case: _ConfigExampleConversionCase
    ) -> type[BackendAISchema]:
        return create_model(
            "SchemaWithConfigExample",
            __base__=BackendAISchema,
            value=(
                Annotated[
                    case.annotation,
                    BackendAIConfigMeta(
                        description="A value.",
                        added_version="26.11.0",
                        example=ConfigExample(local="unused", prod=case.example_text),
                    ),
                ],
                ...,
            ),
        )

    @pytest.fixture
    def schema_without_usable_config_example(
        self, case: _FieldWithoutUsableConfigExampleCase
    ) -> type[BackendAISchema]:
        return create_model(
            "SchemaWithoutUsableConfigExample",
            __base__=BackendAISchema,
            value=case.field_definition,
        )

    @pytest.mark.parametrize(
        "case",
        [
            _ConfigExampleConversionCase(
                description="int", annotation=int, example_text="10", expected_value=10
            ),
            _ConfigExampleConversionCase(
                description="float", annotation=float, example_text="1.5", expected_value=1.5
            ),
            _ConfigExampleConversionCase(
                description="bool", annotation=bool, example_text="true", expected_value=True
            ),
            _ConfigExampleConversionCase(
                description="str_stays_text_when_it_looks_numeric",
                annotation=str,
                example_text="10",
                expected_value="10",
            ),
            _ConfigExampleConversionCase(
                description="path",
                annotation=Path,
                example_text="/var/run/ipc",
                expected_value="/var/run/ipc",
            ),
            _ConfigExampleConversionCase(
                description="enum",
                annotation=DigestModType,
                example_text="sha256",
                expected_value="sha256",
            ),
            _ConfigExampleConversionCase(
                description="list",
                annotation=list[str],
                example_text='["a", "b"]',
                expected_value=["a", "b"],
            ),
            _ConfigExampleConversionCase(
                description="tuple",
                annotation=tuple[int, int],
                example_text="[1, 2]",
                expected_value=[1, 2],
            ),
            _ConfigExampleConversionCase(
                description="dict",
                annotation=dict[str, str],
                example_text='{ "a" = "b" }',
                expected_value={"a": "b"},
            ),
        ],
        ids=lambda case: case.description,
    )
    def test_config_example_is_converted_to_the_field_type(
        self,
        case: _ConfigExampleConversionCase,
        schema_with_config_example: type[BackendAISchema],
    ) -> None:
        assert generate_example_json(schema_with_config_example) == {"value": case.expected_value}

    @pytest.mark.parametrize(
        "case",
        [
            _FieldWithoutUsableConfigExampleCase(
                description="default_is_used",
                field_definition=(int, 5),
                expected_example={"value": 5},
            ),
            _FieldWithoutUsableConfigExampleCase(
                description="default_factory_is_called",
                field_definition=(list[str], Field(default_factory=lambda: ["a"])),
                expected_example={"value": ["a"]},
            ),
            _FieldWithoutUsableConfigExampleCase(
                description="none_default_is_left_out",
                field_definition=(int | None, None),
                expected_example={},
            ),
            _FieldWithoutUsableConfigExampleCase(
                description="none_default_of_annotated_optional_is_left_out",
                field_definition=(FilePath | None, None),
                expected_example={},
            ),
            _FieldWithoutUsableConfigExampleCase(
                description="none_default_is_left_out_even_with_a_config_example",
                field_definition=(
                    Annotated[
                        int | None,
                        BackendAIConfigMeta(
                            description="A value.",
                            added_version="26.11.0",
                            example=ConfigExample(local="10", prod="20"),
                        ),
                    ],
                    None,
                ),
                expected_example={},
            ),
            _FieldWithoutUsableConfigExampleCase(
                description="optional_section_is_described",
                field_definition=(_SectionWithConfigExample | None, None),
                expected_example={"value": {"port": 20}},
            ),
            _FieldWithoutUsableConfigExampleCase(
                description="list_of_sections_is_described",
                field_definition=(list[_SectionWithConfigExample], Field(default_factory=list)),
                expected_example={"value": [{"port": 20}]},
            ),
        ],
        ids=lambda case: case.description,
    )
    def test_field_without_usable_config_example(
        self,
        case: _FieldWithoutUsableConfigExampleCase,
        schema_without_usable_config_example: type[BackendAISchema],
    ) -> None:
        assert generate_example_json(schema_without_usable_config_example) == case.expected_example

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
    @pytest.mark.parametrize(
        "case",
        [
            _ExampleCommandCase(
                description="coordinator",
                cli=coordinator_cli,
                server_config=CoordinatorServerConfig,
            ),
            _ExampleCommandCase(
                description="worker", cli=worker_cli, server_config=WorkerServerConfig
            ),
        ],
        ids=lambda case: case.description,
    )
    def test_stdout_example_passes_server_config_validation_apart_from_host_paths(
        self, case: _ExampleCommandCase
    ) -> None:
        result = CliRunner().invoke(case.cli, ["generate-example-configuration"])

        assert result.exit_code == 0, result.output
        validation_errors: list[dict[str, Any]] = []
        try:
            case.server_config.model_validate(tomllib.loads(result.stdout))
        except BackendAISchemaValidationFailed as e:
            assert e.extra_data is not None
            validation_errors = e.extra_data["errors"]
        assert [
            error
            for error in validation_errors
            if error["type"] not in _MISSING_HOST_PATH_ERROR_TYPES
        ] == []

    @pytest.mark.parametrize(
        "case",
        [
            _ExampleCommandCase(
                description="coordinator",
                cli=coordinator_cli,
                server_config=CoordinatorServerConfig,
            ),
            _ExampleCommandCase(
                description="worker", cli=worker_cli, server_config=WorkerServerConfig
            ),
        ],
        ids=lambda case: case.description,
    )
    def test_output_option_writes_the_same_example_as_stdout(
        self, case: _ExampleCommandCase, example_output_file: Path
    ) -> None:
        stdout_result = CliRunner().invoke(case.cli, ["generate-example-configuration"])
        file_result = CliRunner().invoke(
            case.cli, ["generate-example-configuration", "--output", str(example_output_file)]
        )

        assert file_result.exit_code == 0, file_result.output
        assert tomllib.loads(example_output_file.read_text()) == tomllib.loads(stdout_result.stdout)
