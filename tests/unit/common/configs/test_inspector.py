from __future__ import annotations

from typing import Annotated

import pytest
from pydantic import BaseModel, Field

from ai.backend.common.configs.inspector import (
    ConfigInspector,
    FieldDocumentation,
    FieldSchema,
    FieldTypeInfo,
)
from ai.backend.common.meta import (
    BackendAIConfigMeta,
    CompositeType,
    ConfigEnvironment,
    ConfigExample,
)


class TestFieldTypeInfo:
    def test_frozen_dataclass(self) -> None:
        info = FieldTypeInfo(
            type_name="str",
            default="default_value",
            required=False,
            secret=False,
        )
        assert info.type_name == "str"
        assert info.default == "default_value"
        assert info.required is False
        assert info.secret is False

        # Should be frozen
        with pytest.raises(AttributeError):
            info.type_name = "int"  # type: ignore[misc]

    def test_required_field(self) -> None:
        info = FieldTypeInfo(
            type_name="str",
            default=None,
            required=True,
            secret=False,
        )
        assert info.required is True

    def test_secret_field(self) -> None:
        info = FieldTypeInfo(
            type_name="str",
            default=None,
            required=False,
            secret=True,
        )
        assert info.secret is True


class TestFieldDocumentation:
    def test_required_fields(self) -> None:
        doc = FieldDocumentation(
            description="Test description",
            example=ConfigExample(local="local-val", prod="prod-val"),
            added_version="25.1.0",
        )
        assert doc.description == "Test description"
        assert doc.example is not None
        assert doc.example.local == "local-val"
        assert doc.added_version == "25.1.0"
        assert doc.deprecated_version is None
        assert doc.deprecation_hint is None

    def test_deprecated_field(self) -> None:
        doc = FieldDocumentation(
            description="Old field",
            example=None,
            added_version="24.0.0",
            deprecated_version="25.0.0",
            deprecation_hint="Use new_field instead",
        )
        assert doc.deprecated_version == "25.0.0"
        assert doc.deprecation_hint == "Use new_field instead"

    def test_frozen(self) -> None:
        doc = FieldDocumentation(
            description="Test",
            example=None,
            added_version="25.1.0",
        )
        with pytest.raises(AttributeError):
            doc.description = "changed"  # type: ignore[misc]


class TestFieldSchema:
    def test_leaf_field(self) -> None:
        schema = FieldSchema(
            key="my-field",
            type_info=FieldTypeInfo(
                type_name="str",
                default=None,
                required=True,
                secret=False,
            ),
            doc=FieldDocumentation(
                description="Test field",
                example=ConfigExample(local="test", prod="test"),
                added_version="25.1.0",
            ),
            children=None,
        )
        assert schema.key == "my-field"
        assert schema.children is None

    def test_composite_field(self) -> None:
        child_schema = FieldSchema(
            key="child-field",
            type_info=FieldTypeInfo(
                type_name="int",
                default=10,
                required=False,
                secret=False,
            ),
            doc=FieldDocumentation(
                description="Child field",
                example=ConfigExample(local="10", prod="100"),
                added_version="25.1.0",
            ),
        )
        parent_schema = FieldSchema(
            key="parent-field",
            type_info=FieldTypeInfo(
                type_name="ChildConfig",
                default=None,
                required=True,
                secret=False,
            ),
            doc=FieldDocumentation(
                description="Parent field",
                example=None,
                added_version="25.1.0",
            ),
            children={"child-field": child_schema},
        )
        assert parent_schema.children is not None
        assert "child-field" in parent_schema.children

    def test_frozen(self) -> None:
        schema = FieldSchema(
            key="test",
            type_info=FieldTypeInfo("str", None, True, False),
            doc=FieldDocumentation("desc", None, "25.1.0"),
        )
        with pytest.raises(AttributeError):
            schema.key = "changed"  # type: ignore[misc]


