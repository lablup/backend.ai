"""Base implementation of revision processor with common override logic."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, override
from uuid import UUID

from ai.backend.common.types import RuntimeVariant
from ai.backend.manager.data.deployment.types import (
    DeploymentConfig,
    ModelRevisionSpec,
    ModelRevisionSpecDraft,
)
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.revision_generator.abc import RevisionGenerator


class BaseRevisionGenerator(RevisionGenerator):
    """
    Base implementation of revision processor.
    Subclasses only need to implement variant-specific validation.
    """

    _deployment_repository: DeploymentRepository

    def __init__(self, deployment_repository: DeploymentRepository) -> None:
        self._deployment_repository = deployment_repository

    @override
    async def generate_revision(
        self,
        draft_revision: ModelRevisionSpecDraft,
        vfolder_id: UUID,
        default_architecture: str | None = None,
    ) -> ModelRevisionSpec:
        """
        Generate revision with common override logic and variant-specific validation.
        """
        deployment_config = await self.load_deployment_config(
            vfolder_id=vfolder_id,
            runtime_variant=draft_revision.execution.runtime_variant.value,
        )
        revision = self.merge_revision(draft_revision, deployment_config, default_architecture)
        await self.validate_revision(revision)

        return revision

    @override
    async def load_deployment_config(
        self,
        vfolder_id: UUID,
        runtime_variant: str,
    ) -> DeploymentConfig | None:
        """
        Load deployment config from vfolder with field-level override.

        Override priority (later overrides earlier):
        1. Root level (base configuration)
        2. Runtime variant section (field-level override)

        Example deployment-config.yaml:
        ```yaml
        # Root level (default for all variants)
        environment:
          image: "default-image:latest"
          architecture: "x86_64"

        resource_slots:
          cpu: 4
          mem: "16gb"

        environ:
          MY_VAR: "default"

        resource_opts:
          shmem: "8g"

        # vllm variant (overrides specific fields only)
        vllm:
          environment:
            image: "vllm-optimized:latest"
          resource_slots:
            cpu: 8
          environ:
            VLLM_SPECIFIC: "true"
          resource_opts:
            shmem: "32g"
        ```
        Result for vllm:
        - environment.image: "vllm-optimized:latest" (from vllm)
        - environment.architecture: "x86_64" (from root)
        - resource_slots.cpu: 8 (from vllm)
        - resource_slots.mem: "16gb" (from root)
        - resource_opts.shmem: "32g" (from vllm variant)
        - environ: {MY_VAR: "default", VLLM_SPECIFIC: "true"} (merged)
        """
        deployment_config_dict = await self._deployment_repository.fetch_deployment_config(
            vfolder_id
        )
        if deployment_config_dict is None:
            return None

        all_variant_keys = {variant.value for variant in RuntimeVariant}
        root_level_dict = {
            k: v for k, v in deployment_config_dict.items() if k not in all_variant_keys
        }

        variant_overrides = deployment_config_dict.get(runtime_variant, {})

        # Merge: root level + variant overrides (field-level)
        merged_dict = self._merge_deployment_config_dicts(root_level_dict, variant_overrides)

        return DeploymentConfig.model_validate(merged_dict)

    def _merge_deployment_config_dicts(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Merge deployment config dictionaries with field-level override.
        Override takes precedence over base for each nested field.

        For nested dicts (environment, resource_slots, resource_opts, environ),
        merge field by field rather than replacing the entire dict.
        """
        merged = base.copy()

        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # Deep merge for nested dicts (field-level override)
                merged[key] = {**merged[key], **value}
            else:
                # Simple override for non-dict values
                merged[key] = value

        return merged

    @override
    def merge_revision(
        self,
        draft_revision: ModelRevisionSpecDraft,
        deployment_config: DeploymentConfig | None,
        default_architecture: str | None = None,
    ) -> ModelRevisionSpec:
        """
        Merge requested revision with deployment config.

        Override priority (later overrides earlier):
        1. Default architecture from scaling group (lowest priority)
        2. Root level deployment config (base)
        3. Runtime variant section in deployment config
        4. API request (highest priority)

        If deployment config is None, creates an empty one to ensure
        default_architecture and other common logic is applied consistently.
        """
        effective_config = deployment_config or DeploymentConfig()
        return self._override_revision(draft_revision, effective_config, default_architecture)

    def _override_revision(
        self,
        draft_revision: ModelRevisionSpecDraft,
        deployment_config: DeploymentConfig,
        default_architecture: str | None = None,
    ) -> ModelRevisionSpec:
        """
        Merge deployment config and API request with field-level override.
        API request takes precedence over deployment config for each field.

        Override priority (later overrides earlier):
        1. Default architecture from scaling group (lowest priority)
        2. Deployment config (already merged from root + variant)
        3. API request (field-level override, highest priority)
        """
        config_dict: dict[str, Any] = {}
        if deployment_config.environment is not None:
            config_dict["environment"] = {
                "image": deployment_config.environment.image,
                "architecture": deployment_config.environment.architecture,
            }

        if deployment_config.resource_slots is not None:
            config_dict["resource_slots"] = deployment_config.resource_slots

        if deployment_config.environ is not None:
            config_dict["environ"] = deployment_config.environ

        if deployment_config.resource_opts is not None:
            config_dict["resource_opts"] = deployment_config.resource_opts

        request_dict = draft_revision.model_dump(mode="python")
        merged_dict: dict[str, Any] = {
            "image_identifier": {},
            "resource_spec": {
                "cluster_mode": request_dict["resource_spec"]["cluster_mode"],
                "cluster_size": request_dict["resource_spec"]["cluster_size"],
                "resource_opts": request_dict["resource_spec"]["resource_opts"],
            },
            "mounts": asdict(draft_revision.mounts),
            "execution": {
                "runtime_variant": request_dict["execution"]["runtime_variant"],
                "startup_command": request_dict["execution"]["startup_command"],
            },
        }

        # 1. Default architecture from scaling group (lowest priority)
        if default_architecture is not None:
            merged_dict["image_identifier"]["architecture"] = default_architecture

        # 2. Deployment config overrides default
        if "environment" in config_dict:
            merged_dict["image_identifier"]["canonical"] = config_dict["environment"]["image"]
            if config_dict["environment"]["architecture"] is not None:
                merged_dict["image_identifier"]["architecture"] = config_dict["environment"][
                    "architecture"
                ]

        # 3. API request overrides all (highest priority)
        if request_dict["image_identifier"]["canonical"] is not None:
            merged_dict["image_identifier"]["canonical"] = request_dict["image_identifier"][
                "canonical"
            ]
        if request_dict["image_identifier"]["architecture"] is not None:
            merged_dict["image_identifier"]["architecture"] = request_dict["image_identifier"][
                "architecture"
            ]

        if "resource_slots" in config_dict:
            merged_dict["resource_spec"]["resource_slots"] = config_dict["resource_slots"]

        if request_dict["resource_spec"]["resource_slots"] is not None:
            # Field-level merge for resource_slots
            base_slots = merged_dict["resource_spec"].get("resource_slots", {})
            request_slots = request_dict["resource_spec"]["resource_slots"]
            merged_dict["resource_spec"]["resource_slots"] = {**base_slots, **request_slots}

        # Merge resource_opts: deployment config as base, request overrides field-level
        if "resource_opts" in config_dict:
            merged_dict["resource_spec"]["resource_opts"] = config_dict["resource_opts"]

        if request_dict["resource_spec"]["resource_opts"] is not None:
            base_opts = merged_dict["resource_spec"].get("resource_opts") or {}
            request_opts = request_dict["resource_spec"]["resource_opts"]
            merged_dict["resource_spec"]["resource_opts"] = {**base_opts, **request_opts}

        # Merge environ: deployment config as base, request overrides
        config_environ = config_dict.get("environ", {})
        request_environ = request_dict["execution"].get("environ") or {}
        merged_environ = {**config_environ, **request_environ}
        merged_dict["execution"]["environ"] = merged_environ if merged_environ else None

        return ModelRevisionSpec.model_validate(merged_dict)

    async def validate_revision(self, revision: ModelRevisionSpec) -> None:
        """
        Default validation does nothing.
        Subclasses can override for variant-specific validation.
        """
        pass
