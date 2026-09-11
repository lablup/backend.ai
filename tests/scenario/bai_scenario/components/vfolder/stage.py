"""폴더 시나리오가 딛는 것 — 심어야 하는 행과, 심고 나서 손에 쥐는 값.

폴더는 프로젝트 안에 만들어진다. 자기 폴더면 그 사람의 개인 프로젝트다. 그래서 폴더를
다스리는 스코프는 만든 사람이 아니라 그 프로젝트이고, 부르는 사람 자신의 스코프에 준 권한은
폴더를 만들게 해 주지만 만들어진 폴더에는 닿지 못한다. 이미 서 있는 폴더에 닿는 역할은
도메인에 앉힌다.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import VFolderData

STORAGE_HOST = "local:volume1"

# The permission sets a table asks for, named by what the caller is about to do.
MAKING = (Permission.CREATE, Permission.READ)
READING = (Permission.READ,)


# ---------------------------------------------------------------------------
# 전제가 답하는 것
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AFolderMakerAndTheirDomain:
    """폴더를 만들 사람과, 그 폴더가 놓일 도메인. 아직 폴더는 없다."""

    domain: DomainData
    caller: UserData


@dataclass(frozen=True)
class AFolderAndACaller:
    """이미 서 있는 폴더 하나와, 그것을 부를 사람.

    부르는 사람이 그 폴더의 주인일 수도 있고 아닐 수도 있어서, 주인을 따로 답한다.
    """

    folder: VFolderData
    caller: UserData
    owner: UserData


@dataclass(frozen=True)
class FoldersAndACaller:
    """이 호출이 답해야 하는 폴더들과, 같은 도메인에 있지만 답에 들지 않는 폴더들."""

    seen: tuple[VFolderData, ...]
    unseen: tuple[VFolderData, ...]
    caller: UserData


@dataclass(frozen=True)
class AProjectAndACaller:
    """프로젝트 하나와 그것을 부를 사람, 그리고 그 자리에 이미 있는 폴더들."""

    project: ProjectData
    caller: UserData
    seen: tuple[VFolderData, ...] = ()
    unseen: tuple[VFolderData, ...] = ()
