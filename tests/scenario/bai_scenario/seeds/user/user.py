"""Write specs for a user.

Provisioning a user is not one row. The manager writes the user, its place in the
domain's graph, the roles its presets call for, the keypair it authorizes with, and the
personal project it alone belongs to. A folder or a session made later leans on all of
it, so a seed takes that whole path rather than the user row alone.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import override

from bai_scenario.seeds.seeder import Naming, SeedUser

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.keypair.types import KeyPairSecrets
from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.repositories.ops.v2.user.write import FullUserCreator
from ai.backend.manager.secret.types import SecretValue

PASSWORD = "scenario-password"


@dataclass(frozen=True)
class SeedUserOf(SeedUser[DomainData, UserResourcePolicyData, KeyPairResourcePolicyData]):
    """A user of the given domain, held to the given policies.

    All three are values earlier rows answered, so nothing here names a domain or a
    policy that some other row happens to have made.
    """

    name_hint: str = "user"
    role: UserRole = UserRole.USER
    is_active: bool = True
    secret_key: SecretValue | None = None

    @override
    def kind(self) -> str:
        match self.role:
            case UserRole.SUPERADMIN:
                return "슈퍼관리자"
            case UserRole.ADMIN:
                return "도메인 관리자"
            case UserRole.MONITOR:
                return "모니터"
            case UserRole.USER:
                return "일반 사용자"

    @override
    def detail(self) -> str:
        if self.secret_key is not None and not isinstance(self.secret_key.content, str):
            return "자기 키와 개인 프로젝트를 갖는다, 비밀 키는 암호화돼 있다"
        return "자기 키와 개인 프로젝트를 갖는다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(
        self,
        name: str,
        domain: DomainData,
        policy: UserResourcePolicyData,
        keypair_policy: KeyPairResourcePolicyData,
    ) -> FullUserCreator:
        token = secrets.token_hex(8).upper()
        return FullUserCreator(
            user=UserCreator(
                email=f"{name}@scenario.local",
                username=name,
                password=PasswordInfo(
                    password=PASSWORD,
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=1000,
                    salt_size=16,
                ),
                need_password_change=False,
                domain_id=domain.id,
                role=self.role,
                is_active=self.is_active,
                resource_policy=policy.name,
            ),
            keypair_secrets=KeyPairSecrets(
                access_key=AccessKey(f"AK{token}"),
                secret_key=self.secret_key or SecretValue(f"sk-{token}"),
                ssh_public_key="",
                ssh_private_key="",
            ),
            keypair_resource_policy=keypair_policy.name,
        )
