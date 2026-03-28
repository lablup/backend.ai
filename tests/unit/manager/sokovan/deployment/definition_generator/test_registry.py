"""
Tests for ModelDefinitionGeneratorRegistry implementation.
"""

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.config import ModelDefinition
from ai.backend.common.types import RuntimeVariant
from ai.backend.manager.data.deployment.types import (
    ExecutionSpec,
    MountMetadata,
)
from ai.backend.manager.errors.deployment import DefinitionFileNotFound
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.definition_generator.base import ModelDefinitionContext
from ai.backend.manager.sokovan.deployment.definition_generator.registry import (
    ModelDefinitionGeneratorRegistry,
    RegistryArgs,
)


@dataclass(frozen=True)
class VariantExpectation:
    name: str
    port: int
    health_check_path: str | None


@dataclass(frozen=True)
class OverridePathCase:
    description: str
    # model_definition_path passed to the context (None, empty, or a real filename)
    path: str | None
    # Whether the registry is expected to fetch the definition from vfolder storage
    expect_vfolder_fetch: bool


@dataclass(frozen=True)
class InvalidModelDefinitionCase:
    description: str
    value: ModelDefinition | None


VARIANT_EXPECTATIONS: dict[RuntimeVariant, VariantExpectation] = {
    RuntimeVariant.VLLM: VariantExpectation("vllm-model", 8000, "/health"),
    RuntimeVariant.NIM: VariantExpectation("nim-model", 8000, "/v1/health/ready"),
    RuntimeVariant.HUGGINGFACE_TGI: VariantExpectation("tgi-model", 3000, "/info"),
    RuntimeVariant.SGLANG: VariantExpectation("sglang-model", 9001, "/health"),
    RuntimeVariant.MODULAR_MAX: VariantExpectation("max-model", 8000, "/health"),
    RuntimeVariant.CMD: VariantExpectation("image-model", 8000, None),
}

NON_CUSTOM_VARIANTS = [v for v in RuntimeVariant if v != RuntimeVariant.CUSTOM]
VARIANTS_WITH_HEALTH_CHECK = [v for v in NON_CUSTOM_VARIANTS if v != RuntimeVariant.CMD]


def create_context(
    variant: RuntimeVariant,
    model_definition_path: str | None = None,
    model_definition: ModelDefinition | None = None,
) -> ModelDefinitionContext:
    return ModelDefinitionContext(
        mounts=MountMetadata(
            model_vfolder_id=uuid4(),
            model_mount_destination="/models",
            model_definition_path=model_definition_path,
            extra_mounts=[],
        ),
        execution=ExecutionSpec(
            runtime_variant=variant,
            startup_command="test command",
            bootstrap_script=None,
            environ=None,
        ),
        model_definition=model_definition,
    )


def create_override_dict(expected: VariantExpectation) -> dict[str, Any]:
    service: dict[str, Any] = {
        "start-command": "overridden-command",
        "port": expected.port,
    }
    if expected.health_check_path:
        service["health-check"] = {
            "path": expected.health_check_path,
            "interval": 30.0,
            "initial-delay": 600.0,
        }
    return {
        "models": [
            {
                "name": expected.name,
                "model-path": "/models",
                "service": service,
            }
        ]
    }


@pytest.fixture
def mock_repo() -> MagicMock:
    return MagicMock(spec=DeploymentRepository)


@pytest.fixture
def definition_generator_registry(mock_repo: MagicMock) -> ModelDefinitionGeneratorRegistry:
    """Registry with vfolder override disabled (default)."""
    return ModelDefinitionGeneratorRegistry(
        RegistryArgs(deployment_repository=mock_repo, enable_model_definition_override=False)
    )


@pytest.fixture
def definition_generator_registry_with_override(
    mock_repo: MagicMock,
) -> ModelDefinitionGeneratorRegistry:
    """Registry with vfolder override enabled for non-CUSTOM variants."""
    return ModelDefinitionGeneratorRegistry(
        RegistryArgs(deployment_repository=mock_repo, enable_model_definition_override=True)
    )


@pytest.fixture
def db_model_definition() -> ModelDefinition:
    """Model definition simulating user-provided override."""
    expected = VARIANT_EXPECTATIONS[RuntimeVariant.VLLM]
    return ModelDefinition.model_validate({
        "models": [
            {
                "name": expected.name,
                "model-path": "/models",
                "service": {
                    "start-command": "db-overridden-command",
                    "port": expected.port,
                },
            }
        ]
    })


