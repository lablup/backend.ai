"""Helpers that convert request-level revision inputs into a RevisionDraft.

The request always carries the highest-priority values; these helpers simply
project request fields into the flat ``RevisionDraft`` shape so the
controller can feed them into ``merge_revision_drafts`` alongside drafts
produced from other sources (deployment-config.yaml, preset,
model-definition.yaml).
"""

from __future__ import annotations

from ai.backend.manager.data.deployment.creator import ModelRevisionCreator
from ai.backend.manager.data.deployment.types import ModelRevisionSpecDraft, RevisionDraft


def revision_draft_from_spec(spec: ModelRevisionSpecDraft) -> RevisionDraft:
    """Build a RevisionDraft from a legacy request (pre-resolve image).

    Mount-identifying fields (vfolder, destination, definition_path) are not
    part of RevisionDraft — they live on ``MountMetadata`` and are passed
    alongside into ``add_revision``.
    """
    return RevisionDraft(
        image_canonical=spec.image_identifier.canonical,
        image_architecture=spec.image_identifier.architecture,
        resource_slots=spec.resource_spec.resource_slots,
        resource_opts=spec.resource_spec.resource_opts,
        cluster_mode=spec.resource_spec.cluster_mode,
        cluster_size=spec.resource_spec.cluster_size,
        startup_command=spec.execution.startup_command,
        bootstrap_script=spec.execution.bootstrap_script,
        environ=spec.execution.environ,
        runtime_variant=spec.execution.runtime_variant,
        callback_url=spec.execution.callback_url,
        inference_runtime_config=spec.execution.inference_runtime_config,
    )


def revision_draft_from_creator(creator: ModelRevisionCreator) -> RevisionDraft:
    """Build a RevisionDraft from a v2 request (image already resolved).

    Mount-identifying fields are excluded — see ``revision_draft_from_spec``.
    """
    return RevisionDraft(
        image_id=creator.image_id,
        resource_slots=creator.resource_spec.resource_slots,
        resource_opts=creator.resource_spec.resource_opts,
        cluster_mode=creator.resource_spec.cluster_mode,
        cluster_size=creator.resource_spec.cluster_size,
        startup_command=creator.execution.startup_command,
        bootstrap_script=creator.execution.bootstrap_script,
        environ=creator.execution.environ,
        runtime_variant=creator.execution.runtime_variant,
        callback_url=creator.execution.callback_url,
        inference_runtime_config=creator.execution.inference_runtime_config,
        model_definition=creator.model_definition,
    )
