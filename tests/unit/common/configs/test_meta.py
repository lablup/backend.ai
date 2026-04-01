from __future__ import annotations

from typing import Annotated

import pytest
from pydantic import BaseModel, Field

from ai.backend.common.meta import (
    BackendAIAPIMeta,
    BackendAIConfigMeta,
    BackendAIFieldMeta,
    ConfigExample,
    generate_composite_example,
    generate_example,
    generate_model_example,
    get_field_meta,
    get_field_type,
)


class TestConfigExample:
    def test_frozen_dataclass(self) -> None:
        example = ConfigExample(local="localhost", prod="prod.example.com")
        assert example.local == "localhost"
        assert example.prod == "prod.example.com"

        # Should be frozen
        with pytest.raises(AttributeError):
            example.local = "changed"  # type: ignore[misc]


class TestBackendAIFieldMeta:
    def test_required_fields(self) -> None:
        meta = BackendAIFieldMeta(
            description="Test description",
            added_version="25.1.0",
        )
        assert meta.description == "Test description"
        assert meta.added_version == "25.1.0"
        assert meta.deprecated_version is None
        assert meta.deprecation_hint is None

    def test_optional_fields(self) -> None:
        meta = BackendAIFieldMeta(
            description="Test description",
            added_version="25.1.0",
            deprecated_version="26.0.0",
            deprecation_hint="Use new_field instead",
        )
        assert meta.deprecated_version == "26.0.0"
        assert meta.deprecation_hint == "Use new_field instead"

    def test_frozen(self) -> None:
        meta = BackendAIFieldMeta(
            description="Test",
            added_version="25.1.0",
        )
        with pytest.raises(AttributeError):
            meta.description = "changed"  # type: ignore[misc]


class TestBackendAIConfigMeta:
    def test_inherits_from_field_meta(self) -> None:
        assert issubclass(BackendAIConfigMeta, BackendAIFieldMeta)

    def test_config_specific_fields(self) -> None:
        meta = BackendAIConfigMeta(
            description="Config field",
            added_version="25.1.0",
            example=ConfigExample(local="local-value", prod="prod-value"),
            secret=True,
            composite=None,
        )
        assert isinstance(meta.example, ConfigExample)
        assert meta.example.local == "local-value"
        assert meta.secret is True
        assert meta.composite is None

    def test_defaults(self) -> None:
        meta = BackendAIConfigMeta(
            description="Config field",
            added_version="25.1.0",
        )
        assert meta.example is None
        assert meta.secret is False
        assert meta.composite is None


class TestBackendAIAPIMeta:
    def test_inherits_from_field_meta(self) -> None:
        assert issubclass(BackendAIAPIMeta, BackendAIFieldMeta)

    def test_api_specific_fields(self) -> None:
        meta = BackendAIAPIMeta(
            description="API field",
            added_version="25.1.0",
            example=ConfigExample(local="local-example", prod="prod-example"),
            composite=True,
        )
        assert isinstance(meta.example, ConfigExample)
        assert meta.example.local == "local-example"
        assert meta.example.prod == "prod-example"
        assert meta.composite is True

    def test_defaults(self) -> None:
        meta = BackendAIAPIMeta(
            description="API field",
            added_version="25.1.0",
        )
        assert meta.example is None
        assert meta.composite is False


class TestGetFieldMeta:
    def test_get_config_meta(self) -> None:
        class SampleConfig(BaseModel):
            name: Annotated[
                str,
                Field(default="default"),
                BackendAIConfigMeta(
                    description="Name field",
                    added_version="25.1.0",
                ),
            ]

        meta = get_field_meta(SampleConfig, "name")
        assert meta is not None
        assert isinstance(meta, BackendAIConfigMeta)
        assert meta.description == "Name field"
        assert meta.added_version == "25.1.0"

    def test_get_api_meta(self) -> None:
        class SampleRequest(BaseModel):
            session_name: Annotated[
                str,
                Field(),
                BackendAIAPIMeta(
                    description="Session name",
                    added_version="25.1.0",
                    example=ConfigExample(local="my-session", prod="my-session"),
                ),
            ]

        meta = get_field_meta(SampleRequest, "session_name")
        assert meta is not None
        assert isinstance(meta, BackendAIAPIMeta)
        assert meta.example is not None
        assert meta.example.local == "my-session"

    def test_field_without_meta(self) -> None:
        class SampleModel(BaseModel):
            plain_field: str = Field(default="value")

        meta = get_field_meta(SampleModel, "plain_field")
        assert meta is None

    def test_nonexistent_field(self) -> None:
        class SampleModel(BaseModel):
            name: str

        meta = get_field_meta(SampleModel, "nonexistent")
        assert meta is None


