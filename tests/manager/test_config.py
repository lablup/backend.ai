from pprint import pprint

import pytest
import yarl

from ai.backend.manager.config import SharedConfig


def test_shared_config_flatten():
    data = SharedConfig.flatten(
        "abc/def",
        {
            "": yarl.URL("https://example.com"),
            "normal": "okay",
            "aa:bb/cc": {
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
                "": None,
            },
        )


@pytest.mark.asyncio
async def test_shared_config_add_and_list_container_registry(test_ns, etcd_container) -> None:
    container_id, etcd_host_port = etcd_container
    shared_config = SharedConfig(etcd_host_port, None, None, test_ns)

    items = await shared_config.list_container_registry()
    assert len(items) == 0

    await shared_config.add_container_registry(
        "docker.internal:8080/registry",  # slash is automatically quoted
        {
            "": yarl.URL("https://docker.internal:8080/registry"),
            "project": "wow",
            "username": "admin",
            "password": "dummy",
        },
    )
    items = await shared_config.list_container_registry()
    # The results are automatically unquoted and parsed.
    pprint(items)
    assert len(items) == 1
    assert isinstance(items["docker.internal:8080/registry"][""], yarl.URL)
    assert items["docker.internal:8080/registry"]["project"] == ["wow"]
    assert items["docker.internal:8080/registry"]["username"] == "admin"
    assert items["docker.internal:8080/registry"]["password"] == "dummy"


@pytest.mark.asyncio
async def test_shared_config_modify_container_registry(test_ns, etcd_container) -> None:
    container_id, etcd_host_port = etcd_container
    shared_config = SharedConfig(etcd_host_port, None, None, test_ns)

    await shared_config.add_container_registry(
        "docker.internal:8080/registry",
        {
            "": yarl.URL("https://docker.internal:8080/registry"),
            "project": "wow",
            "username": "admin",
            "password": "dummy",
        },
    )
    await shared_config.add_container_registry(
        "docker.internal:8080/registry2",  # shares the prefix
        {
            "": yarl.URL("https://docker.internal:8080/registry2"),
            "project": "wow",
            "username": "admin",
            "password": "dummy",
        },
    )

    items = await shared_config.list_container_registry()
    print("--> before modification")
    pprint(items)
    assert len(items) == 2
    assert items["docker.internal:8080/registry"][""] == yarl.URL(
        "https://docker.internal:8080/registry"
    )
    assert items["docker.internal:8080/registry"]["project"] == ["wow"]
    assert items["docker.internal:8080/registry"]["username"] == "admin"
    assert items["docker.internal:8080/registry"]["password"] == "dummy"
    assert items["docker.internal:8080/registry2"][""] == yarl.URL(
        "https://docker.internal:8080/registry2"
    )
    assert items["docker.internal:8080/registry2"]["project"] == ["wow"]
    assert items["docker.internal:8080/registry2"]["username"] == "admin"
    assert items["docker.internal:8080/registry2"]["password"] == "dummy"

    # modify the first registry
    await shared_config.modify_container_registry(
        "docker.internal:8080/registry",
        {
            "": yarl.URL("https://docker.internal:8080/registry_first"),
            "password": "ooops",
        },
    )

    items = await shared_config.list_container_registry()
    print("--> after modification")
    pprint(items)
    assert len(items) == 2
    assert items["docker.internal:8080/registry"][""] == yarl.URL(
        "https://docker.internal:8080/registry_first"  # modified
    )
    assert items["docker.internal:8080/registry"]["project"] == ["wow"]
    assert items["docker.internal:8080/registry"]["username"] == "admin"
    assert items["docker.internal:8080/registry"]["password"] == "ooops"  # modified
    assert items["docker.internal:8080/registry2"][""] == yarl.URL(
        "https://docker.internal:8080/registry2"  # should not be modified
    )
    assert items["docker.internal:8080/registry2"]["project"] == ["wow"]
    assert items["docker.internal:8080/registry2"]["username"] == "admin"
    assert items["docker.internal:8080/registry2"]["password"] == "dummy"  # should not be modified


@pytest.mark.asyncio
async def test_shared_config_delete_container_registry(test_ns, etcd_container) -> None:
    container_id, etcd_host_port = etcd_container
    shared_config = SharedConfig(etcd_host_port, None, None, test_ns)

    await shared_config.add_container_registry(
        "docker.internal:8080/registry",
        {
            "": yarl.URL("https://docker.internal:8080/registry"),
            "project": "wow",
            "username": "admin",
            "password": "dummy",
        },
    )
    await shared_config.add_container_registry(
        "docker.internal:8080/registry2",  # shares the prefix
        {
            "": yarl.URL("https://docker.internal:8080/registry2"),
            "project": "wow",
            "username": "admin",
            "password": "waldo",
        },
    )

    items = await shared_config.list_container_registry()
    print("--> before modification")
    pprint(items)
    assert len(items) == 2
    assert items["docker.internal:8080/registry"][""] == yarl.URL(
        "https://docker.internal:8080/registry"
    )
    assert items["docker.internal:8080/registry"]["project"] == ["wow"]
    assert items["docker.internal:8080/registry"]["username"] == "admin"
    assert items["docker.internal:8080/registry"]["password"] == "dummy"
    assert items["docker.internal:8080/registry2"][""] == yarl.URL(
        "https://docker.internal:8080/registry2"
    )
    assert items["docker.internal:8080/registry2"]["project"] == ["wow"]
    assert items["docker.internal:8080/registry2"]["username"] == "admin"
    assert items["docker.internal:8080/registry2"]["password"] == "waldo"

    # delete the first registry
    await shared_config.delete_container_registry("docker.internal:8080/registry")

    items = await shared_config.list_container_registry()
    print("--> after deletion")
    pprint(items)
    assert len(items) == 1
    assert items["docker.internal:8080/registry2"][""] == yarl.URL(
        "https://docker.internal:8080/registry2"  # should not be modified
    )
    assert items["docker.internal:8080/registry2"]["project"] == ["wow"]
    assert items["docker.internal:8080/registry2"]["username"] == "admin"
    assert items["docker.internal:8080/registry2"]["password"] == "waldo"
