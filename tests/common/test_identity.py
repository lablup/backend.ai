import random
import secrets
import socket
from unittest.mock import MagicMock, patch

import aiodns
import pytest
from aioresponses import aioresponses

import ai.backend.common.identity


def test_is_containerized():
    mocked_path = MagicMock()
    mocked_path.read_text.return_value = "\n".join([
        "13:name=systemd:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "12:pids:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "11:hugetlb:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "10:net_prio:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "9:perf_event:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "8:net_cls:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "7:freezer:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "6:devices:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "5:memory:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "4:blkio:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "3:cpuacct:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "2:cpu:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "1:cpuset:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
    ])
    with patch("ai.backend.common.identity.Path", return_value=mocked_path):
        assert ai.backend.common.identity.is_containerized()
    mocked_path = MagicMock()
    mocked_path.read_text.return_value = "\n".join([
        "11:devices:/user.slice",
        "10:pids:/user.slice/user-1000.slice",
        "9:hugetlb:/",
        "8:cpuset:/",
        "7:blkio:/user.slice",
        "6:memory:/user.slice",
        "5:cpu,cpuacct:/user.slice",
        "4:freezer:/",
        "3:net_cls,net_prio:/",
        "2:perf_event:/",
        "1:name=systemd:/user.slice/user-1000.slice/session-3.scope",
    ])
    with patch("ai.backend.common.identity.Path", return_value=mocked_path):
        assert not ai.backend.common.identity.is_containerized()
    mocked_path = MagicMock()
    mocked_path.side_effect = FileNotFoundError("no such file")
    with patch("ai.backend.common.identity.Path", return_value=mocked_path):
        assert not ai.backend.common.identity.is_containerized()


@pytest.mark.skip
@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["amazon", "google", "azure", None])
async def test_get_instance_id(mocker, provider):
    ai.backend.common.identity.current_provider = provider
    ai.backend.common.identity._defined = False
    ai.backend.common.identity._define_functions()

    with aioresponses() as m:
        random_id = secrets.token_hex(16)
        if provider == "amazon":
            m.get("http://169.254.169.254/latest/meta-data/instance-id", body=random_id)
            ret = await ai.backend.common.identity.get_instance_id()
            assert ret == random_id
        elif provider == "azure":
            m.get(
                "http://169.254.169.254/metadata/instance?version=2017-03-01",
                payload={
                    "compute": {
                        "vmId": random_id,
                    },
                },
            )
            ret = await ai.backend.common.identity.get_instance_id()
            assert ret == random_id
        elif provider == "google":
            m.get("http://metadata.google.internal/computeMetadata/v1/instance/id", body=random_id)
            ret = await ai.backend.common.identity.get_instance_id()
            assert ret == random_id
        elif provider is None:
            with patch("socket.gethostname", return_value="myname"):
                ret = await ai.backend.common.identity.get_instance_id()
                assert ret == "i-myname"


@pytest.mark.skip
@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["amazon", "google", "azure", None])
async def test_get_instance_id_failures(mocker, provider):
    ai.backend.common.identity.current_provider = provider
    ai.backend.common.identity._defined = False
    ai.backend.common.identity._define_functions()

    with aioresponses():
        # If we don't set any mocked responses, aioresponses will raise ClientConnectionError.
        ret = await ai.backend.common.identity.get_instance_id()
        assert ret == f"i-{socket.gethostname()}"


@pytest.mark.skip
@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["amazon", "google", "azure", None])
async def test_get_instance_ip(mocker, provider):
    ai.backend.common.identity.current_provider = provider
    ai.backend.common.identity._defined = False
    ai.backend.common.identity._define_functions()

    with aioresponses() as m:
        random_ip = ".".join(str(random.randint(0, 255)) for _ in range(4))
        if provider == "amazon":
            m.get("http://169.254.169.254/latest/meta-data/local-ipv4", body=random_ip)
            ret = await ai.backend.common.identity.get_instance_ip()
            assert ret == random_ip
        elif provider == "azure":
            m.get(
                "http://169.254.169.254/metadata/instance?version=2017-03-01",
                payload={
                    "network": {
                        "interface": [
                            {
                                "ipv4": {
                                    "ipaddress": [
                                        {"ipaddress": random_ip},
                                    ],
                                },
                            },
                        ],
                    },
                },
            )
            ret = await ai.backend.common.identity.get_instance_ip()
            assert ret == random_ip
        elif provider == "google":
            m.get(
                "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/ip",
                body=random_ip,
            )
            ret = await ai.backend.common.identity.get_instance_ip()
            assert ret == random_ip
        elif provider is None:
            mocked_ares_host_result = MagicMock()
            mocked_ares_host_result.addresses = ["10.1.2.3"]
            mocked_resolver = MagicMock()

            async def coro_return_mocked_result(*args):
                return mocked_ares_host_result

            mocked_resolver.gethostbyname = coro_return_mocked_result
            with (
                patch("aiodns.DNSResolver", return_value=mocked_resolver),
                patch("socket.gethostname", return_value="myname"),
            ):
                ret = await ai.backend.common.identity.get_instance_ip()
                assert ret == "10.1.2.3"

            async def coro_raise_error(*args):
                raise aiodns.error.DNSError("domain not found")

            mocked_resolver = MagicMock()
            mocked_resolver.gethostbyname = coro_raise_error
            with (
                patch("aiodns.DNSResolver", return_value=mocked_resolver),
                patch("socket.gethostname", return_value="myname"),
            ):
                ret = await ai.backend.common.identity.get_instance_ip()
                assert ret == "127.0.0.1"


@pytest.mark.skip
@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["amazon", "google", "azure", None])
async def test_get_instance_type(mocker, provider):
    ai.backend.common.identity.current_provider = provider
    ai.backend.common.identity._defined = False
    ai.backend.common.identity._define_functions()

    with aioresponses() as m:
        random_type = secrets.token_hex(16)
        if provider == "amazon":
            m.get("http://169.254.169.254/latest/meta-data/instance-type", body=random_type)
            ret = await ai.backend.common.identity.get_instance_type()
            assert ret == random_type
        elif provider == "azure":
            m.get(
                "http://169.254.169.254/metadata/instance?version=2017-03-01",
                payload={
                    "compute": {
                        "vmSize": random_type,
                    },
                },
            )
            ret = await ai.backend.common.identity.get_instance_type()
            assert ret == random_type
        elif provider == "google":
            m.get(
                "http://metadata.google.internal/computeMetadata/v1/instance/machine-type",
                body=random_type,
            )
            ret = await ai.backend.common.identity.get_instance_type()
            assert ret == random_type
        elif provider is None:
            ret = await ai.backend.common.identity.get_instance_type()
            assert ret == "default"
