import sqlalchemy as sa

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.association_container_registries_groups.updaters import (
    ProjectDefaultRegistryUpdater,
)
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps


class ProjectWriteOps(V2WriteOps):
    async def update_default_registry_flags(self, updater: ProjectDefaultRegistryUpdater) -> None:
        project_id = await self._sess.scalar(
            sa.select(ProjectRow.id).where(ProjectRow.id == updater.project_id).with_for_update()
        )
        if project_id is None:
            raise ProjectNotFound(f"Project not found: {updater.project_id}")
        cleared_registry_id = await self._sess.scalar(
            sa.update(AssociationContainerRegistriesGroupsRow)
            .where(
                AssociationContainerRegistriesGroupsRow.project_id == updater.project_id,
                AssociationContainerRegistriesGroupsRow.is_default.is_(True),
            )
            .values(is_default=False)
            .returning(AssociationContainerRegistriesGroupsRow.registry_id)
        )
        if cleared_registry_id != updater.previous_registry_id:
            # Rollback the change if the current default registry does not match the expected previous registry.
            raise InvalidAPIParameters("The project's default registry changed; retry the request")
        if updater.registry_id is not None:
            assigned_registry_id = await self._sess.scalar(
                sa.update(AssociationContainerRegistriesGroupsRow)
                .where(
                    AssociationContainerRegistriesGroupsRow.project_id == updater.project_id,
                    AssociationContainerRegistriesGroupsRow.registry_id == updater.registry_id,
                )
                .values(is_default=True)
                .returning(AssociationContainerRegistriesGroupsRow.registry_id)
            )
            if assigned_registry_id is None:
                # Rollback the change if the assignment failed.
                raise InvalidAPIParameters(
                    f"Cannot set default registry: project {updater.project_id} has no access association "
                    f"with container registry {updater.registry_id}"
                )
