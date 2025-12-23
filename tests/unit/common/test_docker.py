import collections.abc
import functools
import itertools
import typing
from pathlib import PosixPath
from unittest.mock import MagicMock, call

import aiohttp
import pytest

from ai.backend.common.docker import (
    ImageRef,
    PlatformTagSet,
    _search_docker_socket_files_impl,
    default_registry,
    default_repository,
    get_docker_connector,
    get_docker_context_host,
)


@pytest.mark.asyncio
async def test_get_docker_connector(monkeypatch):
    get_docker_context_host.cache_clear()
    _search_docker_socket_files_impl.cache_clear()
    with monkeypatch.context() as m:
        m.setenv("DOCKER_HOST", "http://localhost:2375")
        connector = get_docker_connector()
        assert str(connector.docker_host) == "http://localhost:2375"
        assert isinstance(connector.connector, aiohttp.TCPConnector)

    get_docker_context_host.cache_clear()
    _search_docker_socket_files_impl.cache_clear()
    with monkeypatch.context() as m:
        m.setenv("DOCKER_HOST", "https://example.com:2375")
        connector = get_docker_connector()
        assert str(connector.docker_host) == "https://example.com:2375"
        assert isinstance(connector.connector, aiohttp.TCPConnector)

    get_docker_context_host.cache_clear()
    _search_docker_socket_files_impl.cache_clear()
    with monkeypatch.context() as m:
        m.setenv("DOCKER_HOST", "unix:///run/docker.sock")
        m.setattr("pathlib.Path.exists", lambda self: True)
        m.setattr("pathlib.Path.is_socket", lambda self: True)
        m.setattr("pathlib.Path.is_fifo", lambda self: False)
        connector = get_docker_connector()
        assert str(connector.docker_host) == "http://docker"
        assert isinstance(connector.connector, aiohttp.UnixConnector)
        assert connector.sock_path == PosixPath("/run/docker.sock")

    get_docker_context_host.cache_clear()
    _search_docker_socket_files_impl.cache_clear()
    with monkeypatch.context() as m:
        m.setenv("DOCKER_HOST", "unix:///run/docker.sock")
        m.setattr("pathlib.Path.exists", lambda self: False)
        m.setattr("pathlib.Path.is_socket", lambda self: False)
        m.setattr("pathlib.Path.is_fifo", lambda self: False)
        with pytest.raises(RuntimeError, match="is not a valid socket file"):
            get_docker_connector()

    get_docker_context_host.cache_clear()
    _search_docker_socket_files_impl.cache_clear()
    with monkeypatch.context() as m:
        m.setenv("DOCKER_HOST", "npipe:////./pipe/docker_engine")
        m.setattr("pathlib.Path.exists", lambda self: True)
        m.setattr("pathlib.Path.is_socket", lambda self: False)
        m.setattr("pathlib.Path.is_fifo", lambda self: True)
        mock_connector = MagicMock()
        m.setattr("aiohttp.NamedPipeConnector", mock_connector)
        connector = get_docker_connector()
        assert str(connector.docker_host) == "http://docker"
        mock_connector.assert_called_once_with(r"\\.\pipe\docker_engine", force_close=True)

    _search_docker_socket_files_impl.cache_clear()
    with monkeypatch.context() as m:
        m.setenv("DOCKER_HOST", "unknown://dockerhost")
        with pytest.raises(RuntimeError, match="unsupported connection scheme"):
            get_docker_connector()

    _search_docker_socket_files_impl.cache_clear()
    with monkeypatch.context() as m:
        m.delenv("DOCKER_HOST", raising=False)
        m.setattr("ai.backend.common.docker.get_docker_context_host", lambda: None)
        m.setattr("sys.platform", "linux")
        mock_path = MagicMock()
        mock_path.home = MagicMock()
        m.setattr("ai.backend.common.docker.Path", mock_path)
        m.setattr("pathlib.Path.exists", lambda self: True)
        m.setattr("pathlib.Path.is_socket", lambda self: True)
        m.setattr("pathlib.Path.is_fifo", lambda self: False)
        connector = get_docker_connector()
        mock_path.assert_has_calls([call("/run/docker.sock"), call("/var/run/docker.sock")])
        assert str(connector.docker_host) == "http://docker"
        assert isinstance(connector.connector, aiohttp.UnixConnector)

    _search_docker_socket_files_impl.cache_clear()
    with monkeypatch.context() as m:
        m.delenv("DOCKER_HOST", raising=False)
        m.setattr("ai.backend.common.docker.get_docker_context_host", lambda: None)
        m.setattr("sys.platform", "win32")
        mock_path = MagicMock()
        m.setattr("ai.backend.common.docker.Path", mock_path)
        m.setattr("pathlib.Path.exists", lambda self: True)
        m.setattr("pathlib.Path.is_socket", lambda self: False)
        m.setattr("pathlib.Path.is_fifo", lambda self: True)
        mock_connector = MagicMock()
        m.setattr("aiohttp.NamedPipeConnector", mock_connector)
        connector = get_docker_connector()
        mock_path.assert_has_calls([call(r"\\.\pipe\docker_engine")])
        assert str(connector.docker_host) == "http://docker"

    get_docker_context_host.cache_clear()
    _search_docker_socket_files_impl.cache_clear()
    with monkeypatch.context() as m:
        m.delenv("DOCKER_HOST", raising=False)
        m.setattr("ai.backend.common.docker.get_docker_context_host", lambda: None)
        m.setattr("sys.platform", "aix")
        with pytest.raises(RuntimeError, match="unsupported platform"):
            get_docker_connector()


