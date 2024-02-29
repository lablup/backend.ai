from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections import UserDict
from typing import TYPE_CHECKING, Any, Callable, Generic, Mapping, Optional, Sequence, TypeVar

import attr

from ai.backend.common.types import ResultSet

if TYPE_CHECKING:
    from ai.backend.client.cli.types import CLIContext


_predefined_humanized_field_names = {
    "id": "ID",
    "uuid": "UUID",
    "group_id": "Group ID",
    "user_id": "User ID",
    "resource_policy": "Res.Policy",
    "concurrency_used": "Concur.Used",
    "fsprefix": "FS Prefix",
    "hardware_metadata": "HW Metadata",
    "performance_metric": "Perf.Metric",
}


def _make_camel_case(name: str) -> str:
    return " ".join(
        map(lambda s: s[0].upper() + s[1:], name.split("_")),
    )


class AbstractOutputFormatter(metaclass=ABCMeta):
    """
    The base implementation of output formats.
    """

    @abstractmethod
    def format_console(self, value: Any, field: FieldSpec) -> str:
        raise NotImplementedError

    @abstractmethod
    def format_json(self, value: Any, field: FieldSpec) -> Any:
        raise NotImplementedError


@attr.define(slots=True, frozen=True)
class FieldSpec:
    """
    The specification on how to represent a GraphQL object field
    in the functional API and CLI output handlers.

    Attributes:
        field_ref: The string to be interpolated inside GraphQL queries.
            It may contain sub-fields if the queried field supports.
        humanized_name: The string to be shown as the field name by the console formatter.
            If not set, it's auto-generated from field_name by camel-casing it and checking
            a predefined humanization mapping.
        field_name: The exact field name slug.  If not set, it's taken from field_ref.
        alt_name: The field name slug to refer the field inside a FieldSet object hosting
            this FieldSpec instance.
        formatter: The formatter instance which provide per-output-type format methods.
            (console and json)
        subfields: A FieldSet instance to represent sub-fields in the GraphQL schema.
            If set, field_ref is Automatically updated to have the braced subfield list
            for actual GraphQL queries.
    """

    field_ref: str = attr.field()
    humanized_name: str = attr.field()
    field_name: str = attr.field()
    alt_name: str = attr.field()
    formatter: AbstractOutputFormatter = attr.field()
    subfields: FieldSet = attr.field(factory=lambda: FieldSet([]))

    def __attrs_post_init__(self) -> None:
        if self.subfields:
            subfields = " ".join(f.field_ref for f in self.subfields.values())
            object.__setattr__(self, "field_ref", f"{self.field_name} {{ {subfields} }}")

    @humanized_name.default
    def _autogen_humanized_name(self) -> str:
        # to handle cases like "groups { id name }", "user_info { full_name }"
        field_name = self.field_ref.partition(" ")[0]
        if h := _predefined_humanized_field_names.get(field_name):
            return h
        if field_name.startswith("is_"):
            return _make_camel_case(field_name[3:]) + "?"
        return _make_camel_case(field_name)

    @field_name.default
    def _default_field_name(self) -> str:
        return self.field_ref.partition(" ")[0]

    @alt_name.default
    def _default_alt_name(self) -> str:
        return self.field_ref.partition(" ")[0]

    @formatter.default
    def _default_formatter(self) -> AbstractOutputFormatter:
        from .formatters import default_output_formatter  # avoid circular import

        return default_output_formatter


class FieldSet(UserDict, Mapping[str, FieldSpec]):
    def __init__(self, fields: Sequence[FieldSpec]) -> None:
        fields_set = {f.alt_name: f for f in fields}
        fields_set.update({f.field_ref: fields_set[f.alt_name] for f in fields})
        super().__init__(fields_set)


T = TypeVar("T")


@attr.define(slots=True)
class PaginatedResult(Generic[T]):
    total_count: int
    items: Sequence[T]
    fields: Sequence[FieldSpec]


class BaseOutputHandler(metaclass=ABCMeta):
    def __init__(self, cli_context: CLIContext) -> None:
        self.ctx = cli_context

    @abstractmethod
    def print_item(
        self,
        item: Mapping[str, Any] | None,
        fields: Sequence[FieldSpec],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_items(
        self,
        items: Sequence[Mapping[str, Any]],
        fields: Sequence[FieldSpec],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_result_set(
        self,
        result_set: ResultSet,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_list(
        self,
        items: Sequence[Mapping[str, Any]],
        fields: Sequence[FieldSpec],
        *,
        is_scalar: bool = False,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_paginated_list(
        self,
        fetch_func: Callable[[int, int], PaginatedResult[T]],
        initial_page_offset: int,
        page_size: int = None,
        plain: bool = False,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_mutation_result(
        self,
        item: Mapping[str, Any],
        item_name: Optional[str] = None,
        action_name: Optional[str] = None,
        extra_info: Mapping = {},
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_mutation_error(
        self,
        error: Optional[Exception] = None,
        msg: str = "Failed",
        item_name: Optional[str] = None,
        action_name: Optional[str] = None,
        extra_info: Mapping = {},
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_error(
        self,
        error: Exception,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_fail(
        self,
        message: str,
    ) -> None:
        raise NotImplementedError
