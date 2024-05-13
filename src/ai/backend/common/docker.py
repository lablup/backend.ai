from __future__ import annotations

import enum
import functools
import ipaddress
import itertools
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Final,
    Iterable,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Union,
)

import aiohttp
import trafaret as t
import yarl
from packaging import version

from . import validators as tx
from .arch import arch_name_aliases
from .etcd import AsyncEtcd
from .etcd import quote as etcd_quote
from .etcd import unquote as etcd_unquote
from .exception import InvalidImageName, InvalidImageTag, UnknownImageRegistry
from .logging import BraceStyleAdapter
from .service_ports import parse_service_ports

__all__ = (
    "arch_name_aliases",
    "default_registry",
    "default_repository",
    "docker_api_arch_aliases",
    "common_image_label_schema",
    "inference_image_label_schema",
    "validate_image_labels",
    "login",
    "get_known_registries",
    "is_known_registry",
    "get_registry_info",
    "MIN_KERNELSPEC",
    "MAX_KERNELSPEC",
    "ImageRef",
)

# generalize architecture symbols to match docker API's norm
docker_api_arch_aliases: Final[Mapping[str, str]] = {
    "aarch64": "arm64",
    "arm64": "arm64",
    "x86_64": "amd64",
    "x64": "amd64",
    "amd64": "amd64",
    "x86": "386",
    "x32": "386",
    "i686": "386",
    "386": "386",
}

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

default_registry = "index.docker.io"
default_repository = "lablup"

MIN_KERNELSPEC = 1
MAX_KERNELSPEC = 1

common_image_label_schema = t.Dict({
    # Required labels
    t.Key("ai.backend.kernelspec"): t.ToInt(lte=MAX_KERNELSPEC, gte=MIN_KERNELSPEC),
    t.Key("ai.backend.features"): tx.StringList(delimiter=" "),
    # ai.backend.resource.min.*
    t.Key("ai.backend.base-distro"): t.String(),
    t.Key("ai.backend.runtime-type"): t.String(),
    t.Key("ai.backend.runtime-path"): tx.PurePath(),
    # Optional labels
    t.Key("ai.backend.role", default="COMPUTE"): t.Enum("COMPUTE", "INFERENCE", "SYSTEM"),
    t.Key("ai.backend.envs.corecount", optional=True): tx.StringList(allow_blank=True),
    t.Key("ai.backend.accelerators", optional=True): tx.StringList(allow_blank=True),
    t.Key("ai.backend.service-ports", optional=True): tx.StringList(allow_blank=True),
}).allow_extra("*")

inference_image_label_schema = t.Dict({
    t.Key("ai.backend.endpoint-ports"): tx.StringList(min_length=1),
    t.Key("ai.backend.model-path"): tx.PurePath(),
    t.Key("ai.backend.model-format"): t.String(),
}).ignore_extra("*")


class DockerConnectorSource(enum.Enum):
    ENV_VAR = enum.auto()
    USER_CONTEXT = enum.auto()
    KNOWN_LOCATION = enum.auto()


@dataclass()
class DockerConnector:
    sock_path: Path | None
    docker_host: yarl.URL
    connector: aiohttp.BaseConnector
    source: DockerConnectorSource


@functools.lru_cache()
def get_docker_context_host() -> str | None:
    try:
        docker_config_path = Path.home() / ".docker" / "config.json"
        docker_config = json.loads(docker_config_path.read_bytes())
    except IOError:
        return None
    current_context_name = docker_config.get("currentContext", "default")
    for meta_path in (Path.home() / ".docker" / "contexts" / "meta").glob("*/meta.json"):
        context_data = json.loads(meta_path.read_bytes())
        if context_data["Name"] == current_context_name:
            return context_data["Endpoints"]["docker"]["Host"]
    return None


