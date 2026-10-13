from __future__ import annotations

import pickle
import uuid
from collections.abc import Collection, MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import override
from unittest.mock import MagicMock

import pytest

from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.kernel_registry.adapter import (
    KernelRecoveryDataAdapter,
    KernelRecoveryDataAdapterTarget,
)
from ai.backend.agent.kernel_registry.exception import KernelRegistryNotFound
from ai.backend.agent.kernel_registry.loader.abc import AbstractKernelRegistryLoader
from ai.backend.agent.kernel_registry.loader.pickle import PickleBasedKernelRegistryLoader
from ai.backend.agent.kernel_registry.writer.abc import AbstractKernelRegistryWriter
from ai.backend.agent.kernel_registry.writer.types import KernelRegistrySaveMetadata
from ai.backend.common.types import KernelId


class FakeLoader(AbstractKernelRegistryLoader):
    _data: MutableMapping[KernelId, AbstractKernel] | None
    migrated: bool

    def __init__(self, data: MutableMapping[KernelId, AbstractKernel] | None) -> None:
        self._data = data
        self.migrated = False

    @override
    async def mark_migrated(self) -> None:
        self.migrated = True

    @override
    async def load_kernel_registry(self) -> MutableMapping[KernelId, AbstractKernel]:
        if self._data is None:
            raise KernelRegistryNotFound
        return dict(self._data)


class RecordingWriter(AbstractKernelRegistryWriter):
    saved: list[MutableMapping[KernelId, AbstractKernel]]

    def __init__(self) -> None:
        self.saved = []

    @override
    async def save_kernel_registry(
        self,
        data: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
    ) -> None:
        self.saved.append(dict(data))


class FailingWriter(AbstractKernelRegistryWriter):
    @override
    async def save_kernel_registry(
        self,
        data: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
    ) -> None:
        raise OSError("disk full")


async def _no_live_kernels() -> Collection[KernelId]:
    return []


def _kernel_id() -> KernelId:
    return KernelId(uuid.uuid4())


def _kernel() -> AbstractKernel:
    return MagicMock(spec=AbstractKernel)


def _adapter(
    source: MutableMapping[KernelId, AbstractKernel] | None,
    target_data: MutableMapping[KernelId, AbstractKernel],
    live: Collection[KernelId],
) -> tuple[KernelRecoveryDataAdapter, RecordingWriter]:
    writer = RecordingWriter()

    async def live_kernel_ids() -> Collection[KernelId]:
        return live

    adapter = KernelRecoveryDataAdapter(
        FakeLoader(source),
        [KernelRecoveryDataAdapterTarget(FakeLoader(target_data), writer)],
        live_kernel_ids,
    )
    return adapter, writer


class TestAdaptRecoveryData:
    async def test_a_source_kernel_this_runtime_still_runs_is_adapted(self) -> None:
        """A snapshot entry whose container is still here fills a gap in the target."""
        kernel_id = _kernel_id()
        adapter, writer = _adapter({kernel_id: _kernel()}, {}, live=[kernel_id])

        await adapter.adapt_recovery_data()

        assert [set(saved) for saved in writer.saved] == [{kernel_id}]

    async def test_a_source_kernel_with_no_container_is_not_adapted(self) -> None:
        """A kernel that terminated before the snapshot was superseded must not come back.

        Adapting it writes its scratch back for a kernel that no longer exists, and nothing
        reclaims that directory.
        """
        gone = _kernel_id()
        adapter, writer = _adapter({gone: _kernel()}, {}, live=[])

        await adapter.adapt_recovery_data()

        assert [set(saved) for saved in writer.saved] == [set()]

    async def test_the_live_target_entries_survive_a_stale_source(self) -> None:
        """Filtering the source never drops what the target loader already resolved."""
        held = _kernel_id()
        gone = _kernel_id()
        adapter, writer = _adapter({gone: _kernel()}, {held: _kernel()}, live=[held])

        await adapter.adapt_recovery_data()

        assert [set(saved) for saved in writer.saved] == [{held}]

    async def test_a_target_entry_is_never_overwritten_by_the_source(self) -> None:
        """The target loader read ground truth; the snapshot does not get to replace it."""
        kernel_id = _kernel_id()
        target_kernel = _kernel()
        adapter, writer = _adapter(
            {kernel_id: _kernel()}, {kernel_id: target_kernel}, live=[kernel_id]
        )

        await adapter.adapt_recovery_data()

        assert writer.saved[0][kernel_id] is target_kernel

    async def test_no_source_registry_writes_nothing(self) -> None:
        """With no snapshot to adapt there is nothing to reconcile and nothing to save."""
        adapter, writer = _adapter(None, {}, live=[])

        await adapter.adapt_recovery_data()

        assert writer.saved == []

    async def test_the_source_is_marked_migrated_only_after_every_target_saved(self) -> None:
        source = FakeLoader({_kernel_id(): _kernel()})
        adapter = KernelRecoveryDataAdapter(
            source,
            [KernelRecoveryDataAdapterTarget(FakeLoader({}), FailingWriter())],
            _no_live_kernels,
        )

        with pytest.raises(OSError):
            await adapter.adapt_recovery_data()
        assert not source.migrated

        ok = KernelRecoveryDataAdapter(
            source,
            [KernelRecoveryDataAdapterTarget(FakeLoader({}), RecordingWriter())],
            _no_live_kernels,
        )
        await ok.adapt_recovery_data()
        assert source.migrated


