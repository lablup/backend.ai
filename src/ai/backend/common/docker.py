import ipaddress
import itertools
import json
import logging
from packaging import version
import re
from typing import (
    Any, Final, Optional, Union,
    Dict, Mapping,
    Iterable,
    Tuple, Sequence,
    MutableMapping,
)

import aiohttp
import yarl

from .logging import BraceStyleAdapter
from .etcd import (
    AsyncEtcd,
    quote as etcd_quote,
    unquote as etcd_unquote,
)
from .exception import UnknownImageRegistry

__all__ = (
    'arch_name_aliases',
    'default_registry',
    'default_repository',
    'docker_api_arch_aliases',
    'login',
    'get_known_registries',
    'is_known_registry',
    'get_registry_info',
    'MIN_KERNELSPEC',
    'MAX_KERNELSPEC',
    'ImageRef',
)

arch_name_aliases: Final[Mapping[str, str]] = {
    "arm64": "aarch64",  # macOS with LLVM
    "amd64": "x86_64",   # Windows/Linux
    "x64": "x86_64",     # Windows
    "x32": "x86",        # Windows
    "i686": "x86",       # Windows
}
# generalize architecture symbols to match docker API's norm
docker_api_arch_aliases: Final[Mapping[str, str]] = {
    'aarch64': 'arm64',
    'arm64': 'arm64',
    'x86_64': 'amd64',
    'x64': 'amd64',
    'amd64': 'amd64',
    'x86': '386',
    'x32': '386',
    'i686': '386',
    '386': '386',
}

log = BraceStyleAdapter(logging.Logger('ai.backend.common.docker'))

default_registry = 'index.docker.io'
default_repository = 'lablup'

MIN_KERNELSPEC = 1
MAX_KERNELSPEC = 1


async def login(
        sess: aiohttp.ClientSession,
        registry_url: yarl.URL,
        credentials: dict,
        scope: str) -> dict:
    """
    Authorize to the docker registry using the given credentials and token scope, and returns a set
    of required aiohttp.ClientSession.request() keyword arguments for further API requests.

    Some registry servers only rely on HTTP Basic Authentication without token-based access controls
    (usually via nginx proxy). We do support them also. :)
    """
    basic_auth: Optional[aiohttp.BasicAuth]

    if credentials.get('username') and credentials.get('password'):
        basic_auth = aiohttp.BasicAuth(
            credentials['username'], credentials['password'],
        )
    else:
        basic_auth = None
    realm = registry_url / 'token'  # fallback
    service = 'registry'            # fallback
    async with sess.get(registry_url / 'v2/', auth=basic_auth) as resp:
        ping_status = resp.status
        www_auth_header = resp.headers.get('WWW-Authenticate')
        if www_auth_header:
            match = re.search(r'realm="([^"]+)"', www_auth_header)
            if match:
                realm = yarl.URL(match.group(1))
            match = re.search(r'service="([^"]+)"', www_auth_header)
            if match:
                service = match.group(1)
    if ping_status == 200:
        log.debug('docker-registry: {0} -> basic-auth', registry_url)
        return {'auth': basic_auth, 'headers': {}}
    elif ping_status == 404:
        raise RuntimeError(f'Unsupported docker registry: {registry_url}! '
                           '(API v2 not implemented)')
    elif ping_status == 401:
        params = {
            'scope': scope,
            'offline_token': 'true',
            'client_id': 'docker',
            'service': service,
        }
        async with sess.get(realm, params=params, auth=basic_auth) as resp:
            log.debug('docker-registry: {0} -> {1}', registry_url, realm)
            if resp.status == 200:
                data = json.loads(await resp.read())
                token = data.get('token', None)
                return {'auth': None, 'headers': {
                    'Authorization': f'Bearer {token}',
                }}
    raise RuntimeError('authentication for docker registry '
                       f'{registry_url} failed')


async def get_known_registries(etcd: AsyncEtcd) -> Mapping[str, yarl.URL]:
    data = await etcd.get_prefix('config/docker/registry/')
    results: MutableMapping[str, yarl.URL] = {}
    for key, value in data.items():
        name = etcd_unquote(key)
        if isinstance(value, str):
            results[name] = yarl.URL(value)
        elif isinstance(value, Mapping):
            results[name] = yarl.URL(value[''])
    return results


def is_known_registry(val: str,
                      known_registries: Union[Mapping[str, Any], Sequence[str]] = None):
    if val == default_registry:
        return True
    if known_registries is not None and val in known_registries:
        return True
    try:
        url = yarl.URL('//' + val)
        if url.host and ipaddress.ip_address(url.host):
            return True
    except ValueError:
        pass
    return False


async def get_registry_info(etcd: AsyncEtcd, name: str) -> Tuple[yarl.URL, dict]:
    reg_path = f'config/docker/registry/{etcd_quote(name)}'
    item = await etcd.get_prefix(reg_path)
    if not item:
        raise UnknownImageRegistry(name)
    registry_addr = item['']
    if not registry_addr:
        raise UnknownImageRegistry(name)
    creds = {}
    username = item.get('username')
    if username is not None:
        creds['username'] = username
    password = item.get('password')
    if password is not None:
        creds['password'] = password
    return yarl.URL(registry_addr), creds