def parse_docker_host_url(
    docker_host: yarl.URL,
) -> tuple[Path | None, yarl.URL, aiohttp.BaseConnector]:
    connector_cls: type[aiohttp.UnixConnector] | type[aiohttp.NamedPipeConnector]
    match docker_host.scheme:
        case "http" | "https":
            return None, docker_host, aiohttp.TCPConnector()
        case "unix":
            path = Path(docker_host.path)
            if not path.exists() or not path.is_socket():
                raise RuntimeError(f"DOCKER_HOST {path} is not a valid socket file.")
            decoded_path = os.fsdecode(path)
            connector_cls = aiohttp.UnixConnector
        case "npipe":
            path = Path(docker_host.path.replace("/", "\\"))
            if not path.exists() or not path.is_fifo():
                raise RuntimeError(f"DOCKER_HOST {path} is not a valid named pipe.")
            decoded_path = os.fsdecode(path)
            connector_cls = aiohttp.NamedPipeConnector
        case _ as unknown_scheme:
            raise RuntimeError("unsupported connection scheme", unknown_scheme)
    return (
        path,
        yarl.URL("http://docker"),  # a fake hostname to construct a valid URL
        connector_cls(decoded_path, force_close=True),
    )


# We may cache the connector type but not connector instances!
@functools.lru_cache()
def _search_docker_socket_files_impl() -> (
    tuple[Path, yarl.URL, type[aiohttp.UnixConnector] | type[aiohttp.NamedPipeConnector]]
):
    connector_cls: type[aiohttp.UnixConnector] | type[aiohttp.NamedPipeConnector]
    match sys.platform:
        case "linux" | "darwin":
            search_paths = [
                Path("/run/docker.sock"),
                Path("/var/run/docker.sock"),
                Path.home() / ".docker/run/docker.sock",
            ]
            connector_cls = aiohttp.UnixConnector
        case "win32":
            search_paths = [
                Path(r"\\.\pipe\docker_engine"),
            ]
            connector_cls = aiohttp.NamedPipeConnector
        case _ as platform_name:
            raise RuntimeError(f"unsupported platform: {platform_name}")
    for p in search_paths:
        if p.exists() and (p.is_socket() or p.is_fifo()):
            return (
                p,
                yarl.URL("http://docker"),  # a fake hostname to construct a valid URL
                connector_cls,
            )
    else:
        searched_paths = ", ".join(map(os.fsdecode, search_paths))
        raise RuntimeError(f"could not find the docker socket; tried: {searched_paths}")


def search_docker_socket_files() -> tuple[Path | None, yarl.URL, aiohttp.BaseConnector]:
    connector_cls: type[aiohttp.UnixConnector] | type[aiohttp.NamedPipeConnector]
    sock_path, docker_host, connector_cls = _search_docker_socket_files_impl()
    return (
        sock_path,
        docker_host,
        connector_cls(os.fsdecode(sock_path), force_close=True),
    )


def get_docker_connector() -> DockerConnector:
    if raw_docker_host := os.environ.get("DOCKER_HOST", None):
        sock_path, docker_host, connector = parse_docker_host_url(yarl.URL(raw_docker_host))
        return DockerConnector(
            sock_path,
            docker_host,
            connector,
            DockerConnectorSource.ENV_VAR,
        )
    if raw_docker_host := get_docker_context_host():
        sock_path, docker_host, connector = parse_docker_host_url(yarl.URL(raw_docker_host))
        return DockerConnector(
            sock_path,
            docker_host,
            connector,
            DockerConnectorSource.USER_CONTEXT,
        )
    sock_path, docker_host, connector = search_docker_socket_files()
    return DockerConnector(
        sock_path,
        docker_host,
        connector,
        DockerConnectorSource.KNOWN_LOCATION,
    )


