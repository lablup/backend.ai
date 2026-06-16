"""Collect revision drafts from every source for a single merge pass.

The reader is the only object that knows about every layer that feeds into
a ``RevisionDraft`` merge chain: the runtime-variant baseline definition,
revision presets, ``deployment-config.yaml`` / ``model-definition.yaml``
stored on the model vfolder, and finally the caller-supplied request
draft. It owns the read phase; the controller performs the merge and the
persistence phase separately.

``reads_vfolder_config_files`` on the runtime variant gates vfolder file
reads — variants that do not ship their own config files (every variant
except ``custom`` at time of writing) skip storage access entirely.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai.backend.common.config import ModelConfigDraft, ModelDefinitionDraft
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.identifier.deployment_preset import DeploymentPresetID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.types import ClusterMode
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    ExecutionSpec,
    MountMetadata,
    RevisionDraft,
)
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
    ResourceSlotEntryData,
)
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData

if TYPE_CHECKING:
    from ai.backend.manager.repositories.deployment import DeploymentRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("RevisionDraftReader",)


class RevisionDraftReader:
    """Fan out the DB + storage reads that feed the revision merge chain.

    One public method per API path (legacy create, legacy modify, v2 add).
    Each returns the ordered list of drafts the controller layers via
    ``RevisionDraft.merge`` — lowest priority first. The model mount
    destination is added as the lowest-priority ``model_path`` default.
    """

    _deployment_repository: DeploymentRepository

    def __init__(
        self,
        deployment_repository: DeploymentRepository,
    ) -> None:
        self._deployment_repository = deployment_repository

    async def read_for_legacy_model_service_deployment(
        self,
        *,
        request_draft: RevisionDraft,
        execution: ExecutionSpec,
        preset_id: DeploymentPresetID | None,
    ) -> list[RevisionDraft]:
        """Legacy model-serving create: no base revision.

        Merge order (low → high):
          1. model mount destination as model_path default
          2. runtime-variant default model definition
          3. revision preset (if supplied)
          4. deployment-config.yaml  (only when the variant reads vfolder files)
          5. model-definition.yaml   (only when the variant reads vfolder files)
          6. request
        """
        bundle = await self._deployment_repository.load_legacy_model_service_deployment_read_bundle(
            runtime_variant_id=execution.runtime_variant_id,
            preset_id=preset_id,
        )
        if request_draft.mounts is None:
            raise InvalidAPIParameters("mounts are required to read revision drafts")
        drafts: list[RevisionDraft] = [
            self._model_mount_path_default_draft(request_draft.mounts),
            self._variant_baseline_to_draft(bundle.variant),
        ]
        if bundle.preset is not None:
            drafts.append(self._preset_to_draft(bundle.preset, bundle.preset_resource_slots or []))
        drafts.extend(await self._read_vfolder_drafts(request_draft.mounts, bundle.variant))
        drafts.append(request_draft)
        return drafts

    async def read_for_deployment_revision(
        self,
        *,
        runtime_variant_id: RuntimeVariantID,
        request_draft: RevisionDraft,
        preset_id: DeploymentPresetID | None,
    ) -> list[RevisionDraft]:
        """v2 ``add_revision``: typed variant id, no base layer."""
        bundle = await self._deployment_repository.load_deployment_revision_read_bundle(
            runtime_variant_id=runtime_variant_id,
            preset_id=preset_id,
        )
        if request_draft.mounts is None:
            raise InvalidAPIParameters("mounts are required to read revision drafts")
        drafts: list[RevisionDraft] = [
            self._model_mount_path_default_draft(request_draft.mounts),
            self._variant_baseline_to_draft(bundle.variant),
        ]
        if bundle.preset is not None:
            drafts.append(self._preset_to_draft(bundle.preset, bundle.preset_resource_slots or []))
        drafts.extend(await self._read_vfolder_drafts(request_draft.mounts, bundle.variant))
        drafts.append(request_draft)
        return drafts

    def _variant_baseline_to_draft(self, variant: RuntimeVariantData) -> RevisionDraft:
        """Project the variant's ``default_model_definition`` into a RevisionDraft."""
        return RevisionDraft(model_definition=variant.default_model_definition)

    def _preset_to_draft(
        self,
        preset: DeploymentRevisionPresetData,
        slot_entries: list[ResourceSlotEntryData],
    ) -> RevisionDraft:
        resource_slots = {entry.resource_type: entry.quantity for entry in slot_entries}
        resource_opts = {o.name: o.value for o in preset.resource_opts}
        environ = {e.key: e.value for e in preset.environ}
        model_definition: ModelDefinitionDraft | None = (
            ModelDefinitionDraft.model_validate(preset.model_definition)
            if preset.model_definition
            else None
        )
        return RevisionDraft(
            image_id=preset.image_id,
            resource_slots=resource_slots or None,
            resource_opts=resource_opts or None,
            cluster_mode=ClusterMode(preset.cluster_mode) if preset.cluster_mode else None,
            cluster_size=preset.cluster_size,
            startup_command=preset.startup_command,
            bootstrap_script=preset.bootstrap_script,
            environ=environ or None,
            model_definition=model_definition,
            runtime_variant_preset_values=preset.runtime_variant_preset_values,
        )

    def _model_mount_path_default_draft(
        self,
        mounts: MountMetadata,
    ) -> RevisionDraft:
        """Build the lowest-priority model_path default draft."""
        model_definition = ModelDefinitionDraft(
            models=[ModelConfigDraft(model_path=mounts.model_mount_destination)]
        )
        return RevisionDraft(mounts=mounts, model_definition=model_definition)

    async def _read_vfolder_drafts(
        self,
        mounts: MountMetadata,
        variant: RuntimeVariantData,
    ) -> list[RevisionDraft]:
        """Read ``deployment-config.yaml`` + ``model-definition.yaml`` when allowed.

        Gated by ``reads_vfolder_config_files`` on the variant. A missing or
        malformed file is logged and skipped — the merge chain remains valid
        without the optional overlay.
        """
        if not variant.reads_vfolder_config_files:
            return []
        vfolder_id = mounts.model_vfolder_id

        drafts: list[RevisionDraft] = []
        try:
            config = await self._deployment_repository.fetch_deployment_config(vfolder_id)
        except Exception:
            log.warning(
                "Failed to read deployment config from vfolder {}, skipping",
                vfolder_id,
                exc_info=True,
            )
            config = None
        if config is not None:
            drafts.append(
                RevisionDraft(
                    image_id=config.image_id,
                    resource_slots=config.resource_slots,
                    resource_opts=config.resource_opts,
                    environ=config.environ,
                )
            )

        try:
            model_def = await self._deployment_repository.fetch_model_definition(
                vfolder_id=vfolder_id,
                model_definition_path=mounts.model_definition_path,
            )
        except Exception:
            log.warning(
                "Failed to read model-definition.yaml from vfolder {}, skipping",
                vfolder_id,
                exc_info=True,
            )
            model_def = None
        if model_def is not None:
            drafts.append(
                RevisionDraft(
                    mounts=MountMetadata(
                        model_vfolder_id=mounts.model_vfolder_id,
                        model_definition_path=model_def.path,
                        model_mount_destination=mounts.model_mount_destination,
                        extra_mounts=list(mounts.extra_mounts),
                        vfolder_subpath=mounts.vfolder_subpath,
                    ),
                    model_definition=model_def.model_definition,
                )
            )
        return drafts
