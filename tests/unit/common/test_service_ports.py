import pytest

from ai.backend.common.service_ports import parse_service_ports


def test_parse_service_ports():
    result = parse_service_ports("", "")
    assert len(result) == 0

    result = parse_service_ports("a:http:1230", "")
    assert len(result) == 1
    assert result[0] == {
        "name": "a",
        "protocol": "http",
        "container_ports": (1230,),
        "host_ports": (None,),
        "is_inference": False,
    }
    result = parse_service_ports("a:preopen:1230", "a,b")
    assert len(result) == 1
    assert result[0] == {
        "name": "a",
        "protocol": "preopen",
        "container_ports": (1230,),
        "host_ports": (None,),
        "is_inference": True,
    }

    result = parse_service_ports("a:tcp:[5000,5005]", "")
    assert len(result) == 1
    assert result[0] == {
        "name": "a",
        "protocol": "tcp",
        "container_ports": (5000, 5005),
        "host_ports": (None, None),
        "is_inference": False,
    }

    result = parse_service_ports("a:tcp:[1230,1240,9000],x:http:3000,t:http:[5000,5001]", "")
    assert len(result) == 3
    assert result[0] == {
        "name": "a",
        "protocol": "tcp",
        "container_ports": (1230, 1240, 9000),
        "host_ports": (None, None, None),
        "is_inference": False,
    }
    assert result[1] == {
        "name": "x",
        "protocol": "http",
        "container_ports": (3000,),
        "host_ports": (None,),
        "is_inference": False,
    }
    assert result[2] == {
        "name": "t",
        "protocol": "http",
        "container_ports": (5000, 5001),
        "host_ports": (None, None),
        "is_inference": False,
    }


def test_parse_service_ports_invalid_values():
    with pytest.raises(ValueError, match="Unsupported"):
        parse_service_ports("x:unsupported:1234", "")

    with pytest.raises(ValueError, match="smaller than"):
        parse_service_ports("x:http:65536", "")

    with pytest.raises(ValueError, match="larger than"):
        parse_service_ports("x:http:1000", "")

    with pytest.raises(ValueError, match="Invalid service-ports format"):
        parse_service_ports("x:http:-1", "")

    with pytest.raises(ValueError, match="Invalid service-ports format"):
        parse_service_ports("abcdefg", "")

    with pytest.raises(ValueError, match="Invalid service-ports format"):
        parse_service_ports("x:tcp:1234,abcdefg", "")

    with pytest.raises(ValueError, match="Invalid service-ports format"):
        parse_service_ports("abcdefg,x:tcp:1234", "")

    with pytest.raises(ValueError, match="already used"):
        parse_service_ports("x:tcp:1234,y:tcp:1234", "")

    with pytest.raises(ValueError, match="reserved"):
        parse_service_ports("y:tcp:7711,x:tcp:2200", "")


def test_parse_service_ports_custom_exception():
    with pytest.raises(ZeroDivisionError):
        parse_service_ports("x:unsupported:1234", [], ZeroDivisionError)


def test_parse_service_ports_ignore_pty():
    result = parse_service_ports("x:pty:1234,y:tcp:1235", "")
    assert len(result) == 1
    assert result[0]["name"] == "y"
