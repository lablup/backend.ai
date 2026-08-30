"""Every value the agent can put on the privnet's wire, and the shape it is held to.

This is the input surface of the one process on the node that holds CAP_NET_ADMIN + CAP_SYS_ADMIN.
Two of these validators compose filesystem paths (`session_id` names a journal record,
`container_id` names a cgroup leaf) and three become arguments to `ip`/`iptables`, so "the regex
looks right" is not the same claim as "the regex refuses `../`". Only `validate_overlay_ip` and
`validate_network_config` were covered; the rest are here.
"""

from __future__ import annotations

import pytest

from ai.backend.agent.network.privnet.policy import (
    PolicyViolation,
    validate_container_id,
    validate_dns_port,
    validate_ipv4,
    validate_mac,
    validate_network_config,
    validate_port_pairs,
    validate_session_id,
)

# The two id validators share one pattern, so they are held to the same cases.
_ID_VALIDATORS = (validate_session_id, validate_container_id)


class TestTheIdsThatBecomePaths:
    """`journal._path()` is `dir/kind/<session_id>` and `_kernel_cgroup()` is derived from
    `container_id`. A traversal here is a privileged write outside the tree."""

    @pytest.mark.parametrize("validate", _ID_VALIDATORS)
    @pytest.mark.parametrize(
        "value",
        [
            "..",
            "../../../etc/cron.d/x",
            "a/../../b",
            "sess/../../etc",
            "/etc/passwd",
            "a/b",
            ".hidden",
            "-leading-dash",
        ],
    )
    def test_nothing_that_could_escape_the_tree_is_accepted(
        self, validate: object, value: str
    ) -> None:
        with pytest.raises(PolicyViolation):
            validate(value)  # type: ignore[operator]

    @pytest.mark.parametrize("validate", _ID_VALIDATORS)
    @pytest.mark.parametrize("value", ["", " ", "\n", "a\nb", "a\x00b", "a b", "a;rm -rf /", "a$b"])
    def test_nothing_that_could_reach_a_shell_or_a_log_line_is_accepted(
        self, validate: object, value: str
    ) -> None:
        with pytest.raises(PolicyViolation):
            validate(value)  # type: ignore[operator]

    @pytest.mark.parametrize("validate", _ID_VALIDATORS)
    def test_a_name_longer_than_the_bound_is_refused(self, validate: object) -> None:
        assert validate("a" * 128) == "a" * 128  # type: ignore[operator]
        with pytest.raises(PolicyViolation):
            validate("a" * 129)  # type: ignore[operator]

    @pytest.mark.parametrize("validate", _ID_VALIDATORS)
    @pytest.mark.parametrize(
        "value",
        [
            "0f9a1c3e-4b5d-6e7f-8a9b-0c1d2e3f4a5b",  # the real shape: a session/kernel UUID
            "i-cd-104",
            "sess.a_b-1",
            "A1",
        ],
    )
    def test_the_names_actually_used_are_accepted(self, validate: object, value: str) -> None:
        assert validate(value) == value  # type: ignore[operator]


class TestDnsPort:
    """The DNAT destination host is fixed to 127.0.0.1, so the agent influences only which of its
    own loopback ports :53 is redirected to — hence the unprivileged floor."""

    def test_an_unprivileged_port_is_accepted(self) -> None:
        assert validate_dns_port(10053) == 10053

    @pytest.mark.parametrize("value", [None, 0, 53, 80, 1023, 65536, -1])
    def test_anything_privileged_or_out_of_range_is_refused(self, value: int | None) -> None:
        with pytest.raises(PolicyViolation):
            validate_dns_port(value)

    def test_the_boundaries(self) -> None:
        assert validate_dns_port(1024) == 1024
        assert validate_dns_port(65535) == 65535


