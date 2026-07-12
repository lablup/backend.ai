"""Choosing a container's nameservers.

The trap this guards against: on a systemd-resolved host, /etc/resolv.conf reads
``nameserver 127.0.0.53``. Copying it verbatim into a container looks correct and resolves
nothing, because the container's network namespace has its own (empty) loopback.
"""

from pathlib import Path

from ai.backend.agent.containerd.dns import (
    FALLBACK_NAMESERVERS,
    parse_resolv_conf,
    resolve_container_dns,
)

_SYSTEMD_STUB = "nameserver 127.0.0.53\noptions edns0 trust-ad\nsearch .\n"
_REAL = "nameserver 168.126.63.1\nnameserver 168.126.63.2\n"


def _write(path: Path, text: str) -> Path:
    path.write_text(text)
    return path


class TestParseResolvConf:
    def test_parses_nameservers_search_and_options(self) -> None:
        parsed = parse_resolv_conf(
            "nameserver 1.1.1.1\nnameserver 8.8.8.8\nsearch corp.example.com\noptions ndots:5\n"
        )
        assert parsed.nameservers == ["1.1.1.1", "8.8.8.8"]
        assert parsed.search == ["corp.example.com"]
        assert parsed.options == ["ndots:5"]

    def test_ignores_comments_and_blank_lines(self) -> None:
        parsed = parse_resolv_conf("# a comment\n\n; another\nnameserver 1.1.1.1  # trailing\n")
        assert parsed.nameservers == ["1.1.1.1"]

    def test_empty_file_yields_nothing(self) -> None:
        assert parse_resolv_conf("").nameservers == []


class TestResolveContainerDns:
    def test_configured_nameservers_win(self, tmp_path: Path) -> None:
        host = _write(tmp_path / "resolv.conf", _REAL)
        result = resolve_container_dns(
            ["10.0.0.53"], host_resolv_conf=host, systemd_uplink=tmp_path / "absent"
        )
        assert result.nameservers == ["10.0.0.53"]

    def test_uses_the_hosts_own_nameservers_when_routable(self, tmp_path: Path) -> None:
        host = _write(tmp_path / "resolv.conf", _REAL)
        result = resolve_container_dns(host_resolv_conf=host, systemd_uplink=tmp_path / "absent")
        assert result.nameservers == ["168.126.63.1", "168.126.63.2"]

    def test_systemd_stub_is_replaced_by_the_uplink(self, tmp_path: Path) -> None:
        # The whole point: 127.0.0.53 is unreachable from the container's netns, so we must reach
        # past the stub to the real upstream servers.
        host = _write(tmp_path / "resolv.conf", _SYSTEMD_STUB)
        uplink = _write(tmp_path / "uplink.conf", _REAL)
        result = resolve_container_dns(host_resolv_conf=host, systemd_uplink=uplink)
        assert result.nameservers == ["168.126.63.1", "168.126.63.2"]
        assert "127.0.0.53" not in result.nameservers

    def test_loopback_nameservers_are_dropped(self, tmp_path: Path) -> None:
        host = _write(tmp_path / "resolv.conf", "nameserver 127.0.0.1\nnameserver 1.1.1.1\n")
        result = resolve_container_dns(host_resolv_conf=host, systemd_uplink=tmp_path / "absent")
        assert result.nameservers == ["1.1.1.1"]

    def test_ipv6_loopback_is_dropped(self, tmp_path: Path) -> None:
        host = _write(tmp_path / "resolv.conf", "nameserver ::1\nnameserver 2001:4860:4860::8888\n")
        result = resolve_container_dns(host_resolv_conf=host, systemd_uplink=tmp_path / "absent")
        assert result.nameservers == ["2001:4860:4860::8888"]

    def test_falls_back_when_nothing_usable_exists(self, tmp_path: Path) -> None:
        host = _write(tmp_path / "resolv.conf", _SYSTEMD_STUB)
        result = resolve_container_dns(host_resolv_conf=host, systemd_uplink=tmp_path / "absent")
        assert result.nameservers == list(FALLBACK_NAMESERVERS)

    def test_falls_back_when_the_host_has_no_resolv_conf(self, tmp_path: Path) -> None:
        result = resolve_container_dns(
            host_resolv_conf=tmp_path / "absent", systemd_uplink=tmp_path / "absent-too"
        )
        assert result.nameservers == list(FALLBACK_NAMESERVERS)

    def test_search_and_options_are_carried_over(self, tmp_path: Path) -> None:
        host = _write(
            tmp_path / "resolv.conf",
            "nameserver 1.1.1.1\nsearch corp.example.com\noptions ndots:5\n",
        )
        result = resolve_container_dns(host_resolv_conf=host, systemd_uplink=tmp_path / "absent")
        assert result.search == ["corp.example.com"]
        assert result.options == ["ndots:5"]

    def test_search_survives_an_operator_override(self, tmp_path: Path) -> None:
        # Pinning a corporate resolver must not cost the user short-name lookups.
        host = _write(tmp_path / "resolv.conf", "nameserver 1.1.1.1\nsearch corp.example.com\n")
        result = resolve_container_dns(
            ["10.0.0.53"], host_resolv_conf=host, systemd_uplink=tmp_path / "absent"
        )
        assert result.nameservers == ["10.0.0.53"]
        assert result.search == ["corp.example.com"]


class TestRender:
    def test_renders_a_valid_resolv_conf(self, tmp_path: Path) -> None:
        host = _write(tmp_path / "resolv.conf", "nameserver 1.1.1.1\nsearch a.example\n")
        rendered = resolve_container_dns(
            host_resolv_conf=host, systemd_uplink=tmp_path / "absent"
        ).render()
        assert rendered == "nameserver 1.1.1.1\nsearch a.example\n"

    def test_nameserver_only(self, tmp_path: Path) -> None:
        host = _write(tmp_path / "resolv.conf", "nameserver 1.1.1.1\n")
        rendered = resolve_container_dns(
            host_resolv_conf=host, systemd_uplink=tmp_path / "absent"
        ).render()
        assert rendered == "nameserver 1.1.1.1\n"