async def login(
    sess: aiohttp.ClientSession, registry_url: yarl.URL, credentials: dict, scope: str
) -> dict:
    """
    Authorize to the docker registry using the given credentials and token scope, and returns a set
    of required aiohttp.ClientSession.request() keyword arguments for further API requests.

    Some registry servers only rely on HTTP Basic Authentication without token-based access controls
    (usually via nginx proxy). We do support them also. :)
    """
    basic_auth: Optional[aiohttp.BasicAuth]

    if credentials.get("username") and credentials.get("password"):
        basic_auth = aiohttp.BasicAuth(
            credentials["username"],
            credentials["password"],
        )
    else:
        basic_auth = None
    realm = registry_url / "token"  # fallback
    service = "registry"  # fallback
    async with sess.get(registry_url / "v2/", auth=basic_auth) as resp:
        ping_status = resp.status
        www_auth_header = resp.headers.get("WWW-Authenticate")
        if www_auth_header:
            match = re.search(r'realm="([^"]+)"', www_auth_header)
            if match:
                realm = yarl.URL(match.group(1))
            match = re.search(r'service="([^"]+)"', www_auth_header)
            if match:
                service = match.group(1)
    if ping_status == 200:
        log.debug("docker-registry: {0} -> basic-auth", registry_url)
        return {"auth": basic_auth, "headers": {}}
    elif ping_status == 404:
        raise RuntimeError(f"Unsupported docker registry: {registry_url}! (API v2 not implemented)")
    elif ping_status == 401:
        params = {
            "scope": scope,
            "offline_token": "true",
            "client_id": "docker",
            "service": service,
        }
        async with sess.get(realm, params=params, auth=basic_auth) as resp:
            log.debug("docker-registry: {0} -> {1}", registry_url, realm)
            if resp.status == 200:
                data = json.loads(await resp.read())
                token = data.get("token", None)
                return {
                    "auth": None,
                    "headers": {
                        "Authorization": f"Bearer {token}",
                    },
                }
    raise RuntimeError(f"authentication for docker registry {registry_url} failed")


async def get_known_registries(etcd: AsyncEtcd) -> Mapping[str, yarl.URL]:
    data = await etcd.get_prefix("config/docker/registry/")
    results: MutableMapping[str, yarl.URL] = {}
    for key, value in data.items():
        name = etcd_unquote(key)
        if isinstance(value, str):
            results[name] = yarl.URL(value)
        elif isinstance(value, Mapping):
            assert isinstance(value[""], str)
            results[name] = yarl.URL(value[""])
    return results


def is_known_registry(
    val: str,
    known_registries: Union[Mapping[str, Any], Sequence[str]] | None = None,
):
    if val == default_registry:
        return True
    if known_registries is not None and val in known_registries:
        return True
    try:
        url = yarl.URL("//" + val)
        if url.host and ipaddress.ip_address(url.host):
            return True
    except ValueError:
        pass
    return False


async def get_registry_info(etcd: AsyncEtcd, name: str) -> tuple[yarl.URL, dict]:
    reg_path = f"config/docker/registry/{etcd_quote(name)}"
    item = await etcd.get_prefix(reg_path)
    if not item:
        raise UnknownImageRegistry(name)
    registry_addr = item[""]
    if not registry_addr:
        raise UnknownImageRegistry(name)
    assert isinstance(registry_addr, str)
    creds = {}
    username = item.get("username")
    if username is not None:
        creds["username"] = username
    password = item.get("password")
    if password is not None:
        creds["password"] = password
    return yarl.URL(registry_addr), creds


def validate_image_labels(labels: dict[str, str]) -> dict[str, str]:
    common_labels = common_image_label_schema.check(labels)
    service_ports = {
        item["name"]: item
        for item in parse_service_ports(
            common_labels.get("ai.backend.service-ports", ""),
            common_labels.get("ai.backend.endpoint-ports", ""),
        )
    }
    match common_labels["ai.backend.role"]:
        case "INFERENCE":
            inference_labels = inference_image_label_schema.check(labels)
            for name in inference_labels["ai.backend.endpoint-ports"]:
                if name not in service_ports:
                    raise ValueError(
                        f"ai.backend.endpoint-ports contains an undefined service port: {name}"
                    )
                # inference images should launch the serving daemons when they start as a container.
                # TODO: enforce this restriction??
                if service_ports[name]["protocol"] != "preopen":
                    raise ValueError(f"The endpoint-port {name} must be a preopen service-port.")
            common_labels.update(inference_labels)
        case _:
            pass
    return common_labels


