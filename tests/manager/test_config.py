from pprint import pprint

import pytest
import yarl

from ai.backend.manager.config import (
    SharedConfig,
    container_registry_iv,
    container_registry_serialize,
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


def test_container_registry_iv() -> None:
    data = container_registry_iv.check({
        "": "http://user:passwd@example.com:8080/registry",
        "username": "hello",
        "password": "world",
        "project": "",
    })
    assert isinstance(data[""], yarl.URL)
    assert data["project"] == []
    assert data["ssl_verify"] is True

    data = container_registry_iv.check({
        "": "http://user:passwd@example.com:8080/registry",
        "username": "hello",
        "password": "world",
        "project": "a,b,c",
        "ssl_verify": "false",  # accepts various true/false expressions in strings
    })
    assert isinstance(data[""], yarl.URL)
    assert data["project"] == ["a", "b", "c"]
    assert data["ssl_verify"] is False

    data = container_registry_iv.check({
        "": "http://user:passwd@example.com:8080/registry",
        "type": "harbor2",
        "project": ["x", "y", "z"],  # already structured
    })
    assert isinstance(data[""], yarl.URL)
    assert data["type"] == "harbor2"
    assert data["project"] == ["x", "y", "z"]
    assert data["ssl_verify"] is True

    serialized_data = container_registry_serialize(data)
    assert isinstance(serialized_data[""], str)
    assert serialized_data["type"] == "harbor2"
    assert serialized_data["project"] == "x,y,z"
    assert serialized_data["ssl_verify"] == "1"
    deserialized_data = container_registry_iv.check(serialized_data)
    assert isinstance(deserialized_data[""], yarl.URL)
    assert deserialized_data["type"] == "harbor2"
    assert deserialized_data["project"] == ["x", "y", "z"]
    assert deserialized_data["ssl_verify"] is True


@pytest.mark.asyncio
async def test_shared_config_add_and_list_container_registry(test_ns, etcd_container) -> None:
    container_id, etcd_host_port = etcd_container
    shared_config = SharedConfig(etcd_host_port, None, None, test_ns)

    items = await shared_config.list_container_registry()
    assert len(items) == 0

    await shared_config.add_container_registry(
        "docker.internal:8080/registry",  # special chars are auto-quoted
        {
            "": "https://docker.internal:8080/registry",
            "project": "wow,bar,baz",
            "username": "admin",
            "password": "dummy",
            "ssl_verify": "0",  # accepts various true/false expressions in strings
        },
    )
    items = await shared_config.list_container_registry()
    # The results are automatically unquoted and parsed.
    pprint(items)
    assert len(items) == 1
    assert isinstance(items["docker.internal:8080/registry"][""], yarl.URL)
    assert items["docker.internal:8080/registry"]["project"] == ["wow", "bar", "baz"]
    assert items["docker.internal:8080/registry"]["username"] == "admin"
    assert items["docker.internal:8080/registry"]["password"] == "dummy"
    assert items["docker.internal:8080/registry"]["ssl_verify"] is False


@pytest.mark.asyncio
async def test_shared_config_modify_container_registry(test_ns, etcd_container) -> None:
    container_id, etcd_host_port = etcd_container
    shared_config = SharedConfig(etcd_host_port, None, None, test_ns)

    await shared_config.add_container_registry(
        "docker.internal:8080/registry",
        {
            "": "https://docker.internal:8080/registry",
            "project": "wow",
            "username": "admin",
            "password": "dummy",
            "ssl_verify": "true",
        },
    )
    await shared_config.add_container_registry(
        "docker.internal:8080/registry2",  # shares the prefix
        {
            "": "https://docker.internal:8080/registry2",
            "project": "wow",
            "username": "admin",
            "password": "dummy",
            "ssl-verify": "1",  # test the key aliasing
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
    assert items["docker.internal:8080/registry"]["ssl_verify"] is True
    assert items["docker.internal:8080/registry2"][""] == yarl.URL(
        "https://docker.internal:8080/registry2"
    )
    assert items["docker.internal:8080/registry2"]["project"] == ["wow"]
    assert items["docker.internal:8080/registry2"]["username"] == "admin"
    assert items["docker.internal:8080/registry2"]["password"] == "dummy"
    assert items["docker.internal:8080/registry2"]["ssl_verify"] is True

    # modify the first registry
    await shared_config.modify_container_registry(
        "docker.internal:8080/registry",
        {
            "": "https://docker.internal:8080/registry_first",
            "project": "foo,bar",
            "ssl-verify": "0",  # test the key aliasing
        },
    )

    items = await shared_config.list_container_registry()
    print("--> after modification")
    pprint(items)
    assert len(items) == 2
    assert items["docker.internal:8080/registry"][""] == yarl.URL(
        "https://docker.internal:8080/registry_first"  # modified
    )
    assert items["docker.internal:8080/registry"]["project"] == ["foo", "bar"]  # modified
    assert items["docker.internal:8080/registry"]["username"] == "admin"  # unmodified
    assert items["docker.internal:8080/registry"]["password"] == "dummy"  # unmodified
    assert items["docker.internal:8080/registry"]["ssl_verify"] is False  # modified
    assert items["docker.internal:8080/registry2"][""] == yarl.URL(
        "https://docker.internal:8080/registry2"  # should not be modified
    )
    assert items["docker.internal:8080/registry2"]["project"] == ["wow"]
    assert items["docker.internal:8080/registry2"]["username"] == "admin"
    assert items["docker.internal:8080/registry2"]["password"] == "dummy"  # should not be modified
    assert items["docker.internal:8080/registry2"]["ssl_verify"] is True  # should not be modified


@pytest.mark.asyncio
async def test_shared_config_delete_container_registry(test_ns, etcd_container) -> None:
    container_id, etcd_host_port = etcd_container
    shared_config = SharedConfig(etcd_host_port, None, None, test_ns)

    await shared_config.add_container_registry(
        "docker.internal:8080/registry",
        {
            "": "https://docker.internal:8080/registry",
            "project": "wow",
            "username": "admin",
            "password": "dummy",
        },
    )
    await shared_config.add_container_registry(
        "docker.internal:8080/registry2",  # shares the prefix
        {
            "": "https://docker.internal:8080/registry2",
            "project": "wow",
            "username": "admin",
            "password": "waldo",
        },
    )

    items = await shared_config.list_container_registry()
    print("--> before deletion")
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