def test_image_ref_typing():
    ref = ImageRef(
        name="python-tensorflow",
        project=default_repository,
        registry=default_registry,
        architecture="x86_64",
        tag="1.5-py36-ubuntu16.04",
        is_local=False,
    )
    assert isinstance(ref, collections.abc.Hashable)


def test_image_ref_parsing():
    result = ImageRef.parse_image_str("c")
    assert result.project_and_image_name == f"{default_repository}/c"
    assert result.tag == "latest"
    assert result.registry == default_registry
    assert result.tag_set == ("latest", set())

    result = ImageRef.parse_image_str("c:gcc6.3-alpine3.8")
    assert result.project_and_image_name == f"{default_repository}/c"
    assert result.tag == "gcc6.3-alpine3.8"
    assert result.registry == default_registry
    assert result.tag_set == ("gcc6.3", {"alpine"})

    result = ImageRef.parse_image_str("python:3.6-ubuntu")
    assert result.project_and_image_name == f"{default_repository}/python"
    assert result.tag == "3.6-ubuntu"
    assert result.registry == default_registry
    assert result.tag_set == ("3.6", {"ubuntu"})

    result = ImageRef.parse_image_str("kernel-python:3.6-ubuntu")
    assert result.project_and_image_name == f"{default_repository}/kernel-python"
    assert result.tag == "3.6-ubuntu"
    assert result.registry == default_registry
    assert result.tag_set == ("3.6", {"ubuntu"})

    result = ImageRef.parse_image_str("lablup/python-tensorflow:1.10-py36-ubuntu")
    assert result.project_and_image_name == "lablup/python-tensorflow"
    assert result.tag == "1.10-py36-ubuntu"
    assert result.registry == default_registry
    assert result.tag_set == ("1.10", {"ubuntu", "py"})

    result = ImageRef.parse_image_str("lablup/kernel-python:3.6-ubuntu")
    assert result.project_and_image_name == "lablup/kernel-python"
    assert result.tag == "3.6-ubuntu"
    assert result.registry == default_registry
    assert result.tag_set == ("3.6", {"ubuntu"})

    # To parse registry URLs correctly, we first need to give
    # the valid registry URLs!
    result = ImageRef.parse_image_str("myregistry.org/lua")
    assert result.project_and_image_name == "myregistry.org/lua"
    assert result.tag == "latest"
    assert result.registry == default_registry
    assert result.tag_set == ("latest", set())

    result = ImageRef.parse_image_str("myregistry.org/lua", "myregistry.org")
    assert result.project_and_image_name == "lua"
    assert result.tag == "latest"
    assert result.registry == "myregistry.org"
    assert result.tag_set == ("latest", set())

    result = ImageRef.parse_image_str("myregistry.org/lua:5.3-alpine", "myregistry.org")
    assert result.project_and_image_name == "lua"
    assert result.tag == "5.3-alpine"
    assert result.registry == "myregistry.org"
    assert result.tag_set == ("5.3", {"alpine"})

    # Non-standard port number should be a part of the known registry value.
    result = ImageRef.parse_image_str(
        "myregistry.org:999/mybase/python:3.6-cuda9-ubuntu", "myregistry.org:999"
    )
    assert result.project_and_image_name == "mybase/python"
    assert result.tag == "3.6-cuda9-ubuntu"
    assert result.registry == "myregistry.org:999"
    assert result.tag_set == ("3.6", {"ubuntu", "cuda"})

    result = ImageRef.parse_image_str(
        "myregistry.org/mybase/moon/python:3.6-cuda9-ubuntu", "myregistry.org"
    )
    assert result.project_and_image_name == "mybase/moon/python"
    assert result.tag == "3.6-cuda9-ubuntu"
    assert result.registry == "myregistry.org"
    assert result.tag_set == ("3.6", {"ubuntu", "cuda"})

    # IP addresses are treated as valid registry URLs.
    result = ImageRef.parse_image_str("127.0.0.1:5000/python:3.6-cuda9-ubuntu")
    assert result.project_and_image_name == "python"
    assert result.tag == "3.6-cuda9-ubuntu"
    assert result.registry == "127.0.0.1:5000"
    assert result.tag_set == ("3.6", {"ubuntu", "cuda"})

    # IPv6 addresses must be bracketted.
    result = ImageRef.parse_image_str("::1/python:3.6-cuda9-ubuntu")
    assert result.project_and_image_name == "::1/python"
    assert result.tag == "3.6-cuda9-ubuntu"
    assert result.registry == default_registry
    assert result.tag_set == ("3.6", {"ubuntu", "cuda"})

    result = ImageRef.parse_image_str("[::1]/python:3.6-cuda9-ubuntu")
    assert result.project_and_image_name == "python"
    assert result.tag == "3.6-cuda9-ubuntu"
    assert result.registry == "[::1]"
    assert result.tag_set == ("3.6", {"ubuntu", "cuda"})

    result = ImageRef.parse_image_str("[::1]:5000/python:3.6-cuda9-ubuntu")
    assert result.project_and_image_name == "python"
    assert result.tag == "3.6-cuda9-ubuntu"
    assert result.registry == "[::1]:5000"
    assert result.tag_set == ("3.6", {"ubuntu", "cuda"})

    result = ImageRef.parse_image_str("[212c:9cb9:eada:e57b:84c9:6a9:fbec:bdd2]:1024/python")
    assert result.project_and_image_name == "python"
    assert result.tag == "latest"
    assert result.registry == "[212c:9cb9:eada:e57b:84c9:6a9:fbec:bdd2]:1024"
    assert result.tag_set == ("latest", set())

    result = ImageRef.from_image_str(
        "myregistry.org/project/kernel-python:3.6-ubuntu",
        "project",
        "myregistry.org",
    )
    assert result.project == "project"
    assert result.name == "kernel-python"
    assert result.tag == "3.6-ubuntu"
    assert result.registry == "myregistry.org"
    assert result.tag_set == ("3.6", {"ubuntu"})

    result = ImageRef.from_image_str(
        "myregistry.org/project/sub/kernel-python:3.6-ubuntu",
        "project",
        "myregistry.org",
    )
    assert result.project == "project"
    assert result.name == "sub/kernel-python"
    assert result.tag == "3.6-ubuntu"
    assert result.registry == "myregistry.org"
    assert result.tag_set == ("3.6", {"ubuntu"})

    result = ImageRef.from_image_str(
        "myregistry.org/project/sub/kernel-python:3.6-ubuntu", "project/sub", "myregistry.org"
    )
    assert result.project == "project/sub"
    assert result.name == "kernel-python"
    assert result.tag == "3.6-ubuntu"
    assert result.registry == "myregistry.org"
    assert result.tag_set == ("3.6", {"ubuntu"})

    with pytest.raises(ValueError):
        result = ImageRef.parse_image_str("a:!")

    with pytest.raises(ValueError):
        result = ImageRef.parse_image_str("127.0.0.1:5000/a:-x-")

    with pytest.raises(ValueError):
        result = ImageRef.parse_image_str("http://127.0.0.1:5000/xyz")

    with pytest.raises(ValueError):
        result = ImageRef.parse_image_str("//127.0.0.1:5000/xyz")

    with pytest.raises(ValueError):
        result = ImageRef.from_image_str("a:!", default_repository, default_registry)

    with pytest.raises(ValueError):
        result = ImageRef.from_image_str(
            "127.0.0.1:5000/a:-x-", default_repository, default_registry
        )

    with pytest.raises(ValueError):
        result = ImageRef.from_image_str(
            "http://127.0.0.1:5000/xyz", default_repository, default_registry
        )

    with pytest.raises(ValueError):
        result = ImageRef.from_image_str(
            "//127.0.0.1:5000/xyz", default_repository, default_registry
        )