class PlatformTagSet(Mapping):

    __slots__ = ('_data', )
    _data: Dict[str, str]
    _rx_ver = re.compile(r'^(?P<tag>[a-zA-Z]+)(?P<version>\d+(?:\.\d+)*[a-z0-9]*)?$')

    def __init__(self, tags: Iterable[str]):
        self._data = dict()
        rx = type(self)._rx_ver
        for t in tags:
            match = rx.search(t)
            if match is None:
                raise ValueError('invalid tag-version string', t)
            key = match.group('tag')
            value = match.group('version')
            if key in self._data:
                raise ValueError('duplicate platform tag with different versions', t)
            if value is None:
                value = ''
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
    __slots__ = ('_registry', '_name', '_tag', '_arch', '_tag_set', '_sha')

    _rx_slug = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9-._]*[A-Za-z0-9])?$')

    def __init__(
        self,
        value: str,
        known_registries: Union[Mapping[str, Any], Sequence[str]] = None,
        architecture='x86_64',
    ):
        self._arch = arch_name_aliases.get(architecture, architecture)
        rx_slug = type(self)._rx_slug
        if '://' in value or value.startswith('//'):
            raise ValueError('ImageRef should not contain the protocol scheme.')
        parts = value.split('/', maxsplit=1)
        if len(parts) == 1:
            self._registry = default_registry
            self._name, self._tag = ImageRef._parse_image_tag(value, True)
            if not rx_slug.search(self._tag):
                raise ValueError('Invalid image tag')
        else:
            if is_known_registry(parts[0], known_registries):
                self._registry = parts[0]
                using_default = (parts[0].endswith('.docker.io') or parts[0] == 'docker.io')
                self._name, self._tag = ImageRef._parse_image_tag(parts[1], using_default)
            # add ['*'] as magic keyword to accept any repository as valid repo
            elif known_registries == ['*']:
                self._registry = parts[0]
                self._name, self._tag = ImageRef._parse_image_tag(parts[1], False)
            else:
                self._registry = default_registry
                self._name, self._tag = ImageRef._parse_image_tag(value, True)
            if not rx_slug.search(self._tag):
                raise ValueError('Invalid image tag')
        self._update_tag_set()

    @staticmethod
    def _parse_image_tag(s: str, using_default_registry: bool = False) -> Tuple[str, str]:
        image_tag = s.rsplit(':', maxsplit=1)
        if len(image_tag) == 1:
            image = image_tag[0]
            tag = 'latest'
        else:
            image = image_tag[0]
            tag = image_tag[1]
        if not image:
            raise ValueError('Empty image repository/name')
        if ('/' not in image) and using_default_registry:
            image = default_repository + '/' + image
        return image, tag

    def _update_tag_set(self):
        if self._tag is None:
            self._tag_set = (None, PlatformTagSet([]))
            return
        tags = self._tag.split('-')
        self._tag_set = (tags[0], PlatformTagSet(tags[1:]))

    def generate_aliases(self) -> Mapping[str, 'ImageRef']:
        basename = self.name.split('/')[-1]
        possible_names = basename.rsplit('-')
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
                tag_list = ['', tag_key, tag_key + tag_ver]
                if '.' in tag_ver:
                    tag_list.append(tag_key + tag_ver.rsplit('.')[0])
                elif tag_key == 'py' and len(tag_ver) > 1:
                    tag_list.append(tag_key + tag_ver[0])
                if 'cuda' in tag_key:
                    tag_list.append('gpu')
                possible_ptags.append(tag_list)

        ret = {}
        for name in possible_names:
            ret[name] = self
        for name, ptags in itertools.product(
                possible_names,
                itertools.product(*possible_ptags)):
            ret[f"{name}:{'-'.join(t for t in ptags if t)}"] = self
        return ret

    @staticmethod
    def merge_aliases(genned_aliases_1, genned_aliases_2) -> Mapping[str, 'ImageRef']:
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
        return f'{self.registry}/{self.name}:{self.tag}'

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
    def tag_set(self) -> Tuple[str, PlatformTagSet]:
        # e.g., '3.6', {'ubuntu', 'cuda', ...}
        return self._tag_set

    @property
    def short(self) -> str:
        """
        Returns the image reference string without the registry part.
        """
        # e.g., python:3.6-ubuntu
        return f'{self.name}:{self.tag}' if self.tag is not None else self.name

    def __str__(self) -> str:
        return self.canonical

    def __repr__(self) -> str:
        return f'<ImageRef: "{self.canonical}" ({self.architecture})>'

    def __hash__(self) -> int:
        return hash((self._name, self._tag, self._registry, self._arch))

    def __eq__(self, other) -> bool:
        return (self._registry == other._registry and
                self._name == other._name and
                self._tag == other._tag and
                self._arch == other._arch)

    def __ne__(self, other) -> bool:
        return (self._registry != other._registry or
                self._name != other._name or
                self._tag != other._tag or
                self._arch != other._arch)

    def __lt__(self, other) -> bool:
        if self == other:   # call __eq__ first for resolved check
            return False
        if self.name != other.name:
            raise ValueError('only the image-refs with same names can be compared.')
        if self.tag_set[0] != other.tag_set[0]:
            return version.parse(self.tag_set[0]) < version.parse(other.tag_set[0])
        ptagset_self, ptagset_other = self.tag_set[1], other.tag_set[1]
        for key_self in ptagset_self:
            if ptagset_other.has(key_self):
                version_self, version_other = ptagset_self.get(key_self), ptagset_other.get(key_self)
                if version_self and version_other:
                    parsed_version_self, parsed_version_other = version.parse(version_self), version.parse(version_other)
                    if parsed_version_self != parsed_version_other:
                        return parsed_version_self < parsed_version_other
        return len(ptagset_self) > len(ptagset_other)
