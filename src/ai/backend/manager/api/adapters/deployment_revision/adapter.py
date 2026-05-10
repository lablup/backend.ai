"""Deployment-revision adapter.

Hosts revision-side conversions kept out of ``DeploymentAdapter`` so the
deployment-revision orchestration paths (currently the admin bulk refresh)
can perform their ``ModelRevisionData → ModelRevisionCreator`` mapping in
the adapter layer rather than inside services. Services receive
already-converted ``ModelRevisionCreator`` instances.
"""

from __future__ import annotations

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.dto.manager.v2.deployment.response import (
    AdminRefreshDeploymentRevisionsPayload,
    RevisionRefreshResultInfo,
)
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.deployment.creator import (
    ModelRevisionCreator,
    VFolderMountsCreator,
)
from ai.backend.manager.data.deployment.types import (
    ExecutionSpec,
    ModelRevisionData,
    ResourceSpec,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.endpoint.conditions import DeploymentConditions
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.services.deployment.actions.refresh_deployment_revisions import (
    RefreshDeploymentRevisionsAction,
)
from ai.backend.manager.services.deployment.actions.search_deployments import (
    SearchDeploymentsAction,
)


class DeploymentRevisionAdapter(BaseAdapter):
    """Adapter for deployment-revision write-side orchestration.

    All ``ModelRevisionData → ModelRevisionCreator`` conversions live here
    so service methods stay free of cross-shape translation logic.
    """

    async def admin_refresh_deployment_revisions(
        self,
    ) -> AdminRefreshDeploymentRevisionsPayload:
        """Create and activate a fresh revision for every active deployment.

        Two-phase orchestration: ``search_deployments`` returns the active
        deployments along with each one's current ``ModelRevisionData``;
        this adapter projects each onto a ``ModelRevisionCreator``
        (per-item conversion failures surface in the response without
        aborting the sweep), and the batch refresh action processes the
        resulting ``creators_by_id`` map in a single service call.
        """
        active_querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[
                DeploymentConditions.by_lifecycle_stages(EndpointLifecycle.active_states()),
            ],
        )
        search_result = await self._processors.deployment.search_deployments.wait_for_complete(
            SearchDeploymentsAction(querier=active_querier)
        )
        creators_by_id: dict[DeploymentID, ModelRevisionCreator] = {}
        conversion_failures: list[RevisionRefreshResultInfo] = []
        for deployment in search_result.data:
            if deployment.revision is None:
                # No current revision (e.g., still PENDING with only a
                # deploying revision) — nothing to refresh from.
                continue
            try:
                creators_by_id[deployment.id] = self._creator_from_data(deployment.revision)
            except InvalidAPIParameters as exc:
                # Conversion failed (e.g., revision missing the model
                # vfolder after a SET-NULL FK cleanup). Surface it as a
                # per-deployment failure rather than aborting the bulk
                # refresh — same contract the inline service loop used
                # to provide via try/except.
                conversion_failures.append(
                    RevisionRefreshResultInfo(
                        deployment_id=deployment.id,
                        new_revision_id=None,
                        success=False,
                        failure_reason=f"{type(exc).__name__}: {exc}",
                    )
                )
        refresh_result = (
            await self._processors.deployment.refresh_deployment_revisions.wait_for_complete(
                RefreshDeploymentRevisionsAction(creators_by_id=creators_by_id)
            )
        )
        return AdminRefreshDeploymentRevisionsPayload(
            results=[
                *conversion_failures,
                *(
                    RevisionRefreshResultInfo(
                        deployment_id=r.deployment_id,
                        new_revision_id=r.new_revision_id,
                        success=r.success,
                        failure_reason=r.failure_reason,
                    )
                    for r in refresh_result.results
                ),
            ]
        )

    @staticmethod
    def _creator_from_data(data: ModelRevisionData) -> ModelRevisionCreator:
        """Project a persisted revision onto a ``ModelRevisionCreator``.

        ``model_definition`` is reset to ``None`` so
        ``DeploymentController.add_revision`` re-resolves it from the
        vfolder. ``revision_preset_id`` and ``preset_values`` carry over so
        the new revision keeps the same preset attribution.
        ``extra_mounts`` is left empty because ``add_revision`` does not
        propagate this field to the new revision spec.
        """
        if data.model_mount_config.vfolder_id is None:
            raise InvalidAPIParameters(
                f"Revision {data.id} has no model vfolder; cannot rebuild creator"
            )
        return ModelRevisionCreator(
            image_id=data.image_id,
            resource_spec=ResourceSpec(
                cluster_mode=data.cluster_config.mode,
                cluster_size=data.cluster_config.size,
                resource_slots=dict(data.resource_config.resource_slot),
                resource_opts=dict(data.resource_config.resource_opts) or None,
            ),
            mounts=VFolderMountsCreator(
                model_vfolder_id=data.model_mount_config.vfolder_id,
                model_definition_path=data.model_mount_config.definition_path or None,
                model_mount_destination=data.model_mount_config.mount_destination or "/models",
                extra_mounts=[],
            ),
            execution=ExecutionSpec(
                startup_command=data.startup_command,
                bootstrap_script=data.bootstrap_script,
                environ=(
                    {k: str(v) for k, v in data.model_runtime_config.environ.items()}
                    if data.model_runtime_config.environ
                    else None
                ),
                runtime_variant_id=data.model_runtime_config.runtime_variant_id,
                callback_url=data.callback_url,
                inference_runtime_config=data.model_runtime_config.inference_runtime_config,
            ),
            model_definition=None,
            revision_preset_id=data.revision_preset_id,
            preset_values=list(data.preset_values),
        )
