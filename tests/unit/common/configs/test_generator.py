from __future__ import annotations

from typing import Annotated

import pytest
from pydantic import BaseModel, Field

from ai.backend.common.configs.generator import (
    BinarySizeFormatter,
    CompositeFormatter,
    DefaultFormatter,
    EnumFormatter,
    FieldVisibility,
    FormattedValue,
    GeneratorConfig,
    HostPortPairFormatter,
    TOMLGenerator,
    create_default_formatter,
    generate_halfstack_toml,
    generate_sample_toml,
)
from ai.backend.common.configs.inspector import FieldDocumentation, FieldSchema, FieldTypeInfo
from ai.backend.common.meta import (
    BackendAIConfigMeta,
    CompositeType,
    ConfigEnvironment,
    ConfigExample,
)


class TestFieldVisibility:
    def test_enum_values(self) -> None:
        assert FieldVisibility.REQUIRED == "required"
        assert FieldVisibility.OPTIONAL == "optional"
        assert FieldVisibility.HIDDEN == "hidden"


class TestFormattedValue:
    def test_value_only(self) -> None:
        fv = FormattedValue(value='"test"')
        assert fv.value == '"test"'
        assert fv.comment is None

    def test_with_comment(self) -> None:
        fv = FormattedValue(value="10", comment="# min=0, max=100")
        assert fv.value == "10"
        assert fv.comment == "# min=0, max=100"


class TestGeneratorConfig:
    def test_defaults(self) -> None:
        config = GeneratorConfig()
        assert config.comment_width == 80
        assert config.indent_size == 2
        assert config.show_deprecated is False
        assert config.mask_secrets is True
        assert config.secret_placeholder == "***SECRET***"

    def test_custom_config(self) -> None:
        config = GeneratorConfig(
            comment_width=100,
            indent_size=4,
            show_deprecated=True,
            mask_secrets=False,
        )
        assert config.comment_width == 100
        assert config.indent_size == 4
        assert config.show_deprecated is True
        assert config.mask_secrets is False


class TestDefaultFormatter:
    @pytest.fixture
    def formatter(self) -> DefaultFormatter:
        return DefaultFormatter()

    @pytest.fixture
    def dummy_field(self) -> FieldSchema:
        return FieldSchema(
            key="test",
            type_info=FieldTypeInfo(type_name="str", default=None, required=True, secret=False),
            doc=FieldDocumentation(description="Test", example=None, added_version="25.1.0"),
        )

    def test_format_string(self, formatter: DefaultFormatter, dummy_field: FieldSchema) -> None:
        result = formatter.format("hello", dummy_field)
        assert result.value == '"hello"'

    def test_format_int(self, formatter: DefaultFormatter, dummy_field: FieldSchema) -> None:
        result = formatter.format(42, dummy_field)
        assert result.value == "42"

    def test_format_float(self, formatter: DefaultFormatter, dummy_field: FieldSchema) -> None:
        result = formatter.format(3.14, dummy_field)
        assert result.value == "3.14"

    def test_format_bool_true(self, formatter: DefaultFormatter, dummy_field: FieldSchema) -> None:
        result = formatter.format(True, dummy_field)
        assert result.value == "true"

    def test_format_bool_false(self, formatter: DefaultFormatter, dummy_field: FieldSchema) -> None:
        result = formatter.format(False, dummy_field)
        assert result.value == "false"

    def test_format_none(self, formatter: DefaultFormatter, dummy_field: FieldSchema) -> None:
        # When value is None, formatter generates type-based placeholder
        # For str type, it returns "..."
        result = formatter.format(None, dummy_field)
        assert result.value == '"..."'

    def test_format_list(self, formatter: DefaultFormatter, dummy_field: FieldSchema) -> None:
        result = formatter.format(["a", "b"], dummy_field)
        assert result.value == '["a", "b"]'

    def test_format_dict(self, formatter: DefaultFormatter, dummy_field: FieldSchema) -> None:
        result = formatter.format({"key": "value"}, dummy_field)
        assert "key" in result.value
        assert "value" in result.value


class TestBinarySizeFormatter:
    @pytest.fixture
    def formatter(self) -> BinarySizeFormatter:
        return BinarySizeFormatter()

    @pytest.fixture
    def binary_field(self) -> FieldSchema:
        return FieldSchema(
            key="size",
            type_info=FieldTypeInfo(
                type_name="BinarySize", default=None, required=True, secret=False
            ),
            doc=FieldDocumentation(description="Size", example=None, added_version="25.1.0"),
        )

    def test_can_format(self, formatter: BinarySizeFormatter) -> None:
        assert formatter.can_format("BinarySize", "1G") is True
        assert formatter.can_format("str", "hello") is False

    def test_format_string_value(
        self, formatter: BinarySizeFormatter, binary_field: FieldSchema
    ) -> None:
        result = formatter.format("1g", binary_field)
        assert result.value == '"1G"'

    def test_format_bytes(self, formatter: BinarySizeFormatter, binary_field: FieldSchema) -> None:
        result = formatter.format(1073741824, binary_field)  # 1GB
        assert result.value == '"1G"'

    def test_format_megabytes(
        self, formatter: BinarySizeFormatter, binary_field: FieldSchema
    ) -> None:
        result = formatter.format(536870912, binary_field)  # 512MB
        assert result.value == '"512M"'


