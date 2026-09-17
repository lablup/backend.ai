from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest

from ai.backend.common.data.entity.global_entity import GlobalEntityID, GlobalEntityName
from ai.backend.manager.data.permission.global_entity import (
    GlobalEntityIDCache,
    global_entity_id,
)
from ai.backend.manager.errors.permission import GlobalEntityMissing, GlobalEntityNotLoaded


class TestGlobalEntityIDCache:
    @pytest.fixture(autouse=True)
    def cleared(self) -> Iterator[None]:
        GlobalEntityIDCache.clear()
        yield
        GlobalEntityIDCache.clear()

    def test_read_before_load_raises(self) -> None:
        with pytest.raises(GlobalEntityNotLoaded):
            global_entity_id(GlobalEntityName.GLOBAL)

    def test_fill_without_every_name_raises_and_stays_unloaded(self) -> None:
        with pytest.raises(GlobalEntityMissing):
            GlobalEntityIDCache.fill({GlobalEntityName.GLOBAL: GlobalEntityID(uuid.uuid4())})

        with pytest.raises(GlobalEntityNotLoaded):
            global_entity_id(GlobalEntityName.GLOBAL)

    def test_reads_the_id_of_each_name(self) -> None:
        ids = {name: GlobalEntityID(uuid.uuid4()) for name in GlobalEntityName}
        GlobalEntityIDCache.fill(ids)

        for name in GlobalEntityName:
            assert global_entity_id(name) == ids[name]