class TestPortPairs:
    """Host-port ingress. The DNAT destination is the address the privnet itself assigned, so what
    the agent chooses is the host port, the interface it is published on, and the transport."""

    def _pair(
        self, host: int = 30001, cont: int = 8080, ip: str | None = None, proto: str = "tcp"
    ) -> tuple[tuple[int, int, str | None, str], ...]:
        return ((host, cont, ip, proto),)

    def test_a_plain_pair_is_accepted(self) -> None:
        assert validate_port_pairs(self._pair()) == self._pair()

    def test_a_privileged_host_port_is_refused(self) -> None:
        """Binding :80 or :443 on the node is not the agent's to ask for."""
        with pytest.raises(PolicyViolation, match="host port out of range"):
            validate_port_pairs(self._pair(host=80))

    def test_the_container_port_may_be_privileged(self) -> None:
        """Inside the container it is the kernel's own namespace; sshd on 22 is ordinary."""
        assert validate_port_pairs(self._pair(cont=22))

    @pytest.mark.parametrize("proto", ["icmp", "TCP", "", "tcp; iptables -F", None])
    def test_only_tcp_and_udp_reach_iptables(self, proto: object) -> None:
        """It becomes iptables `-p`."""
        with pytest.raises(PolicyViolation, match="protocol"):
            validate_port_pairs(((30001, 8080, None, proto),))  # type: ignore[arg-type]

    def test_a_duplicate_host_port_is_refused(self) -> None:
        with pytest.raises(PolicyViolation, match="duplicate"):
            validate_port_pairs(((30001, 1, None, "tcp"), (30001, 2, None, "tcp")))

    def test_tcp_and_udp_may_share_a_number(self) -> None:
        """They do on any host; keying the duplicate check on the port alone would refuse it."""
        pairs = ((30001, 1, None, "tcp"), (30001, 2, None, "udp"))
        assert validate_port_pairs(pairs) == pairs

    def test_a_host_ip_that_is_not_one_is_refused(self) -> None:
        with pytest.raises(PolicyViolation, match="host_ip"):
            validate_port_pairs(self._pair(ip="not-an-ip"))

    def test_no_host_ip_means_every_interface(self) -> None:
        assert validate_port_pairs(self._pair(ip=None))

    @pytest.mark.parametrize("value", [None, ()])
    def test_an_empty_request_is_refused(self, value: object) -> None:
        with pytest.raises(PolicyViolation, match="missing ports"):
            validate_port_pairs(value)  # type: ignore[arg-type]

    def test_the_batch_is_bounded(self) -> None:
        """One request must not be able to write an unbounded number of iptables rules."""
        assert validate_port_pairs(tuple((30000 + i, 1, None, "tcp") for i in range(64)))
        with pytest.raises(PolicyViolation, match="too many"):
            validate_port_pairs(tuple((30000 + i, 1, None, "tcp") for i in range(65)))


class TestIpv4AndMac:
    @pytest.mark.parametrize("value", ["192.168.0.10", "10.0.0.1", "0.0.0.0", "255.255.255.255"])
    def test_an_address_is_accepted(self, value: str) -> None:
        assert validate_ipv4(value, what="host_ip") == value

    @pytest.mark.parametrize(
        "value", [None, "", "1.2.3", "1.2.3.4.5", "256.0.0.1", "::1", "1.2.3.4/24", "1.2.3.4 "]
    )
    def test_anything_else_is_refused(self, value: str | None) -> None:
        with pytest.raises(PolicyViolation):
            validate_ipv4(value, what="host_ip")

    def test_the_field_name_reaches_the_message(self) -> None:
        """These are refusals an operator reads out of a log; 'invalid' alone names nothing."""
        with pytest.raises(PolicyViolation, match="vtep_ip"):
            validate_ipv4("nope", what="vtep_ip")

    @pytest.mark.parametrize("value", ["02:42:ac:11:00:02", "AA:BB:CC:DD:EE:FF"])
    def test_a_mac_is_accepted(self, value: str) -> None:
        assert validate_mac(value) == value

    @pytest.mark.parametrize(
        "value",
        [
            None,
            "",
            "02:42:ac:11:00",
            "02-42-ac-11-00-02",
            "02:42:ac:11:00:0g",
            "02:42:ac:11:00:02 ",
        ],
    )
    def test_anything_else_is_not(self, value: str | None) -> None:
        with pytest.raises(PolicyViolation):
            validate_mac(value)