class TestHostPortPairFormatter:
    @pytest.fixture
    def formatter(self) -> HostPortPairFormatter:
        return HostPortPairFormatter()

    @pytest.fixture
    def hostport_field(self) -> FieldSchema:
        return FieldSchema(
            key="addr",
            type_info=FieldTypeInfo(
                type_name="HostPortPair", default=None, required=True, secret=False
            ),
            doc=FieldDocumentation(description="Address", example=None, added_version="25.1.0"),
        )

    def test_can_format(self, formatter: HostPortPairFormatter) -> None:
        assert formatter.can_format("HostPortPair", {}) is True
        assert formatter.can_format("str", "hello") is False

    def test_format_dict(
        self, formatter: HostPortPairFormatter, hostport_field: FieldSchema
    ) -> None:
        result = formatter.format({"host": "127.0.0.1", "port": 8080}, hostport_field)
        assert result.value == '{ host = "127.0.0.1", port = 8080 }'

    def test_format_string(
        self, formatter: HostPortPairFormatter, hostport_field: FieldSchema
    ) -> None:
        result = formatter.format("localhost:3000", hostport_field)
        assert result.value == '{ host = "localhost", port = 3000 }'


class TestEnumFormatter:
    @pytest.fixture
    def formatter(self) -> EnumFormatter:
        return EnumFormatter()

    @pytest.fixture
    def enum_field(self) -> FieldSchema:
        return FieldSchema(
            key="status",
            type_info=FieldTypeInfo(type_name="Status", default=None, required=True, secret=False),
            doc=FieldDocumentation(description="Status", example=None, added_version="25.1.0"),
        )

    def test_format_string_enum(self, formatter: EnumFormatter, enum_field: FieldSchema) -> None:
        from enum import Enum

        class Status(Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        result = formatter.format(Status.ACTIVE, enum_field)
        assert result.value == '"active"'


class TestCompositeFormatter:
    def test_default_formatters(self) -> None:
        formatter = create_default_formatter()
        assert isinstance(formatter, CompositeFormatter)

    def test_uses_matching_formatter(self) -> None:
        formatter = create_default_formatter()
        binary_field = FieldSchema(
            key="size",
            type_info=FieldTypeInfo(
                type_name="BinarySize", default=None, required=True, secret=False
            ),
            doc=FieldDocumentation(description="Size", example=None, added_version="25.1.0"),
        )
        result = formatter.format("1G", binary_field)
        assert result.value == '"1G"'

    def test_falls_back_to_default(self) -> None:
        formatter = create_default_formatter()
        str_field = FieldSchema(
            key="name",
            type_info=FieldTypeInfo(type_name="str", default=None, required=True, secret=False),
            doc=FieldDocumentation(description="Name", example=None, added_version="25.1.0"),
        )
        result = formatter.format("test", str_field)
        assert result.value == '"test"'


class TestTOMLGenerator:
    def test_env_property(self) -> None:
        generator = TOMLGenerator(env=ConfigEnvironment.PROD)
        assert generator.env == ConfigEnvironment.PROD

    def test_generate_simple_config(self) -> None:
        class SimpleConfig(BaseModel):
            name: Annotated[
                str,
                Field(default="default-name"),
                BackendAIConfigMeta(
                    description="The configuration name",
                    added_version="25.1.0",
                    example=ConfigExample(local="local-name", prod="prod-name"),
                ),
            ]

        generator = TOMLGenerator(env=ConfigEnvironment.LOCAL)
        result = generator.generate(SimpleConfig)

        assert "name" in result
        # Example value is used for sample.toml generation
        assert "local-name" in result
        assert "# The configuration name" in result

    def test_generate_uses_prod_example(self) -> None:
        """PROD environment uses prod example value."""

        class EnvConfig(BaseModel):
            endpoint: Annotated[
                str,
                Field(default="default-endpoint"),
                BackendAIConfigMeta(
                    description="Endpoint URL",
                    added_version="25.1.0",
                    example=ConfigExample(local="localhost:8080", prod="api.example.com"),
                ),
            ]

        generator = TOMLGenerator(env=ConfigEnvironment.PROD)
        result = generator.generate(EnvConfig)

        # Example value is used, not default
        assert "api.example.com" in result

    def test_generate_uses_local_example(self) -> None:
        """LOCAL environment uses local example value."""

        class EnvConfig(BaseModel):
            endpoint: Annotated[
                str,
                Field(default="default-endpoint"),
                BackendAIConfigMeta(
                    description="Endpoint URL",
                    added_version="25.1.0",
                    example=ConfigExample(local="localhost:8080", prod="api.example.com"),
                ),
            ]

        generator = TOMLGenerator(env=ConfigEnvironment.LOCAL)
        result = generator.generate(EnvConfig)

        # Example value is used
        assert "localhost:8080" in result

    def test_optional_field_commented(self) -> None:
        class OptionalConfig(BaseModel):
            optional_field: Annotated[
                str | None,
                Field(default=None),
                BackendAIConfigMeta(
                    description="Optional field",
                    added_version="25.1.0",
                    example=ConfigExample(local="optional", prod="optional"),
                ),
            ]

        generator = TOMLGenerator()
        result = generator.generate(OptionalConfig)

        # Optional fields should be commented with ##
        assert "##" in result
        assert "optional_field" in result

    def test_secret_field_masked(self) -> None:
        class SecretConfig(BaseModel):
            password: Annotated[
                str,
                Field(default="secret123"),
                BackendAIConfigMeta(
                    description="Password",
                    added_version="25.1.0",
                    example=ConfigExample(local="dev-pass", prod="prod-pass"),
                    secret=True,
                ),
            ]

        config = GeneratorConfig(mask_secrets=True)
        generator = TOMLGenerator(config=config)
        result = generator.generate(SecretConfig)

        assert "***SECRET***" in result
        assert "dev-pass" not in result

    def test_secret_field_unmasked(self) -> None:
        class SecretConfig(BaseModel):
            password: Annotated[
                str,
                Field(default="secret123"),
                BackendAIConfigMeta(
                    description="Password",
                    added_version="25.1.0",
                    example=ConfigExample(local="dev-pass", prod="prod-pass"),
                    secret=True,
                ),
            ]

        config = GeneratorConfig(mask_secrets=False)
        generator = TOMLGenerator(env=ConfigEnvironment.LOCAL, config=config)
        result = generator.generate(SecretConfig)

        # Example value is used when unmasked
        assert "dev-pass" in result
        assert "***SECRET***" not in result

    def test_nested_config_section(self) -> None:
        class InnerConfig(BaseModel):
            value: Annotated[
                int,
                Field(default=10),
                BackendAIConfigMeta(
                    description="Inner value",
                    added_version="25.1.0",
                    example=ConfigExample(local="10", prod="100"),
                ),
            ]

        class OuterConfig(BaseModel):
            inner: Annotated[
                InnerConfig,
                Field(default_factory=InnerConfig),
                BackendAIConfigMeta(
                    description="Inner section",
                    added_version="25.1.0",
                    composite=CompositeType.FIELD,
                ),
            ]

        generator = TOMLGenerator()
        result = generator.generate(OuterConfig)

        assert "[inner]" in result
        assert "value" in result

    def test_runtime_field_hidden(self) -> None:
        class RuntimeConfig(BaseModel):
            runtime_field: Annotated[
                str,
                Field(default="runtime"),
                BackendAIConfigMeta(
                    description="This field is injected at runtime",
                    added_version="25.1.0",
                    example=ConfigExample(local="runtime", prod="runtime"),
                ),
            ]
            normal_field: Annotated[
                str,
                Field(default="normal"),
                BackendAIConfigMeta(
                    description="Normal field",
                    added_version="25.1.0",
                    example=ConfigExample(local="normal", prod="normal"),
                ),
            ]

        generator = TOMLGenerator()
        result = generator.generate(RuntimeConfig)

        # Runtime field should be hidden
        assert "runtime_field" not in result
        # Normal field should be present
        assert "normal_field" in result

    def test_skips_fields_without_meta(self) -> None:
        class MixedConfig(BaseModel):
            with_meta: Annotated[
                str,
                Field(default="has-meta"),
                BackendAIConfigMeta(
                    description="With meta",
                    added_version="25.1.0",
                    example=ConfigExample(local="val", prod="val"),
                ),
            ]
            without_meta: str = Field(default="no-meta")

        generator = TOMLGenerator()
        result = generator.generate(MixedConfig)

        assert "with_meta" in result
        assert "without_meta" not in result


class TestConvenienceFunctions:
    def test_generate_sample_toml(self) -> None:
        class SampleConfig(BaseModel):
            field: Annotated[
                str,
                Field(default="default"),
                BackendAIConfigMeta(
                    description="Field",
                    added_version="25.1.0",
                    example=ConfigExample(local="local", prod="prod"),
                ),
            ]

        result = generate_sample_toml(SampleConfig)
        # sample.toml uses LOCAL (dev) environment, so local example is used
        assert "local" in result

    def test_generate_halfstack_toml(self) -> None:
        class HalfstackConfig(BaseModel):
            field: Annotated[
                str,
                Field(default="default"),
                BackendAIConfigMeta(
                    description="Field",
                    added_version="25.1.0",
                    example=ConfigExample(local="local", prod="prod"),
                ),
            ]

        result = generate_halfstack_toml(HalfstackConfig)
        # halfstack.toml uses LOCAL environment, so local example is used
        assert "local" in result
