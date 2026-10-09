"""What a containerd kernel's /etc/resolv.conf ends up containing (BEP-1079): the host's file is
never copied verbatim, since a loopback stub like 127.0.0.53 is unreachable from the container.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ai.backend.agent.network.dns import (
    FALLBACK_NAMESERVERS,
    ResolvConf,
    parse_resolv_conf,
    resolve_container_dns,
)


@pytest.fixture
def host(tmp_path: Path) -> Path:
    return tmp_path / "resolv.conf"


@pytest.fixture
def uplink(tmp_path: Path) -> Path:
    return tmp_path / "uplink.conf"


def _resolve(host: Path, uplink: Path, *configured: str) -> ResolvConf:
    return resolve_container_dns(configured, host_resolv_conf=host, systemd_uplink=uplink)


class TestReadingAResolvConf:
    def test_the_three_directives_are_kept_in_order(self) -> None:
        parsed = parse_resolv_conf(
            "nameserver 1.1.1.1\nnameserver 8.8.8.8\nsearch a.example b.example\noptions ndots:5\n"
        )
        assert parsed.nameservers == ["1.1.1.1", "8.8.8.8"]
        assert parsed.search == ["a.example", "b.example"]
        assert parsed.options == ["ndots:5"]

    @pytest.mark.parametrize("comment", ("#", ";"))
    def test_a_commented_nameserver_is_not_one(self, comment: str) -> None:
        # Both markers are resolv.conf comments. Reading a commented-out server as live points the
        # container at whatever an operator deliberately disabled.
        parsed = parse_resolv_conf(f"{comment} nameserver 1.1.1.1\nnameserver 8.8.8.8\n")
        assert parsed.nameservers == ["8.8.8.8"]

    def test_a_trailing_comment_is_stripped_from_the_value(self) -> None:
        assert parse_resolv_conf("nameserver 1.1.1.1 # the fast one\n").nameservers == ["1.1.1.1"]

    def test_a_bare_keyword_contributes_nothing(self) -> None:
        assert parse_resolv_conf("nameserver\nsearch\noptions\n") == ResolvConf()

    def test_blank_lines_and_unknown_directives_are_ignored(self) -> None:
        parsed = parse_resolv_conf("\n\nsortlist 10.0.0.0/8\n   \nnameserver 1.1.1.1\n")
        assert parsed == ResolvConf(nameservers=["1.1.1.1"])

    def test_a_file_that_says_nothing_is_empty_not_an_error(self) -> None:
        assert parse_resolv_conf("") == ResolvConf()


class TestRenderingOne:
    def test_only_the_directives_that_have_a_value_are_written(self) -> None:
        assert ResolvConf(nameservers=["1.1.1.1"]).render() == "nameserver 1.1.1.1\n"

    def test_it_reads_back_as_what_it_was(self) -> None:
        conf = ResolvConf(
            nameservers=["1.1.1.1", "8.8.8.8"], search=["a.example"], options=["ndots:0"]
        )
        assert parse_resolv_conf(conf.render()) == conf


class TestWhichNameserversAContainerGets:
    def test_what_the_operator_configured_wins(self, host: Path, uplink: Path) -> None:
        host.write_text("nameserver 9.9.9.9\n")
        assert _resolve(host, uplink, "1.1.1.1").nameservers == ["1.1.1.1"]

    def test_otherwise_the_hosts_own(self, host: Path, uplink: Path) -> None:
        host.write_text("nameserver 9.9.9.9\nnameserver 8.8.8.8\n")
        assert _resolve(host, uplink).nameservers == ["9.9.9.9", "8.8.8.8"]

    def test_a_loopback_server_is_dropped(self, host: Path, uplink: Path) -> None:
        """127.0.0.53 is the container's own loopback, where nothing listens."""
        host.write_text("nameserver 127.0.0.53\nnameserver 9.9.9.9\n")
        assert _resolve(host, uplink).nameservers == ["9.9.9.9"]

    def test_an_all_loopback_host_falls_through_to_the_uplink(
        self, host: Path, uplink: Path
    ) -> None:
        # The systemd-resolved case: the stub is all the host's file names, and the real upstream
        # servers are behind it.
        host.write_text("nameserver 127.0.0.53\n")
        uplink.write_text("nameserver 9.9.9.9\n")
        assert _resolve(host, uplink).nameservers == ["9.9.9.9"]

    def test_a_loopback_only_uplink_falls_through_too(self, host: Path, uplink: Path) -> None:
        host.write_text("nameserver ::1\n")
        uplink.write_text("nameserver 127.0.0.1\n")
        assert _resolve(host, uplink).nameservers == list(FALLBACK_NAMESERVERS)

    def test_a_host_file_that_cannot_be_read_falls_through(self, host: Path, uplink: Path) -> None:
        uplink.write_text("nameserver 9.9.9.9\n")
        assert _resolve(host, uplink).nameservers == ["9.9.9.9"]

    def test_with_nothing_usable_anywhere_the_container_still_gets_a_resolver(
        self, host: Path, uplink: Path
    ) -> None:
        # Without this last step the container has no nameserver line at all, which resolves
        # nothing rather than resolving badly.
        assert _resolve(host, uplink).nameservers == list(FALLBACK_NAMESERVERS)

    def test_a_scoped_address_is_judged_without_its_zone(self, host: Path, uplink: Path) -> None:
        # `ipaddress` rejects the zone suffix outright, and a nameserver that cannot be judged
        # must not be silently dropped.
        host.write_text("nameserver fe80::1%eth0\n")
        assert _resolve(host, uplink).nameservers == ["fe80::1%eth0"]

    def test_a_name_that_is_not_an_address_is_left_alone(self, host: Path, uplink: Path) -> None:
        host.write_text("nameserver resolver.internal\n")
        assert _resolve(host, uplink).nameservers == ["resolver.internal"]


class TestWhatIsCarriedOverFromTheHost:
    def test_search_domains_come_along(self, host: Path, uplink: Path) -> None:
        # Short-name lookups keep working; harmless even when the nameservers came from elsewhere.
        host.write_text("nameserver 9.9.9.9\nsearch a.example b.example\n")
        assert _resolve(host, uplink).search == ["a.example", "b.example"]

    def test_ndots_is_forced_to_zero(self, host: Path, uplink: Path) -> None:
        """`ndots:0` is forced: peer names are bare labels, and an inherited `ndots:5` queries
        every search suffix first."""
        host.write_text("nameserver 9.9.9.9\noptions ndots:5 timeout:2\n")
        assert _resolve(host, uplink).options == ["timeout:2", "ndots:0"]

    def test_it_is_set_even_where_the_host_asked_for_nothing(
        self, host: Path, uplink: Path
    ) -> None:
        host.write_text("nameserver 9.9.9.9\n")
        assert _resolve(host, uplink).options == ["ndots:0"]

    def test_an_unreadable_host_file_carries_nothing_over(self, host: Path, uplink: Path) -> None:
        resolved = _resolve(host, uplink, "1.1.1.1")
        assert resolved.search == []
        assert resolved.options == ["ndots:0"]
