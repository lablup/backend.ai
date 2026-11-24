import ast
from collections.abc import Iterator

from flake8_bai.rules.action_frozen import ActionFrozenRule
from flake8_bai.rules.action_pair import ActionPairRule
from flake8_bai.rules.admin_resolver_check import AdminResolverCheckRule
from flake8_bai.rules.appproxy_native_enum import AppProxyNativeEnumRule
from flake8_bai.rules.base import Rule, SourcePath
from flake8_bai.rules.cli_dto_import import CliDtoImportRule
from flake8_bai.rules.data_frozen import DataFrozenRule
from flake8_bai.rules.dto_conversion import DtoConversionRule
from flake8_bai.rules.dto_dataclass import DtoDataclassRule
from flake8_bai.rules.dto_schema_base import DtoSchemaBaseRule
from flake8_bai.rules.init_import import InitImportRule
from flake8_bai.rules.lazy_group_target import LazyGroupTargetRule
from flake8_bai.rules.storage_module_handler import StorageModuleHandlerRule


class Plugin:
    """flake8 entry point (`flake8.extension` in `tools/flake8-plugins/pyproject.toml`)."""

    rule_types: tuple[type[Rule], ...] = (
        InitImportRule,
        DataFrozenRule,
        ActionFrozenRule,
        ActionPairRule,
        DtoDataclassRule,
        DtoSchemaBaseRule,
        DtoConversionRule,
        CliDtoImportRule,
        LazyGroupTargetRule,
        AdminResolverCheckRule,
        StorageModuleHandlerRule,
        AppProxyNativeEnumRule,
    )

    _tree: ast.Module
    _path: SourcePath

    def __init__(self, tree: ast.Module, filename: str) -> None:
        self._tree = tree
        self._path = SourcePath(filename)

    def run(self) -> Iterator[tuple[int, int, str, type["Plugin"]]]:
        for rule_type in self.rule_types:
            rule = rule_type(self._path)
            if not rule.applies_to(self._path):
                continue
            for violation in rule.check(self._tree):
                message = f"{violation.code.code} {violation.code.message}"
                yield violation.line, violation.col, message, type(self)