class PlatformTagSet(Mapping):
    __slots__ = ("_data",)
    _data: dict[str, str]
    _rx_ver = re.compile(r"^(?P<tag>[a-zA-Z_]+)(?P<version>\d+(?:\.\d+)*[a-z0-9]*)?$")

    def __init__(self, tags: Iterable[str], value: str = None) -> None:
        self._data = dict()
        rx = type(self)._rx_ver
        for tag in tags:
            match = rx.search(tag)
            if match is None:
                raise InvalidImageTag(tag, value)
            key = match.group("tag")
            value = match.group("version")
            if key in self._data:
                raise InvalidImageTag(tag, value)
            if value is None:
                value = ""
            self._data[key] = value

    def has(self, key: str, version: str = None):
        if version is None:
            return key in self._data
        _v = self._data.get(key, None)
        return _v == version

    def __getitem__(self, key: str):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __eq__(self, other):
        if isinstance(other, (set, frozenset)):
            return set(self._data.keys()) == other
        return self._data == other


class ImageRef:
    """
    Class to represent image reference.
    passing ['*'] to `known_registries` when creating object
    will allow any repository on canonical string.
    """

    _value: str
    _is_local: bool
    _arch: str
    _registry: str

    _name: str
    _tag: str

    __slots__ = ("_registry", "_name", "_tag", "_arch", "_tag_set", "_sha", "_is_local", "_value")

    _rx_slug = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-._]*[A-Za-z0-9])?$")

    def __init__(
        self,
        value: str,
        known_registries: Optional[Mapping[str, Any] | Sequence[str]] = None,
        architecture: str = "x86_64",
        is_local: bool = False,
    ) -> None:
        self._value = value
        self._is_local = is_local
        self._arch = arch_name_aliases.get(architecture, architecture)
        rx_slug = type(self)._rx_slug
        if "://" in self._value or self._value.startswith("//"):
            raise InvalidImageName(self._value)
        parts = self._value.split("/", maxsplit=1)
        if len(parts) == 1:
            self._registry = default_registry
            self._name, self._tag = ImageRef._parse_image_tag(self._value, True)
            if not rx_slug.search(self._tag):
                raise InvalidImageTag(self._tag, self._value)
        else:
            if is_known_registry(parts[0], known_registries):
                self._registry = parts[0]
                using_default = parts[0].endswith(".docker.io") or parts[0] == "docker.io"
                self._name, self._tag = ImageRef._parse_image_tag(parts[1], using_default)
            # add ['*'] as magic keyword to accept any repository as valid repo
            elif known_registries == ["*"]:
                self._registry = parts[0]
                self._name, self._tag = ImageRef._parse_image_tag(parts[1], False)
            else:
                self._registry = default_registry
                self._name, self._tag = ImageRef._parse_image_tag(self._value, True)
            if not rx_slug.search(self._tag):
                raise InvalidImageTag(self._tag, self._value)
        self._update_tag_set()

    @staticmethod
    def _parse_image_tag(s: str, using_default_registry: bool = False) -> tuple[str, str]:
        image_tag = s.rsplit(":", maxsplit=1)
        if len(image_tag) == 1:
            image = image_tag[0]
            tag = "latest"
        else:
            image = image_tag[0]
            tag = image_tag[1]
        if not image:
            raise InvalidImageName("Empty image repository/name")
        if ("/" not in image) and using_default_registry:
            image = default_repository + "/" + image
        return image, tag

    def _update_tag_set(self):
        if self._tag is None:
            self._tag_set = (None, PlatformTagSet([], self._value))
            return
        tags = self._tag.split("-")
        self._tag_set = (tags[0], PlatformTagSet(tags[1:], self._value))

    def generate_aliases(self) -> Mapping[str, "ImageRef"]:
        basename = self.name.split("/")[-1]
        possible_names = basename.rsplit("-")
        if len(possible_names) > 1:
            possible_names = [basename, possible_names[1]]

        possible_ptags = []
        tag_set = self.tag_set
        if not tag_set[0]:
            pass
        else:
            possible_ptags.append([tag_set[0]])
            for tag_key in tag_set[1]:
                tag_ver = tag_set[1][tag_key]
                tag_list = ["", tag_key, tag_key + tag_ver]
                if "." in tag_ver:
                    tag_list.append(tag_key + tag_ver.rsplit(".")[0])
                elif tag_key == "py" and len(tag_ver) > 1:
                    tag_list.append(tag_key + tag_ver[0])
                if "cuda" in tag_key:
                    tag_list.append("gpu")
                possible_ptags.append(tag_list)

        ret = {}
        for name in possible_names:
            ret[name] = self
        for name, ptags in itertools.product(possible_names, itertools.product(*possible_ptags)):
            ret[f"{name}:{'-'.join(t for t in ptags if t)}"] = self
        return ret

    @staticmethod
    def merge_aliases(genned_aliases_1, genned_aliases_2) -> Mapping[str, "ImageRef"]:
        ret = {}
        aliases_set_1, aliases_set_2 = set(genned_aliases_1.keys()), set(genned_aliases_2.keys())
        aliases_dup = aliases_set_1 & aliases_set_2

        for alias in aliases_dup:
            ret[alias] = max(genned_aliases_1[alias], genned_aliases_2[alias])

        for alias in aliases_set_1 - aliases_dup:
            ret[alias] = genned_aliases_1[alias]
        for alias in aliases_set_2 - aliases_dup:
            ret[alias] = genned_aliases_2[alias]

        return ret

    @property
    def canonical(self) -> str:
        # e.g., registry.docker.io/lablup/kernel-python:3.6-ubuntu
        return f"{self.registry}/{self.name}:{self.tag}"

    @property
    def registry(self) -> str:
        # e.g., lablup
        return self._registry

    @property
    def name(self) -> str:
        # e.g., python
        return self._name

    @property
    def tag(self) -> str:
        # e.g., 3.6-ubuntu
        return self._tag

    @property
    def architecture(self) -> str:
        # e.g., aarch64
        return self._arch

    @property
    def tag_set(self) -> tuple[str, PlatformTagSet]:
        # e.g., '3.6', {'ubuntu', 'cuda', ...}
        return self._tag_set

    @property
    def is_local(self) -> bool:
        return self._is_local

    @property
    def short(self) -> str:
        """
        Returns the image reference string without the registry part.
        """
        # e.g., python:3.6-ubuntu
        return f"{self.name}:{self.tag}" if self.tag is not None else self.name

    def __str__(self) -> str:
        return self.canonical

    def __repr__(self) -> str:
        return f'<ImageRef: "{self.canonical}" ({self.architecture})>'

    def __hash__(self) -> int:
        return hash((self._name, self._tag, self._registry, self._arch))

    def __eq__(self, other) -> bool:
        return (
            self._registry == other._registry
            and self._name == other._name
            and self._tag == other._tag
            and self._arch == other._arch
        )

    def __ne__(self, other) -> bool:
        return (
            self._registry != other._registry
            or self._name != other._name
            or self._tag != other._tag
            or self._arch != other._arch
        )

    def __lt__(self, other) -> bool:
        if self == other:  # call __eq__ first for resolved check
            return False
        if self.name != other.name:
            raise ValueError("only the image-refs with same names can be compared.")
        if self.tag_set[0] != other.tag_set[0]:
            return version.parse(self.tag_set[0]) < version.parse(other.tag_set[0])
        ptagset_self, ptagset_other = self.tag_set[1], other.tag_set[1]
        for key_self in ptagset_self:
            if ptagset_other.has(key_self):
                version_self, version_other = (
                    ptagset_self.get(key_self),
                    ptagset_other.get(key_self),
                )
                if version_self and version_other:
                    parsed_version_self, parsed_version_other = (
                        version.parse(version_self),
                        version.parse(version_other),
                    )
                    if parsed_version_self != parsed_version_other:
                        return parsed_version_self < parsed_version_other
        return len(ptagset_self) > len(ptagset_other)
