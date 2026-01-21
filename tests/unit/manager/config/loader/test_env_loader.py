from copy import deepcopy

import pytest

from ai.backend.manager.config.loader.env_loader import EnvLoader
from ai.backend.manager.config.loader.loader_chain import merge_configs


@pytest.fixture
def env_vars(monkeypatch) -> None:
    monkeypatch.setenv("TEST_DB_USER", "admin")
    monkeypatch.setenv("TEST_DB_PASSWORD", "secret")
    monkeypatch.setenv("TEST_MANAGER_NPROC", "4")


def test_deep_merge_overrides():
    base = {"db": {"host": "localhost", "port": 5432}, "log_level": "INFO"}
    overlay = {"db": {"port": 6543}, "extra": True}

    result = merge_configs(deepcopy(base), overlay)

    assert result == {
        "db": {"host": "localhost", "port": 6543},
        "log_level": "INFO",
        "extra": True,
    }


async def test_env_loader(env_vars):
    env_map = [
        (["db", "user"], "TEST_DB_USER"),
        (["db", "password"], "TEST_DB_PASSWORD"),
        (["manager", "num-proc"], "TEST_MANAGER_NPROC"),
    ]

    loader = EnvLoader(env_map)
    result = await loader.load()

    assert result == {
        "db": {
            "user": "admin",
            "password": "secret",
        },
        "manager": {
            "num-proc": "4",
        },
    }
