"""Revision draft generator backed by deployment-config.yaml in the model vfolder."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from ai.backend.common.types import MODEL_SERVICE_RUNTIME_PROFILES, RuntimeVariant
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import DeploymentConfig, RevisionDraft
from ai.backend.manager.repositories.deployment import DeploymentRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DeploymentConfigDraftGenerator:
    """Load deployment-config.yaml from the model vfolder and emit a RevisionDraft.

    The file is read independently of any other source — the generator does
    not know about user requests, presets, or model definitions. Failure to
    load falls back to an empty draft so the pipeline remains unaffected.
    """

    _deployment_repository: DeploymentRepository

    def __init__(self, deployment_repository: DeploymentRepository) -> None:
        self._deployment_repository = deployment_repository

    async def generate(
        self,
        vfolder_id: UUID,
        runtime_variant: RuntimeVariant,
    ) -> RevisionDraft:
        try:
            config_dict = await self._deployment_repository.fetch_deployment_config(vfolder_id)
        except Exception:
            log.warning(
                "Failed to load deployment-config.yaml for vfolder {}, proceeding without it",
                vfolder_id,
                exc_info=True,
            )
            return RevisionDraft()
        if config_dict is None:
            return RevisionDraft()

        variant_keys = set(MODEL_SERVICE_RUNTIME_PROFILES.keys())
        root_dict = {k: v for k, v in config_dict.items() if k not in variant_keys}
        variant_overrides = config_dict.get(runtime_variant, {})
        merged = self._merge_dicts(root_dict, variant_overrides)
        config = DeploymentConfig.model_validate(merged)
        return self._to_draft(config)

    def _merge_dicts(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        merged = base.copy()
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value
        return merged

    def _to_draft(self, config: DeploymentConfig) -> RevisionDraft:
        return RevisionDraft(
            image_canonical=config.environment.image if config.environment else None,
            image_architecture=config.environment.architecture if config.environment else None,
            resource_slots=config.resource_slots,
            resource_opts=config.resource_opts,
            environ=config.environ,
        )
