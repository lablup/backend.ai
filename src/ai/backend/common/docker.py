from __future__ import annotations

import enum
import functools
import itertools
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import (
    TYPE_CHECKING,
    Final,
    Iterable,
    Literal,
    Mapping,
    NamedTuple,
    Optional,
    Self,
)

import aiohttp
import trafaret as t
import yarl
from packaging import version

from ai.backend.logging import BraceStyleAdapter

from . import validators as tx
from .arch import arch_name_aliases
from .exception import InvalidImageName, InvalidImageTag, ProjectMismatchWithCanonical
from .service_ports import parse_service_ports
from .utils import is_ip_address_format, join_non_empty

if TYPE_CHECKING:
    from .types import ImageConfig

__all__ = (
    "arch_name_aliases",
    "default_registry",
    "default_repository",
    "docker_api_arch_aliases",
    "common_image_label_schema",
    "inference_image_label_schema",
    "validate_image_labels",
    "login",
    "MIN_KERNELSPEC",
    "MAX_KERNELSPEC",
    "ImageRef",
    "ParsedImageStr",
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

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

default_registry = "index.docker.io"
default_repository = "lablup"

MIN_KERNELSPEC = 1
MAX_KERNELSPEC = 1

rx_slug = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-._]*[A-Za-z0-9])?$")

