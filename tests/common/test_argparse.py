import argparse
import ipaddress

import pytest

from ai.backend.common.argparse import (
    port_no, port_range, positive_int, non_negative_int,
    HostPortPair, host_port_pair, ipaddr, path,
)

localhost_ipv4 = ipaddress.ip_address('127.0.0.1')
localhost_ipv6 = ipaddress.ip_address('::1')


def test_port_no():
    assert port_no(1) == 1
    assert port_no(20) == 20
    assert port_no(65535) == 65535

    with pytest.raises(argparse.ArgumentTypeError):
        port_no(-1)
    with pytest.raises(argparse.ArgumentTypeError):
        port_no(0)
    with pytest.raises(argparse.ArgumentTypeError):
        port_no(65536)
    with pytest.raises(argparse.ArgumentTypeError):
        port_no(65537)


def test_port_range():
    assert port_range('1-2') == (1, 2)
    assert port_range('1000-2000') == (1000, 2000)
    assert port_range('1-65535') == (1, 65535)

    with pytest.raises(argparse.ArgumentTypeError):
        port_range('0-65535')
    with pytest.raises(argparse.ArgumentTypeError):
        port_range('1-65536')
    with pytest.raises(argparse.ArgumentTypeError):
        port_range('1-2-3')
    with pytest.raises(argparse.ArgumentTypeError):
        port_range('1')
    with pytest.raises(argparse.ArgumentTypeError):
        port_range('xxx')
    with pytest.raises(argparse.ArgumentTypeError):
        port_range('-')
    with pytest.raises(argparse.ArgumentTypeError):
        port_range('')
    with pytest.raises(argparse.ArgumentTypeError):
        port_range('10-5')


def test_positive_int():
    assert positive_int(1)
    assert positive_int(100000)

    with pytest.raises(argparse.ArgumentTypeError):
        positive_int(0)
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int(-1)
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int(-10)


def test_non_positive_int():
    assert non_negative_int(1)
    assert non_negative_int(100000)
    assert non_negative_int(0) == 0

    with pytest.raises(argparse.ArgumentTypeError):
        non_negative_int(-1)
    with pytest.raises(argparse.ArgumentTypeError):
        non_negative_int(-10)


def test_host_port_pair_direct_creation():
    ip = ipaddress.ip_address('1.2.3.4')
    pair = HostPortPair(ip, 8000)

    assert pair.as_sockaddr() == ('1.2.3.4', 8000)
    assert '{}'.format(pair) == '1.2.3.4:8000'
    assert str(pair) == '1.2.3.4:8000'


def test_host_port_pair_parse():
    with pytest.raises(argparse.ArgumentTypeError):
        host_port_pair('oihasdfoih')
    with pytest.raises(argparse.ArgumentTypeError):
        host_port_pair('99999')
    with pytest.raises(argparse.ArgumentTypeError):
        host_port_pair('oihasdfoih:oixzcghboihx')
    with pytest.raises(argparse.ArgumentTypeError):
        host_port_pair('oihasdfoih:-1')
    with pytest.raises(argparse.ArgumentTypeError):
        host_port_pair('oihasdfoih:99999')
    with pytest.raises(argparse.ArgumentTypeError):
        host_port_pair('oihasdfoih:123.45')
    with pytest.raises(argparse.ArgumentTypeError):
        host_port_pair(':')
    with pytest.raises(argparse.ArgumentTypeError):
        host_port_pair('::')
    with pytest.raises(argparse.ArgumentTypeError):
        host_port_pair(':::')

    a = host_port_pair('oihasdfoih:123')
    assert a.host == 'oihasdfoih'
    assert a.port == 123

    a = host_port_pair('[::1]:9871')
    assert a.host == localhost_ipv6
    assert a.port == 9871

    a = host_port_pair('::1:9871')
    assert a.host == localhost_ipv6
    assert a.port == 9871


def test_host_port_pair_comparison():
    a = host_port_pair('oihasdfoih:123')
    b = host_port_pair('oihasdfoih:123')
    assert a == b
    b = host_port_pair('oihasdfoih:124')
    assert a != b
    b = host_port_pair('oihasdfoix:123')
    assert a != b


def test_ipaddr():
    assert ipaddr('[192.168.0.1]') == ipaddress.ip_address('192.168.0.1')
    assert ipaddr('192.168.0.1') == ipaddress.ip_address('192.168.0.1')
    assert ipaddr('2001:DB8::1') == ipaddress.ip_address('2001:DB8::1')

    with pytest.raises(argparse.ArgumentTypeError):
        ipaddr('50')
    with pytest.raises(argparse.ArgumentTypeError):
        ipaddr('1.1')
    with pytest.raises(argparse.ArgumentTypeError):
        ipaddr('1.1.1')


def test_path(tmpdir):
    assert path(None) is None
    assert path(tmpdir) == tmpdir
    with pytest.raises(argparse.ArgumentTypeError):
        assert path('/path/not/exist/')
