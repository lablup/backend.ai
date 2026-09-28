"""Domain provisioning writes: creating a domain in full within one transaction.

A domain is registered with a model-store project, so the two are written together
rather than left to each caller to remember.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.manager.models.project.creators import ProjectCreator
from ai.backend.manager.repositories.ops.v2.resource_policy.write import (
    V2ResourcePolicyWriteOps,
)

__all__ = ("FullDomainCreatorResult", "V2DomainWriteOps")


@dataclass
class FullDomainCreatorResult:
    """A fully provisioned domain and the model-store project it was registered with."""

    domain: DomainData
    model_store_project: ProjectData


class V2DomainWriteOps(V2ResourcePolicyWriteOps):
    """The resource policy write ops plus provisioning a domain."""

    async def create_domain(self, creator: DomainCreator) -> FullDomainCreatorResult:
        """Provision a domain: the row, the roles its scope's presets call for, and the
        model-store project it is registered with."""
        domain = await self.create_role_managed_entity(creator)
        model_store_project = await self._create_model_store_project(
            DomainID(domain.id), domain.name
        )
        return FullDomainCreatorResult(domain=domain, model_store_project=model_store_project)

    async def _create_model_store_project(
        self, domain_id: DomainID, domain_name: str
    ) -> ProjectData:
        """Create the domain's model-store project and lend it the resource policy it
        is subject to, the way the project's own create does."""
        project = await self.create_role_managed_entity(
            ProjectCreator.model_store(domain_id=domain_id, domain_name=domain_name)
        )
        await self.restate_project_resource_policy_share(ProjectID(project.id))
        return project
