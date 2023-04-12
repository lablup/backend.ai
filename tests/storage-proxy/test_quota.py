import asyncio
import secrets

import pytest

from ai.backend.storage.abc import CAP_QUOTA, AbstractVolume
from ai.backend.storage.types import QuotaConfig


@pytest.mark.asyncio
async def test_quota_capability(volume: AbstractVolume) -> None:
    caps = await volume.get_capabilities()
    print(caps)


@pytest.mark.asyncio
async def test_quota_limit(test_id: str, volume: AbstractVolume) -> None:
    caps = await volume.get_capabilities()
    if CAP_QUOTA not in caps:
        pytest.skip("this backend does not support quota management")

    qsid = f"test-{test_id}-qs-{secrets.token_hex(8)}"
    qspath = volume.quota_model.mangle_qspath(qsid)
    MiB = 2**20

    await volume.quota_model.create_quota_scope(qsid, QuotaConfig(10 * MiB))
    assert qspath.exists() and qspath.is_dir()

    qusage = await volume.quota_model.describe_quota_scope(qsid)
    assert 0 <= qusage.used_bytes <= 4096
    assert 10 * MiB - 4096 <= qusage.limit_bytes <= 10 * MiB

    (qspath / "test.txt").write_bytes(secrets.token_bytes(8192))

    await asyncio.sleep(2)  # the filesystem may have some delay to update this info.
    qusage = await volume.quota_model.describe_quota_scope(qsid)
    assert qusage.used_bytes >= 8192

    (qspath / "test.txt").unlink()

    await volume.quota_model.delete_quota_scope(qsid)
    assert not qspath.exists()