common_image_label_schema = t.Dict({
    # Required labels
    t.Key("ai.backend.kernelspec", default=1): t.ToInt(lte=MAX_KERNELSPEC, gte=MIN_KERNELSPEC),
    t.Key("ai.backend.features", default=["uid-match"]): tx.StringList(delimiter=" "),
    # ai.backend.resource.min.*
    t.Key("ai.backend.base-distro", default=None): t.Null | t.String(),
    t.Key("ai.backend.runtime-type", default="app"): t.String(),
    t.Key("ai.backend.runtime-path", default=PurePath("/bin/true")): tx.PurePath(),
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
def _search_docker_socket_files_impl() -> tuple[
    Path, yarl.URL, type[aiohttp.UnixConnector] | type[aiohttp.NamedPipeConnector]
]:
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
    # Check also 400 response since the AWS ECR Public server returns a 400 response
    # when given invalid credential authorization.
    elif ping_status in [400, 401]:
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

    def __init__(self, tags: Iterable[str], value: Optional[str] = None) -> None:
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

    def has(self, key: str, version: Optional[str] = None):
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


class ParsedImageStr(NamedTuple):
    registry: str
    project_and_image_name: str
    tag: str

    @property
    def canonical(self) -> str:
        return f"{self.registry}/{self.project_and_image_name}:{self.tag}"

    @property
    def short(self) -> str:
        return f"{self.project_and_image_name}:{self.tag}"

    @property
    def tag_set(self) -> tuple[str, PlatformTagSet]:
        tags = self.tag.split("-")
        return (tags[0], PlatformTagSet(tags[1:], self.project_and_image_name))

    def __str__(self) -> str:
        return self.canonical


@dataclass
class ImageRef:
    """
    Represent image reference.
    """

    name: str
    project: str | None
    tag: str
    registry: str
    architecture: str
    is_local: bool

    @classmethod
    def from_image_config(cls, config: ImageConfig) -> Self:
        return cls.from_image_str(
            config["canonical"],
            config["project"],
            config["registry"]["name"],
            is_local=config["is_local"],
            architecture=config["architecture"],
        )

    @classmethod
    def from_image_str(
        cls,
        image_str: str,
        project: str | None,
        registry: str,
        *,
        architecture: str = "x86_64",
        is_local: bool = False,
    ) -> Self:
        """
        Parse the image reference string and return an ImageRef object from the string.
        """

        parsed = cls.parse_image_str(image_str, registry)

        if not project:
            image_name = parsed.project_and_image_name
        elif parsed.project_and_image_name == project:
            image_name = ""
        else:
            if not parsed.project_and_image_name.startswith(f"{project}/"):
                raise ProjectMismatchWithCanonical(project, parsed.canonical)

            image_name = parsed.project_and_image_name.split(f"{project}/", maxsplit=1)[1]

        return cls(
            name=image_name,
            project=project,
            registry=registry,
            tag=parsed.tag,
            architecture=architecture,
            is_local=is_local,
        )

    @classmethod
    def parse_image_tag(
        cls, image_str: str, *, using_default_repository: bool = False
    ) -> tuple[str, str]:
        """
        Parses the image name and tag from the given image string.

        When the `image_str` does not contain '/', and `using_default_repository` is True, it includes the `default_repository` (lablup) in the image.
        """
        image_tag = image_str.rsplit(":", maxsplit=1)
        if len(image_tag) == 1:
            image_str = image_tag[0]
            tag = "latest"
        else:
            image_str = image_tag[0]
            tag = image_tag[1]
        if not image_str:
            raise InvalidImageName("Empty image repository/name")
        if ("/" not in image_str) and using_default_repository:
            image_str = default_repository + "/" + image_str
        return image_str, tag

    @classmethod
    def parse_image_str(
        cls, image_str: str, registry: str | Literal["*"] | None = None
    ) -> ParsedImageStr:
        """
        Parses a string representing an image.

        `image_str` basically follow the format below: `<registry>/<project>/<image name>:<version>-<tag>-<tag>...`
        And if certain values are not provided (for example, if only the image name is given), hardcoded default values will be used.
        Tags must begin with a letter and cannot end with a hyphen. And since hyphens are used to separate tags, a tag cannot contain a hyphen within itself.
        For more details, you can refer to the `tests/common/test_docker.py`.

        Here are some details about this function's behavior.
        1. Passing '*' to `registry` parse any characters before the first '/' as the registry part.
        2. Passing 'None' to `registry` use the default registry (`index.docker.io`).
           In this case, the `image_str` should be a combination of the project and image name without the registry part.
        3. If the registry part of the `image_str` is in IP address format, it parses that value as the registry part regardless of the `registry` argument.
        4. `ParsedImageStr` can not distinguish the project and the image name.
           If you already know the project value of the image, use `from_image_str()` instead of this function.
        """

        if "://" in image_str or image_str.startswith("//"):
            raise InvalidImageName(image_str)

        def divide_parts(image_str: str, registry: str | Literal["*"] | None) -> tuple[str, str]:
            if "/" not in image_str:
                return (default_registry, image_str)

            maybe_registry, maybe_project_and_image_name = image_str.split("/", maxsplit=1)

            if (
                registry == maybe_registry
                or registry == "*"
                or is_ip_address_format(maybe_registry)
            ):
                return (maybe_registry, maybe_project_and_image_name)
            elif registry is None:
                return (default_registry, image_str)
            else:
                return (registry, image_str)

        registry_part, project_and_image_name_part = divide_parts(image_str, registry)

        using_default_repository = (
            registry_part.endswith(".docker.io") or registry_part == "docker.io"
        )

        project_and_image_name, tag = cls.parse_image_tag(
            project_and_image_name_part, using_default_repository=using_default_repository
        )

        if not rx_slug.search(tag):
            raise InvalidImageTag(tag, image_str)

        return ParsedImageStr(
            registry=registry_part,
            project_and_image_name=project_and_image_name,
            tag=tag,
        )

    def __post_init__(
        self,
    ) -> None:
        self.architecture = arch_name_aliases.get(self.architecture, self.architecture)
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
        tags = self.tag.split("-")
        self._tag_set = (tags[0], PlatformTagSet(tags[1:], self.name))

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
        join = functools.partial(join_non_empty, sep="/")
        # e.g., cr.backend.ai/stable/python:3.9-ubuntu
        return f"{join(self.registry, self.project, self.name)}:{self.tag}"

    @property
    def tag_set(self) -> tuple[str, PlatformTagSet]:
        # e.g., '3.9', {'ubuntu', ...}
        return self._tag_set

    @property
    def short(self) -> str:
        """
        Returns the image reference string without the registry part.
        """
        # e.g., stable/python:3.9-ubuntu
        join = functools.partial(join_non_empty, sep="/")
        return f"{join(self.project, self.name)}:{self.tag}"

    def __str__(self) -> str:
        return self.canonical

    def __repr__(self) -> str:
        return f'<ImageRef: "{self.canonical}" ({self.architecture})>'

    def __hash__(self) -> int:
        return hash((self.project, self.name, self.tag, self.registry, self.architecture))

    def __lt__(self, other) -> bool:
        if self == other:  # call __eq__ first for resolved check
            return False
        if not (self.name == other.name and self.project == other.project):
            raise ValueError(
                "Only the image-refs with the same names and projects can be compared."
            )
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
