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
    ref = ImageRef("c")
    assert isinstance(ref, collections.abc.Hashable)


def test_image_ref_parsing():
    ref = ImageRef("c")
    assert ref.name == f"{default_repository}/c"
    assert ref.architecture == "x86_64"
    assert ref.tag == "latest"
    assert ref.registry == default_registry
    assert ref.tag_set == ("latest", set())

    ref = ImageRef("c:gcc6.3-alpine3.8", architecture="aarch64")
    assert ref.name == f"{default_repository}/c"
    assert ref.architecture == "aarch64"
    assert ref.tag == "gcc6.3-alpine3.8"
    assert ref.registry == default_registry
    assert ref.tag_set == ("gcc6.3", {"alpine"})

    ref = ImageRef("python:3.6-ubuntu", architecture="amd64")
    assert ref.name == f"{default_repository}/python"
    assert ref.architecture == "x86_64"
    assert ref.tag == "3.6-ubuntu"
    assert ref.registry == default_registry
    assert ref.tag_set == ("3.6", {"ubuntu"})

    ref = ImageRef("kernel-python:3.6-ubuntu")
    assert ref.name == f"{default_repository}/kernel-python"
    assert ref.tag == "3.6-ubuntu"
    assert ref.registry == default_registry
    assert ref.tag_set == ("3.6", {"ubuntu"})

    ref = ImageRef("lablup/python-tensorflow:1.10-py36-ubuntu")
    assert ref.name == "lablup/python-tensorflow"
    assert ref.tag == "1.10-py36-ubuntu"
    assert ref.registry == default_registry
    assert ref.tag_set == ("1.10", {"ubuntu", "py"})

    ref = ImageRef("lablup/kernel-python:3.6-ubuntu")
    assert ref.name == "lablup/kernel-python"
    assert ref.tag == "3.6-ubuntu"
    assert ref.registry == default_registry
    assert ref.tag_set == ("3.6", {"ubuntu"})

    # To parse registry URLs correctly, we first need to give
    # the valid registry URLs!
    ref = ImageRef("myregistry.org/lua", [])
    assert ref.name == "myregistry.org/lua"
    assert ref.tag == "latest"
    assert ref.registry == default_registry
    assert ref.tag_set == ("latest", set())

    ref = ImageRef("myregistry.org/lua", ["myregistry.org"])
    assert ref.name == "lua"
    assert ref.tag == "latest"
    assert ref.registry == "myregistry.org"
    assert ref.tag_set == ("latest", set())

    ref = ImageRef("myregistry.org/lua:5.3-alpine", ["myregistry.org"])
    assert ref.name == "lua"
    assert ref.tag == "5.3-alpine"
    assert ref.registry == "myregistry.org"
    assert ref.tag_set == ("5.3", {"alpine"})

    # Non-standard port number should be a part of the known registry value.
    ref = ImageRef("myregistry.org:999/mybase/python:3.6-cuda9-ubuntu", ["myregistry.org:999"])
    assert ref.name == "mybase/python"
    assert ref.tag == "3.6-cuda9-ubuntu"
    assert ref.registry == "myregistry.org:999"
    assert ref.tag_set == ("3.6", {"ubuntu", "cuda"})

    ref = ImageRef("myregistry.org/mybase/moon/python:3.6-cuda9-ubuntu", ["myregistry.org"])
    assert ref.name == "mybase/moon/python"
    assert ref.tag == "3.6-cuda9-ubuntu"
    assert ref.registry == "myregistry.org"
    assert ref.tag_set == ("3.6", {"ubuntu", "cuda"})

    # IP addresses are treated as valid registry URLs.
    ref = ImageRef("127.0.0.1:5000/python:3.6-cuda9-ubuntu")
    assert ref.name == "python"
    assert ref.tag == "3.6-cuda9-ubuntu"
    assert ref.registry == "127.0.0.1:5000"
    assert ref.tag_set == ("3.6", {"ubuntu", "cuda"})

    # IPv6 addresses must be bracketted.
    ref = ImageRef("::1/python:3.6-cuda9-ubuntu")
    assert ref.name == "::1/python"
    assert ref.tag == "3.6-cuda9-ubuntu"
    assert ref.registry == default_registry
    assert ref.tag_set == ("3.6", {"ubuntu", "cuda"})

    ref = ImageRef("[::1]/python:3.6-cuda9-ubuntu")
    assert ref.name == "python"
    assert ref.tag == "3.6-cuda9-ubuntu"
    assert ref.registry == "[::1]"
    assert ref.tag_set == ("3.6", {"ubuntu", "cuda"})

    ref = ImageRef("[::1]:5000/python:3.6-cuda9-ubuntu")
    assert ref.name == "python"
    assert ref.tag == "3.6-cuda9-ubuntu"
    assert ref.registry == "[::1]:5000"
    assert ref.tag_set == ("3.6", {"ubuntu", "cuda"})

    ref = ImageRef("[212c:9cb9:eada:e57b:84c9:6a9:fbec:bdd2]:1024/python")
    assert ref.name == "python"
    assert ref.tag == "latest"
    assert ref.registry == "[212c:9cb9:eada:e57b:84c9:6a9:fbec:bdd2]:1024"
    assert ref.tag_set == ("latest", set())

    with pytest.raises(ValueError):
        ref = ImageRef("a:!")

    with pytest.raises(ValueError):
        ref = ImageRef("127.0.0.1:5000/a:-x-")

    with pytest.raises(ValueError):
        ref = ImageRef("http://127.0.0.1:5000/xyz")

    with pytest.raises(ValueError):
        ref = ImageRef("//127.0.0.1:5000/xyz")


