"""Base implementation of revision processor with common override logic."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional, override
from uuid import UUID

from ai.backend.common.types import RuntimeVariant
from ai.backend.manager.data.deployment.types import (
    ModelRevisionSpec,
    ModelRevisionSpecDraft,
    ModelServiceDefinition,
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
        model_definition_path: Optional[str],
        default_architecture: Optional[str] = None,
    ) -> ModelRevisionSpec:
        """
        Generate revision with common override logic and variant-specific validation.
        """
        service_definition = await self.load_service_definition(
            vfolder_id=vfolder_id,
            model_definition_path=model_definition_path,
            runtime_variant=draft_revision.execution.runtime_variant.value,
        )
        revision = self.merge_revision(draft_revision, service_definition, default_architecture)
        await self.validate_revision(revision)

        return revision

    @override
    async def load_service_definition(
        self,
        vfolder_id: UUID,
        model_definition_path: Optional[str],
        runtime_variant: str,
    ) -> Optional[ModelServiceDefinition]:
        """
        Load service definition from vfolder with field-level override.

        Override priority (later overrides earlier):
        1. Root level (base configuration)
        2. Runtime variant section (field-level override)

        Example service-definition.toml:
        ```toml
        # Root level (default for all variants)
        [environment]
        image = "default-image:latest"
        architecture = "x86_64"

        [resource_slots]
        cpu = 4
        mem = "16gb"

        [environ]
        MY_VAR = "default"

        # vllm variant (overrides specific fields only)
        [vllm.environment]
        image = "vllm-optimized:latest"

        [vllm.resource_slots]
        cpu = 8

        [vllm.environ]
        VLLM_SPECIFIC = "true"
        ```
        Result for vllm:
        - environment.image: "vllm-optimized:latest" (from vllm)
        - environment.architecture: "x86_64" (from root)
        - resource_slots.cpu: 8 (from vllm)
        - resource_slots.mem: "16gb" (from root)
        - environ: {MY_VAR: "default", VLLM_SPECIFIC: "true"} (merged)
        """
        service_definition_dict = await self._deployment_repository.fetch_service_definition(
            vfolder_id
        )
        if service_definition_dict is None:
            return None

        all_variant_keys = {variant.value for variant in RuntimeVariant}
        root_level_dict = {
            k: v for k, v in service_definition_dict.items() if k not in all_variant_keys
        }

        variant_overrides = service_definition_dict.get(runtime_variant, {})

        # Merge: root level + variant overrides (field-level)
        merged_dict = self._merge_service_definition_dicts(root_level_dict, variant_overrides)

        return ModelServiceDefinition.model_validate(merged_dict)

    def _merge_service_definition_dicts(self, base: dict, override: dict) -> dict:
        """
        Merge service definition dictionaries with field-level override.
        Override takes precedence over base for each nested field.

        For nested dicts (environment, resource_slots, environ),
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
        service_definition: Optional[ModelServiceDefinition],
        default_architecture: Optional[str] = None,
    ) -> ModelRevisionSpec:
        """
        Merge requested revision with service definition.

        Override priority (later overrides earlier):
        1. Default architecture from scaling group (lowest priority)
        2. Root level service definition (base)
        3. Runtime variant section in service definition
        4. API request (highest priority)

        If service definition is None, validates and converts request to revision spec.
        Otherwise, starts with service definition and applies request overrides.
        """
        if service_definition is None:
            # No service definition, validate and convert request directly
            return ModelRevisionSpec.model_validate(draft_revision.model_dump(mode="python"))

        return self._override_revision(draft_revision, service_definition, default_architecture)

    def _override_revision(
        self,
        draft_revision: ModelRevisionSpecDraft,
        service_definition: ModelServiceDefinition,
        default_architecture: Optional[str] = None,
    ) -> ModelRevisionSpec:
        """
        Merge service definition and API request with field-level override.
        API request takes precedence over service definition for each field.

        Override priority (later overrides earlier):
        1. Default architecture from scaling group (lowest priority)
        2. Service definition (already merged from root + variant)
        3. API request (field-level override, highest priority)
        """
        service_dict: dict = {}
        if service_definition.environment is not None:
            service_dict["environment"] = {
                "image": service_definition.environment.image,
                "architecture": service_definition.environment.architecture,
            }

        if service_definition.resource_slots is not None:
            service_dict["resource_slots"] = service_definition.resource_slots

        if service_definition.environ is not None:
            service_dict["environ"] = service_definition.environ

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

        # 2. Service definition overrides default
        if "environment" in service_dict:
            merged_dict["image_identifier"]["canonical"] = service_dict["environment"]["image"]
            if service_dict["environment"]["architecture"] is not None:
                merged_dict["image_identifier"]["architecture"] = service_dict["environment"][
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

        if "resource_slots" in service_dict:
            merged_dict["resource_spec"]["resource_slots"] = service_dict["resource_slots"]

        if request_dict["resource_spec"]["resource_slots"] is not None:
            # Field-level merge for resource_slots
            base_slots = merged_dict["resource_spec"].get("resource_slots", {})
            request_slots = request_dict["resource_spec"]["resource_slots"]
            merged_dict["resource_spec"]["resource_slots"] = {**base_slots, **request_slots}

        # Merge environ: service definition as base, request overrides
        service_environ = service_dict.get("environ", {})
        request_environ = request_dict["execution"].get("environ") or {}
        merged_environ = {**service_environ, **request_environ}
        merged_dict["execution"]["environ"] = merged_environ if merged_environ else None

        return ModelRevisionSpec.model_validate(merged_dict)

    async def validate_revision(self, revision: ModelRevisionSpec) -> None:
        """
        Default validation does nothing.
        Subclasses can override for variant-specific validation.
        """
        pass