def test_image_ref_formats():
    result = ImageRef.parse_image_str("python:3.6-cuda9-ubuntu")
    assert result.canonical == "index.docker.io/lablup/python:3.6-cuda9-ubuntu"
    assert result.short == "lablup/python:3.6-cuda9-ubuntu"
    assert str(result) == result.canonical

    result = ImageRef.parse_image_str(
        "myregistry.org/user/python:3.6-cuda9-ubuntu", "myregistry.org"
    )
    assert result.canonical == "myregistry.org/user/python:3.6-cuda9-ubuntu"
    assert result.short == "user/python:3.6-cuda9-ubuntu"
    assert str(result) == result.canonical

    result = ImageRef.from_image_str("python:3.6-cuda9-ubuntu", "lablup", "index.docker.io")
    assert result.canonical == "index.docker.io/lablup/python:3.6-cuda9-ubuntu"
    assert result.short == "lablup/python:3.6-cuda9-ubuntu"
    assert str(result) == result.canonical
    assert repr(result) == f'<ImageRef: "{result.canonical}" ({result.architecture})>'

    result = ImageRef.from_image_str(
        "myregistry.org/user/python:3.6-cuda9-ubuntu", "user", "myregistry.org"
    )
    assert result.canonical == "myregistry.org/user/python:3.6-cuda9-ubuntu"
    assert result.short == "user/python:3.6-cuda9-ubuntu"
    assert str(result) == result.canonical
    assert repr(result) == f'<ImageRef: "{result.canonical}" ({result.architecture})>'

    result = ImageRef.from_image_str(
        "registry.gitlab.com/user/python:3.6-cuda9-ubuntu", "user/python", "registry.gitlab.com"
    )
    assert result.canonical == "registry.gitlab.com/user/python:3.6-cuda9-ubuntu"
    assert result.short == "user/python:3.6-cuda9-ubuntu"
    assert str(result) == result.canonical
    assert repr(result) == f'<ImageRef: "{result.canonical}" ({result.architecture})>'

    result = ImageRef.from_image_str(
        "registry.gitlab.com/user/python/img:3.6-cuda9-ubuntu", "user/python", "registry.gitlab.com"
    )
    assert result.canonical == "registry.gitlab.com/user/python/img:3.6-cuda9-ubuntu"
    assert result.short == "user/python/img:3.6-cuda9-ubuntu"
    assert str(result) == result.canonical
    assert repr(result) == f'<ImageRef: "{result.canonical}" ({result.architecture})>'

    result = ImageRef.from_image_str(
        "registry.gitlab.com/user/workspace/python/img:3.6-cuda9-ubuntu",
        "user/workspace/python",
        "registry.gitlab.com",
    )
    assert result.canonical == "registry.gitlab.com/user/workspace/python/img:3.6-cuda9-ubuntu"
    assert result.short == "user/workspace/python/img:3.6-cuda9-ubuntu"
    assert str(result) == result.canonical
    assert repr(result) == f'<ImageRef: "{result.canonical}" ({result.architecture})>'