class TestGetFieldType:
    def test_annotated_type(self) -> None:
        class SampleModel(BaseModel):
            count: Annotated[
                int,
                Field(),
                BackendAIAPIMeta(description="Count", added_version="25.1.0"),
            ]

        field_type = get_field_type(SampleModel, "count")
        assert field_type is int

    def test_plain_type(self) -> None:
        class SampleModel(BaseModel):
            name: str = Field(default="default")

        field_type = get_field_type(SampleModel, "name")
        assert field_type is str

    def test_nonexistent_field(self) -> None:
        class SampleModel(BaseModel):
            name: str

        field_type = get_field_type(SampleModel, "nonexistent")
        assert field_type is None


class TestGenerateExample:
    def test_simple_example(self) -> None:
        class SampleModel(BaseModel):
            name: Annotated[
                str,
                Field(),
                BackendAIAPIMeta(
                    description="Name",
                    added_version="25.1.0",
                    example=ConfigExample(local="sample-name", prod="sample-name-prod"),
                ),
            ]

        example = generate_example(SampleModel, "name")
        assert example == "sample-name"

    def test_config_example_returns_local_value(self) -> None:
        class SampleConfig(BaseModel):
            endpoint: Annotated[
                str,
                Field(),
                BackendAIConfigMeta(
                    description="Endpoint",
                    added_version="25.1.0",
                    example=ConfigExample(local="localhost:8080", prod="api.example.com"),
                ),
            ]

        # Default env is LOCAL, so returns local value as string
        example = generate_example(SampleConfig, "endpoint")
        assert example == "localhost:8080"

    def test_no_example_raises_error(self) -> None:
        class SampleModel(BaseModel):
            name: Annotated[
                str,
                Field(),
                BackendAIAPIMeta(
                    description="Name",
                    added_version="25.1.0",
                ),
            ]

        with pytest.raises(ValueError, match="has no example defined"):
            generate_example(SampleModel, "name")

    def test_field_without_meta_raises_error(self) -> None:
        class SampleModel(BaseModel):
            name: str = Field(default="value")

        with pytest.raises(ValueError, match="has no BackendAI metadata"):
            generate_example(SampleModel, "name")

    def test_composite_field_raises_error_without_example(self) -> None:
        """Composite fields require generate_composite_example instead of generate_example."""

        class ChildConfig(BaseModel):
            cpu: Annotated[
                int,
                Field(),
                BackendAIAPIMeta(
                    description="CPU cores",
                    added_version="25.1.0",
                    example=ConfigExample(local="4", prod="8"),
                ),
            ]

        class ParentConfig(BaseModel):
            config: Annotated[
                ChildConfig,
                Field(),
                BackendAIAPIMeta(
                    description="Configuration",
                    added_version="25.1.0",
                    composite=True,
                ),
            ]

        # generate_example raises error for composite fields without example
        # Use generate_composite_example instead for composite types
        with pytest.raises(ValueError, match="has no example defined"):
            generate_example(ParentConfig, "config")


