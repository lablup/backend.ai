from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

if TYPE_CHECKING:
    from ai.backend.common.etcd import AsyncEtcd
    from ai.backend.common.types import RedisConnectionInfo

    from ..models.utils import ExtendedAsyncSAEngine


@attrs.define(slots=True, auto_attribs=True)
class DBContext:
    sa_engine: ExtendedAsyncSAEngine
    redis_stat: RedisConnectionInfo
    etcd: AsyncEtcd
