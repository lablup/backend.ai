"""Deployment-revision adapter.

Hosts revision-side conversions kept out of ``DeploymentAdapter`` so the
deployment-revision orchestration paths (currently the admin bulk refresh)
can perform their ``ModelRevisionData → ModelRevisionCreator`` mapping in
the adapter layer rather than inside services. Services receive
already-converted ``ModelRevisionCreator`` instances.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.deployment.response import (
    AdminRefreshDeploymentRevisionsPayload,
    RevisionRefreshResultInfo,
)
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
from ai.backend.manager.services.deployment.actions.list_active_deployments_with_current_revision import (
    ListActiveDeploymentsWithCurrentRevisionAction,
)
from ai.backend.manager.services.deployment.actions.refresh_deployment_revision import (
    RefreshDeploymentRevisionAction,
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

        Two-phase orchestration: a read-side action returns
        ``(deployment_id, ModelRevisionData)`` pairs, this adapter projects
        each pair into a ``ModelRevisionCreator`` (failures here surface
        per-item without aborting the whole sweep), and the per-deployment
        refresh action runs the controller call.
        """
        list_result = await self._processors.deployment.list_active_deployments_with_current_revision.wait_for_complete(
            ListActiveDeploymentsWithCurrentRevisionAction()
        )
        results: list[RevisionRefreshResultInfo] = []
        for revision in list_result.revisions:
            try:
                creator = self._creator_from_data(revision)
            except InvalidAPIParameters as exc:
                # Conversion failed (e.g., revision missing the model
                # vfolder after a SET-NULL FK cleanup). Surface it as a
                # per-deployment failure rather than aborting the bulk
                # refresh — same contract the inline service loop used
                # to provide via try/except.
                results.append(
                    RevisionRefreshResultInfo(
                        deployment_id=revision.deployment_id,
                        new_revision_id=None,
                        success=False,
                        failure_reason=f"{type(exc).__name__}: {exc}",
                    )
                )
                continue
            refresh_result = (
                await self._processors.deployment.refresh_deployment_revision.wait_for_complete(
                    RefreshDeploymentRevisionAction(
                        deployment_id=revision.deployment_id,
                        creator=creator,
                    )
                )
            )
            r = refresh_result.result
            results.append(
                RevisionRefreshResultInfo(
                    deployment_id=r.deployment_id,
                    new_revision_id=r.new_revision_id,
                    success=r.success,
                    failure_reason=r.failure_reason,
                )
            )
        return AdminRefreshDeploymentRevisionsPayload(results=results)

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
