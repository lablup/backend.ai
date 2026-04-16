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
    Optional ``resource_spec`` / ``execution`` are projected only when set;
    leaving them ``None`` lets preset (or other lower-priority sources)
    supply the missing fields without being overridden.
    """
    rs = creator.resource_spec
    ex = creator.execution
    return RevisionDraft(
        image_id=creator.image_id,
        resource_slots=rs.resource_slots if rs is not None else None,
        resource_opts=rs.resource_opts if rs is not None else None,
        cluster_mode=rs.cluster_mode if rs is not None else None,
        cluster_size=rs.cluster_size if rs is not None else None,
        startup_command=ex.startup_command if ex is not None else None,
        bootstrap_script=ex.bootstrap_script if ex is not None else None,
        environ=ex.environ if ex is not None else None,
        runtime_variant=ex.runtime_variant if ex is not None else None,
        callback_url=ex.callback_url if ex is not None else None,
        inference_runtime_config=ex.inference_runtime_config if ex is not None else None,
        model_definition=creator.model_definition,
    )
