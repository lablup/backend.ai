"""Write specs for the resource policy a project is held to."""

from __future__ import annotations

from bai_scenario.seeds.seeder import Spec

from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.creators import ProjectResourcePolicyCreator

PERSONAL_PROJECT_POLICY = "default"
"""The name ``ProjectCreator.personal`` asks for. Provisioning a user makes that user's
personal project, and the project refuses to be written without a policy of this name.
"""


def seed_project_policy(
    *,
    name: str = PERSONAL_PROJECT_POLICY,
    max_vfolder_count: int = 10,
    max_quota_scope_size: int = -1,
    max_network_count: int = 3,
) -> Spec[ProjectResourcePolicyData]:
    """What a project is allowed.

    The name is given rather than made: the personal project a user provisioning writes
    names its policy, so a scenario laying a user has to lay that policy under the name
    the manager will look for.
    """

    def build(_generated: str) -> ProjectResourcePolicyCreator:
        return ProjectResourcePolicyCreator(
            name=name,
            max_vfolder_count=max_vfolder_count,
            max_quota_scope_size=max_quota_scope_size,
            max_network_count=max_network_count,
        )

    return Spec(name, build)