class TestConfigInspector:
    def test_extract_simple_field(self) -> None:
        class SimpleConfig(BaseModel):
            name: Annotated[
                str,
                Field(default="default-name"),
                BackendAIConfigMeta(
                    description="The name field",
                    added_version="25.1.0",
                    example=ConfigExample(local="local-name", prod="prod-name"),
                ),
            ]

        inspector = ConfigInspector()
        schema = inspector.extract(SimpleConfig)

        assert "name" in schema
        field = schema["name"]
        assert field.key == "name"
        assert field.type_info.type_name == "str"
        assert field.type_info.default == "default-name"
        # required is True because the field type is NOT nullable (str, not str | None)
        # The 'required' flag determines if a field gets ## prefix in TOML output
        assert field.type_info.required is True
        assert field.doc.description == "The name field"
        assert field.doc.added_version == "25.1.0"

    def test_extract_uses_serialization_alias(self) -> None:
        class AliasedConfig(BaseModel):
            my_field: Annotated[
                str,
                Field(default="value", serialization_alias="my-field"),
                BackendAIConfigMeta(
                    description="Aliased field",
                    added_version="25.1.0",
                    example=ConfigExample(local="val", prod="val"),
                ),
            ]

        inspector = ConfigInspector()
        schema = inspector.extract(AliasedConfig)

        # Key should be the serialization_alias
        assert "my-field" in schema
        assert "my_field" not in schema

    def test_extract_required_field(self) -> None:
        class RequiredConfig(BaseModel):
            required_field: Annotated[
                str,
                Field(),
                BackendAIConfigMeta(
                    description="Required field",
                    added_version="25.1.0",
                    example=ConfigExample(local="val", prod="val"),
                ),
            ]

        inspector = ConfigInspector()
        schema = inspector.extract(RequiredConfig)

        assert schema["required_field"].type_info.required is True

    def test_extract_secret_field(self) -> None:
        class SecretConfig(BaseModel):
            password: Annotated[
                str,
                Field(default="secret123"),
                BackendAIConfigMeta(
                    description="Password field",
                    added_version="25.1.0",
                    example=ConfigExample(local="dev-pass", prod="prod-pass"),
                    secret=True,
                ),
            ]

        inspector = ConfigInspector()
        schema = inspector.extract(SecretConfig)

        assert schema["password"].type_info.secret is True

    def test_extract_composite_field(self) -> None:
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
                    description="Inner config",
                    added_version="25.1.0",
                    composite=CompositeType.FIELD,
                ),
            ]

        inspector = ConfigInspector()
        schema = inspector.extract(OuterConfig)

        assert "inner" in schema
        assert schema["inner"].children is not None
        assert "value" in schema["inner"].children
        assert schema["inner"].children["value"].type_info.type_name == "int"

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

        inspector = ConfigInspector()
        schema = inspector.extract(MixedConfig)

        assert "with_meta" in schema
        assert "without_meta" not in schema

    def test_get_example_value_local(self) -> None:
        class ExampleConfig(BaseModel):
            endpoint: Annotated[
                str,
                Field(default="localhost"),
                BackendAIConfigMeta(
                    description="Endpoint",
                    added_version="25.1.0",
                    example=ConfigExample(local="localhost:8080", prod="api.example.com"),
                ),
            ]

        inspector = ConfigInspector(env=ConfigEnvironment.LOCAL)
        schema = inspector.extract(ExampleConfig)

        example = inspector.get_example_value(schema["endpoint"])
        assert example == "localhost:8080"

    def test_get_example_value_prod(self) -> None:
        class ExampleConfig(BaseModel):
            endpoint: Annotated[
                str,
                Field(default="localhost"),
                BackendAIConfigMeta(
                    description="Endpoint",
                    added_version="25.1.0",
                    example=ConfigExample(local="localhost:8080", prod="api.example.com"),
                ),
            ]

        inspector = ConfigInspector(env=ConfigEnvironment.PROD)
        schema = inspector.extract(ExampleConfig)

        example = inspector.get_example_value(schema["endpoint"])
        assert example == "api.example.com"

    def test_get_fields_by_version(self) -> None:
        class VersionedConfig(BaseModel):
            old_field: Annotated[
                str,
                Field(default="old"),
                BackendAIConfigMeta(
                    description="Old field",
                    added_version="24.0.0",
                    example=ConfigExample(local="old", prod="old"),
                ),
            ]
            new_field: Annotated[
                str,
                Field(default="new"),
                BackendAIConfigMeta(
                    description="New field",
                    added_version="25.1.0",
                    example=ConfigExample(local="new", prod="new"),
                ),
            ]
            mid_field: Annotated[
                str,
                Field(default="mid"),
                BackendAIConfigMeta(
                    description="Mid field",
                    added_version="24.6.0",
                    example=ConfigExample(local="mid", prod="mid"),
                ),
            ]

        inspector = ConfigInspector()
        schema = inspector.extract(VersionedConfig)

        # Descending order (newest first)
        sorted_fields = inspector.get_fields_by_version(schema, descending=True)
        versions = [f[1].doc.added_version for f in sorted_fields]
        assert versions == ["25.1.0", "24.6.0", "24.0.0"]

        # Ascending order (oldest first)
        sorted_fields = inspector.get_fields_by_version(schema, descending=False)
        versions = [f[1].doc.added_version for f in sorted_fields]
        assert versions == ["24.0.0", "24.6.0", "25.1.0"]

    def test_get_deprecated_fields(self) -> None:
        class DeprecatedConfig(BaseModel):
            current_field: Annotated[
                str,
                Field(default="current"),
                BackendAIConfigMeta(
                    description="Current field",
                    added_version="25.1.0",
                    example=ConfigExample(local="val", prod="val"),
                ),
            ]
            deprecated_field: Annotated[
                str,
                Field(default="deprecated"),
                BackendAIConfigMeta(
                    description="Deprecated field",
                    added_version="24.0.0",
                    example=ConfigExample(local="val", prod="val"),
                    deprecated_version="25.0.0",
                    deprecation_hint="Use current_field instead",
                ),
            ]

        inspector = ConfigInspector()
        schema = inspector.extract(DeprecatedConfig)

        deprecated = inspector.get_deprecated_fields(schema)
        assert len(deprecated) == 1
        assert deprecated[0][0] == "deprecated_field"
        assert deprecated[0][1].doc.deprecation_hint == "Use current_field instead"

    def test_get_secret_fields(self) -> None:
        class SecretsConfig(BaseModel):
            public_field: Annotated[
                str,
                Field(default="public"),
                BackendAIConfigMeta(
                    description="Public field",
                    added_version="25.1.0",
                    example=ConfigExample(local="val", prod="val"),
                ),
            ]
            secret_field: Annotated[
                str,
                Field(default="secret"),
                BackendAIConfigMeta(
                    description="Secret field",
                    added_version="25.1.0",
                    example=ConfigExample(local="val", prod="val"),
                    secret=True,
                ),
            ]

        inspector = ConfigInspector()
        schema = inspector.extract(SecretsConfig)

        secrets = inspector.get_secret_fields(schema)
        assert len(secrets) == 1
        assert secrets[0][0] == "secret_field"

    def test_type_name_simple_types(self) -> None:
        class TypesConfig(BaseModel):
            str_field: Annotated[
                str,
                Field(default=""),
                BackendAIConfigMeta(
                    description="String",
                    added_version="25.1.0",
                    example=ConfigExample(local="s", prod="s"),
                ),
            ]
            int_field: Annotated[
                int,
                Field(default=0),
                BackendAIConfigMeta(
                    description="Integer",
                    added_version="25.1.0",
                    example=ConfigExample(local="0", prod="0"),
                ),
            ]
            bool_field: Annotated[
                bool,
                Field(default=False),
                BackendAIConfigMeta(
                    description="Boolean",
                    added_version="25.1.0",
                    example=ConfigExample(local="false", prod="false"),
                ),
            ]

        inspector = ConfigInspector()
        schema = inspector.extract(TypesConfig)

        assert schema["str_field"].type_info.type_name == "str"
        assert schema["int_field"].type_info.type_name == "int"
        assert schema["bool_field"].type_info.type_name == "bool"

    def test_type_name_optional(self) -> None:
        class OptionalConfig(BaseModel):
            optional_field: Annotated[
                str | None,
                Field(default=None),
                BackendAIConfigMeta(
                    description="Optional string",
                    added_version="25.1.0",
                    example=ConfigExample(local="val", prod="val"),
                ),
            ]

        inspector = ConfigInspector()
        schema = inspector.extract(OptionalConfig)

        assert "None" in schema["optional_field"].type_info.type_name

    def test_env_property(self) -> None:
        inspector = ConfigInspector(env=ConfigEnvironment.PROD)
        assert inspector.env == ConfigEnvironment.PROD
