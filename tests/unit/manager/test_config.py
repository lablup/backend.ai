from pprint import pprint

import pytest
import yarl

from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader


def test_shared_config_flatten():
    data = LegacyEtcdLoader.flatten(
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
        LegacyEtcdLoader.flatten(
            "abc/def",
            {
                "": None,  # undefined serialization
            },
        )
    with pytest.raises(ValueError):
        LegacyEtcdLoader.flatten(
            "abc/def",
            {
                "key": [0, 1, 2],  # undefined serialization
            },
        )