def test_image_ref_generate_aliases():
    ref = ImageRef(
        name="python-tensorflow",
        project=default_repository,
        registry=default_registry,
        architecture="x86_64",
        tag="1.5-py36-ubuntu16.04",
        is_local=False,
    )

    aliases = ref.generate_aliases()
    possible_names = ["python-tensorflow", "tensorflow"]
    possible_platform_tags = [
        ["1.5"],
        ["", "py", "py3", "py36"],
        ["", "ubuntu", "ubuntu16", "ubuntu16.04"],
    ]
    # combinations of abbreviated/omitted platforms tags
    for name, ptags in itertools.product(
        possible_names, itertools.product(*possible_platform_tags)
    ):
        assert f"{name}:{'-'.join(t for t in ptags if t)}" in aliases


def test_image_ref_generate_aliases_with_accelerator():
    ref = ImageRef(
        name="python-tensorflow",
        project=default_repository,
        registry=default_registry,
        architecture="x86_64",
        tag="1.5-py36-ubuntu16.04-cuda10.0",
        is_local=False,
    )
    aliases = ref.generate_aliases()
    possible_names = ["python-tensorflow", "tensorflow"]
    possible_platform_tags = [
        ["1.5"],
        ["", "py", "py3", "py36"],
        ["", "ubuntu", "ubuntu16", "ubuntu16.04"],
        ["cuda", "cuda10", "cuda10.0"],  # cannot be empty!
    ]
    # combinations of abbreviated/omitted platforms tags
    for name, ptags in itertools.product(
        possible_names, itertools.product(*possible_platform_tags)
    ):
        assert f"{name}:{'-'.join(t for t in ptags if t)}" in aliases


