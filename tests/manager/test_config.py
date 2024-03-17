from pprint import pprint

import pytest
import yarl

from ai.backend.manager.config import (
    SharedConfig,
)


def test_shared_config_flatten():
    data = SharedConfig.flatten(
        "abc/def",
        {
            "": yarl.URL("https://example.com"),
            "normal": "okay",
            "aa:bb/cc": {  # special chars are auto-quoted
                "f1": "hello",
                "f2": 1234,
            },
        },
    )
    pprint(data)
    assert len(data) == 4
    assert data["abc/def"] == "https://example.com"
    assert data["abc/def/normal"] == "okay"
    assert data["abc/def/aa%3Abb%2Fcc/f1"] == "hello"
    assert data["abc/def/aa%3Abb%2Fcc/f2"] == "1234"

    with pytest.raises(ValueError):
        SharedConfig.flatten(
            "abc/def",
            {
                "": None,  # undefined serialization
            },
        )
    with pytest.raises(ValueError):
        SharedConfig.flatten(
            "abc/def",
            {
                "key": [0, 1, 2],  # undefined serialization
            },
        )
