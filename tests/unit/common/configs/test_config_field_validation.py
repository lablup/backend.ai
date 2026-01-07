from __future__ import annotations

import typing
from collections.abc import Iterator
from typing import Annotated, Any, get_args, get_origin

import pytest
from pydantic import BaseModel

from ai.backend.common.meta import BackendAIConfigMeta, CompositeType


def get_annotation_with_metadata(model: type[BaseModel], field_name: str) -> Any:
    """Get the full annotation including Annotated metadata.

    Pydantic v2 stores annotations in __pydantic_fields__ but the original
    Annotated type with metadata can be accessed via typing.get_type_hints
    with include_extras=True.
    """
    try:
        hints = typing.get_type_hints(model, include_extras=True)
        return hints.get(field_name)
    except Exception:
        # Fallback to model_fields annotation
        field_info = model.model_fields.get(field_name)
        return field_info.annotation if field_info else None


def get_all_fields_without_meta(
    model: type[BaseModel],
    path: str = "",
    allowed_packages: tuple[str, ...] = (
        "ai.backend.manager",
        "ai.backend.agent",
        "ai.backend.storage",
        "ai.backend.web",
        "ai.backend.appproxy",
        "ai.backend.common.configs",
    ),
) -> Iterator[tuple[str, str, type]]:
    """Recursively find all fields without BackendAIConfigMeta.

    Args:
        model: The Pydantic model to check.
        path: Current field path (for nested fields).
        allowed_packages: Only validate fields from these packages.
            External packages like ai.backend.logging are excluded.

    Yields:
        Tuple of (field_path, field_name, field_type) for fields missing metadata.
    """
    # Skip validation for models outside allowed packages
    model_module = model.__module__
    if not any(model_module.startswith(pkg) for pkg in allowed_packages):
        return

    for field_name in model.model_fields:
        field_path = f"{path}.{field_name}" if path else field_name
        annotation = get_annotation_with_metadata(model, field_name)

        # Check if the field has BackendAIConfigMeta in its Annotated metadata
        has_meta = False
        is_composite: CompositeType | None = None
        inner_type = annotation

        if get_origin(annotation) is Annotated:
            args = get_args(annotation)
            inner_type = args[0]
            for arg in args[1:]:
                if isinstance(arg, BackendAIConfigMeta):
                    has_meta = True
                    is_composite = arg.composite
                    break

        if not has_meta:
            yield (field_path, field_name, annotation)

        # Recursively check nested BaseModel types if composite
        if is_composite and isinstance(inner_type, type) and issubclass(inner_type, BaseModel):
            yield from get_all_fields_without_meta(inner_type, field_path, allowed_packages)


def get_secret_fields(
    model: type[BaseModel],
    path: str = "",
) -> Iterator[tuple[str, bool]]:
    """Find fields that should be marked as secret but aren't.

    Yields:
        Tuple of (field_path, is_marked_secret) for potential secret fields.
    """
    secret_patterns = ("password", "secret", "token", "api_key", "credentials", "privkey")

    for field_name in model.model_fields:
        field_path = f"{path}.{field_name}" if path else field_name
        annotation = get_annotation_with_metadata(model, field_name)

        # Check if field name suggests it should be secret
        field_lower = field_name.lower()
        should_be_secret = any(pattern in field_lower for pattern in secret_patterns)

        if not should_be_secret:
            continue

        # Check if it's marked as secret
        is_marked_secret = False
        if get_origin(annotation) is Annotated:
            args = get_args(annotation)
            for arg in args[1:]:
                if isinstance(arg, BackendAIConfigMeta) and arg.secret:
                    is_marked_secret = True
                    break

        yield (field_path, is_marked_secret)


