import datetime

import pytest
from pydantic import BaseModel, ValidationError

from ai.backend.common import typed_validators as tv
from ai.backend.common.typed_validators import HostPortPair


def test_time_duration() -> None:
    class NormalModel(BaseModel):
        duration: tv.TimeDuration

    class GenerousModel(BaseModel):
        duration: tv.NaiveTimeDuration

    NormalModel.model_validate({"duration": "3s"})
    NormalModel.model_validate({"duration": "10"})
    NormalModel.model_validate({"duration": "20.5"})
    NormalModel.model_validate({"duration": 8})
    NormalModel.model_validate({"duration": 7.2})
    NormalModel.model_validate({"duration": "2d"})
    NormalModel.model_validate({"duration": "6yr"})
    with pytest.raises(ValidationError):
        NormalModel.model_validate({"duration": "6y"})
    with pytest.raises(ValidationError):
        NormalModel.model_validate({"duration": "6k"})
    with pytest.raises(ValidationError):
        NormalModel.model_validate({"duration": "-6y"})
    GenerousModel.model_validate({"duration": -12})
    GenerousModel.model_validate({"duration": 2})

    NormalModel(duration=datetime.timedelta(days=5)).model_dump_json()


@pytest.mark.parametrize(
    "input, expected",
    [
        ("127.0.0.1:8080", HostPortPair(host="127.0.0.1", port=8080)),
        ("[::1]:443", HostPortPair(host="::1", port=443)),
        (["localhost", 5000], HostPortPair(host="localhost", port=5000)),
        ({"host": "0.0.0.0", "port": 80}, HostPortPair(host="0.0.0.0", port=80)),
        (HostPortPair(host="example.com", port=1234), HostPortPair(host="example.com", port=1234)),
    ],
)
def test_hostport_pair_valid(input, expected) -> None:
    result = HostPortPair.model_validate(input)
    assert result == expected
    assert result.address == f"{expected.host}:{expected.port}"


@pytest.mark.parametrize(
    "input",
    [
        "127.0.0.1",
        "127.0.0.1:70000",
        "127.0.0.1:notaport",
        ["127.0.0.1"],
        {"host": "127.0.0.1"},
        1234,
    ],
)
def test_hostport_pair_invalid(input) -> None:
    with pytest.raises((ValidationError, TypeError)):
        HostPortPair.model_validate(input)
