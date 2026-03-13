from collections.abc import Callable
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ai.backend.kernel.intrinsic import (
    AGENT_HOST_KEY_PATH,
    LEGACY_HOST_KEY_PATH,
    init_sshd_service,
    prepare_sshd_service,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_subprocess(returncode: int = 0, stdout: bytes = b"", stderr: bytes = b"") -> AsyncMock:
    """Create a mock for asyncio.create_subprocess_exec."""
    mock_proc = AsyncMock()
    mock_proc.returncode = returncode
    mock_proc.communicate = AsyncMock(return_value=(stdout, stderr))
    return AsyncMock(return_value=mock_proc)


# ---------------------------------------------------------------------------
# prepare_sshd_service tests
# ---------------------------------------------------------------------------


class TestPrepareSshdService:
    @pytest.mark.asyncio
    async def test_uses_agent_host_key_when_present(self) -> None:
        """When agent host key exists, cmdargs should reference AGENT_HOST_KEY_PATH."""
        service_info = {"port": [2200]}

        with patch.object(Path, "is_file", return_value=True):
            cmdargs, env = await prepare_sshd_service(service_info)

        assert str(AGENT_HOST_KEY_PATH) in cmdargs
        assert str(LEGACY_HOST_KEY_PATH) not in cmdargs

    @pytest.mark.asyncio
    async def test_uses_legacy_host_key_when_agent_absent(self) -> None:
        """When agent host key is absent, cmdargs should reference LEGACY_HOST_KEY_PATH."""
        service_info = {"port": [2200]}

        with patch.object(Path, "is_file", return_value=False):
            cmdargs, env = await prepare_sshd_service(service_info)

        assert str(LEGACY_HOST_KEY_PATH) in cmdargs
        assert str(AGENT_HOST_KEY_PATH) not in cmdargs

    @pytest.mark.asyncio
    async def test_returns_empty_env(self) -> None:
        service_info = {"port": [2200]}

        with patch.object(Path, "is_file", return_value=True):
            _cmdargs, env = await prepare_sshd_service(service_info)

        assert env == {}

    @pytest.mark.asyncio
    async def test_single_port(self) -> None:
        service_info = {"port": 2200}

        with patch.object(Path, "is_file", return_value=True):
            cmdargs, _env = await prepare_sshd_service(service_info)

        port_flags = [cmdargs[i + 1] for i, v in enumerate(cmdargs) if v == "-p"]
        assert port_flags == ["0.0.0.0:2200"]

    @pytest.mark.asyncio
    async def test_multiple_ports(self) -> None:
        service_info = {"port": [2200, 2201, 2202]}

        with patch.object(Path, "is_file", return_value=True):
            cmdargs, _env = await prepare_sshd_service(service_info)

        port_flags = [cmdargs[i + 1] for i, v in enumerate(cmdargs) if v == "-p"]
        assert port_flags == ["0.0.0.0:2200", "0.0.0.0:2201", "0.0.0.0:2202"]


# ---------------------------------------------------------------------------
# init_sshd_service tests — host key generation logic
# ---------------------------------------------------------------------------


def _make_is_file(agent_key_exists: bool) -> Callable[[Path], bool]:
    """Return a side_effect callable for Path.is_file() (autospec=True).

    Controls whether AGENT_HOST_KEY_PATH appears to exist while returning
    False for all other paths (so that auth_path, cluster key paths, etc.
    take their "not found" branches).
    """

    def _side_effect(self: Path) -> bool:
        if self == AGENT_HOST_KEY_PATH:
            return agent_key_exists
        return False

    return _side_effect


class TestInitSshdServiceHostKey:
    @pytest.mark.asyncio
    async def test_skips_keygen_when_agent_host_key_exists(self) -> None:
        """When agent-generated host key exists, no host-key generation subprocess is spawned."""
        child_env: dict[str, str] = {}

        # dropbearkey for user key generation (auth_path branch) — returns pubkey on line 2
        user_keygen = _mock_subprocess(
            returncode=0, stdout=b"Will output 2048 bit rsa secret key\nssh-rsa AAAA... user@host\n"
        )
        user_convert = _mock_subprocess(returncode=0)

        call_count = 0

        async def _subprocess_router(*args: object, **kwargs: object) -> object:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return await user_keygen(*args, **kwargs)
            return await user_convert(*args, **kwargs)

        mock_create = AsyncMock(side_effect=_subprocess_router)

        with (
            patch.object(
                Path, "is_file", autospec=True, side_effect=_make_is_file(agent_key_exists=True)
            ),
            patch.object(Path, "is_dir", return_value=False),
            patch.object(Path, "mkdir"),
            patch.object(Path, "chmod"),
            patch.object(Path, "write_bytes"),
            patch("shutil.rmtree"),
            patch("asyncio.create_subprocess_exec", mock_create),
        ):
            await init_sshd_service(child_env)

        # Only 2 subprocess calls expected: user keygen + convert.
        # Host key generation should be skipped.
        assert mock_create.call_count == 2
        # Verify none of the calls targeted the host key path
        for call in mock_create.call_args_list:
            args = call[0]
            assert "/tmp/dropbear/dropbear_rsa_host_key" not in args

    @pytest.mark.asyncio
    async def test_generates_key_when_agent_host_key_absent(self) -> None:
        """When agent-generated host key is absent, a host key is generated at the legacy path."""
        child_env: dict[str, str] = {}

        user_keygen = _mock_subprocess(
            returncode=0, stdout=b"Will output 2048 bit rsa secret key\nssh-rsa AAAA... user@host\n"
        )
        user_convert = _mock_subprocess(returncode=0)
        host_keygen = _mock_subprocess(returncode=0)

        call_count = 0

        async def _subprocess_router(*args: object, **kwargs: object) -> object:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return await user_keygen(*args, **kwargs)
            if call_count == 2:
                return await user_convert(*args, **kwargs)
            return await host_keygen(*args, **kwargs)

        mock_create = AsyncMock(side_effect=_subprocess_router)

        with (
            patch.object(
                Path, "is_file", autospec=True, side_effect=_make_is_file(agent_key_exists=False)
            ),
            patch.object(Path, "is_dir", return_value=False),
            patch.object(Path, "mkdir"),
            patch.object(Path, "chmod"),
            patch.object(Path, "write_bytes"),
            patch("shutil.rmtree"),
            patch("asyncio.create_subprocess_exec", mock_create),
        ):
            await init_sshd_service(child_env)

        # 3 subprocess calls: user keygen + convert + host keygen
        assert mock_create.call_count == 3
        # Third call should be for host key at legacy path
        host_key_call_args = mock_create.call_args_list[2][0]
        assert "/tmp/dropbear/dropbear_rsa_host_key" in host_key_call_args
