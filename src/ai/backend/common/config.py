from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import (
    Any, Optional, Union,
    Dict, Mapping, MutableMapping,
    Tuple,
    cast,
)

import toml
from toml.decoder import InlineTableDict
import trafaret as t

from . import validators as tx
from .etcd import AsyncEtcd, ConfigScopes
from .exception import ConfigurationError

__all__ = (
    'ConfigurationError',
    'etcd_config_iv',
    'redis_config_iv',
    'vfolder_config_iv',
    'read_from_file',
    'read_from_etcd',
    'override_key',
    'override_with_env',
    'check',
    'merge',
)


etcd_config_iv = t.Dict({
    t.Key('etcd'): t.Dict({
        t.Key('namespace'): t.String,
        t.Key('addr', ('127.0.0.1', 2379)): tx.HostPortPair,
        t.Key('user', default=''): t.Null | t.String(allow_blank=True),
        t.Key('password', default=''): t.Null | t.String(allow_blank=True),
    }).allow_extra('*'),
}).allow_extra('*')

redis_config_iv = t.Dict({
    t.Key('addr', default=('127.0.0.1', 6379)): tx.HostPortPair,
    t.Key('password', default=None): t.Null | t.String,
}).allow_extra('*')

vfolder_config_iv = t.Dict({
    tx.AliasedKey(['mount', '_mount'], default=None): t.Null | tx.Path(type='dir'),
    tx.AliasedKey(['fsprefix', '_fsprefix'], default=''):
        tx.Path(type='dir', resolve=False, relative_only=True, allow_nonexisting=True),
}).allow_extra('*')


def find_config_file(daemon_name: str) -> Path:
    toml_path_from_env = os.environ.get('BACKEND_CONFIG_FILE', None)
    if not toml_path_from_env:
        toml_paths = [
            Path.cwd() / f'{daemon_name}.toml',
        ]
        if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
            toml_paths += [
                Path.home() / '.config' / 'backend.ai' / f'{daemon_name}.toml',
                Path(f'/etc/backend.ai/{daemon_name}.toml'),
            ]
        else:
            raise ConfigurationError({
                'read_from_file()': f"Unsupported platform for config path auto-discovery: {sys.platform}",
            })
    else:
        toml_paths = [Path(toml_path_from_env)]
    for _path in toml_paths:
        if _path.is_file():
            return _path
    else:
        searched_paths = ','.join(map(str, toml_paths))
        raise ConfigurationError({
            'find_config_file()': f"Could not read config from: {searched_paths}",
        })


def read_from_file(toml_path: Optional[Union[Path, str]], daemon_name: str) -> Tuple[Dict[str, Any], Path]:
    config: Dict[str, Any]
    discovered_path: Path
    if toml_path is None:
        discovered_path = find_config_file(daemon_name)
    else:
        discovered_path = Path(toml_path)
    try:
        config = cast(Dict[str, Any], toml.loads(discovered_path.read_text()))
        config = _sanitize_inline_dicts(config)
    except IOError:
        raise ConfigurationError({
            'read_from_file()': f"Could not read config from: {discovered_path}",
        })
    else:
        return config, discovered_path


async def read_from_etcd(etcd_config: Mapping[str, Any],
                         scope_prefix_map: Mapping[ConfigScopes, str]) \
                        -> Optional[Dict[str, Any]]:
    etcd = AsyncEtcd(etcd_config['addr'], etcd_config['namespace'], scope_prefix_map)
    raw_value = await etcd.get('daemon/config')
    if raw_value is None:
        return None
    config: Dict[str, Any]
    config = cast(Dict[str, Any], toml.loads(raw_value))
    config = _sanitize_inline_dicts(config)
    return config


def override_key(table: MutableMapping[str, Any], key_path: Tuple[str, ...], value: Any):
    for k in key_path[:-1]:
        if k not in table:
            table[k] = {}
        table = table[k]
    table[key_path[-1]] = value


def override_with_env(table: MutableMapping[str, Any], key_path: Tuple[str, ...], env_key: str):
    val = os.environ.get(env_key, None)
    if val is None:
        return
    override_key(table, key_path, val)


def check(table: Any, iv: t.Trafaret):
    try:
        config = iv.check(table)
    except t.DataError as e:
        raise ConfigurationError(e.as_dict())
    else:
        return config


def merge(table: Mapping[str, Any], updates: Mapping[str, Any]) -> Mapping[str, Any]:
    result = {**table}
    for k, v in updates.items():
        if isinstance(v, Mapping):
            orig = result.get(k, {})
            assert isinstance(orig, Mapping)
            result[k] = merge(orig, v)
        else:
            result[k] = v
    return result


def _sanitize_inline_dicts(table: Dict[str, Any] | InlineTableDict) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    # Due to the way of toml.decoder to use Python class hierarchy to annotate
    # inline or non-inline tables of TOML, we need to skip type checking here.
    for k, v in table.items():  # type: ignore
        if isinstance(v, InlineTableDict):
            # Since this function always returns a copied dict,
            # this automatically converts InlineTableDict to dict.
            result[k] = _sanitize_inline_dicts(cast(Dict[str, Any], v))
        elif isinstance(v, Dict):
            result[k] = _sanitize_inline_dicts(v)
        else:
            result[k] = v
    return result