def test_image_ref_generate_aliases_of_names():
    # an alias may include only last framework name in the name.
    ref = ImageRef(
        name="python-tensorflow",
        project=default_repository,
        registry=default_registry,
        architecture="x86_64",
        tag="1.5-py36-ubuntu16.04-cuda10.0",
        is_local=False,
    )
    aliases = ref.generate_aliases()
    assert "python-tensorflow" in aliases
    assert "tensorflow" in aliases
    assert "python" not in aliases


def test_image_ref_generate_aliases_disallowed():
    # an alias must include the main platform version tag
    ref = ImageRef(
        name="python-tensorflow",
        project=default_repository,
        registry=default_registry,
        architecture="x86_64",
        tag="1.5-py36-ubuntu16.04-cuda10.0",
        is_local=False,
    )
    aliases = ref.generate_aliases()
    # always the main version must be included!
    assert "python-tensorflow:py3" not in aliases
    assert "python-tensorflow:py36" not in aliases
    assert "python-tensorflow:ubuntu" not in aliases
    assert "python-tensorflow:ubuntu16.04" not in aliases
    assert "python-tensorflow:cuda" not in aliases
    assert "python-tensorflow:cuda10.0" not in aliases


def test_image_ref_ordering():
    # ordering is defined as the tuple-ordering of platform tags.
    # (tag components that come first have higher priority when comparing.)
    r1 = ImageRef.from_image_str(
        "lablup/python-tensorflow:1.5-py36-ubuntu16.04-cuda10.0",
        default_repository,
        default_registry,
    )
    r2 = ImageRef.from_image_str(
        "lablup/python-tensorflow:1.7-py36-ubuntu16.04-cuda10.0",
        default_repository,
        default_registry,
    )
    r3 = ImageRef.from_image_str(
        "lablup/python-tensorflow:1.7-py37-ubuntu16.04-cuda9.0",
        default_repository,
        default_registry,
    )

    assert r1 < r2
    assert r1 < r3
    assert r2 < r3

    # only the image-refs with same names can be compared.
    rx = ImageRef.from_image_str("lablup/python:3.6-ubuntu", default_repository, default_registry)
    with pytest.raises(ValueError):
        rx < r1
    with pytest.raises(ValueError):
        r1 < rx

    # test case added for explicit behavior documentation
    # ImageRef.from_image_str(...:ubuntu16.04) > ImageRef.from_image_str(...:ubuntu) == False
    # ImageRef.from_image_str(...:ubuntu16.04) > ImageRef.from_image_str(...:ubuntu) == False
    # by keeping naming convetion, no need to handle these cases
    r4 = ImageRef.from_image_str(
        "lablup/python-tensorflow:1.5-py36-ubuntu16.04-cuda9.0",
        default_repository,
        default_registry,
    )
    r5 = ImageRef.from_image_str(
        "lablup/python-tensorflow:1.5-py36-ubuntu-cuda9.0", default_repository, default_registry
    )
    assert not r4 > r5
    assert not r5 > r4


