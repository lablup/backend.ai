from __future__ import annotations

import json
from typing import Any, Callable, Mapping, Optional, Sequence, TypeVar

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.common.types import ResultSet

from .types import BaseOutputHandler, FieldSpec, PaginatedResult

_json_opts: Mapping[str, Any] = {"indent": 2}

T = TypeVar("T")


class JsonOutputHandler(BaseOutputHandler):
    def print_item(
        self,
        item: Mapping[str, Any] | None,
        fields: Sequence[FieldSpec],
    ) -> None:
        if item is None:
            print(
                json.dumps({
                    "count": 0,
                    "total_count": 0,
                    "items": [],
                })
            )
            return
        field_map = {f.field_name: f for f in fields}
        print(
            json.dumps(
                {
                    "count": 1,
                    "total_count": 1,
                    "items": [
                        {
                            field_map[k].alt_name: field_map[k].formatter.format_json(
                                v, field_map[k]
                            )
                            for k, v in item.items()
                            if k in field_map
                        },
                    ],
                },
                **_json_opts,
            )
        )

    def print_items(
        self,
        items: Sequence[Mapping[str, Any]],
        fields: Sequence[FieldSpec],
    ) -> None:
        field_map = {f.field_name: f for f in fields}
        print(
            json.dumps(
                {
                    "count": len(items),
                    "total_count": len(items),
                    "items": [
                        {
                            field_map[k].alt_name: field_map[k].formatter.format_json(
                                v, field_map[k]
                            )
                            for k, v in item.items()
                            if k in field_map
                        }
                        for item in items
                    ],
                },
                **_json_opts,
            )
        )

    def print_result_set(
        self,
        result_set: ResultSet,
    ) -> None:
        print(json.dumps(result_set))

    def print_list(
        self,
        items: Sequence[Mapping[str, Any]],
        fields: Sequence[FieldSpec],
        *,
        is_scalar: bool = False,
    ) -> None:
        if is_scalar:
            assert len(fields) == 1
            item_list = [
                {
                    fields[0].alt_name: fields[0].formatter.format_json(item, fields[0]),
                }
                for item in items
            ]
        else:
            field_map = {f.field_name: f for f in fields}
            item_list = [
                {
                    field_map[k].alt_name: field_map[k].formatter.format_json(v, field_map[k])
                    for k, v in item.items()
                    if k in field_map
                }
                for item in items
            ]
        print(
            json.dumps(
                {
                    "count": len(items),
                    "total_count": len(items),
                    "items": item_list,
                },
                **_json_opts,
            )
        )

    def print_paginated_list(
        self,
        fetch_func: Callable[[int, int], PaginatedResult],
        initial_page_offset: int,
        page_size: int = None,
        plain=False,
    ) -> None:
        page_size = page_size or 20
        result = fetch_func(initial_page_offset, page_size)
        field_map = {f.field_name: f for f in result.fields}
        print(
            json.dumps(
                {
                    "count": len(result.items),
                    "total_count": result.total_count,
                    "items": [
                        {
                            field_map[k].alt_name: field_map[k].formatter.format_json(
                                v, field_map[k]
                            )
                            for k, v in item.items()
                            if k in field_map
                        }
                        for item in result.items
                    ],
                },
                **_json_opts,
            )
        )

    def print_mutation_result(
        self,
        item: Mapping[str, Any],
        item_name: Optional[str] = None,
        action_name: Optional[str] = None,
        extra_info: Mapping = {},
    ) -> None:
        data = {
            "ok": item.get("ok", False),
            "msg": item.get("msg", "Failed"),
            **extra_info,
        }
        if item_name is not None and item_name in item:
            data = {
                **data,
                item_name: {k: v for k, v in item[item_name].items()},
            }
        print(
            json.dumps(
                data,
                **_json_opts,
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
        data = {
            "ok": False,
            "msg": msg,
            "item_name": item_name,
            "action_name": action_name,
            **extra_info,
        }
        if error is not None:
            data["error"] = str(error)
        print(
            json.dumps(
                data,
                **_json_opts,
            )
        )

    def print_error(
        self,
        error: Exception,
    ) -> None:
        match error:
            case BackendAPIError():
                print(
                    json.dumps(
                        {
                            "error": error.data["title"],
                            "api": {
                                "status": error.status,
                                "reason": error.reason,
                                **error.data,
                            },
                        },
                        **_json_opts,
                    )
                )
            case _:
                print(
                    json.dumps(
                        {
                            "error": str(error),
                        },
                        **_json_opts,
                    )
                )

    def print_fail(
        self,
        message: str,
    ) -> None:
        print(
            json.dumps(
                {
                    "error": message,
                },
                **_json_opts,
            )
        )
