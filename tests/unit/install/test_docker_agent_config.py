"""
The DOCKER install mode moves the agent's bind addresses off the loopback
interface; the DEVELOP/PACKAGE modes keep the bundled loopback defaults.
"""

from __future__ import annotations

import importlib.resources
from pathlib import Path

import pytest

from ai.backend.install.context import DockerContext

PUBLIC_ADDR = "10.0.0.5"
RPC_PORT = 6011


@pytest.fixture
def agent_toml() -> str:
    return (
        importlib.resources.files("ai.backend.install.configs").joinpath("agent.toml").read_text()
    )


def test_bundled_agent_toml_binds_to_loopback(agent_toml: str) -> None:
    # The premise of the fixup: the shared template — which DEVELOP and
    # PACKAGE mode use as-is — pins both addresses to the loopback.
    assert 'bind-host = "127.0.0.1"' in agent_toml
    assert 'rpc-listen-addr = { host = "127.0.0.1", port = 6001 }' in agent_toml


def test_agent_bind_address_subs_rewrite_both_addresses(agent_toml: str, tmp_path: Path) -> None:
    toml_path = tmp_path / "agent.toml"
    toml_path.write_text(agent_toml)

    DockerContext.sed_in_place_multi(
        toml_path,
        DockerContext.agent_bind_address_subs(public_addr=PUBLIC_ADDR, rpc_port=RPC_PORT),
    )

    rewritten = toml_path.read_text()
    assert f'bind-host = "{PUBLIC_ADDR}"' in rewritten
    assert f'rpc-listen-addr = {{ host = "{PUBLIC_ADDR}", port = {RPC_PORT} }}' in rewritten
    # No loopback bind address survives; the watcher/metadata addresses are
    # not part of this rewrite and keep their own hosts.
    assert 'bind-host = "127.0.0.1"' not in rewritten
    assert 'rpc-listen-addr = { host = "127.0.0.1"' not in rewritten


def test_agent_bind_address_subs_are_line_anchored(tmp_path: Path) -> None:
    # `bind-host` is a suffix of other keys (e.g. metadata-server-bind-host),
    # which must not be caught by the rewrite.
    toml_path = tmp_path / "agent.toml"
    toml_path.write_text('metadata-server-bind-host = "0.0.0.0"\nbind-host = "127.0.0.1"\n')

    DockerContext.sed_in_place_multi(
        toml_path,
        DockerContext.agent_bind_address_subs(public_addr=PUBLIC_ADDR, rpc_port=RPC_PORT),
    )

    assert toml_path.read_text() == (
        f'metadata-server-bind-host = "0.0.0.0"\nbind-host = "{PUBLIC_ADDR}"\n'
    )