def test_image_ref_formats():
    ref = ImageRef("python:3.6-cuda9-ubuntu", [])
    assert ref.canonical == "index.docker.io/lablup/python:3.6-cuda9-ubuntu"
    assert ref.short == "lablup/python:3.6-cuda9-ubuntu"
    assert str(ref) == ref.canonical
    assert repr(ref) == f'<ImageRef: "{ref.canonical}" (x86_64)>'

    ref = ImageRef("myregistry.org/user/python:3.6-cuda9-ubuntu", ["myregistry.org"], "aarch64")
    assert ref.canonical == "myregistry.org/user/python:3.6-cuda9-ubuntu"
    assert ref.short == "user/python:3.6-cuda9-ubuntu"
    assert str(ref) == ref.canonical
    assert repr(ref) == f'<ImageRef: "{ref.canonical}" (aarch64)>'


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


def test_image_ref_generate_aliases():
    ref = ImageRef("lablup/python-tensorflow:1.5-py36-ubuntu16.04")
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
    ref = ImageRef("lablup/python-tensorflow:1.5-py36-ubuntu16.04-cuda10.0")
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
    ref = ImageRef("lablup/python-tensorflow:1.5-py36-ubuntu16.04-cuda10.0")
    aliases = ref.generate_aliases()
    assert "python-tensorflow" in aliases
    assert "tensorflow" in aliases
    assert "python" not in aliases


def test_image_ref_generate_aliases_disallowed():
    # an alias must include the main platform version tag
    ref = ImageRef("lablup/python-tensorflow:1.5-py36-ubuntu16.04-cuda10.0")
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
    r1 = ImageRef("lablup/python-tensorflow:1.5-py36-ubuntu16.04-cuda10.0")
    r2 = ImageRef("lablup/python-tensorflow:1.7-py36-ubuntu16.04-cuda10.0")
    r3 = ImageRef("lablup/python-tensorflow:1.7-py37-ubuntu18.04-cuda9.0")
    assert r1 < r2
    assert r1 < r3
    assert r2 < r3

    # only the image-refs with same names can be compared.
    rx = ImageRef("lablup/python:3.6-ubuntu")
    with pytest.raises(ValueError):
        rx < r1
    with pytest.raises(ValueError):
        r1 < rx

    # test case added for explicit behavior documentation
    # ImageRef(...:ubuntu16.04) > ImageRef(...:ubuntu) == False
    # ImageRef(...:ubuntu16.04) > ImageRef(...:ubuntu) == False
    # by keeping naming convetion, no need to handle these cases
    r4 = ImageRef("lablup/python-tensorflow:1.5-py36-ubuntu16.04-cuda9.0")
    r5 = ImageRef("lablup/python-tensorflow:1.5-py36-ubuntu-cuda9.0")
    assert not r4 > r5
    assert not r5 > r4


def test_image_ref_merge_aliases():
    # After merging, aliases that indicates two or more references should
    # indicate most recent versions.
    refs = [
        ImageRef("lablup/python:3.7-ubuntu18.04"),  # 0
        ImageRef("lablup/python-tensorflow:1.5-py36-ubuntu16.04-cuda10.0"),  # 1
        ImageRef("lablup/python-tensorflow:1.7-py36-ubuntu16.04-cuda10.0"),  # 2
        ImageRef("lablup/python-tensorflow:1.7-py37-ubuntu16.04-cuda9.0"),  # 3
        ImageRef("lablup/python-tensorflow:1.5-py36-ubuntu16.04"),  # 4
        ImageRef("lablup/python-tensorflow:1.7-py36-ubuntu16.04"),  # 5
        ImageRef("lablup/python-tensorflow:1.7-py37-ubuntu16.04"),  # 6
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
