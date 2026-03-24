"""
Tests for ModelDefinitionGeneratorRegistry implementation.
"""

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.data.deployment.types import (
    ExecutionSpec,
    ModelRevisionSpec,
    MountMetadata,
    ResourceSpec,
)
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.errors.deployment import DefinitionFileNotFound
from ai.backend.manager.repositories.deployment import DeploymentRepository
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
class InvalidModelDefinitionCase:
    description: str
    value: dict[str, Any] | None


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


def create_revision(
    variant: RuntimeVariant,
    model_definition_path: str | None = None,
    model_definition: dict[str, Any] | None = None,
) -> ModelRevisionSpec:
    return ModelRevisionSpec(
        image_identifier=ImageIdentifier(
            canonical=f"{variant.value}-image:latest", architecture="x86_64"
        ),
        resource_spec=ResourceSpec(
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            resource_slots={"cpu": 4, "mem": "8gb"},
            resource_opts=None,
        ),
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
def db_model_definition() -> dict[str, Any]:
    """Model definition dict simulating what is stored in the DB revision record."""
    expected = VARIANT_EXPECTATIONS[RuntimeVariant.VLLM]
    return {
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
    }


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
    def test_initializes_all_generators(self, mock_repo: MagicMock) -> None:
        registry = ModelDefinitionGeneratorRegistry(
            RegistryArgs(deployment_repository=mock_repo, enable_model_definition_override=False)
        )
        for variant in RuntimeVariant:
            assert registry.get(variant) is not None

    @pytest.mark.parametrize("variant", NON_CUSTOM_VARIANTS)
    async def test_generates_definition_without_override(
        self, mock_repo: MagicMock, variant: RuntimeVariant
    ) -> None:
        registry = ModelDefinitionGeneratorRegistry(
            RegistryArgs(deployment_repository=mock_repo, enable_model_definition_override=False)
        )
        expected = VARIANT_EXPECTATIONS[variant]

        result = await registry.generate_model_definition(
            create_revision(variant, model_definition_path="model.yaml")
        )

        mock_repo.fetch_model_definition.assert_not_called()
        model = result.models[0]
        assert model.name == expected.name
        assert model.service is not None
        assert model.service.port == expected.port

    @pytest.mark.parametrize("enable_override", [True, False])
    async def test_custom_variant_always_fetches(
        self, mock_repo: MagicMock, enable_override: bool
    ) -> None:
        registry = ModelDefinitionGeneratorRegistry(
            RegistryArgs(
                deployment_repository=mock_repo, enable_model_definition_override=enable_override
            )
        )
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

        result = await registry.generate_model_definition(create_revision(RuntimeVariant.CUSTOM))

        mock_repo.fetch_model_definition.assert_called_once()
        assert result.models[0].name == "custom-model"

    @pytest.mark.parametrize(
        ("path", "should_fetch"),
        [(None, False), ("", False), ("model.yaml", True)],
        ids=["none", "empty", "exists"],
    )
    async def test_override_requires_path(
        self, mock_repo: MagicMock, path: str | None, should_fetch: bool
    ) -> None:
        registry = ModelDefinitionGeneratorRegistry(
            RegistryArgs(deployment_repository=mock_repo, enable_model_definition_override=True)
        )
        expected = VARIANT_EXPECTATIONS[RuntimeVariant.VLLM]
        mock_repo.fetch_model_definition = AsyncMock(return_value=create_override_dict(expected))

        result = await registry.generate_model_definition(
            create_revision(RuntimeVariant.VLLM, model_definition_path=path)
        )

        model = result.models[0]
        assert model.service is not None
        if should_fetch:
            mock_repo.fetch_model_definition.assert_called_once()
            assert model.service.start_command == "overridden-command"
        else:
            mock_repo.fetch_model_definition.assert_not_called()
            assert model.service.port == expected.port

    @pytest.mark.parametrize("variant", VARIANTS_WITH_HEALTH_CHECK)
    async def test_override_merges_with_generated(
        self, mock_repo: MagicMock, variant: RuntimeVariant
    ) -> None:
        registry = ModelDefinitionGeneratorRegistry(
            RegistryArgs(deployment_repository=mock_repo, enable_model_definition_override=True)
        )
        expected = VARIANT_EXPECTATIONS[variant]
        mock_repo.fetch_model_definition = AsyncMock(return_value=create_override_dict(expected))

        result = await registry.generate_model_definition(
            create_revision(variant, model_definition_path="model.yaml")
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
    async def test_fallback_on_exception(self, mock_repo: MagicMock, exception: Exception) -> None:
        registry = ModelDefinitionGeneratorRegistry(
            RegistryArgs(deployment_repository=mock_repo, enable_model_definition_override=True)
        )
        mock_repo.fetch_model_definition = AsyncMock(side_effect=exception)
        expected = VARIANT_EXPECTATIONS[RuntimeVariant.VLLM]

        result = await registry.generate_model_definition(
            create_revision(RuntimeVariant.VLLM, model_definition_path="model.yaml")
        )

        mock_repo.fetch_model_definition.assert_called_once()
        model = result.models[0]
        assert model.name == expected.name
        assert model.service is not None
        assert model.service.port == expected.port

    @pytest.mark.parametrize("variant", VARIANTS_WITH_HEALTH_CHECK)
    async def test_revision_db_model_definition_merges_with_generated(
        self, mock_repo: MagicMock, variant: RuntimeVariant, db_model_definition: dict[str, Any]
    ) -> None:
        """DB model_definition is merged on top of generated definition."""
        registry = ModelDefinitionGeneratorRegistry(
            RegistryArgs(deployment_repository=mock_repo, enable_model_definition_override=False)
        )

        result = await registry.generate_model_definition(
            create_revision(variant, model_definition=db_model_definition)
        )

        model = result.models[0]
        assert model.service is not None
        assert model.service.start_command == "db-overridden-command"

    @pytest.mark.parametrize(
        "case",
        [
            InvalidModelDefinitionCase(description="not provided", value=None),
            InvalidModelDefinitionCase(description="empty dict", value={}),
            InvalidModelDefinitionCase(
                description="malformed models field", value={"models": "not-a-list"}
            ),
        ],
        ids=lambda c: c.description,
    )
    async def test_revision_db_model_definition_ignored_when_absent_or_invalid(
        self, mock_repo: MagicMock, case: InvalidModelDefinitionCase
    ) -> None:
        """When model_definition is None, empty, or invalid, generated definition is returned unchanged."""
        registry = ModelDefinitionGeneratorRegistry(
            RegistryArgs(deployment_repository=mock_repo, enable_model_definition_override=False)
        )
        expected = VARIANT_EXPECTATIONS[RuntimeVariant.VLLM]

        result = await registry.generate_model_definition(
            create_revision(RuntimeVariant.VLLM, model_definition=case.value)
        )

        model = result.models[0]
        assert model.name == expected.name
        assert model.service is not None
        assert model.service.port == expected.port

    async def test_storage_override_takes_precedence_over_db_model_definition(
        self,
        mock_repo: MagicMock,
        db_model_definition: dict[str, Any],
        storage_override_definition: dict[str, Any],
    ) -> None:
        """Storage file override has higher priority than DB model_definition."""
        registry = ModelDefinitionGeneratorRegistry(
            RegistryArgs(deployment_repository=mock_repo, enable_model_definition_override=True)
        )
        mock_repo.fetch_model_definition = AsyncMock(return_value=storage_override_definition)

        result = await registry.generate_model_definition(
            create_revision(
                RuntimeVariant.VLLM,
                model_definition_path="model.yaml",
                model_definition=db_model_definition,
            )
        )

        model = result.models[0]
        assert model.service is not None
        assert model.service.start_command == "storage-command"
