"""Write specs for the resource policy a user is held to."""

from __future__ import annotations

from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.creators import UserResourcePolicyCreator
from bai_scenario.seeds.seeder import Spec


def seed_user_policy(
    *,
    name_hint: str = "user-policy",
    max_vfolder_count: int = 10,
    max_quota_scope_size: int = -1,
    max_session_count_per_model_session: int = 10,
    max_customized_image_count: int = 3,
) -> Spec[UserResourcePolicyData]:
    """What a user is allowed, as a row of its own rather than a name borrowed from
    somewhere else."""

    def build(name: str) -> UserResourcePolicyCreator:
        return UserResourcePolicyCreator(
            name=name,
            max_vfolder_count=max_vfolder_count,
            max_quota_scope_size=max_quota_scope_size,
            max_session_count_per_model_session=max_session_count_per_model_session,
            max_customized_image_count=max_customized_image_count,
        )

    return Spec("a user policy", name_hint, build)
