from __future__ import annotations

import sys
from typing import Any, Callable, Iterator, List, Mapping, Optional, Sequence

from tabulate import tabulate

from ai.backend.client.cli.pagination import echo_via_pager, get_preferred_page_size, tabulate_items
from ai.backend.client.cli.pretty import print_done, print_error, print_fail
from ai.backend.common.types import ResultSet

from .types import BaseOutputHandler, FieldSpec, PaginatedResult

_Item = Mapping[str, Any]


class NoItems(Exception):
    pass


class ConsoleOutputHandler(BaseOutputHandler):
    def print_item(
        self,
        item: Optional[_Item],
        fields: Sequence[FieldSpec],
    ) -> None:
        if item is None:
            print_fail("No matching entry found.")
            return
        field_map = {f.field_name: f for f in fields}
        print(
            tabulate(
                [
                    (
                        field_map[k].humanized_name,
                        field_map[k].formatter.format_console(v, field_map[k]),
                    )
                    for k, v in item.items()
                    if k in field_map
                ],
                headers=("Field", "Value"),
            )
        )

    def print_items(
        self,
        items: Sequence[_Item],
        fields: Sequence[FieldSpec],
    ) -> None:
        field_map = {f.field_name: f for f in fields}
        for idx, item in enumerate(items):
            if idx > 0:
                print("-" * 20)
            print(
                tabulate(
                    [
                        (
                            field_map[k].humanized_name,
                            field_map[k].formatter.format_console(v, field_map[k]),
                        )
                        for k, v in item.items()
                        if k in field_map
                    ],
                    headers=("Field", "Value"),
                )
            )

    def print_result_set(
        self,
        result_set: ResultSet,
    ) -> None:
        if result_set["success"]:
            print_done("Successfully created:")
            print(
                tabulate(
                    map(lambda item: [item["item"]], result_set["success"]),
                    tablefmt="plain",
                )
            )
        if result_set["failed"]:
            print_fail("Failed to create:")
            print(
                tabulate(
                    map(lambda item: [item["item"], item["msg"]], result_set["failed"]),
                    tablefmt="plain",
                )
            )

    def print_list(
        self,
        items: Sequence[_Item],
        fields: Sequence[FieldSpec],
        *,
        is_scalar: bool = False,
    ) -> None:
        if is_scalar:
            assert len(fields) == 1
        if sys.stdout.isatty():

            def infinite_fetch():
                current_offset = 0
                page_size = get_preferred_page_size()
                while True:
                    if len(items) == 0:
                        raise NoItems
                    if is_scalar:
                        yield from map(
                            lambda v: {fields[0].field_name: v},
                            items[current_offset : current_offset + page_size],
                        )
                    else:
                        yield from items[current_offset : current_offset + page_size]
                    current_offset += page_size
                    if current_offset >= len(items):
                        break

            try:
                echo_via_pager(
                    tabulate_items(
                        infinite_fetch(),
                        fields,
                    ),
                )
            except NoItems:
                print("No matching items.")
        else:
            if is_scalar:
                for line in tabulate_items(
                    map(lambda v: {fields[0].field_name: v}, items),  # type: ignore
                    fields,
                ):
                    print(line, end="")
            else:
                for line in tabulate_items(
                    items,  # type: ignore
                    fields,
                ):
                    print(line, end="")

    def print_paginated_list(
        self,
        fetch_func: Callable[[int, int], PaginatedResult],
        initial_page_offset: int,
        page_size: Optional[int] = None,
        plain=False,
    ) -> None:
        fields: List[FieldSpec] = []

        def infinite_fetch(_page_size: int) -> Iterator[_Item]:
            nonlocal fields
            current_offset = initial_page_offset
            while True:
                result = fetch_func(current_offset, _page_size)
                if result.total_count == 0:
                    raise NoItems
                current_offset += len(result.items)
                if not fields:
                    fields.extend(result.fields)
                yield from result.items
                if current_offset >= result.total_count:
                    break

        if sys.stdout.isatty() and page_size is None:
            preferred_page_size = get_preferred_page_size()
            try:
                echo_via_pager(
                    tabulate_items(
                        infinite_fetch(preferred_page_size),
                        fields,
                        tablefmt="plain" if plain else "simple",
                    ),
                )
            except NoItems:
                print("No matching items.")
        else:
            if page_size is None:
                page_size = 20
            for line in tabulate_items(
                infinite_fetch(page_size),
                fields,
                tablefmt="plain" if plain else "simple",
            ):
                print(line, end="")

    def print_mutation_result(
        self,
        item: _Item,
        item_name: Optional[str] = None,
        action_name: Optional[str] = None,
        extra_info: Mapping = {},
    ) -> None:
        t = [
            ["ok", item["ok"]],
            ["msg", item["msg"]],
            *[(k, v) for k, v in extra_info.items()],
        ]
        if action_name is not None:
            t += [["Action", action_name]]
        if item_name is not None:
            t += [(k, v) for k, v in item[item_name].items()]
        print(
            tabulate(
                t,
                headers=("Field", "Value"),
            )
        )

    def print_mutation_error(
        self,
        error: Optional[Exception] = None,
        msg: str = "Failed",
        item_name: Optional[str] = None,
        action_name: Optional[str] = None,
        extra_info: Mapping = {},
    ) -> None:
        t = [
            ["Message", msg],
        ]
        if item_name is not None:
            t += [["Item", item_name]]
        if action_name is not None:
            t += [["Action", action_name]]
        print(
            tabulate(
                t,
                headers=("Field", "Value"),
            )
        )
        if error is not None:
            print_error(error)

    def print_error(
        self,
        error: Exception,
    ) -> None:
        print_error(error)

    def print_fail(
        self,
        message: str,
    ) -> None:
        print_fail(message)
