from pathlib import Path, PurePath
from typing import Dict, Any, TypeAlias, TypeVar
import uuid
import weakref

import attrs
from pydantic import BaseModel
from ai.backend.common.types import VFolderID


VolumeID: TypeAlias = uuid.UUID
StorageID: TypeAlias = uuid.UUID


@attrs.define(slots=True)
class PrivateContext:
    deletion_tasks: weakref.WeakValueDictionary[VFolderID, asyncio.Task]


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class VolumeBaseData:
    volume_id: uuid.UUID
    # VolumeID, StorageID는 단순한 Type alias였어서 그냥 uuid.UUID로 바꿔도 될 거 같음


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class VolumeData(VolumeBaseData):  # 이미 storage.types에 있는데 굳이 따로 정의?
    backend: str
    path: Path
    mount_path: Path
    fsprefix: PurePath | None
    options: Dict[str, Any] | None   # Dict 구체화 고민 더 해보기
    # update_option할 때는 evolve로 처리해야 함! (frozen 때문) -> 자주 수정되지 않을 거라고 판단했음


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class VFolderData(VolumeBaseData):
    vid: VFolderID
    # options에 deprecate 표시가 있는데 필요한가?
    # QuotaConfig 사용됨 (limit_bytes: int)


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class CloneVFolderData(VFolderData):
    dst_vfid: VFolderID


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class VolumeConfig:
    ...


class SpaceInfo(BaseModel):
    available: int
    used: int
    size: int


# 파이단틱 필드 사용법 적용하기
class SVMInfo(BaseModel):
    # Storage Virtual Machine
    svm_id: uuid.UUID   # 기존에 netappclient.py에서는 uuid라고 해놓고 str로 받아왔는데 이렇게 바꾸는 게 맞는지 확인 필요
    svm_name: str


class VolumeInfo(BaseModel):
    name: str
    volume_id: uuid.UUID
    path: Path
    space: SpaceInfo | None
    statistics: Dict[str, Any] | None
    svm: SVMInfo | None


class VFolderOptions:
    def __init__(self, ):
        ...
