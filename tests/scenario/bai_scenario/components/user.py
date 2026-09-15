"""What a user scenario table says besides the call.

Rows come from ``seeds``, the adapters from the tables' conftest. This holds the grant a
row leans on and the way a user node and a keypair node are looked at whole.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.dto.manager.v2.keypair import KeypairNode
from ai.backend.common.dto.manager.v2.user.response import UserNode
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import Condition, Held, Same, SameAs, Skipped, Verdict


@dataclass(frozen=True)
class AGrant(SeedNest[Laid[None]]):
    """스코프 하나에 사용자 권한을 담은 역할을 만들어 한 사람에게 준다.

    스코프가 그 사람 자신이면 자기 사용자에 대한 권한이 되고, 도메인이나 프로젝트면 그
    아래 사용자 전원에 대한 권한이 된다.
    """

    scope: Laid[Any]
    scope_of: Callable[[Any], EntityIdentifier]
    to: Laid[UserData]
    permissions: Sequence[Permission]

    @classmethod
    def on_user(cls, user: Laid[UserData], to: Laid[UserData], *permissions: Permission) -> AGrant:
        return cls(user, lambda one: UserID(one.id), to, permissions)

    @classmethod
    def on_domain(
        cls, domain: Laid[DomainData], to: Laid[UserData], *permissions: Permission
    ) -> AGrant:
        return cls(domain, lambda one: one.id, to, permissions)

    @classmethod
    def on_project(
        cls, project: Laid[ProjectData], to: Laid[UserData], *permissions: Permission
    ) -> AGrant:
        return cls(project, lambda one: ProjectID(one.id), to, permissions)

    @override
    def kind(self) -> str:
        names = ", ".join(str(one.name) for one in self.permissions)
        return f"사용자 {names} 권한을 준 역할 배정"

    @override
    def lay(self, seed: Seeder) -> Laid[None]:
        role = seed.creating_from(SeedRole(self.scope_of, name_hint="user-role"), self.scope)
        for permission in self.permissions:
            seed.adding(SeedPermission(entity_type=UserEntityType(), permission=permission), role)
        return seed.granting(
            role, self.to, role_id=lambda one: one.id, user_id=lambda one: UserID(one.id)
        )


@dataclass(frozen=True)
class AKeyIsThere(Condition[str | None]):
    """기본 키가 채워져 있다. 키 값은 실행마다 새로 만들어진다."""

    @override
    def says(self) -> str:
        return "그 사용자의 기본 키가 채워져 있다"

    @override
    def holds(self, got: str | None) -> bool:
        return bool(got)


@dataclass(frozen=True)
class UserNodeLook:
    """사용자 노드 하나를 통째로 본다.

    기대는 심은 사용자에서 온다. 시나리오가 바꾼 자리는 호출자가 그 사용자를 고쳐 넘긴다.
    """

    started: datetime

    def verdicts(
        self,
        node: UserNode,
        expected: UserData,
        main_access_key: Condition[str | None] | None = None,
        at: str = "",
    ) -> list[Verdict]:
        """``at``은 답이 목록일 때 원소 자리를 앞에 붙인다."""
        written = WrittenByThisRun(self.started)
        key: Verdict = (
            Held(
                f"{at}organization.main_access_key",
                node.organization.main_access_key,
                main_access_key,
            )
            if main_access_key is not None
            else Held(
                f"{at}organization.main_access_key",
                node.organization.main_access_key,
                AKeyIsThere(),
            )
        )
        return [
            Held(f"{at}id", node.id, SameAs(expected.id, "심은 사용자")),
            Same(f"{at}basic_info.username", node.basic_info.username, expected.username),
            Same(f"{at}basic_info.email", node.basic_info.email, expected.email),
            Same(f"{at}basic_info.full_name", node.basic_info.full_name, expected.full_name),
            Same(f"{at}basic_info.description", node.basic_info.description, expected.description),
            Same(
                f"{at}basic_info.integration_name",
                node.basic_info.integration_name,
                expected.integration_name,
            ),
            Same(f"{at}status.status", str(node.status.status), str(expected.status)),
            Same(f"{at}status.status_info", node.status.status_info, expected.status_info),
            Same(
                f"{at}status.need_password_change",
                node.status.need_password_change,
                expected.need_password_change,
            ),
            Same(
                f"{at}organization.domain_name", node.organization.domain_name, expected.domain_name
            ),
            Same(
                f"{at}organization.role",
                str(node.organization.role) if node.organization.role else None,
                str(expected.role),
            ),
            Same(
                f"{at}organization.resource_policy",
                node.organization.resource_policy,
                expected.resource_policy,
            ),
            key,
            Same(
                f"{at}security.allowed_client_ip",
                node.security.allowed_client_ip,
                expected.allowed_client_ip,
            ),
            Same(
                f"{at}security.totp_activated",
                node.security.totp_activated,
                expected.totp_activated,
            ),
            Same(f"{at}security.totp_activated_at", node.security.totp_activated_at, None),
            Same(
                f"{at}security.sudo_session_enabled",
                node.security.sudo_session_enabled,
                expected.sudo_session_enabled,
            ),
            Same(f"{at}container.container_uid", node.container.container_uid, None),
            Same(f"{at}container.container_main_gid", node.container.container_main_gid, None),
            Same(f"{at}container.container_gids", node.container.container_gids, None),
            Held(f"{at}timestamps.created_at", node.timestamps.created_at, written),
            Held(f"{at}timestamps.modified_at", node.timestamps.modified_at, written),
        ]


@dataclass(frozen=True)
class KeypairNodeLook:
    """키페어 노드 하나를 통째로 본다. 기대는 심은 키에서 온다."""

    started: datetime

    def verdicts(self, node: KeypairNode, expected: KeyPairData, owner: UserData) -> list[Verdict]:
        written = WrittenByThisRun(self.started)
        return [
            Held("id", node.id, SameAs(str(expected.access_key), "심은 키")),
            Held("access_key", node.access_key, SameAs(str(expected.access_key), "심은 키")),
            Same("is_active", node.is_active, expected.is_active),
            Same("is_admin", node.is_admin, expected.is_admin),
            Same("is_default", node.is_default, expected.is_default),
            Same("rate_limit", node.rate_limit, expected.rate_limit),
            Same("resource_policy", node.resource_policy, expected.resource_policy_name),
            Same("ssh_public_key", node.ssh_public_key, expected.ssh_public_key),
            Same("num_queries", node.num_queries, 0),
            Same("last_used", node.last_used, None),
            Held("user_id", node.user_id, SameAs(owner.id, "키의 주인")),
            Held("created_at", node.created_at, written),
            Held("modified_at", node.modified_at, written),
        ]

    def generated(
        self,
        node: KeypairNode,
        owner: UserData,
        *,
        is_active: bool,
        is_admin: bool,
        is_default: bool,
        rate_limit: int,
        resource_policy: str,
    ) -> list[Verdict]:
        """방금 만들어진 키. 키 값과 SSH 키는 매니저가 만든다."""
        written = WrittenByThisRun(self.started)
        return [
            Skipped("id", "매니저가 만든 access key다"),
            Skipped("access_key", "매니저가 만든다"),
            Same("is_active", node.is_active, is_active),
            Same("is_admin", node.is_admin, is_admin),
            Same("is_default", node.is_default, is_default),
            Same("rate_limit", node.rate_limit, rate_limit),
            Same("resource_policy", node.resource_policy, resource_policy),
            Skipped("ssh_public_key", "매니저가 만든 RSA 키다"),
            Same("num_queries", node.num_queries, 0),
            Same("last_used", node.last_used, None),
            Held("user_id", node.user_id, SameAs(owner.id, "키의 주인")),
            Held("created_at", node.created_at, written),
            Held("modified_at", node.modified_at, written),
        ]
