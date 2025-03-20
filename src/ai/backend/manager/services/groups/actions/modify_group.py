from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.groups.base import GroupAction


@dataclass
class ModifyGroupAction(GroupAction):
    username: Optional[str]
    password: Optional[str]
    need_password_change: Optional[bool]
    full_name: Optional[str]
    description: Optional[str]
    is_active: Optional[bool]
    status: Optional[str]
    domain_name: Optional[str]
    role: Optional[str]
    group_ids: Optional[list[str]]
    allowed_client_ip: Optional[list[str]]
    resource_policy: Optional[str]
    main_access_key: Optional[str]
    container_uid: Optional[int]
    container_main_gid: Optional[int]
    container_gids: Optional[list[int]]
    totp_activated: Optional[bool] = False
    sudo_session_enabled: Optional[bool] = False

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "modify"


@dataclass
class ModifyGroupActionResult(BaseActionResult):
    data: Optional[Any]

    @override
    def entity_id(self) -> Optional[str]:
        return None
