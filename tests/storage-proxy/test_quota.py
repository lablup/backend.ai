import secrets

import pytest
from tenacity import AsyncRetrying, stop_after_delay, wait_exponential

from ai.backend.storage.abc import CAP_QUOTA, AbstractQuotaModel, AbstractVolume
from ai.backend.storage.types import QuotaConfig, QuotaUsage


@pytest.mark.asyncio
async def test_quota_capability(volume: AbstractVolume) -> None:
    caps = await volume.get_capabilities()
    print(caps)


async def wait_until_quota_changed(
    quota_model: AbstractQuotaModel,
    quota_scope_id: str,
    prev_usage: QuotaUsage,
) -> QuotaUsage:
    wait_config = wait_exponential(multiplier=1, min=1, max=5)
    stop_config = stop_after_delay(max_delay=30.0)
    qusage = prev_usage
    async for attempt in AsyncRetrying(wait=wait_config, stop=stop_config):
        with attempt:
            qusage = await quota_model.describe_quota_scope(quota_scope_id)
            if qusage != prev_usage:
                break
            prev_usage = qusage
            raise RuntimeError("The result of describe_quota_scope() did not change.")
    return qusage


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

    qusage = await wait_until_quota_changed(volume.quota_model, qsid, qusage)
    assert qusage.used_bytes >= 8192

    (qspath / "test.txt").unlink()

    await volume.quota_model.delete_quota_scope(qsid)
    assert not qspath.exists()
