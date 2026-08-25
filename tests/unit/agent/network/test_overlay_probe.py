"""The ARP frames the overlay reach probe sends and accepts."""

from __future__ import annotations

import ipaddress
import struct

from ai.backend.agent.network.overlay_probe import (
    build_arp_request,
    is_arp_reply_from,
)

_SRC = "02:42:0a:80:07:01"
_DST = "02:42:0a:80:07:02"
_TARGET_IP = "10.128.7.2"


def _arp_frame(oper: int, sender_mac: str, sender_ip: str) -> bytes:
    arp = struct.pack(
        "!HHBBH6s4s6s4s",
        1,
        0x0800,
        6,
        4,
        oper,
        bytes.fromhex(sender_mac.replace(":", "")),
        ipaddress.IPv4Address(sender_ip).packed,
        bytes.fromhex(_SRC.replace(":", "")),
        ipaddress.IPv4Address("0.0.0.0").packed,
    )
    return (
        bytes.fromhex(_SRC.replace(":", ""))
        + bytes.fromhex(sender_mac.replace(":", ""))
        + struct.pack("!H", 0x0806)
        + arp
    )


class TestBuildArpRequest:
    def test_is_a_unicast_request_to_the_endpoint_mac(self) -> None:
        frame = build_arp_request(_SRC, _DST, _TARGET_IP)
        assert len(frame) == 42
        # Unicast, not broadcast: a reply then proves the FDB entry for that MAC reaches the peer,
        # not merely that BUM flooding works.
        assert frame[:6] == bytes.fromhex(_DST.replace(":", ""))
        assert struct.unpack("!H", frame[12:14])[0] == 0x0806
        arp = frame[14:]
        assert struct.unpack("!H", arp[6:8])[0] == 1  # request
        assert arp[24:28] == ipaddress.IPv4Address(_TARGET_IP).packed

    def test_claims_no_address_on_the_overlay(self) -> None:
        # Sender protocol address 0.0.0.0 -- the bridge holds no overlay address, and claiming one
        # could collide with a container's.
        arp = build_arp_request(_SRC, _DST, _TARGET_IP)[14:]
        assert arp[14:18] == ipaddress.IPv4Address("0.0.0.0").packed


class TestIsArpReplyFrom:
    def test_accepts_a_reply_from_the_target(self) -> None:
        assert is_arp_reply_from(_arp_frame(2, _DST, _TARGET_IP), _TARGET_IP)

    def test_rejects_a_reply_about_someone_else(self) -> None:
        assert not is_arp_reply_from(_arp_frame(2, _DST, "10.128.7.9"), _TARGET_IP)

    def test_rejects_a_request(self) -> None:
        # Our own outgoing request is visible on the same socket; counting it as an answer would
        # make the probe always succeed.
        assert not is_arp_reply_from(build_arp_request(_SRC, _DST, _TARGET_IP), _TARGET_IP)

    def test_rejects_a_non_arp_frame(self) -> None:
        assert not is_arp_reply_from(
            b"\x00" * 6 + b"\x11" * 6 + b"\x08\x00" + b"\x00" * 40, _TARGET_IP
        )

    def test_rejects_a_truncated_frame(self) -> None:
        assert not is_arp_reply_from(_arp_frame(2, _DST, _TARGET_IP)[:20], _TARGET_IP)