def test_image_ref_merge_aliases():
    # After merging, aliases that indicates two or more references should
    # indicate most recent versions.
    refs = [
        ImageRef.from_image_str(
            "lablup/python:3.7-ubuntu18.04", default_repository, default_registry
        ),  # 0
        ImageRef.from_image_str(
            "lablup/python-tensorflow:1.5-py36-ubuntu16.04-cuda10.0",
            default_repository,
            default_registry,
        ),  # 1
        ImageRef.from_image_str(
            "lablup/python-tensorflow:1.7-py36-ubuntu16.04-cuda10.0",
            default_repository,
            default_registry,
        ),  # 2
        ImageRef.from_image_str(
            "lablup/python-tensorflow:1.7-py37-ubuntu16.04-cuda9.0",
            default_repository,
            default_registry,
        ),  # 3
        ImageRef.from_image_str(
            "lablup/python-tensorflow:1.5-py36-ubuntu16.04", default_repository, default_registry
        ),  # 4
        ImageRef.from_image_str(
            "lablup/python-tensorflow:1.7-py36-ubuntu16.04", default_repository, default_registry
        ),  # 5
        ImageRef.from_image_str(
            "lablup/python-tensorflow:1.7-py37-ubuntu16.04", default_repository, default_registry
        ),  # 6
    ]
    aliases = [ref.generate_aliases() for ref in refs]
    aliases = functools.reduce(ImageRef.merge_aliases, aliases)
    assert aliases["python-tensorflow"] is refs[6]
    assert aliases["python-tensorflow:1.5"] is refs[4]
    assert aliases["python-tensorflow:1.7"] is refs[6]
    assert aliases["python-tensorflow:1.7-py36"] is refs[5]
    assert aliases["python-tensorflow:1.5"] is refs[4]
    assert aliases["python-tensorflow:1.5-cuda"] is refs[1]
    assert aliases["python-tensorflow:1.7-cuda10"] is refs[2]
    assert aliases["python-tensorflow:1.7-cuda9"] is refs[3]
    assert aliases["python"] is refs[0]


def test_platform_tag_set_typing():
    tags = PlatformTagSet(["py36", "cuda9"])
    assert isinstance(tags, collections.abc.Mapping)
    assert isinstance(tags, typing.Mapping)
    assert not isinstance(tags, collections.abc.MutableMapping)
    assert not isinstance(tags, typing.MutableMapping)


def test_platform_tag_set():
    tags = PlatformTagSet(["py36", "cuda9", "ubuntu16.04", "mkl2018.3"])
    assert "py" in tags
    assert "cuda" in tags
    assert "ubuntu" in tags
    assert "mkl" in tags
    assert tags["py"] == "36"
    assert tags["cuda"] == "9"
    assert tags["ubuntu"] == "16.04"
    assert tags["mkl"] == "2018.3"

    with pytest.raises(ValueError):
        tags = PlatformTagSet(["cuda9", "cuda8"])

    tags = PlatformTagSet(["myplatform9b1", "other"])
    assert "myplatform" in tags
    assert tags["myplatform"] == "9b1"
    assert "other" in tags
    assert tags["other"] == ""

    with pytest.raises(ValueError):
        tags = PlatformTagSet(["1234"])


def test_platform_tag_set_abbreviations():
    pass