@dataclass(frozen=True)
class _PickledKernel:
    kernel_id: KernelId


class TestUpgradeFromPickleOnlyRegistry:
    async def test_a_second_boot_finds_no_snapshot_to_adapt(self, tmp_path: Path) -> None:
        registry_file = tmp_path / "last_registry.i-test.dat"
        with registry_file.open("wb") as f:
            pickle.dump({}, f)
        loader = PickleBasedKernelRegistryLoader(registry_file, tmp_path / "legacy.dat")

        await loader.mark_migrated()

        with pytest.raises(KernelRegistryNotFound):
            await loader.load_kernel_registry()

    async def test_marking_an_absent_snapshot_migrated_is_harmless(self, tmp_path: Path) -> None:
        loader = PickleBasedKernelRegistryLoader(tmp_path / "none.dat", tmp_path / "legacy.dat")

        await loader.mark_migrated()

        assert list(tmp_path.iterdir()) == []

    async def test_running_kernels_of_a_pickle_only_agent_are_adapted(self, tmp_path: Path) -> None:
        """An agent upgraded with only a pickle on disk recovers every kernel still running."""
        running = [_kernel_id(), _kernel_id()]
        terminated = _kernel_id()
        registry_file = tmp_path / "last_registry.i-test.dat"
        with registry_file.open("wb") as f:
            pickle.dump({kid: _PickledKernel(kid) for kid in [*running, terminated]}, f)
        writer = RecordingWriter()

        async def live_kernel_ids() -> Collection[KernelId]:
            return running

        adapter = KernelRecoveryDataAdapter(
            PickleBasedKernelRegistryLoader(registry_file, tmp_path / "legacy.dat"),
            [KernelRecoveryDataAdapterTarget(FakeLoader({}), writer)],
            live_kernel_ids,
        )

        await adapter.adapt_recovery_data()

        assert [set(saved) for saved in writer.saved] == [set(running)]
        assert not registry_file.exists(), "a downgraded agent would adapt it again"
        migrated = tmp_path / "last_registry.i-test.dat.migrated"
        assert set(pickle.loads(migrated.read_bytes())) == {*running, terminated}


@pytest.mark.parametrize("live", [[], [KernelId(uuid.uuid4())]])
async def test_liveness_is_asked_once_per_adaptation(live: Collection[KernelId]) -> None:
    """The container enumeration is not repeated per source entry."""
    calls = 0

    async def live_kernel_ids() -> Collection[KernelId]:
        nonlocal calls
        calls += 1
        return live

    source = {_kernel_id(): _kernel(), _kernel_id(): _kernel()}
    adapter = KernelRecoveryDataAdapter(
        FakeLoader(source),
        [KernelRecoveryDataAdapterTarget(FakeLoader({}), RecordingWriter())],
        live_kernel_ids,
    )

    await adapter.adapt_recovery_data()

    assert calls == 1