@pytest.fixture
def storage_override_definition() -> dict[str, Any]:
    """Model definition dict simulating what is fetched from storage file."""
    expected = VARIANT_EXPECTATIONS[RuntimeVariant.VLLM]
    return {
        "models": [
            {
                "name": expected.name,
                "model-path": "/models",
                "service": {
                    "start-command": "storage-command",
                    "port": expected.port,
                },
            }
        ]
    }


class TestModelDefinitionGeneratorRegistry:
    def test_initializes_all_generators(
        self, definition_generator_registry: ModelDefinitionGeneratorRegistry
    ) -> None:
        for variant in RuntimeVariant:
            assert definition_generator_registry.get(variant) is not None

    @pytest.mark.parametrize("variant", NON_CUSTOM_VARIANTS)
    async def test_generates_definition_without_vfolder_path(
        self,
        definition_generator_registry: ModelDefinitionGeneratorRegistry,
        mock_repo: MagicMock,
        variant: RuntimeVariant,
    ) -> None:
        """Without model_definition_path, no vfolder fetch happens."""
        expected = VARIANT_EXPECTATIONS[variant]

        result = await definition_generator_registry.generate_model_definition(
            create_context(variant)
        )

        mock_repo.fetch_model_definition.assert_not_called()
        model = result.models[0]
        assert model.name == expected.name
        assert model.service is not None
        assert model.service.port == expected.port

    async def test_custom_variant_fetches_from_vfolder(
        self,
        definition_generator_registry: ModelDefinitionGeneratorRegistry,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.fetch_model_definition = AsyncMock(
            return_value={
                "models": [
                    {
                        "name": "custom-model",
                        "model_path": "/models",
                        "service": {"start_command": "cmd", "port": 8080},
                    }
                ]
            }
        )

        result = await definition_generator_registry.generate_model_definition(
            create_context(RuntimeVariant.CUSTOM, model_definition_path="model.yaml")
        )

        mock_repo.fetch_model_definition.assert_called_once()
        assert result.models[0].name == "custom-model"

    @pytest.mark.parametrize(
        "case",
        [
            OverridePathCase(description="none", path=None, expect_vfolder_fetch=False),
            OverridePathCase(description="empty", path="", expect_vfolder_fetch=False),
            OverridePathCase(description="exists", path="model.yaml", expect_vfolder_fetch=True),
        ],
        ids=lambda c: c.description,
    )
    async def test_override_requires_path(
        self,
        definition_generator_registry_with_override: ModelDefinitionGeneratorRegistry,
        mock_repo: MagicMock,
        case: OverridePathCase,
    ) -> None:
        expected = VARIANT_EXPECTATIONS[RuntimeVariant.VLLM]
        mock_repo.fetch_model_definition = AsyncMock(return_value=create_override_dict(expected))

        result = await definition_generator_registry_with_override.generate_model_definition(
            create_context(RuntimeVariant.VLLM, model_definition_path=case.path)
        )

        model = result.models[0]
        assert model.service is not None
        if case.expect_vfolder_fetch:
            mock_repo.fetch_model_definition.assert_called_once()
            assert model.service.start_command == "overridden-command"
        else:
            mock_repo.fetch_model_definition.assert_not_called()
            assert model.service.port == expected.port

    @pytest.mark.parametrize("variant", VARIANTS_WITH_HEALTH_CHECK)
    async def test_override_merges_with_generated(
        self,
        definition_generator_registry_with_override: ModelDefinitionGeneratorRegistry,
        mock_repo: MagicMock,
        variant: RuntimeVariant,
    ) -> None:
        expected = VARIANT_EXPECTATIONS[variant]
        mock_repo.fetch_model_definition = AsyncMock(return_value=create_override_dict(expected))

        result = await definition_generator_registry_with_override.generate_model_definition(
            create_context(variant, model_definition_path="model.yaml")
        )

        model = result.models[0]
        assert model.name == expected.name
        assert model.service is not None
        assert model.service.start_command == "overridden-command"
        assert model.service.health_check is not None
        assert model.service.health_check.interval == 30.0
        assert model.service.health_check.initial_delay == 600.0

    @pytest.mark.parametrize(
        "exception",
        [DefinitionFileNotFound, RuntimeError("error"), ValueError("error")],
        ids=["not_found", "runtime", "value"],
    )
    async def test_fallback_on_exception(
        self,
        definition_generator_registry_with_override: ModelDefinitionGeneratorRegistry,
        mock_repo: MagicMock,
        exception: Exception,
    ) -> None:
        mock_repo.fetch_model_definition = AsyncMock(side_effect=exception)
        expected = VARIANT_EXPECTATIONS[RuntimeVariant.VLLM]

        result = await definition_generator_registry_with_override.generate_model_definition(
            create_context(RuntimeVariant.VLLM, model_definition_path="model.yaml")
        )

        mock_repo.fetch_model_definition.assert_called_once()
        model = result.models[0]
        assert model.name == expected.name
        assert model.service is not None
        assert model.service.port == expected.port

    @pytest.mark.parametrize("variant", VARIANTS_WITH_HEALTH_CHECK)
    async def test_revision_db_model_definition_merges_with_generated(
        self,
        definition_generator_registry: ModelDefinitionGeneratorRegistry,
        variant: RuntimeVariant,
        db_model_definition: ModelDefinition,
    ) -> None:
        """User-provided model_definition is merged on top of generated definition."""
        result = await definition_generator_registry.generate_model_definition(
            create_context(variant, model_definition=db_model_definition)
        )

        model = result.models[0]
        assert model.service is not None
        assert model.service.start_command == "db-overridden-command"

    @pytest.mark.parametrize(
        "case",
        [
            InvalidModelDefinitionCase(description="not provided", value=None),
            InvalidModelDefinitionCase(description="empty definition", value=ModelDefinition()),
        ],
        ids=lambda c: c.description,
    )
    async def test_revision_model_definition_ignored_when_absent_or_empty(
        self,
        definition_generator_registry: ModelDefinitionGeneratorRegistry,
        case: InvalidModelDefinitionCase,
    ) -> None:
        """When model_definition is None or empty, generated definition is returned unchanged."""
        expected = VARIANT_EXPECTATIONS[RuntimeVariant.VLLM]

        result = await definition_generator_registry.generate_model_definition(
            create_context(RuntimeVariant.VLLM, model_definition=case.value)
        )

        model = result.models[0]
        assert model.name == expected.name
        assert model.service is not None
        assert model.service.port == expected.port

    async def test_user_override_takes_precedence_over_vfolder_definition(
        self,
        definition_generator_registry_with_override: ModelDefinitionGeneratorRegistry,
        mock_repo: MagicMock,
        db_model_definition: ModelDefinition,
        storage_override_definition: dict[str, Any],
    ) -> None:
        """User-provided model_definition has higher priority than vfolder file."""
        mock_repo.fetch_model_definition = AsyncMock(return_value=storage_override_definition)

        result = await definition_generator_registry_with_override.generate_model_definition(
            create_context(
                RuntimeVariant.VLLM,
                model_definition_path="model.yaml",
                model_definition=db_model_definition,
            )
        )

        model = result.models[0]
        assert model.service is not None
        assert model.service.start_command == "db-overridden-command"

    @pytest.fixture
    def custom_vfolder_definition(self) -> dict[str, Any]:
        """Model definition simulating vfolder model-definition.yaml for CUSTOM variant."""
        return {
            "models": [
                {
                    "name": "test-model",
                    "model-path": "/models",
                    "service": {
                        "start-command": ["python3", "-m", "http.server", "8080"],
                        "port": 8080,
                        "health-check": {
                            "path": "/",
                            "max-retries": 10,
                        },
                    },
                }
            ]
        }

    @pytest.fixture
    def custom_user_override(self) -> ModelDefinition:
        """User-provided override that changes port and health check for CUSTOM variant."""
        return ModelDefinition.model_validate({
            "models": [
                {
                    "name": "test-model",
                    "model-path": "/models",
                    "service": {
                        "start-command": ["python3", "-m", "http.server", "8080"],
                        "port": 9999,
                        "health-check": {
                            "path": "/healthz",
                            "max-retries": 3,
                        },
                    },
                }
            ]
        })

    async def test_custom_variant_merges_vfolder_and_user_override(
        self,
        definition_generator_registry: ModelDefinitionGeneratorRegistry,
        mock_repo: MagicMock,
        custom_vfolder_definition: dict[str, Any],
        custom_user_override: ModelDefinition,
    ) -> None:
        """CUSTOM variant: vfolder base + user override deep merged into DB."""
        mock_repo.fetch_model_definition = AsyncMock(return_value=custom_vfolder_definition)

        result = await definition_generator_registry.generate_model_definition(
            create_context(
                RuntimeVariant.CUSTOM,
                model_definition_path="model-definition.yaml",
                model_definition=custom_user_override,
            )
        )

        model = result.models[0]
        assert model.name == "test-model"
        assert model.model_path == "/models"  # preserved from vfolder
        assert model.service is not None
        assert model.service.start_command == [  # preserved from vfolder
            "python3",
            "-m",
            "http.server",
            "8080",
        ]
        assert model.service.port == 9999  # overridden by user
        assert model.service.health_check is not None
        assert model.service.health_check.path == "/healthz"  # overridden by user
        assert model.service.health_check.max_retries == 3  # overridden by user

    async def test_custom_variant_without_user_override_stores_vfolder_as_is(
        self,
        definition_generator_registry: ModelDefinitionGeneratorRegistry,
        mock_repo: MagicMock,
        custom_vfolder_definition: dict[str, Any],
    ) -> None:
        """CUSTOM variant without user override: vfolder definition stored unchanged."""
        mock_repo.fetch_model_definition = AsyncMock(return_value=custom_vfolder_definition)

        result = await definition_generator_registry.generate_model_definition(
            create_context(
                RuntimeVariant.CUSTOM,
                model_definition_path="model-definition.yaml",
                model_definition=None,
            )
        )

        model = result.models[0]
        assert model.name == "test-model"
        assert model.model_path == "/models"
        assert model.service is not None
        assert model.service.start_command == ["python3", "-m", "http.server", "8080"]
        assert model.service.port == 8080
        assert model.service.health_check is not None
        assert model.service.health_check.path == "/"
        assert model.service.health_check.max_retries == 10

    @pytest.fixture
    def vllm_vfolder_definition(self) -> dict[str, Any]:
        """Model definition simulating vfolder file for VLLM variant override."""
        return {
            "models": [
                {
                    "name": "vllm-model",
                    "model-path": "/models",
                    "service": {
                        "start-command": "vfolder-command",
                        "port": 8000,
                        "health-check": {
                            "path": "/health",
                            "max-retries": 20,
                            "initial-delay": 300.0,
                        },
                    },
                }
            ]
        }

    @pytest.fixture
    def vllm_user_override(self) -> ModelDefinition:
        """User-provided override that changes start-command and port for VLLM variant.
        health-check is absent so vfolder's health-check fields are fully preserved in the merge."""
        return ModelDefinition.model_validate({
            "models": [
                {
                    "name": "vllm-model",
                    "model-path": "/models",
                    "service": {
                        "start-command": "user-override-command",
                        "port": 9000,
                    },
                }
            ]
        })

    async def test_vfolder_and_user_override_merged_on_generated_definition(
        self,
        definition_generator_registry_with_override: ModelDefinitionGeneratorRegistry,
        mock_repo: MagicMock,
        vllm_vfolder_definition: dict[str, Any],
        vllm_user_override: ModelDefinition,
    ) -> None:
        """Non-CUSTOM with override enabled: vfolder file and user override are both
        deep-merged on top of the generator-produced definition."""
        mock_repo.fetch_model_definition = AsyncMock(return_value=vllm_vfolder_definition)

        result = await definition_generator_registry_with_override.generate_model_definition(
            create_context(
                RuntimeVariant.VLLM,
                model_definition_path="model.yaml",
                model_definition=vllm_user_override,
            )
        )

        model = result.models[0]
        assert model.service is not None
        # from user override (overrode vfolder and generator — vfolder had "vfolder-command")
        assert model.service.start_command == "user-override-command"
        assert model.service.port == 9000
        assert model.service.health_check is not None
        # from vfolder (preserved since user override has no health-check)
        assert model.service.health_check.initial_delay == 300.0
        assert model.service.health_check.path == "/health"
        assert model.service.health_check.max_retries == 20
