from __future__ import annotations

import logging
import types
import typing
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from copy import deepcopy
from typing import Any, Final, override

from pydantic import AliasChoices, BaseModel
from pydantic.fields import FieldInfo

from ai.backend.common.configs.loader.types import AbstractConfigLoader
from ai.backend.common.meta.meta import BackendAIConfigMeta
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

# A path step matches one of the key spellings of a field, or `ANY_KEY` for a dict key or a list item.
ANY_KEY: Final = None
type PathStep = frozenset[str] | None
type FieldPath = tuple[PathStep, ...]

_MAPPING_ORIGINS: Final = frozenset({dict, Mapping, MutableMapping})
_SEQUENCE_ORIGINS: Final = frozenset({list, tuple, set, frozenset, Sequence, MutableSequence})


def _nested_models(annotation: Any) -> list[tuple[int, type[BaseModel]]]:
    """Return the models in `annotation` with the number of dict/list levels above each."""
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return [(0, annotation)]
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin is typing.Annotated:
        return _nested_models(args[0])
    if origin is typing.Union or origin is types.UnionType:
        return [found for arg in args for found in _nested_models(arg)]
    if origin in _MAPPING_ORIGINS and len(args) == 2:
        return [(depth + 1, model) for depth, model in _nested_models(args[1])]
    if origin in _SEQUENCE_ORIGINS:
        return [(depth + 1, model) for arg in args for depth, model in _nested_models(arg)]
    return []


def _drop_path(node: Any, path: FieldPath, prefix: str, dropped: list[str]) -> None:
    step, rest = path[0], path[1:]
    if isinstance(node, MutableMapping):
        keys = list(node.keys()) if step is ANY_KEY else [k for k in node if k in step]
        children = [(f"{prefix}{key}", key) for key in keys]
    elif isinstance(node, MutableSequence) and step is ANY_KEY:
        children = [(f"{prefix}{index}", index) for index in range(len(node))]
    else:
        return
    for full_key, key in reversed(children):
        if not rest:
            del node[key]
            dropped.append(full_key)
        else:
            _drop_path(node[key], rest, f"{full_key}.", dropped)


class LocalOnlyFieldFilter(AbstractConfigLoader):
    """Wraps a remote loader such as etcd and drops the fields marked `local_only` in `model`."""

    _loader: AbstractConfigLoader
    _paths: tuple[FieldPath, ...]

    def __init__(self, loader: AbstractConfigLoader, model: type[BaseModel]) -> None:
        self._loader = loader
        self._paths = tuple(self._collect_paths(model, (), frozenset({model})))

    @override
    async def load(self) -> Mapping[str, Any]:
        config, dropped = self._drop_local_only_fields(await self._loader.load())
        if dropped:
            log.warning(
                "local-only config fields from a remote source are ignored",
                loader_name=self._loader.source_name,
                config_keys=",".join(dropped),
            )
        return config

    @property
    @override
    def source_name(self) -> str:
        return f"local-only-filtered:{self._loader.source_name}"

    def _field_keys(self, name: str, field_info: FieldInfo) -> frozenset[str]:
        keys = {name}
        for alias in (field_info.alias, field_info.serialization_alias):
            if alias is not None:
                keys.add(alias)
        match field_info.validation_alias:
            case str() as alias:
                keys.add(alias)
            case AliasChoices(choices=choices):
                keys.update(choice for choice in choices if isinstance(choice, str))
        return frozenset(keys)

    def _collect_paths(
        self, model: type[BaseModel], prefix: FieldPath, visiting: frozenset[type[BaseModel]]
    ) -> list[FieldPath]:
        paths: list[FieldPath] = []
        for name, field_info in model.model_fields.items():
            path = (*prefix, self._field_keys(name, field_info))
            meta = next(
                (m for m in field_info.metadata if isinstance(m, BackendAIConfigMeta)), None
            )
            if meta is not None and meta.local_only:
                paths.append(path)
                continue
            for depth, nested in _nested_models(field_info.annotation):
                if nested not in visiting:
                    nested_prefix = (*path, *([ANY_KEY] * depth))
                    paths.extend(self._collect_paths(nested, nested_prefix, visiting | {nested}))
        return paths

    def _drop_local_only_fields(
        self, raw_config: Mapping[str, Any]
    ) -> tuple[dict[str, Any], list[str]]:
        config = deepcopy(dict(raw_config))
        dropped: list[str] = []
        for path in self._paths:
            _drop_path(config, path, "", dropped)
        return config, sorted(dropped)