class TestGenerateCompositeExample:
    def test_flat_model(self) -> None:
        class SessionConfig(BaseModel):
            cpu: Annotated[
                int,
                Field(),
                BackendAIAPIMeta(
                    description="CPU cores",
                    added_version="25.1.0",
                    example=ConfigExample(local="4", prod="8"),
                ),
            ]
            memory: Annotated[
                str,
                Field(),
                BackendAIAPIMeta(
                    description="Memory size",
                    added_version="25.1.0",
                    example=ConfigExample(local="8g", prod="32g"),
                ),
            ]

        result = generate_composite_example(SessionConfig)
        assert result == {"cpu": "4", "memory": "8g"}

    def test_nested_composite(self) -> None:
        class InnerConfig(BaseModel):
            value: Annotated[
                str,
                Field(),
                BackendAIAPIMeta(
                    description="Inner value",
                    added_version="25.1.0",
                    example=ConfigExample(local="inner", prod="inner-prod"),
                ),
            ]

        class OuterConfig(BaseModel):
            inner: Annotated[
                InnerConfig,
                Field(),
                BackendAIAPIMeta(
                    description="Inner config", added_version="25.1.0", composite=True
                ),
            ]
            name: Annotated[
                str,
                Field(),
                BackendAIAPIMeta(
                    description="Name",
                    added_version="25.1.0",
                    example=ConfigExample(local="outer-name", prod="outer-name-prod"),
                ),
            ]

        result = generate_composite_example(OuterConfig)
        assert result == {"inner": {"value": "inner"}, "name": "outer-name"}

    def test_skips_fields_without_meta(self) -> None:
        class MixedConfig(BaseModel):
            with_meta: Annotated[
                str,
                Field(),
                BackendAIAPIMeta(
                    description="With meta",
                    added_version="25.1.0",
                    example=ConfigExample(local="has-meta", prod="has-meta-prod"),
                ),
            ]
            without_meta: str = Field(default="no-meta")

        result = generate_composite_example(MixedConfig)
        assert result == {"with_meta": "has-meta"}
        assert "without_meta" not in result

    def test_config_example_in_composite(self) -> None:
        class EnvConfig(BaseModel):
            endpoint: Annotated[
                str,
                Field(),
                BackendAIConfigMeta(
                    description="Endpoint",
                    added_version="25.1.0",
                    example=ConfigExample(local="localhost", prod="prod.example.com"),
                ),
            ]

        # generate_composite_example returns the value from ConfigExample.get(env)
        result = generate_composite_example(EnvConfig)
        assert result == {"endpoint": "localhost"}


class TestGenerateModelExample:
    def test_full_model_example(self) -> None:
        class CreateSessionRequest(BaseModel):
            name: Annotated[
                str,
                Field(),
                BackendAIAPIMeta(
                    description="Session name",
                    added_version="25.1.0",
                    example=ConfigExample(local="my-session", prod="my-session-prod"),
                ),
            ]
            image: Annotated[
                str,
                Field(),
                BackendAIAPIMeta(
                    description="Container image",
                    added_version="25.1.0",
                    example=ConfigExample(local="python:3.11", prod="python:3.11"),
                ),
            ]

        result = generate_model_example(CreateSessionRequest)
        assert result == {"name": "my-session", "image": "python:3.11"}

    def test_model_with_composite_skips_composite_fields(self) -> None:
        """generate_model_example skips composite fields - use generate_composite_example for them."""

        class ResourceConfig(BaseModel):
            cpu: Annotated[
                int,
                Field(),
                BackendAIAPIMeta(
                    description="CPU",
                    added_version="25.1.0",
                    example=ConfigExample(local="2", prod="8"),
                ),
            ]

        class SessionRequest(BaseModel):
            name: Annotated[
                str,
                Field(),
                BackendAIAPIMeta(
                    description="Name",
                    added_version="25.1.0",
                    example=ConfigExample(local="session-1", prod="session-prod"),
                ),
            ]
            resources: Annotated[
                ResourceConfig,
                Field(),
                BackendAIAPIMeta(description="Resources", added_version="25.1.0", composite=True),
            ]

        # generate_model_example skips composite fields
        result = generate_model_example(SessionRequest)
        assert result == {"name": "session-1"}
        assert "resources" not in result

        # Use generate_composite_example for composite types
        composite_result = generate_composite_example(SessionRequest)
        assert composite_result == {"name": "session-1", "resources": {"cpu": "2"}}

    def test_empty_model(self) -> None:
        class EmptyModel(BaseModel):
            plain_field: str = "value"

        result = generate_model_example(EmptyModel)
        assert result == {}
