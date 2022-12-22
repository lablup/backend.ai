import argparse
import ipaddress
import pathlib
from typing import Tuple, cast

from .types import HostPortPair


def port_no(s: str) -> int:
    try:
        port = int(s)
        assert port > 0
        assert port < 65536
    except (ValueError, AssertionError):
        msg = f"{s!r} is not a valid port number."
        raise argparse.ArgumentTypeError(msg)
    return port


def port_range(s: str) -> Tuple[int, int]:
    try:
        port_range = tuple(map(int, s.split("-")))
    except (TypeError, ValueError):
        msg = f"{s!r} should be a hyphen-separated pair of integers."
        raise argparse.ArgumentTypeError(msg)
    if len(port_range) != 2:
        msg = f"{s!r} should have exactly two integers."
        raise argparse.ArgumentTypeError(msg)
    if not (0 < port_range[0] < 65536):
        msg = f"{port_range[0]} is not a valid port number."
        raise argparse.ArgumentTypeError(msg)
    if not (0 < port_range[1] < 65536):
        msg = f"{port_range[1]} is not a valid port number."
        raise argparse.ArgumentTypeError(msg)
    if not (port_range[0] < port_range[1]):
        msg = f"{port_range[0]} should be less than {port_range[1]}."
        raise argparse.ArgumentTypeError(msg)
    return cast(Tuple[int, int], port_range)


def positive_int(s: str) -> int:
    try:
        val = int(s)
        assert val > 0
    except (ValueError, AssertionError):
        msg = f"{s!r} is not a positive integer."
        raise argparse.ArgumentTypeError(msg)
    return val


def non_negative_int(s: str) -> int:
    try:
        val = int(s)
        assert val >= 0
    except (ValueError, AssertionError):
        msg = f"{s!r} is not a non-negative integer."
        raise argparse.ArgumentTypeError(msg)
    return val


def host_port_pair(s: str) -> Tuple[ipaddress._BaseAddress, int]:
    host: str | ipaddress._BaseAddress
    pieces = s.rsplit(":", maxsplit=1)
    if len(pieces) == 1:
        msg = f"{s!r} should contain both IP address and port number."
        raise argparse.ArgumentTypeError(msg)
    elif len(pieces) == 2:
        # strip potential brackets in IPv6 hostname-port strings (RFC 3986).
        host = pieces[0].strip("[]")
        try:
            host = ipaddress.ip_address(host)
        except ValueError:
            # Let it be just a hostname.
            host = host
        try:
            port = int(pieces[1])
            assert port > 0
            assert port < 65536
        except (ValueError, AssertionError):
            msg = f"{pieces[1]!r} is not a valid port number."
            raise argparse.ArgumentTypeError(msg)
    return HostPortPair(host, port)


def ipaddr(s: str) -> ipaddress._BaseAddress:
    try:
        ip = ipaddress.ip_address(s.strip("[]"))
    except ValueError:
        msg = f"{s!r} is not a valid IP address."
        raise argparse.ArgumentTypeError(msg)
    return ip


def path(val: str) -> pathlib.Path:
    if val is None:
        return None
    p = pathlib.Path(val)
    if not p.exists():
        msg = f"{val!r} is not a valid file/dir path."
        raise argparse.ArgumentTypeError(msg)
    return p
