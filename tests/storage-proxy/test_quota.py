import os
import secrets
import uuid
from typing import Final

import pytest
from tenacity import AsyncRetrying, stop_after_delay, wait_exponential

from ai.backend.common.types import QuotaScopeID, QuotaScopeType
from ai.backend.storage.abc import CAP_QUOTA, AbstractQuotaModel, AbstractVolume
from ai.backend.storage.types import QuotaConfig, QuotaUsage

MiB: Final = 2**20


@pytest.mark.asyncio
async def test_quota_capability(volume: AbstractVolume) -> None:
    caps = await volume.get_capabilities()
    print(caps)


async def wait_until_quota_changed(
    quota_model: AbstractQuotaModel,
    quota_scope_id: QuotaScopeID,
    prev_usage: QuotaUsage,
) -> QuotaUsage:
    wait_config = wait_exponential(multiplier=1, min=1, max=5)
    stop_config = stop_after_delay(max_delay=30.0)
    qusage = prev_usage
    async for attempt in AsyncRetrying(wait=wait_config, stop=stop_config):
        with attempt:
            new_usage = await quota_model.describe_quota_scope(quota_scope_id)
            assert new_usage
            qusage = new_usage
            if qusage != prev_usage:
                break
            prev_usage = qusage
            raise RuntimeError("The result of describe_quota_scope() did not change.")
    return qusage


@pytest.mark.asyncio
async def test_quota_scope_creation_and_deletion(volume: AbstractVolume) -> None:
    qs = QuotaScopeID(QuotaScopeType.USER, uuid.uuid4())
    await volume.quota_model.create_quota_scope(qs)
    assert volume.quota_model.mangle_qspath(qs).is_dir()
    await volume.quota_model.delete_quota_scope(qs)
    assert not volume.quota_model.mangle_qspath(qs).exists()

    if CAP_QUOTA in (await volume.get_capabilities()):
        qs = QuotaScopeID(QuotaScopeType.USER, uuid.uuid4())
        await volume.quota_model.create_quota_scope(qs, QuotaConfig(10 * MiB))
        assert volume.quota_model.mangle_qspath(qs).is_dir()
        await volume.quota_model.delete_quota_scope(qs)
        assert not volume.quota_model.mangle_qspath(qs).exists()


@pytest.mark.asyncio
async def test_quota_limit(volume: AbstractVolume) -> None:
    caps = await volume.get_capabilities()
    if CAP_QUOTA not in caps:
        pytest.skip("this backend does not support quota management")

    block_size = os.statvfs(volume.mount_path).f_bsize
    qsid = QuotaScopeID(QuotaScopeType.USER, uuid.uuid4())
    qspath = volume.quota_model.mangle_qspath(qsid)

    await volume.quota_model.create_quota_scope(qsid, QuotaConfig(10 * MiB))
    assert qspath.exists() and qspath.is_dir()

    qusage = await volume.quota_model.describe_quota_scope(qsid)
    assert qusage
    assert 0 <= qusage.used_bytes <= block_size
    assert 10 * MiB - block_size <= qusage.limit_bytes <= 10 * MiB

    (qspath / "test.txt").write_bytes(secrets.token_bytes(8192))

    qusage = await wait_until_quota_changed(volume.quota_model, qsid, qusage)
    assert 8192 <= qusage.used_bytes <= 8192 + block_size

    (qspath / "test.txt").unlink()

    await volume.quota_model.delete_quota_scope(qsid)
    assert not qspath.exists()


@pytest.mark.asyncio
async def test_move_tree_between_quota_scopes(test_id: str, volume: AbstractVolume) -> None:
    """
    Tests if the storage backend could guarantee the correct behavior of the vfolder v2 -> v3 migration script.
    """
    qsrc = QuotaScopeID(QuotaScopeType.USER, uuid.uuid4())
    qdst = QuotaScopeID(QuotaScopeType.USER, uuid.uuid4())
    await volume.quota_model.create_quota_scope(qsrc, QuotaConfig(10 * MiB))
    await volume.quota_model.create_quota_scope(qdst, QuotaConfig(10 * MiB))
    qsrc_path = volume.quota_model.mangle_qspath(qsrc)
    qdst_path = volume.quota_model.mangle_qspath(qdst)
    (qsrc_path / "vf1").mkdir(parents=True)
    (qsrc_path / "vf1" / "a.txt").write_bytes(b"abc")
    (qsrc_path / "vf1" / "b.txt").write_bytes(b"bcd")
    (qsrc_path / "vf1" / "inner1").mkdir(parents=True)
    (qsrc_path / "vf1" / "inner1" / "c.txt").write_bytes(b"cde")
    (qsrc_path / "vf1" / "inner2").mkdir(parents=True)
    (qsrc_path / "vf1" / "inner2" / "d.txt").write_bytes(b"def")
    try:
        tree = [item async for item in volume.fsop_model.scan_tree(qsrc_path)]
        assert len(tree) == 7
        tree = [item async for item in volume.fsop_model.scan_tree(qdst_path)]
        assert len(tree) == 0
        await volume.fsop_model.move_tree(qsrc_path / "vf1", qdst_path)
        assert (qdst_path / "vf1").is_dir()
        assert (qdst_path / "vf1" / "a.txt").read_bytes() == b"abc"
        assert (qdst_path / "vf1" / "b.txt").read_bytes() == b"bcd"
        assert (qdst_path / "vf1" / "inner1").is_dir()
        assert (qdst_path / "vf1" / "inner1" / "c.txt").read_bytes() == b"cde"
        assert (qdst_path / "vf1" / "inner2" / "d.txt").read_bytes() == b"def"
        tree = [item async for item in volume.fsop_model.scan_tree(qsrc_path)]
        assert len(tree) == 0
        tree = [item async for item in volume.fsop_model.scan_tree(qdst_path)]
        assert len(tree) == 7
    finally:
        if (qsrc_path / "vf1").exists():
            await volume.fsop_model.delete_tree(qsrc_path / "vf1")
        if (qdst_path / "vf1").exists():
            await volume.fsop_model.delete_tree(qdst_path / "vf1")
        await volume.quota_model.delete_quota_scope(qsrc)
        await volume.quota_model.delete_quota_scope(qdst)
