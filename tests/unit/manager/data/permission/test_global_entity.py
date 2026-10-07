from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest

from ai.backend.common.data.entity.global_entity import GlobalEntityID, GlobalEntityName
from ai.backend.manager.data.permission.global_entity import (
    GlobalEntityIDCache,
    GlobalEntityNameCache,
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


class TestGlobalEntityNameCache:
    @pytest.fixture(autouse=True)
    def cleared(self) -> Iterator[None]:
        GlobalEntityNameCache.clear()
        yield
        GlobalEntityNameCache.clear()

    @pytest.fixture
    def loaded_ids(self) -> dict[GlobalEntityName, GlobalEntityID]:
        ids = {name: GlobalEntityID(uuid.uuid4()) for name in GlobalEntityName}
        GlobalEntityNameCache.fill({id_: name for name, id_ in ids.items()})
        return ids

    def test_fill_without_every_name_raises_and_stays_unloaded(self) -> None:
        with pytest.raises(GlobalEntityMissing):
            GlobalEntityNameCache.fill({GlobalEntityID(uuid.uuid4()): GlobalEntityName.GLOBAL})

        with pytest.raises(GlobalEntityNotLoaded):
            GlobalEntityNameCache.name_of(GlobalEntityID(uuid.uuid4()))

    @pytest.mark.parametrize("name", list(GlobalEntityName), ids=lambda name: name.value)
    def test_reads_the_name_of_each_id(
        self, loaded_ids: dict[GlobalEntityName, GlobalEntityID], name: GlobalEntityName
    ) -> None:
        assert GlobalEntityNameCache.name_of(loaded_ids[name]) == name

    def test_name_read_before_load_raises(self) -> None:
        with pytest.raises(GlobalEntityNotLoaded):
            GlobalEntityNameCache.name_of(GlobalEntityID(uuid.uuid4()))

    def test_name_of_an_unknown_id_raises(
        self, loaded_ids: dict[GlobalEntityName, GlobalEntityID]
    ) -> None:
        with pytest.raises(GlobalEntityMissing):
            GlobalEntityNameCache.name_of(GlobalEntityID(uuid.uuid4()))

    def test_clear_forgets_the_names(
        self, loaded_ids: dict[GlobalEntityName, GlobalEntityID]
    ) -> None:
        GlobalEntityNameCache.clear()

        with pytest.raises(GlobalEntityNotLoaded):
            GlobalEntityNameCache.name_of(loaded_ids[GlobalEntityName.GLOBAL])