class TestTheSubnetPool:
    """A session's subnet decides where its data plane points; public space would put a session's
    bridge in front of the real internet route."""

    @pytest.mark.parametrize("subnet", ["10.128.7.0/24", "172.30.0.0/26", "192.168.99.0/24"])
    def test_rfc1918_is_accepted(self, subnet: str) -> None:
        assert validate_network_config({"backend": "bridge", "subnet": subnet}).subnet == subnet

    @pytest.mark.parametrize(
        "subnet",
        [
            "8.8.8.0/24",
            "0.0.0.0/0",  # everything
            "10.0.0.0/7",  # straddles the pool boundary rather than sitting inside it
            "169.254.0.0/16",  # link-local
            "fd00::/8",  # not IPv4
            "not-a-subnet",
        ],
    )
    def test_anything_outside_the_private_pools_is_refused(self, subnet: str) -> None:
        with pytest.raises(PolicyViolation):
            validate_network_config({"backend": "bridge", "subnet": subnet})


class TestTheVxlanFields:
    def test_a_vni_and_mtu_round_trip(self) -> None:
        cfg = validate_network_config({
            "backend": "vxlan",
            "subnet": "10.128.7.0/24",
            "vni": 4103,
            "mtu": 1450,
        })
        assert (cfg.vni, cfg.mtu) == (4103, 1450)

    @pytest.mark.parametrize("vni", [0, 1 << 24, -1, "nope"])
    def test_a_vni_outside_24_bits_is_refused(self, vni: object) -> None:
        with pytest.raises(PolicyViolation, match="vni"):
            validate_network_config({"backend": "vxlan", "subnet": "10.128.7.0/24", "vni": vni})

    @pytest.mark.parametrize("mtu", [575, 9001, "nope"])
    def test_an_unusable_mtu_is_refused(self, mtu: object) -> None:
        with pytest.raises(PolicyViolation, match="mtu"):
            validate_network_config({"backend": "vxlan", "subnet": "10.128.7.0/24", "mtu": mtu})

    @pytest.mark.parametrize("field", ["vni", "mtu"])
    @pytest.mark.parametrize("value", [1.5, 4103.0, True, False])
    def test_a_number_that_is_not_an_integer_is_refused_rather_than_truncated(
        self, field: str, value: object
    ) -> None:
        """`int()` accepts a float and truncates it, so a JSON 1.5 used to become VNI 1 — a segment
        another session on the node may already hold. `bool` is an `int` subclass and rode the same
        path to 0/1."""
        with pytest.raises(PolicyViolation, match=field):
            validate_network_config({"backend": "vxlan", "subnet": "10.128.7.0/24", field: value})

    @pytest.mark.parametrize("field", ["vni", "mtu"])
    def test_a_string_of_digits_is_still_accepted(self, field: str) -> None:
        """JSON-over-the-wire has carried these as strings; only the lossy conversions are new
        refusals."""
        cfg = validate_network_config({
            "backend": "vxlan",
            "subnet": "10.128.7.0/24",
            field: "1450",
        })
        assert getattr(cfg, field) == 1450

    def test_an_unknown_backend_is_refused(self) -> None:
        with pytest.raises(PolicyViolation, match="backend"):
            validate_network_config({"backend": "wireguard", "subnet": "10.128.7.0/24"})


class TestTheEncryptionKey:
    """It becomes an XFRM key on an `ip xfrm` command line."""

    def test_a_256_bit_hex_key_is_accepted(self) -> None:
        key = "de" * 32
        assert validate_network_config({"backend": "vxlan", "encryption_key": key}).encryption_key

    @pytest.mark.parametrize(
        "key",
        [
            "de" * 31,  # too short
            "de" * 33,  # too long
            "z" * 64,  # not hex
            "de" * 31 + ";x",  # a metacharacter riding in at the right length
            "de" * 31 + " x",
        ],
    )
    def test_anything_that_is_not_exactly_64_hex_chars_is_refused(self, key: str) -> None:
        with pytest.raises(PolicyViolation, match="encryption_key"):
            validate_network_config({"backend": "vxlan", "encryption_key": key})

    def test_no_key_means_no_encryption(self) -> None:
        assert validate_network_config({"backend": "vxlan"}).encryption_key is None