class TestManagerConfigFieldValidation:
    """Validate Manager config fields have BackendAIConfigMeta."""

    @pytest.fixture
    def manager_config(self) -> type[BaseModel]:
        from ai.backend.manager.config.unified import ManagerUnifiedConfig

        return ManagerUnifiedConfig

    def test_all_fields_have_meta(self, manager_config: type[BaseModel]) -> None:
        """All fields in ManagerUnifiedConfig should have BackendAIConfigMeta."""
        missing_fields = list(get_all_fields_without_meta(manager_config))

        if missing_fields:
            field_list = "\n".join(f"  - {path} ({typ})" for path, _, typ in missing_fields)
            pytest.fail(f"Fields missing BackendAIConfigMeta:\n{field_list}")

    def test_secret_fields_marked(self, manager_config: type[BaseModel]) -> None:
        """Fields with secret-like names should be marked with secret=True."""
        unmarked_secrets = [
            (path, marked) for path, marked in get_secret_fields(manager_config) if not marked
        ]

        if unmarked_secrets:
            field_list = "\n".join(f"  - {path}" for path, _ in unmarked_secrets)
            pytest.fail(f"Potential secret fields not marked with secret=True:\n{field_list}")


class TestAgentConfigFieldValidation:
    """Validate Agent config fields have BackendAIConfigMeta."""

    @pytest.fixture
    def agent_configs(self) -> list[type[BaseModel]]:
        from ai.backend.agent.config.unified import (
            AgentGlobalConfig,
            AgentOverrideConfig,
            AgentSpecificConfig,
        )

        return [AgentGlobalConfig, AgentSpecificConfig, AgentOverrideConfig]

    def test_all_fields_have_meta(self, agent_configs: list[type[BaseModel]]) -> None:
        """All fields in Agent configs should have BackendAIConfigMeta."""
        all_missing: list[tuple[str, str, type]] = []

        for config in agent_configs:
            missing = list(get_all_fields_without_meta(config))
            all_missing.extend([(f"{config.__name__}.{p}", n, t) for p, n, t in missing])

        if all_missing:
            field_list = "\n".join(f"  - {path} ({typ})" for path, _, typ in all_missing)
            pytest.fail(f"Fields missing BackendAIConfigMeta:\n{field_list}")


class TestStorageConfigFieldValidation:
    """Validate Storage config fields have BackendAIConfigMeta."""

    @pytest.fixture
    def storage_config(self) -> type[BaseModel]:
        from ai.backend.storage.config.unified import StorageProxyUnifiedConfig

        return StorageProxyUnifiedConfig

    def test_all_fields_have_meta(self, storage_config: type[BaseModel]) -> None:
        """All fields in StorageProxyUnifiedConfig should have BackendAIConfigMeta."""
        missing_fields = list(get_all_fields_without_meta(storage_config))

        if missing_fields:
            field_list = "\n".join(f"  - {path} ({typ})" for path, _, typ in missing_fields)
            pytest.fail(f"Fields missing BackendAIConfigMeta:\n{field_list}")


class TestWebConfigFieldValidation:
    """Validate Web config fields have BackendAIConfigMeta."""

    @pytest.fixture
    def web_config(self) -> type[BaseModel]:
        from ai.backend.web.config.unified import WebServerUnifiedConfig

        return WebServerUnifiedConfig

    def test_all_fields_have_meta(self, web_config: type[BaseModel]) -> None:
        """All fields in WebServerUnifiedConfig should have BackendAIConfigMeta."""
        missing_fields = list(get_all_fields_without_meta(web_config))

        if missing_fields:
            field_list = "\n".join(f"  - {path} ({typ})" for path, _, typ in missing_fields)
            pytest.fail(f"Fields missing BackendAIConfigMeta:\n{field_list}")


class TestAppProxyConfigFieldValidation:
    """Validate AppProxy config fields have BackendAIConfigMeta."""

    @pytest.fixture
    def appproxy_configs(self) -> list[type[BaseModel]]:
        from ai.backend.appproxy.coordinator.config import ProxyCoordinatorConfig
        from ai.backend.appproxy.worker.config import ProxyWorkerConfig

        return [ProxyCoordinatorConfig, ProxyWorkerConfig]

    def test_all_fields_have_meta(self, appproxy_configs: list[type[BaseModel]]) -> None:
        """All fields in AppProxy configs should have BackendAIConfigMeta."""
        all_missing: list[tuple[str, str, type]] = []

        for config in appproxy_configs:
            missing = list(get_all_fields_without_meta(config))
            all_missing.extend([(f"{config.__name__}.{p}", n, t) for p, n, t in missing])

        if all_missing:
            field_list = "\n".join(f"  - {path} ({typ})" for path, _, typ in all_missing)
            pytest.fail(f"Fields missing BackendAIConfigMeta:\n{field_list}")
