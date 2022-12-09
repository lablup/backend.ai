import os
from unittest import mock

import pytest
from yarl import URL

from ai.backend.client.config import APIConfig, bool_env, get_config, get_env, set_config


@pytest.fixture
def cfg_params():
    return {
        "endpoint": "http://127.0.0.1:8081",
        "version": "vtest",
        "user_agent": "Backed.AI Client Test",
        "access_key": "AKIAIOSFODNN7EXAMPLE",
        "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "hash_type": "md5",
        "vfolder_mounts": ["abc", "def"],
    }


def test_get_env():
    with pytest.raises(KeyError):
        get_env("TESTKEY")
    with pytest.raises(KeyError):
        with mock.patch.dict(os.environ, {"TESTKEY": "testkey"}):
            get_env("TESTKEY")
    with mock.patch.dict(os.environ, {"BACKEND_TESTKEY": "testkey"}):
        r = get_env("TESTKEY")
        assert r == "testkey"
    with mock.patch.dict(os.environ, {"SORNA_TESTKEY": "testkey"}):
        r = get_env("TESTKEY")
        assert r == "testkey"


def test_bool_env():
    assert bool_env("y")
    assert bool_env("Y")
    assert bool_env("yes")
    assert bool_env("YES")
    assert bool_env("t")
    assert bool_env("T")
    assert bool_env("true")
    assert bool_env("TRUE")
    assert bool_env("1")

    assert not bool_env("n")
    assert not bool_env("N")
    assert not bool_env("no")
    assert not bool_env("NO")
    assert not bool_env("f")
    assert not bool_env("F")
    assert not bool_env("false")
    assert not bool_env("FALSE")
    assert not bool_env("0")

    with pytest.raises(ValueError):
        bool_env("other")


def test_api_config_initialization(cfg_params):
    params = cfg_params
    cfg = APIConfig(**params)

    assert str(cfg.endpoint) == params["endpoint"]
    assert str(cfg.endpoint) == params["endpoint"]
    assert cfg.user_agent == params["user_agent"]
    assert cfg.access_key == params["access_key"]
    assert cfg.secret_key == params["secret_key"]
    assert cfg.version == params["version"]
    assert cfg.hash_type == params["hash_type"]
    assert set(cfg.vfolder_mounts) == set(params["vfolder_mounts"])

    assert isinstance(cfg.endpoint, URL)
    assert isinstance(cfg.version, str)
    assert isinstance(cfg.user_agent, str)
    assert isinstance(cfg.access_key, str)
    assert isinstance(cfg.secret_key, str)
    assert isinstance(cfg.hash_type, str)
    assert isinstance(cfg.vfolder_mounts, list)


def test_validation():
    mandatory_args = {"access_key": "a", "secret_key": "s"}
    with pytest.raises(ValueError):
        APIConfig(endpoint="/mylocalpath", **mandatory_args)
    cfg = APIConfig(vfolder_mounts=["abc"], **mandatory_args)
    assert cfg.vfolder_mounts == ["abc"]
    cfg = APIConfig(vfolder_mounts="", **mandatory_args)
    assert cfg.vfolder_mounts == []
    cfg = APIConfig(vfolder_mounts=["abc", "def"], **mandatory_args)
    assert set(cfg.vfolder_mounts) == set(["abc", "def"])


def test_set_and_get_config(mocker, cfg_params):
    # Mocking the global variable ``_config``.
    # The value of a global variable will affect other test cases.
    mocker.patch("ai.backend.client.config._config", None)
    cfg = APIConfig(**cfg_params)
    set_config(cfg)
    assert get_config() == cfg


def test_get_config_return_default_config_when_config_is_none(mocker, cfg_params):
    mocker.patch("ai.backend.client.config._config", None)
    mocker.patch(
        "os.environ",
        {
            "BACKEND_ACCESS_KEY": cfg_params["access_key"],
            "BACKEND_SECRET_KEY": cfg_params["secret_key"],
        },
    )

    cfg = get_config()
    assert str(cfg.endpoint) == APIConfig.DEFAULTS["endpoint"]
    assert cfg.version == APIConfig.DEFAULTS["version"]
    assert cfg.access_key == cfg_params["access_key"]
    assert cfg.secret_key == cfg_params["secret_key"]
